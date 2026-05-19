"""
JOURNEY TO THE WEST — Tang Dynasty China, 627 AD

The player is a foreign pilgrim traveling west with a ragtag band of
companions. Learning Mandarin Chinese to survive bandits, spirits, and
the politics of the Silk Road. Bimbo (AI companion) can freeze time
to teach vocabulary.

Inspired by 西游记 (Xī Yóu Jì) — Journey to the West.
"""

import os
import asyncio
from story.manifest import Character, Location, PanelSpec, get_panel_references
from story.skeleton import (
    StorySkeleton, Anchor, ChapterDef, BranchConfig, ReputationGateConfig,
    LearningObjective, StoryCategory,
)
from image.google import generate_character_ref, generate_location_ref

# Paths
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "image_cache")
CHARACTER_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "characters")
LOCATION_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "locations")


# ============================================================
# STORY METADATA
# ============================================================

STORY_ID = "journey_west"
STORY_TITLE = "The Monkey King's Road"
STORY_SUBTITLE = "Tang Dynasty China, 627 AD"


# ============================================================
# CHARACTERS
# ============================================================

CHARACTERS = {
    "bimbo": Character(
        id="bimbo",
        name="Bimbo",
        description="Young woman AI hologram. Long straight hair with purple-to-cyan gradient (purple at roots, cyan at tips). Warm friendly expression. Soft holographic glow emanating from her form. Floating particles trail behind her. Manhwa style with large expressive eyes.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "bimbo.png"),
        variants={
            "teaching": os.path.join(CHARACTER_REF_DIR, "bimbo_teaching.png"),
            "casual": os.path.join(CHARACTER_REF_DIR, "bimbo_casual.png"),
            "danger": os.path.join(CHARACTER_REF_DIR, "bimbo_danger.png"),
        }
    ),

    "wukong": Character(
        id="wukong",
        name="Sun Wukong (孙悟空)",
        description="The Monkey King. Lean muscular figure with golden-furred monkey features but humanoid body. Wild golden eyes, sharp canines visible in grin. Wears golden chainmail over red silk. Golden phoenix-feather cap (紧箍咒 headband visible). Carries a red-tasseled iron staff (如意金箍棒). Mischievous, dangerous, charismatic. Manhwa style, dynamic poses.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "wukong.png"),
    ),

    "sanzang": Character(
        id="sanzang",
        name="Tang Sanzang (唐三藏)",
        description="Buddhist monk, 30s. Serene handsome face with shaved head. Wears elaborate golden kasaya robe over white robes. Carries prayer beads and a monk's staff with rings. Gentle but resolute expression. He radiates calm authority. Tang Dynasty Buddhist monk aesthetic.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "sanzang.png"),
    ),

    "bajie": Character(
        id="bajie",
        name="Zhu Bajie (猪八戒)",
        description="Half-pig half-man, heavyset and round. Pig snout, floppy ears, but wears human monk robes loosely. Carries a nine-toothed rake (九齿钉耙). Lazy grin, always eating or thinking about food. Comic relief but surprisingly strong. Manhwa style, exaggerated expressions.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "bajie.png"),
    ),

    "wujing": Character(
        id="wujing",
        name="Sha Wujing (沙悟净)",
        description="River spirit turned monk. Tall, blue-tinged skin, calm stoic expression. Wears prayer beads as necklace — nine skulls. Simple brown monk robes. Carries a crescent-moon spade (降妖宝杖). Quiet, dependable, loyal. Most human-looking of the companions.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "wujing.png"),
    ),

    "innkeeper": Character(
        id="innkeeper",
        name="Innkeeper Chen",
        description="Middle-aged Chinese innkeeper, Tang Dynasty. Round face, shrewd eyes, ready smile. Wears simple merchant clothes with an apron. Wiping hands on cloth. Warm but calculating.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "innkeeper_chen.png"),
    ),

    "bandit_chief": Character(
        id="bandit_chief",
        name="Bandit Chief",
        description="Mountain bandit leader, 40s. Scarred face, missing ear. Leather armor over rough clothes. Two swords crossed on back. Commanding presence. Dangerous smile.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "bandit_chief.png"),
    ),

    "jade_spirit": Character(
        id="jade_spirit",
        name="Jade Spirit (玉灵)",
        description="Beautiful female spirit. Semi-transparent, glowing with pale green jade light. Long flowing black hair that moves like water. Traditional Tang Dynasty hanfu dress in white and jade green. Ethereal, mysterious, not entirely trustworthy.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "jade_spirit.png"),
    ),

    "magistrate": Character(
        id="magistrate",
        name="Magistrate Wang",
        description="Tang Dynasty magistrate. Official black gauze cap (乌纱帽). Formal green official robes. Thin mustache, sharp eyes behind scholarly composure. Holds a folding fan. Powerful but cautious.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "magistrate_wang.png"),
    ),

    "tea_master": Character(
        id="tea_master",
        name="Master Lü",
        description="Old tea master, 70s. Wispy white beard, calm eyes that have seen everything. Simple gray Taoist robes. Weathered hands that move with precision. Sits in perpetual stillness until he moves, and then moves like water.",
        reference_path=os.path.join(CHARACTER_REF_DIR, "tea_master_lu.png"),
    ),
}


# ============================================================
# LOCATIONS
# ============================================================

LOCATIONS = {
    "ship_observation": Location(
        id="ship_observation",
        name="Spaceship Observation Deck",
        description="Spaceship observation deck. Wide curved window showing infinite stars and void of space. Purple and cyan ambient lighting. Minimalist futuristic furniture. Contemplative atmosphere.",
        reference_path=os.path.join(LOCATION_REF_DIR, "ship_observation.png"),
    ),

    "mountain_pass": Location(
        id="mountain_pass",
        name="Mountain Pass",
        description="Narrow mountain pass in Tang Dynasty China. Steep cliff on one side, drop on the other. Mist swirling below. Ancient stone path worn smooth by centuries of travelers. Silk Road atmosphere.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_mountain_pass.png"),
    ),

    "roadside_inn": Location(
        id="roadside_inn",
        name="Roadside Inn",
        description="Tang Dynasty roadside inn. Warm lantern light spilling from wooden doors. Red paper lanterns hanging from eaves. Horses tied outside. Smoke rising from kitchen. Inviting but isolated.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_roadside_inn.png"),
    ),

    "bamboo_forest": Location(
        id="bamboo_forest",
        name="Bamboo Forest",
        description="Dense bamboo forest. Tall green bamboo stalks creating a cathedral of green light. Narrow path winding through. Mist and filtered sunlight. Peaceful but something watching from the shadows.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_bamboo_forest.png"),
    ),

    "river_crossing": Location(
        id="river_crossing",
        name="River Crossing",
        description="Wide river with an ancient wooden ferry. Mountains reflected in still water. Tang Dynasty boats with square sails. Dawn light. A ferryman waits.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_river_crossing.png"),
    ),

    "temple_mountain": Location(
        id="temple_mountain",
        name="Mountain Temple",
        description="Buddhist temple perched on a mountain cliff. Red and gold pagoda structure. Incense smoke rising. Stone steps carved into the mountain. Clouds below. Serene and ancient.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_temple_mountain.png"),
    ),

    "market_town": Location(
        id="market_town",
        name="Silk Road Market Town",
        description="Bustling Tang Dynasty market town on the Silk Road. Merchants from many lands. Silk, spices, pottery on display. Camels and horses. Colorful awnings. Multicultural chaos.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_market_town.png"),
    ),

    "bandit_camp": Location(
        id="bandit_camp",
        name="Mountain Bandit Camp",
        description="Hidden camp in a mountain valley. Rough tents and stolen goods. Campfire smoke. Lookout posts on ridges. Dangerous but organized.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_bandit_camp.png"),
    ),

    "spirit_cave": Location(
        id="spirit_cave",
        name="Spirit Cave",
        description="Luminous cave interior. Jade-colored light emanating from walls. Underground pool of still water reflecting strange stars. Ancient Chinese characters carved into stone. Otherworldly, beautiful, dangerous.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_spirit_cave.png"),
    ),

    "tea_house": Location(
        id="tea_house",
        name="Mountain Tea House",
        description="Small tea house on a cliff edge overlooking clouds. Simple wooden structure with open sides. Low tables, ceramic tea sets. Wind chimes. Peace above the world.",
        reference_path=os.path.join(LOCATION_REF_DIR, "jw_tea_house.png"),
    ),
}


# ============================================================
# PANELS — PROLOGUE + CHAPTER 1
# ============================================================

PANELS = [
    # === PROLOGUE ===
    PanelSpec(
        id="jw_pro_01_stars",
        chapter="prologue",
        panel_type="establishing",
        description="POV looking out through the curved observation window. The infinite void of space. You are alone with your thoughts, about to choose a new simulation.",
        characters=[],
        location="ship_observation",
        mood="contemplative",
        is_holographic=True,
    ),

    PanelSpec(
        id="jw_pro_02_bimbo",
        chapter="prologue",
        panel_type="dialogue",
        description="POV looking at Bimbo floating before you. She looks directly at the viewer with excitement. Stars visible behind her. She's about to offer a new world.",
        characters=["bimbo"],
        location="ship_observation",
        speaker="bimbo",
        mood="excited",
        is_holographic=True,
    ),

    PanelSpec(
        id="jw_pro_03_china",
        chapter="prologue",
        panel_type="emotional",
        description="Holographic projection of ancient China materializing. Mountains, rivers, the Silk Road stretching into distance. Bimbo gestures at it with pride. The world is forming around you.",
        characters=["bimbo"],
        location="ship_observation",
        speaker="bimbo",
        mood="wonder",
        is_holographic=True,
    ),

    # === CHAPTER 1: THE MOUNTAIN PASS ===
    PanelSpec(
        id="jw_ch1_01_wake",
        chapter="ch01",
        panel_type="pov",
        description="POV waking on a narrow mountain path. Clouds below you, peaks above. You're sitting against a rock wall, dressed in simple Tang Dynasty traveler clothes. Your pack is beside you.",
        characters=[],
        location="mountain_pass",
        mood="disoriented",
    ),

    PanelSpec(
        id="jw_ch1_02_wukong",
        chapter="ch01",
        panel_type="action",
        description="POV looking up at Sun Wukong perched on a rock above you. He's crouched like a monkey, golden staff across his shoulders, grinning down with sharp canines. Backlit by sunrise. Magnificent and terrifying.",
        characters=["wukong"],
        location="mountain_pass",
        speaker="wukong",
        mood="mischievous",
    ),

    PanelSpec(
        id="jw_ch1_03_freeze",
        chapter="ch01",
        panel_type="time_freeze",
        description="POV of the mountain scene FROZEN. Wukong frozen mid-leap. Clouds stopped. Bimbo appears in warm color, explaining urgently.",
        characters=["bimbo", "wukong"],
        location="mountain_pass",
        is_time_freeze=True,
    ),

    PanelSpec(
        id="jw_ch1_04_teach",
        chapter="ch01",
        panel_type="dialogue",
        description="POV looking at Bimbo in teaching mode. She faces you with patient expression. Holographic Chinese characters float around her: 你好 (nǐ hǎo), 我是 (wǒ shì). Frozen mountain background.",
        characters=["bimbo"],
        location="mountain_pass",
        speaker="bimbo",
        is_time_freeze=True,
        is_holographic=True,
    ),

    PanelSpec(
        id="jw_ch1_05_speak",
        chapter="ch01",
        panel_type="dialogue",
        description="POV seeing Wukong react to your words. His grin shifts from predatory to amused. He tilts his head like a curious animal. Your hands visible in surrender gesture.",
        characters=["wukong"],
        location="mountain_pass",
        mood="surprised",
    ),

    PanelSpec(
        id="jw_ch1_06_group",
        chapter="ch01",
        panel_type="establishing",
        description="POV following Wukong down the mountain path. Sanzang visible ahead on the path with Bajie and Wujing. The pilgrim group. Mountains and clouds around them. You are joining the journey.",
        characters=["wukong", "sanzang", "bajie", "wujing"],
        location="mountain_pass",
        mood="adventure",
    ),
]


# ============================================================
# STORY SKELETON
# ============================================================

IMAGE_BASE_URL = "/images/generated"

JOURNEY_CATEGORIES = [
    StoryCategory(key="diplomatic", label="Respectful (礼)", color="#86efac", icon="🕊", description="Words that honor"),
    StoryCategory(key="pragmatic", label="Clever (智)", color="#93c5fd", icon="⚖", description="Words that solve"),
    StoryCategory(key="bold", label="Bold (勇)", color="#fdba74", icon="⚡", description="Words that dare"),
    StoryCategory(key="trickster", label="Trickster (猴)", color="#fca5a5", icon="🐵", description="Words that deceive"),
    StoryCategory(key="enlightened", label="Enlightened (悟)", color="#e9d5ff", icon="✦", description="Words that see truth"),
]

JOURNEY_STYLE_TO_CATEGORY = {
    "polite": "diplomatic", "humble": "diplomatic", "respectful": "diplomatic", "formal": "diplomatic",
    "cautious": "pragmatic", "honest": "pragmatic", "practical": "pragmatic", "safe": "pragmatic",
    "direct": "bold", "bold": "bold", "brave": "bold", "confrontational": "bold",
    "sly": "trickster", "deceptive": "trickster", "cunning": "trickster", "playful": "trickster",
    "insightful": "enlightened", "compassionate": "enlightened", "philosophical": "enlightened",
}

JOURNEY_SKELETON = StorySkeleton(
    id=STORY_ID,
    title=STORY_TITLE,
    subtitle=STORY_SUBTITLE,
    setting="Tang Dynasty China, 627 AD — the Silk Road westward, inspired by Journey to the West",
    target_language="Mandarin Chinese",
    tone="Epic, mythological, vivid. Beauty and danger on the ancient road. Words unlock doors and defeat demons.",
    categories=JOURNEY_CATEGORIES,
    style_to_category=JOURNEY_STYLE_TO_CATEGORY,
    character_ids=list(CHARACTERS.keys()),
    location_ids=list(LOCATIONS.keys()),
    meta_narrative=(
        "Ch01-03: Meeting companions, learning basic survival Mandarin on the road. Bimbo as guide. "
        "Ch04-06: First real dangers — bandits, spirits. Language saves your life. "
        "Ch07-09: Deeper into China. Court politics, market bargaining, reading people. "
        "Ch10-12: The road grows strange. Spirit world bleeds through. Ancient Chinese unlocks power. "
        "Ch13-15: The destination. What you learned matters more than where you arrived."
    ),

    chapters=[
        ChapterDef(id="prologue", title="Prologue: The Ship", anchor_ids=["jw_pro_ship", "jw_pro_immersion"]),
        ChapterDef(id="ch01", title="Chapter 1: The Mountain Pass", anchor_ids=["jw_ch01_wake", "jw_ch01_branch_greeting", "jw_ch01_join", "jw_ch01_road"]),
        ChapterDef(id="ch02", title="Chapter 2: The Inn", anchor_ids=["jw_ch02_arrive", "jw_ch02_order_food", "jw_ch02_bajie_trouble", "jw_ch02_night"]),
        ChapterDef(id="ch03", title="Chapter 3: River Crossing", anchor_ids=["jw_ch03_ferry", "jw_ch03_wujing_lesson", "jw_ch03_storm", "jw_ch03_shore"]),
        ChapterDef(id="ch04", title="Chapter 4: The Bandits", anchor_ids=["jw_ch04_ambush", "jw_ch04_branch_negotiate", "jw_ch04_aftermath"]),
        ChapterDef(id="ch05", title="Chapter 5: Market Town", anchor_ids=["jw_ch05_market", "jw_ch05_merchant", "jw_ch05_magistrate", "jw_ch05_depart"]),
        ChapterDef(id="ch06", title="Chapter 6: The Spirit Cave", anchor_ids=["jw_ch06_cave", "jw_ch06_jade_spirit", "jw_ch06_branch_trust", "jw_ch06_escape"]),
        ChapterDef(id="ch07", title="Chapter 7: The Tea Master", anchor_ids=["jw_ch07_tea_house", "jw_ch07_lesson", "jw_ch07_wisdom"]),
        ChapterDef(id="ch08", title="Chapter 8: The Temple", anchor_ids=["jw_ch08_arrive", "jw_ch08_meditation", "jw_ch08_test"]),
    ],

    anchors=[
        # ────────────────────────────────────────────
        # PROLOGUE
        # ────────────────────────────────────────────
        Anchor(
            id="jw_pro_ship",
            chapter="prologue",
            title="Stars and Choices",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="contemplative",
            panels=[
                {
                    "id": "jw_pro_01_stars",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_prologue/jw_pro_01_stars.png",
                    "aspect": "wide",
                    "narration": "The observation deck is quiet. You've finished the Japan simulation — survived samurai, learned to bow at the right depth, spoke words that kept your head attached. But something is pulling you further east. Or is it west?",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "jw_pro_02_bimbo",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_prologue/jw_pro_02_bimbo.png",
                    "aspect": "square",
                    "narration": "Bimbo materializes with a different energy today. She's excited, particles spinning faster than usual.",
                    "dialogue": "I found something incredible. Tang Dynasty China. 627 AD. The year a monk named Xuanzang walked west to India for Buddhist scriptures. But in the legends... he had companions. A monkey god. A pig spirit. A river demon.",
                    "speaker": "bimbo",
                },
            ],
        ),

        Anchor(
            id="jw_pro_immersion",
            chapter="prologue",
            title="The Road West",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="excited",
            panels=[
                {
                    "id": "jw_pro_03_pitch",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_prologue/jw_pro_03_china.png",
                    "aspect": "wide",
                    "narration": "A holographic map of ancient China blooms between you. The Silk Road stretches west like a golden thread through mountains and deserts. Cities glow like embers.",
                    "dialogue": "You'll join the pilgrimage as a foreign traveler. No one speaks your language. The only way forward is Mandarin. And the companions... they're not exactly patient teachers.",
                    "speaker": "bimbo",
                },
                {
                    "id": "jw_pro_04_go",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_prologue/jw_pro_03_china.png",
                    "aspect": "square",
                    "narration": "You reach toward the holographic mountains. They feel almost warm.",
                    "dialogue": "Send me in.",
                    "speaker": "player",
                },
            ],
        ),

        # ────────────────────────────────────────────
        # CHAPTER 1: The Mountain Pass
        # ────────────────────────────────────────────
        Anchor(
            id="jw_ch01_wake",
            chapter="ch01",
            title="Mountain Dawn",
            type="linear",
            location="mountain_pass",
            characters=["wukong"],
            mood="disoriented",
            learning=LearningObjective(
                vocabulary=["nǐ hǎo (hello)", "wǒ shì (I am)", "shéi (who)", "péngyou (friend)"],
                grammar=["wǒ shì X (I am X)", "nǐ shì shéi (who are you)"],
                cultural=["Greetings establish hierarchy — how you address someone matters"],
                difficulty="beginner",
            ),
            panels=[
                {
                    "id": "jw_ch1_01_wake",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_01_wake.png",
                    "aspect": "wide",
                    "narration": "Wind. Cold thin air. You open your eyes to a sky so blue it hurts. You're sitting against a rock wall on a mountain path barely wide enough for two people. Clouds drift below you like slow rivers. Your clothes are rough cotton — a traveler's clothes from another century.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "jw_ch1_01b_sound",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_01_wake.png",
                    "aspect": "wide",
                    "narration": "A sound above you. Scraping stone. Something — someone — is perched on the rock overhead. You hear breathing. And then a laugh, high and sharp like cracking ice.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "jw_ch1_02_wukong",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_02_wukong.png",
                    "aspect": "tall",
                    "narration": "He drops into your field of vision — crouched on a boulder like a predator at rest. Golden fur. Golden eyes. A staff of iron across his shoulders, red tassel swinging. He grins, and the grin has too many teeth.",
                    "dialogue": "「你是谁？」",
                    "speaker": "wukong",
                },
                {
                    "id": "jw_ch1_03_freeze",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_03_freeze.png",
                    "aspect": "tall",
                    "narration": "The world stops. The wind dies. Wukong's grin freezes mid-curl. Even the clouds pause. Bimbo's voice, close and warm:",
                    "dialogue": "Don't panic. That's Sun Wukong — the Monkey King. He just asked who you are. Answer wrong and he might decide you're not worth keeping alive. Answer right... and you might have the most powerful ally on the Silk Road.",
                    "speaker": "bimbo",
                },
            ],
        ),

        Anchor(
            id="jw_ch01_branch_greeting",
            chapter="ch01",
            title="First Words (B1)",
            type="branch_point",
            location="mountain_pass",
            characters=["bimbo", "wukong"],
            mood="tense",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":  {"next_anchor": "jw_ch01_join", "life_delta": 0, "reputation_delta": {"diplomatic": 1}},
                    "pragmatic":   {"next_anchor": "jw_ch01_join", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "bold":        {"next_anchor": "jw_ch01_join", "life_delta": 0, "reputation_delta": {"bold": 1}},
                    "trickster":   {"next_anchor": "jw_ch01_join", "life_delta": -1, "reputation_delta": {"trickster": 1}},
                    "enlightened": {"next_anchor": "jw_ch01_join", "life_delta": 0, "reputation_delta": {"enlightened": 2}},
                },
                default_outcome={"next_anchor": "jw_ch01_join", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="jw_ch01_join",
            panels=[
                {
                    "id": "jw_ch1_04_teach",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_04_teach.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "He asked 你是谁 — 'nǐ shì shéi' — who are you? You need to introduce yourself. Say 我是... — 'wǒ shì...' — I am...",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":  {"next_panel": "jw_ch1_05_speak", "life_delta": 0, "reputation_delta": {"diplomatic": 1}},
                        "pragmatic":   {"next_panel": "jw_ch1_05_speak", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                        "bold":        {"next_panel": "jw_ch1_05_speak", "life_delta": 0, "reputation_delta": {"bold": 1}},
                        "trickster":   {"next_panel": "jw_ch1_05_speak", "life_delta": -1, "reputation_delta": {"trickster": 1}},
                        "enlightened": {"next_panel": "jw_ch1_05_speak", "life_delta": 0, "reputation_delta": {"enlightened": 2}},
                    },
                    "default_outcome": {"next_panel": "jw_ch1_05_speak", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {"text": "我是朋友。(I am a friend.)", "style": "polite", "keywords": ["朋友", "péngyou", "friend"]},
                        {"text": "我是旅人。(I am a traveler.)", "style": "honest", "keywords": ["旅人", "lǚrén", "traveler"]},
                        {"text": "你管我呢！(None of your business!)", "style": "bold", "keywords": ["你管", "business"]},
                        {"text": "我是大圣的弟子。(I am the Great Sage's disciple.)", "style": "sly", "keywords": ["大圣", "弟子", "disciple"]},
                        {"text": "我是来学习的。(I am here to learn.)", "style": "insightful", "keywords": ["学习", "xuéxí", "learn"]},
                    ],
                },
            ],
        ),

        Anchor(
            id="jw_ch01_join",
            chapter="ch01",
            title="Joining the Pilgrimage",
            type="linear",
            location="mountain_pass",
            characters=["wukong", "sanzang", "bajie", "wujing"],
            mood="adventure",
            panels=[
                {
                    "id": "jw_ch1_05_speak",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_05_speak.png",
                    "aspect": "square",
                    "narration": "Wukong's eyes widen. He leans closer, nostrils flaring. Then — a bark of laughter that echoes off the mountains.",
                    "dialogue": "「有意思！跟我来。」",
                    "speaker": "wukong",
                },
                {
                    "id": "jw_ch1_05b_bimbo",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_05_speak.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "He said 'interesting — follow me.' You're alive. Nice work.",
                    "speaker": "bimbo",
                },
                {
                    "id": "jw_ch1_06_group",
                    "image": f"{IMAGE_BASE_URL}/panels/jw_ch01/jw_ch1_06_group.png",
                    "aspect": "wide",
                    "narration": "He bounds ahead, impossibly fast, and you stumble after him down the mountain path. Around a bend — a clearing. And there they are. A monk in golden robes, serene as still water. A heavyset creature with a pig's snout, asleep against a boulder. A tall blue-skinned figure sharpening a crescent blade. The Journey to the West. And you just joined it.",
                    "dialogue": None,
                    "speaker": None,
                },
            ],
        ),

        Anchor(
            id="jw_ch01_road",
            chapter="ch01",
            title="The Road West Begins",
            type="linear",
            location="mountain_pass",
            characters=["sanzang", "bimbo"],
            mood="hopeful",
            generation_hint=(
                "Sanzang welcomes the player with gentle calm. He speaks slowly and clearly — good for a beginner. "
                "Bimbo translates key phrases. The group begins walking west. Introduce basic directions: "
                "西 (xī/west), 走 (zǒu/walk), 路 (lù/road). End with the group on the road, mountains ahead."
            ),
            next_anchor="jw_ch02_arrive",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 2-8: Generation hints only
        # ────────────────────────────────────────────
        Anchor(id="jw_ch02_arrive", chapter="ch02", title="The Inn", type="linear",
               location="roadside_inn", characters=["innkeeper", "bajie"], mood="warm",
               generation_hint="Group arrives at a roadside inn. Player must order food and rooms in Mandarin. Bajie causes comic trouble by eating too much. Teach: 吃 (eat), 喝 (drink), 多少钱 (how much), 房间 (room).",
               next_anchor="jw_ch02_order_food"),

        Anchor(id="jw_ch02_order_food", chapter="ch02", title="Ordering Food", type="branch_point",
               location="roadside_inn", characters=["innkeeper", "bimbo"], mood="warm",
               branch_config=BranchConfig(
                   category_outcomes={
                       "diplomatic": {"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"diplomatic": 1}},
                       "pragmatic":  {"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                       "bold":       {"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"bold": 1}},
                       "trickster":  {"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"trickster": 1}},
                       "enlightened":{"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"enlightened": 1}},
                   },
                   default_outcome={"next_anchor": "jw_ch02_bajie_trouble", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
               ),
               convergence_anchor="jw_ch02_bajie_trouble",
               generation_hint="Time freeze to teach ordering food. Player chooses how to order: politely, practically, boldly, cleverly, or with insight about local customs."),

        Anchor(id="jw_ch02_bajie_trouble", chapter="ch02", title="Bajie's Appetite", type="linear",
               location="roadside_inn", characters=["bajie", "innkeeper"], mood="comic",
               generation_hint="Bajie eats everything. Innkeeper demands more money. Player must mediate. Teach: 对不起 (sorry), 太多了 (too much), 我们付钱 (we'll pay).",
               next_anchor="jw_ch02_night"),

        Anchor(id="jw_ch02_night", chapter="ch02", title="Night Stories", type="linear",
               location="roadside_inn", characters=["wukong", "sanzang"], mood="contemplative",
               generation_hint="Evening at the inn. Wukong tells stories of his past — 500 years under a mountain. Sanzang quotes scripture. Cultural moment about storytelling. Teach: 故事 (story), 山 (mountain), 年 (year).",
               next_anchor="jw_ch03_ferry"),

        Anchor(id="jw_ch03_ferry", chapter="ch03", title="The Ferry", type="linear",
               location="river_crossing", characters=["wujing"], mood="peaceful",
               generation_hint="Wide river, old ferry. Wujing (former river spirit) is in his element. He teaches the player about water, patience. Teach: 水 (water), 河 (river), 等 (wait), 过 (cross).",
               next_anchor="jw_ch03_wujing_lesson"),

        Anchor(id="jw_ch03_wujing_lesson", chapter="ch03", title="Wujing's Lesson", type="linear",
               location="river_crossing", characters=["wujing", "bimbo"], mood="calm",
               generation_hint="Wujing teaches patience through Mandarin. Water metaphors. Bimbo helps with tones. Teach: tone practice, 慢 (slow), 快 (fast), 听 (listen).",
               next_anchor="jw_ch03_storm"),

        Anchor(id="jw_ch03_storm", chapter="ch03", title="River Storm", type="linear",
               location="river_crossing", characters=["wukong", "wujing"], mood="danger",
               generation_hint="Sudden storm on the river. Supernatural origin. Player must shout commands in Mandarin to help. Teach: 小心 (careful), 帮忙 (help), 快走 (hurry).",
               next_anchor="jw_ch03_shore"),

        Anchor(id="jw_ch03_shore", chapter="ch03", title="Safe Shore", type="linear",
               location="river_crossing", characters=["sanzang"], mood="relief",
               generation_hint="Made it across. Sanzang grateful. Quiet moment of connection. Player's Mandarin improving. End chapter looking west toward mountains.",
               next_anchor="jw_ch04_ambush"),

        Anchor(id="jw_ch04_ambush", chapter="ch04", title="Mountain Ambush", type="linear",
               location="bamboo_forest", characters=["bandit_chief", "wukong"], mood="danger",
               generation_hint="Bandits block the path in bamboo forest. Wukong wants to fight. The bandit chief speaks. Player must decide approach. Teach: 让路 (make way), 不要打 (don't fight), 钱 (money).",
               next_anchor="jw_ch04_branch_negotiate"),

        Anchor(id="jw_ch04_branch_negotiate", chapter="ch04", title="Negotiate or Fight", type="branch_point",
               location="bamboo_forest", characters=["bandit_chief", "bimbo"], mood="tense",
               branch_config=BranchConfig(
                   category_outcomes={
                       "diplomatic": {"next_anchor": "jw_ch04_aftermath", "life_delta": 0, "reputation_delta": {"diplomatic": 2}},
                       "pragmatic":  {"next_anchor": "jw_ch04_aftermath", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                       "bold":       {"next_anchor": "jw_ch04_aftermath", "life_delta": -1, "reputation_delta": {"bold": 2}},
                       "trickster":  {"next_anchor": "jw_ch04_aftermath", "life_delta": 0, "reputation_delta": {"trickster": 2}},
                       "enlightened":{"next_anchor": "jw_ch04_aftermath", "life_delta": 0, "reputation_delta": {"enlightened": 1}},
                   },
                   default_outcome={"next_anchor": "jw_ch04_aftermath", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
               ),
               convergence_anchor="jw_ch04_aftermath",
               generation_hint="Time freeze — Bimbo helps player negotiate with bandits. Diplomatic = talk them down. Bold = challenge chief. Trickster = trick them. Enlightened = see their desperation."),

        Anchor(id="jw_ch04_aftermath", chapter="ch04", title="After the Bandits", type="linear",
               location="bamboo_forest", characters=["wukong", "sanzang"], mood="reflective",
               generation_hint="Resolution. Wukong impressed or amused by player's approach. Sanzang offers wisdom about violence vs words. Road continues.",
               next_anchor="jw_ch05_market"),

        Anchor(id="jw_ch05_market", chapter="ch05", title="Silk Road Market", type="linear",
               location="market_town", characters=["bajie"], mood="bustling",
               generation_hint="Colorful market town. Bajie wants to shop. Player navigates vendors, bargains, explores. Teach: 买 (buy), 卖 (sell), 太贵了 (too expensive), 便宜 (cheap).",
               next_anchor="jw_ch05_merchant"),

        Anchor(id="jw_ch05_merchant", chapter="ch05", title="The Merchant", type="linear",
               location="market_town", characters=["innkeeper"], mood="suspicious",
               generation_hint="A merchant offers information about the road ahead — for a price. Player must read intentions and negotiate. Teach: 相信 (believe/trust), 路 (road), 危险 (dangerous).",
               next_anchor="jw_ch05_magistrate"),

        Anchor(id="jw_ch05_magistrate", chapter="ch05", title="Magistrate's Court", type="linear",
               location="market_town", characters=["magistrate"], mood="formal",
               generation_hint="Called before the magistrate. Foreign travelers are suspect. Player must explain their purpose formally. Teach: 旅行 (travel), 学习 (study), 请问 (may I ask), 大人 (your honor).",
               next_anchor="jw_ch05_depart"),

        Anchor(id="jw_ch05_depart", chapter="ch05", title="Leaving Town", type="linear",
               location="market_town", characters=["wukong", "sanzang"], mood="determined",
               generation_hint="Group departs. The road grows wilder. Wukong warns about spirits ahead. Transition to supernatural territory.",
               next_anchor="jw_ch06_cave"),

        Anchor(id="jw_ch06_cave", chapter="ch06", title="The Cave", type="linear",
               location="spirit_cave", characters=["jade_spirit"], mood="eerie",
               generation_hint="Group finds a glowing cave. The Jade Spirit appears — beautiful, helpful, offering shelter. But something is wrong. Teach: 漂亮 (beautiful), 小心 (careful), 相信 (trust), 假的 (fake).",
               next_anchor="jw_ch06_jade_spirit"),

        Anchor(id="jw_ch06_jade_spirit", chapter="ch06", title="The Jade Spirit's Offer", type="linear",
               location="spirit_cave", characters=["jade_spirit", "bimbo"], mood="seductive",
               generation_hint="The spirit offers a shortcut, comfort, answers. Bimbo is uneasy. Wukong's eyes narrow. Something is being tested.",
               next_anchor="jw_ch06_branch_trust"),

        Anchor(id="jw_ch06_branch_trust", chapter="ch06", title="Trust or Doubt", type="branch_point",
               location="spirit_cave", characters=["jade_spirit", "bimbo", "wukong"], mood="tension",
               branch_config=BranchConfig(
                   category_outcomes={
                       "diplomatic": {"next_anchor": "jw_ch06_escape", "life_delta": 0, "reputation_delta": {"diplomatic": 1}},
                       "pragmatic":  {"next_anchor": "jw_ch06_escape", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                       "bold":       {"next_anchor": "jw_ch06_escape", "life_delta": -1, "reputation_delta": {"bold": 1}},
                       "trickster":  {"next_anchor": "jw_ch06_escape", "life_delta": 0, "reputation_delta": {"trickster": 2}},
                       "enlightened":{"next_anchor": "jw_ch06_escape", "life_delta": 0, "reputation_delta": {"enlightened": 2}},
                   },
                   default_outcome={"next_anchor": "jw_ch06_escape", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
               ),
               convergence_anchor="jw_ch06_escape",
               generation_hint="Player decides: accept help (risk), politely decline, challenge the spirit, trick it, or see its true nature. Enlightened path reveals the spirit is testing them."),

        Anchor(id="jw_ch06_escape", chapter="ch06", title="Escape the Cave", type="linear",
               location="spirit_cave", characters=["wukong"], mood="action",
               generation_hint="Resolution of spirit encounter. Wukong fights or the spirit releases them. Group escapes. Lesson about appearances in China.",
               next_anchor="jw_ch07_tea_house"),

        Anchor(id="jw_ch07_tea_house", chapter="ch07", title="The Tea Master", type="linear",
               location="tea_house", characters=["tea_master"], mood="serene",
               generation_hint="Mountain tea house above the clouds. Master Lü serves tea and wisdom. Quiet conversation. Teach: 茶 (tea), 喝 (drink), 坐 (sit), 安静 (quiet/peaceful). A rest before the final challenges.",
               next_anchor="jw_ch07_lesson"),

        Anchor(id="jw_ch07_lesson", chapter="ch07", title="Tea and Tones", type="linear",
               location="tea_house", characters=["tea_master", "bimbo"], mood="meditative",
               generation_hint="Master Lü teaches through tea preparation. Each step has a Mandarin word. Bimbo marvels. The old man's hands move like poetry. Teach: advanced tones, 热 (hot), 冷 (cold), 慢慢来 (take it slowly).",
               next_anchor="jw_ch07_wisdom"),

        Anchor(id="jw_ch07_wisdom", chapter="ch07", title="Parting Wisdom", type="linear",
               location="tea_house", characters=["tea_master", "sanzang"], mood="bittersweet",
               generation_hint="Master Lü and Sanzang share words. The old man gifts something to the player. A moment of connection across language and time. The road continues.",
               next_anchor="jw_ch08_arrive"),

        Anchor(id="jw_ch08_arrive", chapter="ch08", title="The Temple Gates", type="linear",
               location="temple_mountain", characters=["sanzang"], mood="awe",
               generation_hint="The mountain temple. Journey's waypoint. Sanzang prays. The player reflects on how far their Mandarin has come. Teach: 到了 (arrived), 谢谢 (thank you), 再见 (goodbye).",
               next_anchor="jw_ch08_meditation"),

        Anchor(id="jw_ch08_meditation", chapter="ch08", title="Meditation", type="linear",
               location="temple_mountain", characters=["bimbo"], mood="peaceful",
               generation_hint="Quiet moment. Bimbo reflects on the journey with the player. The language learned, the friends made. A sense of accomplishment but also that the road continues.",
               next_anchor="jw_ch08_test"),

        Anchor(id="jw_ch08_test", chapter="ch08", title="The Road Continues", type="linear",
               location="temple_mountain", characters=["wukong", "sanzang", "bajie", "wujing"],
               mood="determined",
               generation_hint="The group prepares to leave the temple and continue west. Wukong grins. Bajie complains about the food. Wujing checks supplies. Sanzang smiles. The road stretches on. End of current content — to be continued."),
    ],
)


# ============================================================
# REGISTRY — expose to story_panels router
# ============================================================

STORY_SKELETONS = {
    STORY_ID: JOURNEY_SKELETON,
}


# ============================================================
# CLI UTILITIES
# ============================================================

async def _check():
    from story.panels_test import build_manifest_prompt
    missing_chars = [c for c in CHARACTERS.values() if not os.path.exists(c.reference_path)]
    missing_locs = [l for l in LOCATIONS.values() if not os.path.exists(l.reference_path)]
    print(f"Characters: {len(CHARACTERS)} total, {len(missing_chars)} missing references")
    for c in missing_chars:
        print(f"  MISSING: {c.id} -> {c.reference_path}")
    print(f"Locations: {len(LOCATIONS)} total, {len(missing_locs)} missing references")
    for l in missing_locs:
        print(f"  MISSING: {l.id} -> {l.reference_path}")
    print(f"Panels: {len(PANELS)} defined")
    missing_panels = []
    for p in PANELS:
        chapter = p.chapter
        path = os.path.join(IMAGE_CACHE_DIR, "panels", f"jw_{chapter}", f"{p.id}.png")
        if not os.path.exists(path):
            missing_panels.append(p.id)
    print(f"  Missing panel images: {len(missing_panels)}")
    for pid in missing_panels:
        print(f"    MISSING: {pid}")


async def _generate(force=False):
    print("Generating character references...")
    for char in CHARACTERS.values():
        if char.id == "bimbo":
            continue  # Shared with shogun
        if not force and os.path.exists(char.reference_path):
            print(f"  SKIP {char.id} (exists)")
            continue
        print(f"  Generating {char.id}...")
        await generate_character_ref(char.id, char.description, force=force)

    print("Generating location references...")
    for loc in LOCATIONS.values():
        if loc.id == "ship_observation":
            continue  # Shared with shogun
        if not force and os.path.exists(loc.reference_path):
            print(f"  SKIP {loc.id} (exists)")
            continue
        print(f"  Generating {loc.id}...")
        await generate_location_ref(loc.id, loc.description, force=force)


async def _panels(force=False):
    from story.panels_test import generate_single_panel
    for panel in PANELS:
        print(f"  Generating panel {panel.id}...")
        await generate_single_panel(panel.id, force=force)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    force = "--force" in sys.argv
    if cmd == "check":
        asyncio.run(_check())
    elif cmd == "generate":
        asyncio.run(_generate(force))
    elif cmd == "panels":
        asyncio.run(_panels(force))
    elif cmd == "all":
        asyncio.run(_generate(force))
        asyncio.run(_panels(force))
    else:
        print(f"Usage: python -m story.journey [check|generate|panels|all] [--force]")
