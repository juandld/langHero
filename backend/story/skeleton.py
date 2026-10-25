"""
Story Skeleton System — Anchor-based story structure.

Stories are defined as a sequence of Anchors (key story beats) with
AI-generated bridge content (Segments) filling the gaps between them.

Anchors can be:
- linear: simple story progression
- branch_point: player choice diverges the story
- reputation_gate: story path depends on accumulated reputation
- convergence: where divergent branches re-merge
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LearningObjective:
    """What the player should learn in this segment."""
    vocabulary: list[str] = field(default_factory=list)     # ["arigatou", "sumimasen"]
    grammar: list[str] = field(default_factory=list)        # ["X wa Y desu", "kara (from)"]
    cultural: list[str] = field(default_factory=list)       # ["bowing", "honorifics"]
    difficulty: str = "beginner"                             # beginner/elementary/intermediate/advanced


@dataclass
class StoryCategory:
    """A response category for this story (not all stories use the same set)."""
    key: str            # "diplomatic"
    label: str          # "Diplomatic"
    color: str          # "#86efac"
    icon: str           # emoji icon
    description: str = ""


@dataclass
class BranchConfig:
    """Configuration for a branch_point anchor."""
    category_outcomes: dict = field(default_factory=dict)
    # { "diplomatic": { "next_anchor": "...", "life_delta": 0, "reputation_delta": {...} }, ... }
    default_outcome: dict = field(default_factory=dict)
    # { "next_anchor": "...", "life_delta": 0, "reputation_delta": {...} }


@dataclass
class ReputationGateConfig:
    """Configuration for a reputation_gate anchor."""
    category: str = ""              # Which reputation category to check
    threshold: int = 0              # Minimum value to pass
    pass_anchor: str = ""           # Anchor ID if gate passes
    fail_anchor: str = ""           # Anchor ID if gate fails


@dataclass
class Anchor:
    """A mandatory story beat — the structural spine of the story."""
    id: str                                         # "ch01_branch_firstwords"
    chapter: str                                    # "ch01"
    title: str                                      # "First Words on the Beach"
    type: str = "linear"                            # linear | branch_point | reputation_gate | convergence

    # Content — hand-written panels use the same format as generated ones
    panels: list[dict] = field(default_factory=list)
    generation_hint: str = ""                       # Prose hint for AI bridge generation

    # Context
    location: str = ""                              # Location ID
    characters: list[str] = field(default_factory=list)
    mood: str = ""                                  # "tense", "warm", etc.
    learning: Optional[LearningObjective] = None

    # Branching (branch_point only)
    branch_config: Optional[BranchConfig] = None

    # Reputation gate (reputation_gate only)
    gate_config: Optional[ReputationGateConfig] = None

    # Sequencing
    next_anchor: Optional[str] = None               # Explicit next (None = sequential)
    convergence_anchor: Optional[str] = None         # Where branches re-merge


@dataclass
class ChapterDef:
    """Chapter definition within a skeleton."""
    id: str                 # "ch01"
    title: str              # "Chapter 1: The Beach"
    anchor_ids: list[str] = field(default_factory=list)


@dataclass
class StorySkeleton:
    """The complete structural definition of a story."""
    id: str
    title: str
    subtitle: str = ""
    setting: str = ""                   # "Sengoku Japan, 1600"
    target_language: str = "Japanese"
    tone: str = ""                      # "cinematic, literary, tense"

    # Per-story response categories
    categories: list[StoryCategory] = field(default_factory=list)

    # Style-to-category mapping for this story
    style_to_category: dict = field(default_factory=dict)

    # Characters and locations (references, not full definitions)
    character_ids: list[str] = field(default_factory=list)
    location_ids: list[str] = field(default_factory=list)

    # Story structure
    anchors: list[Anchor] = field(default_factory=list)
    chapters: list[ChapterDef] = field(default_factory=list)

    # Meta-narrative notes (for generation context)
    meta_narrative: str = ""

    # UI chrome: '' = follow the learner's narration-language setting (English default); 'es' = Spanish-immersion
    ui_lang: str = ""
    # The in-game guide shown in the assistant bubble / hint label (Bimbo by default)
    assistant: dict = field(default_factory=lambda: {"name": "Bimbo", "title": "", "avatar": ""})

    def get_anchor(self, anchor_id: str) -> Optional[Anchor]:
        """Find an anchor by ID."""
        for a in self.anchors:
            if a.id == anchor_id:
                return a
        return None

    def get_chapter(self, chapter_id: str) -> Optional[ChapterDef]:
        """Find a chapter definition by ID."""
        for ch in self.chapters:
            if ch.id == chapter_id:
                return ch
        return None

    def get_chapter_anchors(self, chapter_id: str) -> list[Anchor]:
        """Get all anchors for a chapter, in order."""
        ch = self.get_chapter(chapter_id)
        if not ch:
            return []
        return [a for a in self.anchors if a.id in ch.anchor_ids]

    def get_anchor_pair(self, anchor_id: str) -> tuple[Optional[Anchor], Optional[Anchor]]:
        """Get an anchor and its next anchor (for segment generation)."""
        anchor = self.get_anchor(anchor_id)
        if not anchor:
            return None, None

        if anchor.next_anchor:
            return anchor, self.get_anchor(anchor.next_anchor)

        # Find sequential next
        for i, a in enumerate(self.anchors):
            if a.id == anchor_id and i + 1 < len(self.anchors):
                return anchor, self.anchors[i + 1]

        return anchor, None

    def to_api_response(self) -> dict:
        """Serialize skeleton for the /skeleton API (lightweight, no panel content)."""
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "setting": self.setting,
            "target_language": self.target_language,
            "tone": self.tone,
            "categories": [
                {
                    "key": c.key,
                    "label": c.label,
                    "color": c.color,
                    "icon": c.icon,
                    "description": c.description,
                }
                for c in self.categories
            ],
            "style_to_category": self.style_to_category,
            "chapters": [
                {
                    "id": ch.id,
                    "title": ch.title,
                    "anchor_ids": ch.anchor_ids,
                }
                for ch in self.chapters
            ],
            "anchors": [
                {
                    "id": a.id,
                    "chapter": a.chapter,
                    "title": a.title,
                    "type": a.type,
                    "location": a.location,
                    "characters": a.characters,
                    "mood": a.mood,
                    "has_panels": len(a.panels) > 0,
                    "has_generation_hint": bool(a.generation_hint),
                    "next_anchor": a.next_anchor,
                    "convergence_anchor": a.convergence_anchor,
                    "learning": {
                        "vocabulary": a.learning.vocabulary,
                        "grammar": a.learning.grammar,
                        "cultural": a.learning.cultural,
                        "difficulty": a.learning.difficulty,
                    } if a.learning else None,
                    "branch_config": {
                        "categories": list(a.branch_config.category_outcomes.keys()),
                    } if a.branch_config else None,
                    "gate_config": {
                        "category": a.gate_config.category,
                        "threshold": a.gate_config.threshold,
                    } if a.gate_config else None,
                }
                for a in self.anchors
            ],
        }
