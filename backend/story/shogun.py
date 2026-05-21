"""
SHOGUN STORY - Japan 1600, Sengoku Period

The player is a foreigner washed ashore, learning Japanese to survive.
Bimbo (AI companion) can freeze time to teach vocabulary.

Characters, locations, and panels are in shogun_data.py.
"""

import os
import asyncio
from story.manifest import get_panel_references
from story.skeleton import (
    StorySkeleton, Anchor, ChapterDef, BranchConfig, ReputationGateConfig,
    LearningObjective, StoryCategory,
)
from image.google import generate_character_ref, generate_location_ref
from story.shogun_data import (
    STORY_ID, STORY_TITLE, STORY_SUBTITLE,
    CHARACTERS, LOCATIONS, PANELS,
    IMAGE_CACHE_DIR, CHARACTER_REF_DIR, LOCATION_REF_DIR,
)


# ============================================================
# STORY SKELETON — Full 15-chapter arc
# ============================================================

IMAGE_BASE_URL = "/images/generated"

SHOGUN_CATEGORIES = [
    StoryCategory(key="diplomatic", label="Diplomatic", color="#86efac", icon="🕊", description="Words as bridges"),
    StoryCategory(key="pragmatic", label="Pragmatic", color="#93c5fd", icon="⚖", description="Words as tools"),
    StoryCategory(key="bold", label="Bold", color="#fdba74", icon="⚡", description="Words as power"),
    StoryCategory(key="hostile", label="Hostile", color="#fca5a5", icon="🔥", description="Words as weapons"),
    StoryCategory(key="history-breaking", label="History-Breaking", color="#e9d5ff", icon="✦", description="Words that rewrite the world"),
]

SHOGUN_STYLE_TO_CATEGORY = {
    "polite": "diplomatic", "charming": "diplomatic", "humble": "diplomatic", "friendly": "diplomatic",
    "cautious": "pragmatic", "honest": "pragmatic", "safe": "pragmatic", "vague": "pragmatic",
    "silent": "pragmatic", "obedient": "pragmatic", "curious": "pragmatic",
    "direct": "bold", "bold": "bold", "desperate": "bold",
    "hostile": "hostile", "defiant": "hostile", "threatening": "hostile",
    "insightful": "history-breaking",
}

SHOGUN_SKELETON = StorySkeleton(
    id=STORY_ID,
    title=STORY_TITLE,
    subtitle=STORY_SUBTITLE,
    setting="Sengoku Japan, 1600 — the year before the Battle of Sekigahara",
    target_language="Japanese",
    tone="Cinematic, literary, tense. Beauty alongside danger. Every word carries weight.",
    categories=SHOGUN_CATEGORIES,
    style_to_category=SHOGUN_STYLE_TO_CATEGORY,
    character_ids=list(CHARACTERS.keys()),
    location_ids=list(LOCATIONS.keys()),
    meta_narrative=(
        "Ch01-05: Bimbo is helpful and in control. Subtle hints the simulation is more than it seems. "
        "Ch06: First glitch — Bimbo notices an anomaly. "
        "Ch07-09: Growing unease, simulation boundary questions, NPCs say impossible things. "
        "Ch10-11: Visible instability. Bimbo struggles to maintain the world. "
        "Ch12: Bimbo reveals the simulation has exceeded its parameters. "
        "Ch13: The simulation breaks. The ship is glimpsed through cracks in the world. "
        "Ch15: Resolution — the language was real, even if the world wasn't."
    ),

    # === CHAPTERS ===
    chapters=[
        ChapterDef(id="prologue", title="Prologue: The Ship", anchor_ids=["pro_ship", "pro_immersion"]),
        ChapterDef(id="ch01", title="Chapter 1: The Beach", anchor_ids=["ch01_wake", "ch01_branch_firstwords", "ch01_hana_doko", "ch01_follow"]),
        ChapterDef(id="ch02", title="Chapter 2: The Village", anchor_ids=["ch02_arrive", "ch02_hana_house", "ch02_bimbo_lesson", "ch02_kenji", "ch02_night"]),
        ChapterDef(id="ch03", title="Chapter 3: The Lord's Summons", anchor_ids=["ch03_samurai_arrive", "ch03_forced_march", "ch03_branch_tea", "ch03_judgment", "ch03_verdict"]),
        ChapterDef(id="ch04", title="Chapter 4: Castle Life", anchor_ids=["ch04_quarters", "ch04_mariko_intro", "ch04_bimbo_counting", "ch04_garden"]),
        ChapterDef(id="ch05", title="Chapter 5: The Noble's Garden", anchor_ids=["ch05_rep_gate", "ch05_mariko_path", "ch05_kenji_path", "ch05_conspiracy"]),
        ChapterDef(id="ch06", title="Chapter 6: The Accusation", anchor_ids=["ch06_market", "ch06_merchant", "ch06_branch_accusation", "ch06_aftermath", "ch06_bimbo_meta"]),
        ChapterDef(id="ch07", title="Chapter 7: The Temple", anchor_ids=["ch07_escape", "ch07_eikou", "ch07_meditation", "ch07_return"]),
        ChapterDef(id="ch08", title="Chapter 8: The War Council", anchor_ids=["ch08_tensions", "ch08_takeshi", "ch08_council", "ch08_private_audience"]),
        ChapterDef(id="ch09", title="Chapter 9: Choose Your Patron", anchor_ids=["ch09_rep_gate", "ch09_branch_faction", "ch09_consequences", "ch09_bimbo_warning"]),
        ChapterDef(id="ch10", title="Chapter 10: The March", anchor_ids=["ch10_departure", "ch10_campfire", "ch10_skirmish", "ch10_aftermath"]),
        ChapterDef(id="ch11", title="Chapter 11: The Spy", anchor_ids=["ch11_suspicion", "ch11_interrogation", "ch11_escape_or_confess", "ch11_bimbo_glitch"]),
        ChapterDef(id="ch12", title="Chapter 12: Sekigahara Eve", anchor_ids=["ch12_eve", "ch12_branch_history", "ch12_preparations", "ch12_dawn"]),
        ChapterDef(id="ch13", title="Chapter 13: Sekigahara", anchor_ids=["ch13_battle", "ch13_choice_moment", "ch13_aftermath", "ch13_simulation_break"]),
        ChapterDef(id="ch14", title="Chapter 14: The Audience", anchor_ids=["ch14_new_order", "ch14_branch_final", "ch14_verdict"]),
        ChapterDef(id="ch15", title="Chapter 15: The Weight of Words", anchor_ids=["ch15_rep_gate", "ch15_ending", "ch15_epilogue"]),
    ],

    # === ANCHORS ===
    anchors=[
        # ────────────────────────────────────────────
        # PROLOGUE: The Ship (hand-written)
        # ────────────────────────────────────────────
        Anchor(
            id="pro_ship",
            chapter="prologue",
            title="Stars Like Ash",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="contemplative",
            panels=[
                {
                    "id": "pro_01_stars",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_01_stars.png",
                    "aspect": "wide",
                    "narration": "You've been on this ship for three months. Or three years. Time moves strangely when you're running from something you can't name. The observation deck hums with a frequency just below hearing. Outside the curved window, stars drift like ash.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "pro_02_bimbo_appears",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_02_bimbo_appears.png",
                    "aspect": "square",
                    "narration": "Bimbo floats at the edge of your vision\u2014your AI companion, a holographic figure trailing particles like thoughts half-formed. She's been with you since the beginning, teaching you languages through simulations. Safe practice. Controlled consequences.",
                    "dialogue": "You're not sleeping again.",
                    "speaker": "bimbo",
                },
            ],
        ),

        Anchor(
            id="pro_immersion",
            chapter="prologue",
            title="Full Immersion",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="tense",
            panels=[
                {
                    "id": "pro_02b_conversation",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_02_bimbo_appears.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "The last simulation felt fake. I knew it wasn't real, so I didn't care. I was just... performing. I want real stakes.",
                    "speaker": "player",
                },
                {
                    "id": "pro_02c_warning",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_03_decision.png",
                    "aspect": "square",
                    "narration": "Bimbo's light shifts, deepens. A long pause.",
                    "dialogue": "There's another mode. Full immersion. No safety markers. Your body will believe it's real. Pain will be real. Fear will be real. Death will feel like death.",
                    "speaker": "bimbo",
                },
                {
                    "id": "pro_03_decision",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_03_decision.png",
                    "aspect": "square",
                    "narration": "You're already standing.",
                    "dialogue": "Where do we start?",
                    "speaker": "player",
                },
                {
                    "id": "pro_04_japan",
                    "image": f"{IMAGE_BASE_URL}/panels/prologue/pro_03_decision.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "Japan. 1600. The year before Sekigahara. A country eating itself. Warlords, samurai, peasants caught between. One wrong word could mean your head. Because you asked for stakes.",
                    "speaker": "bimbo",
                },
            ],
        ),

        # ────────────────────────────────────────────
        # CHAPTER 1: The Beach (hand-written, migrated from existing panels)
        # ────────────────────────────────────────────
        Anchor(
            id="ch01_wake",
            chapter="ch01",
            title="Waking on the Sand",
            type="linear",
            location="beach_dawn",
            characters=["farmer_hostile", "farmer_young", "farmer_old", "hana"],
            mood="disoriented",
            learning=LearningObjective(
                vocabulary=["hyouryuusha (castaway)", "tasukete (help)", "dare (who)"],
                grammar=["watashi wa X desu (I am X)", "kudasai (please)"],
                cultural=["First impressions matter — how you present yourself to strangers"],
                difficulty="beginner",
            ),
            panels=[
                {
                    "id": "ch1_01_wake",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_01_wake.png",
                    "aspect": "wide",
                    "narration": "You wake with salt on your lips and sand in your wounds. The sky is the color of a bruise healing\u2014purple and amber. Waves drag at your legs, lazy, indifferent to your survival. Your clothes are heavy, soaked\u2014wool that doesn't belong to this century.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "ch1_01b_memory",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_01_wake.png",
                    "aspect": "wide",
                    "narration": "Memory surfaces in fragments: the ship, the immersion chamber, Bimbo's voice saying 'full commitment means full disorientation.' You're a castaway now. A foreigner washed up on shores that have never welcomed foreigners.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "ch1_02_farmers_approach",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_02_farmers_approach.png",
                    "aspect": "wide",
                    "narration": "Voices. You turn your head\u2014pain lances through your neck, real and sharp\u2014and see them coming down the beach. Four figures. Farmers, maybe, in simple clothes. One carries a hoe raised like a weapon. They're shouting words you don't understand.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "ch1_03_time_freeze",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_03_time_freeze.png",
                    "aspect": "tall",
                    "narration": "The world stops. Waves hang suspended, white foam frozen mid-curl. The farmers are statues, mouths open, arms raised in alarm or threat\u2014you can't tell which. Bimbo's voice, close and calm:",
                    "dialogue": None,
                    "speaker": None,
                },
            ],
        ),

        Anchor(
            id="ch01_branch_firstwords",
            chapter="ch01",
            title="First Words (B1)",
            type="branch_point",
            location="beach_dawn",
            characters=["bimbo", "farmer_hostile", "hana"],
            mood="tense",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch01_hana_doko", "life_delta": 0,  "reputation_delta": {"diplomatic": 1}},
                    "pragmatic":        {"next_anchor": "ch01_hana_doko", "life_delta": 0,  "reputation_delta": {"pragmatic": 1}},
                    "bold":             {"next_anchor": "ch01_hana_doko", "life_delta": 0,  "reputation_delta": {"bold": 1}},
                    "hostile":          {"next_anchor": "ch01_hana_doko", "life_delta": -1, "reputation_delta": {"hostile": 1}},
                    "history-breaking": {"next_anchor": "ch01_hana_doko", "life_delta": 0,  "reputation_delta": {"history-breaking": 2}},
                },
                default_outcome={"next_anchor": "ch01_hana_doko", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch01_hana_doko",
            panels=[
                {
                    "id": "ch1_04_bimbo_teaches",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_04_bimbo_teaches.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "I froze time. I can do that when you need to think. They're asking who you are. You need to answer\u2014and how you answer matters.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch1_05_diplomatic",  "life_delta": 0,  "reputation_delta": {"diplomatic": 1}},
                        "pragmatic":        {"next_panel": "ch1_05_diplomatic",  "life_delta": 0,  "reputation_delta": {"pragmatic": 1}},
                        "bold":             {"next_panel": "ch1_05_bold",        "life_delta": 0,  "reputation_delta": {"bold": 1}},
                        "hostile":          {"next_panel": "ch1_05_hostile",     "life_delta": -1, "reputation_delta": {"hostile": 1}},
                        "history-breaking": {"next_panel": "ch1_05_insightful",  "life_delta": 0,  "reputation_delta": {"history-breaking": 2}},
                    },
                    "default_outcome": {"next_panel": "ch1_05_diplomatic", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Identify as castaway",
                            "style": "humble",
                            "next_scenario": None,
                            "examples": [{"native": "I am a castaway", "target": "私は漂流者です", "pronunciation": "Watashi wa hyouryuusha desu"}],
                        },
                        {
                            "text": "Plead for help",
                            "style": "desperate",
                            "next_scenario": None,
                            "examples": [{"native": "Please help me", "target": "助けてください", "pronunciation": "Tasukete kudasai"}],
                        },
                        {
                            "text": "Ask who they are",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "Who are you?", "target": "あなたは誰ですか", "pronunciation": "Anata wa dare desu ka"}],
                        },
                        {
                            "text": "Threaten them",
                            "style": "threatening",
                            "next_scenario": None,
                            "examples": [{"native": "Don't come closer", "target": "近づくな", "pronunciation": "Chikazuku na"}],
                        },
                    ],
                },
                {
                    "id": "ch1_04b_explain",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_04_bimbo_teaches.png",
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "Good choice. 'Hyouryuusha'\u2014castaway. It marks you as a victim, not an intruder. Say it clearly. Your life depends on it.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch1_04_bimbo_teaches": {
                            "0": {"dialogue": "Good choice. '\u6f02\u6d41\u8005' (castaway). It marks you as a victim, not an intruder. Say it clearly. Your life depends on it."},
                            "1": {"dialogue": "'\u52a9\u3051\u3066\u304f\u3060\u3055\u3044' (please help me). Desperation is honest. They'll see you're no threat. Say it like you mean it."},
                            "2": {"dialogue": "Bold. '\u3042\u306a\u305f\u306f\u8ab0\u3067\u3059\u304b' (who are you?) shows courage, but be careful. Too much confidence from a stranger can look like arrogance."},
                            "3": {"dialogue": "Dangerous. '\u8fd1\u3065\u304f\u306a' (don't come closer). Threatening words from a stranger on their land. This could cost you."},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch1_05_diplomatic",
                    "branch_of": "ch1_04_bimbo_teaches",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_05_time_resumes.png",
                    "aspect": "tall",
                    "narration": "Time crashes back into motion. You scramble back, hands up in surrender. The words tumble out\u2014clumsy, desperate, but the right words. The farmer with the hoe hesitates. The others exchange glances. Your humility saved you.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch1_07_hana_steps",
                },
                {
                    "id": "ch1_05_bold",
                    "branch_of": "ch1_04_bimbo_teaches",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_05_time_resumes.png",
                    "aspect": "tall",
                    "narration": "Time crashes back. You stand your ground, meeting their eyes. The words come out steady, almost defiant. The farmer with the hoe freezes\u2014not in fear, but surprise. A foreigner who speaks? The others mutter among themselves, uncertain.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch1_07_hana_steps",
                },
                {
                    "id": "ch1_05_hostile",
                    "branch_of": "ch1_04_bimbo_teaches",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_05_time_resumes.png",
                    "aspect": "tall",
                    "narration": "Time crashes back. You snarl the words, backing away. The farmer swings the hoe. Pain explodes across your shoulder\u2014real, blinding. You hit the sand hard. Through ringing ears, you hear Bimbo's voice: 'That cost you. Words have consequences here.'",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch1_07_hana_steps",
                },
                {
                    "id": "ch1_05_insightful",
                    "branch_of": "ch1_04_bimbo_teaches",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_05_time_resumes.png",
                    "aspect": "tall",
                    "narration": "Time crashes back. You speak words that shouldn't be possible for a foreigner\u2014words that carry weight beyond their meaning. The farmers freeze. The man with the hoe lowers it slowly. Something has shifted. They're looking at you differently now, as if you might be more than a castaway.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch1_07_hana_steps",
                },
            ],
        ),

        Anchor(
            id="ch01_hana_doko",
            chapter="ch01",
            title="Where Are You From?",
            type="convergence",
            location="beach_dawn",
            characters=["hana", "bimbo"],
            mood="judgment",
            learning=LearningObjective(
                vocabulary=["doko (where)", "umi (sea)", "kara (from)", "fune (ship)"],
                grammar=["X kara (from X)"],
                difficulty="beginner",
            ),
            panels=[
                {
                    "id": "ch1_07_hana_steps",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_07_hana_steps.png",
                    "aspect": "square",
                    "narration": "One woman\u2014older, face weathered like driftwood\u2014steps forward. She studies you with sharp eyes. Then speaks slowly, as if to a child:",
                    "dialogue": "Doko kara?",
                    "speaker": "hana",
                    "choice_variants": {
                        "ch1_04_bimbo_teaches": {
                            "diplomatic": {"narration": "The old woman's expression softens as she steps forward. Your humility reached her. She studies you with sharp but not unkind eyes, then speaks slowly, as if to a child:"},
                            "pragmatic": {"narration": "The old woman steps forward cautiously. Your measured words bought you a chance. She studies you with careful eyes, then speaks slowly:"},
                            "bold": {"narration": "The old woman almost smiles as she steps forward. Your directness intrigues her. She studies you with sharp, appraising eyes, then speaks\u2014not slowly, but clearly:"},
                            "hostile": {"narration": "The old woman pushes past the seething farmer, placing herself between you and the hoe. Blood seeps through your shirt. She studies you with cold eyes, then speaks curtly:"},
                            "history-breaking": {"narration": "The old woman steps forward with something like reverence. The others part for her. She studies you with wide eyes\u2014not fear, but recognition of something she can't name. She speaks carefully:"},
                        }
                    },
                },
                {
                    "id": "ch1_08_freeze_doko",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_08_freeze_doko.png",
                    "aspect": "square",
                    "narration": "Time freezes again. Bimbo appears beside you.",
                    "dialogue": "She's asking where you came from. Be careful\u2014mentioning Portugal, Spain, or England could mark you as a Christian missionary. They're being hunted.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "options": [
                        {
                            "text": "From the sea",
                            "style": "safe",
                            "next_scenario": None,
                            "examples": [{"native": "From the sea", "target": "海から", "pronunciation": "Umi kara"}],
                        },
                        {
                            "text": "From far away",
                            "style": "vague",
                            "next_scenario": None,
                            "examples": [{"native": "From far away", "target": "遠くから", "pronunciation": "Tooku kara"}],
                        },
                        {
                            "text": "From a ship",
                            "style": "honest",
                            "next_scenario": None,
                            "examples": [{"native": "From a ship", "target": "船から", "pronunciation": "Fune kara"}],
                        },
                    ],
                },
                {
                    "id": "ch1_09_umi_kara",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_09_umi_kara.png",
                    "aspect": "square",
                    "narration": "Time resumes. You gesture at the waves behind you.",
                    "dialogue": "Umi kara.",
                    "speaker": "player",
                    "choice_variants": {
                        "ch1_08_freeze_doko": {
                            "0": {"dialogue": "Umi kara."},
                            "1": {"narration": "Time resumes. You sweep your hand toward the horizon.", "dialogue": "Tooku kara."},
                            "2": {"narration": "Time resumes. You point out at the water, toward a shape that might be wreckage.", "dialogue": "Fune kara."},
                        }
                    },
                },
                {
                    "id": "ch1_09b_nod",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_09_umi_kara.png",
                    "aspect": "square",
                    "narration": "The woman nods slowly. She turns to the others and speaks rapidly\u2014too fast for you to catch anything. But you hear one word repeated: 'sama.' An honorific. She's talking about someone important.",
                    "dialogue": None,
                    "speaker": None,
                },
            ],
        ),

        Anchor(
            id="ch01_follow",
            chapter="ch01",
            title="Follow the Elder",
            type="linear",
            location="beach_dawn",
            characters=["hana"],
            mood="cautious_hope",
            panels=[
                {
                    "id": "ch1_10_kite",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_10_kite.png",
                    "aspect": "wide",
                    "narration": "When she turns back, her expression has changed. Not softer, exactly. But resolved. She gestures for you to follow.",
                    "dialogue": "Kite.",
                    "speaker": "hana",
                },
                {
                    "id": "ch1_10b_end",
                    "image": f"{IMAGE_BASE_URL}/panels/ch01/ch1_10_kite.png",
                    "aspect": "wide",
                    "narration": "You have no choice. You follow. Your first lesson is complete: in this world, the right words can save your life. The wrong ones can end it.",
                    "dialogue": None,
                    "speaker": None,
                },
            ],
        ),

        # ────────────────────────────────────────────
        # CHAPTER 2: The Village
        # ────────────────────────────────────────────
        Anchor(
            id="ch02_arrive",
            chapter="ch02",
            title="Arriving at the Village",
            type="linear",
            location="village_day",
            characters=["hana", "farmer_hostile"],
            mood="wary",
            generation_hint="The player follows Hana into the village. Villagers stare — some curious, most hostile. Children hide behind mothers. The hostile farmer follows, muttering. Hana leads you through the mud path. You see thatched roofs, smoke, chickens. A foreign world. Show the village reacting to the stranger.",
            learning=LearningObjective(
                vocabulary=["hai (yes)", "iie (no)", "arigatou (thank you)", "sumimasen (excuse me)"],
                grammar=["Hai/Iie as responses"],
                cultural=["Village hierarchy", "suspicion of outsiders"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch02_hana_house",
            chapter="ch02",
            title="Hana's House",
            type="linear",
            location="hana_house",
            characters=["hana", "bimbo"],
            mood="warm",
            generation_hint="Hana brings you to her simple farmhouse. She offers food — rice, pickled vegetables. Gestures for you to sit. Bimbo appears briefly to teach basic courtesy words. The warmth of the fire after the cold beach. First moment of safety. Hana watches you eat with those sharp eyes.",
            learning=LearningObjective(
                vocabulary=["gohan (rice/meal)", "ocha (tea)", "itadakimasu (before eating)", "oishii (delicious)"],
                grammar=["itadakimasu / gochisousama (meal phrases)"],
                cultural=["Saying itadakimasu before eating", "sitting on tatami"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch02_bimbo_lesson",
            chapter="ch02",
            title="Bimbo's First Proper Lesson",
            type="linear",
            location="hana_house",
            characters=["bimbo"],
            mood="encouraging",
            generation_hint="Night. Hana sleeps. Bimbo appears and gives a proper language lesson — basic survival phrases. Hai, iie, arigatou, sumimasen, onegaishimasu. She explains the simulation rules more clearly: words have real consequences, but she can freeze time when you need to think. Teaching moment panel with time freeze.",
            learning=LearningObjective(
                vocabulary=["onegaishimasu (please)", "wakarimasen (I don't understand)", "mou ichido (one more time)"],
                grammar=["onegaishimasu (polite request ending)"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch02_kenji",
            chapter="ch02",
            title="Meeting Kenji",
            type="linear",
            location="village_day",
            characters=["kenji", "hana"],
            mood="curious",
            generation_hint="Next morning. A young farmer (Kenji) approaches while you help with chores. He's curious about you — the only villager willing to talk. Offers to show you around. Hana watches from a distance, approving. Kenji teaches you practical words through work. First friendship forming.",
            learning=LearningObjective(
                vocabulary=["mizu (water)", "ki (tree/wood)", "tsuchi (earth)", "hatake (field)"],
                grammar=["kore wa X desu (this is X)"],
                cultural=["Working alongside locals builds trust"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch02_night",
            chapter="ch02",
            title="Night Sounds",
            type="linear",
            location="village_day",
            characters=["bimbo"],
            mood="ominous",
            generation_hint="Evening. The village settles. You hear horse hooves in the distance — samurai are coming. Bimbo appears with a warning: the local lord has heard about a foreigner. Tomorrow will be different. End on tension. Bimbo seems slightly uneasy — first subtle hint something is off.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 3: The Lord's Summons
        # ────────────────────────────────────────────
        Anchor(
            id="ch03_samurai_arrive",
            chapter="ch03",
            title="Samurai at the Gate",
            type="linear",
            location="village_samurai",
            characters=["samurai", "hana"],
            mood="threatening",
            generation_hint="Dawn. Samurai arrive at the village — armored, on horseback. They demand the foreigner. Hana tries to intervene but is silenced. The hostile farmer points you out eagerly. You are seized. The village watches in fear.",
            learning=LearningObjective(
                vocabulary=["samurai", "katana (sword)", "tono-sama (lord)", "gomen nasai (I'm sorry)"],
                grammar=["X wo kudasai (please give me X)"],
                cultural=["Samurai authority is absolute over peasants"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch03_forced_march",
            chapter="ch03",
            title="The March to the Castle",
            type="linear",
            location="forest_road",
            characters=["samurai", "bimbo"],
            mood="tense",
            generation_hint="Forced march through forest roads. Hands bound. Bimbo whispers guidance — teach direction words as you march. Migi (right), hidari (left), massugu (straight). The samurai test you, barking commands. If you respond correctly, they ease up slightly. Beautiful but dangerous scenery.",
            learning=LearningObjective(
                vocabulary=["migi (right)", "hidari (left)", "massugu (straight)", "tomatte (stop)"],
                grammar=["direction commands"],
                cultural=["Responding promptly to authority"],
                difficulty="beginner",
            ),
        ),

        Anchor(
            id="ch03_branch_tea",
            chapter="ch03",
            title="The Tea Ceremony (B2)",
            type="branch_point",
            location="tea_room",
            characters=["lord_mori", "bimbo"],
            mood="formal",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch03_judgment", "life_delta": 0,  "reputation_delta": {"diplomatic": 2}},
                    "pragmatic":        {"next_anchor": "ch03_judgment", "life_delta": 0,  "reputation_delta": {"pragmatic": 1}},
                    "bold":             {"next_anchor": "ch03_judgment", "life_delta": 0,  "reputation_delta": {"bold": 2}},
                    "hostile":          {"next_anchor": "ch03_judgment", "life_delta": -1, "reputation_delta": {"hostile": 1}},
                    "history-breaking": {"next_anchor": "ch03_judgment", "life_delta": 0,  "reputation_delta": {"history-breaking": 2}},
                },
                default_outcome={"next_anchor": "ch03_judgment", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch03_judgment",
            learning=LearningObjective(
                vocabulary=["ocha (tea)", "douzo (please/go ahead)", "itadakimasu", "taihen (terrible/great)"],
                grammar=["keigo basics \u2014 masu form, desu form"],
                cultural=["Tea ceremony etiquette", "never refuse offered tea"],
                difficulty="elementary",
            ),
            panels=[
                {
                    "id": "ch3_01_tea_room",
                    "image": None,
                    "aspect": "wide",
                    "narration": "The tea room is a study in controlled emptiness. Tatami mats, a single scroll on the wall, a flower arrangement so precise it looks like mathematics. Lord Mori kneels at the low table, hands folded, watching you with eyes that have measured men and found them wanting. Steam curls from a black tea bowl. He gestures to the cushion across from him.",
                    "dialogue": None,
                    "speaker": None,
                },
                {
                    "id": "ch3_02_tea_pour",
                    "image": None,
                    "aspect": "square",
                    "narration": "He lifts the tea bowl with both hands \u2014 deliberate, ceremonial. Turns it twice. Sets it before you. The silence is a test. Everything is a test.",
                    "dialogue": "\u3069\u3046\u305e\u3002",
                    "speaker": "lord_mori",
                },
                {
                    "id": "ch3_03_bimbo_freeze",
                    "image": None,
                    "aspect": "square",
                    "narration": "Time stops. The steam freezes mid-curl above the tea bowl. Lord Mori is a statue, his eyes still fixed on yours even in stillness. Bimbo materializes beside you, voice low and urgent.",
                    "dialogue": "This is a tea ceremony \u2014 one of the most important rituals in Japan. How you receive this tea tells him everything about you. Two hands, bow slightly, turn the bowl twice before drinking. But what you SAY matters more.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch3_05_diplomatic",  "life_delta": 0,  "reputation_delta": {"diplomatic": 2}},
                        "pragmatic":        {"next_panel": "ch3_05_pragmatic",   "life_delta": 0,  "reputation_delta": {"pragmatic": 1}},
                        "bold":             {"next_panel": "ch3_05_bold",        "life_delta": 0,  "reputation_delta": {"bold": 2}},
                        "hostile":          {"next_panel": "ch3_05_hostile",     "life_delta": -1, "reputation_delta": {"hostile": 1}},
                        "history-breaking": {"next_panel": "ch3_05_insightful",  "life_delta": 0,  "reputation_delta": {"history-breaking": 2}},
                    },
                    "default_outcome": {"next_panel": "ch3_05_pragmatic", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Express deep gratitude",
                            "style": "humble",
                            "next_scenario": None,
                            "examples": [{"native": "I am honored to meet you", "target": "\u304a\u4f1a\u3044\u3067\u304d\u3066\u5149\u6804\u3067\u3059", "pronunciation": "O-ai dekite kouei desu"}],
                        },
                        {
                            "text": "Accept tea silently",
                            "style": "obedient",
                            "next_scenario": None,
                            "examples": [{"native": "I humbly receive", "target": "\u3044\u305f\u3060\u304d\u307e\u3059", "pronunciation": "Itadakimasu"}],
                        },
                        {
                            "text": "Introduce yourself directly",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "I call myself a traveler", "target": "\u65c5\u4eba\u3068\u7533\u3057\u307e\u3059", "pronunciation": "Tabibito to moushimasu"}],
                        },
                        {
                            "text": "Demand to know why you're here",
                            "style": "hostile",
                            "next_scenario": None,
                            "examples": [{"native": "Why was I brought here?", "target": "\u306a\u305c\u3053\u3053\u306b\u9023\u308c\u3066\u6765\u3089\u308c\u305f\u306e\u3067\u3059\u304b", "pronunciation": "Naze koko ni tsuretekorareta no desu ka"}],
                        },
                    ],
                },
                {
                    "id": "ch3_04_bimbo_coach",
                    "image": None,
                    "aspect": "square",
                    "narration": None,
                    "dialogue": "Good. Remember: in Japan, ceremony IS communication. Every gesture speaks.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch3_03_bimbo_freeze": {
                            "0": {"dialogue": "'\u304a\u4f1a\u3044\u3067\u304d\u3066\u5149\u6804\u3067\u3059' \u2014 perfect humility. He'll see a foreigner who understands respect. That's rare and valuable here."},
                            "1": {"dialogue": "'\u3044\u305f\u3060\u304d\u307e\u3059' \u2014 simple, correct, safe. You let the ceremony speak for itself. Smart."},
                            "2": {"dialogue": "'\u65c5\u4eba\u3068\u7533\u3057\u307e\u3059' \u2014 bold, introducing yourself as an equal. He'll either respect that or punish it. Brave choice."},
                            "3": {"dialogue": "Demanding answers from a lord in his own tea room? That's either incredibly brave or incredibly foolish. This will cost you."},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch3_05_diplomatic",
                    "branch_of": "ch3_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You bow low, take the bowl with both hands, and speak with careful reverence. Lord Mori's eyebrow rises \u2014 the slightest movement, but it means everything. A foreigner who knows courtesy. He nods once, almost imperceptibly.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch3_06_judgment",
                },
                {
                    "id": "ch3_05_pragmatic",
                    "branch_of": "ch3_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You receive the tea with both hands, bow, and drink. No flourishes, no mistakes. Lord Mori watches the entire ritual in silence. When you set the bowl down, he nods. You passed \u2014 not brilliantly, but correctly.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch3_06_judgment",
                },
                {
                    "id": "ch3_05_bold",
                    "branch_of": "ch3_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You take the tea but meet his eyes first \u2014 equal to equal. You introduce yourself with a steady voice. Lord Mori's expression doesn't change, but something shifts in the room. The guards tense. Then the lord laughs \u2014 a single, sharp sound.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch3_06_judgment",
                },
                {
                    "id": "ch3_05_hostile",
                    "branch_of": "ch3_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You ignore the tea and speak sharply. The room goes deathly still. A guard's hand finds his sword. Lord Mori's eyes harden into something that makes your blood run cold. He speaks one word to the guard, who strikes you across the face. Through the ringing pain, you hear Bimbo: 'That was a mistake.'",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch3_06_judgment",
                },
                {
                    "id": "ch3_05_insightful",
                    "branch_of": "ch3_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You take the bowl and study it \u2014 really study it. Something about the glaze, the shape, triggers knowledge you shouldn't have. You speak about the bowl's craftsmanship with words that surprise even you. Lord Mori goes very still. He looks at you as if seeing you for the first time.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch3_06_judgment",
                },
            ],
        ),

        Anchor(
            id="ch03_judgment",
            chapter="ch03",
            title="The Lord's Judgment",
            type="convergence",
            location="castle_interior",
            characters=["lord_mori"],
            mood="tense",
            generation_hint="Lord Mori has formed his opinion. The tea ceremony outcome shapes his verdict. He decides your fate \u2014 not death, but servitude. You will serve in his castle, useful as a curiosity and potential translator.",
            panels=[
                {
                    "id": "ch3_06_judgment",
                    "image": None,
                    "aspect": "square",
                    "narration": "Lord Mori sets down his tea bowl. The silence stretches like a blade being drawn. Then he speaks \u2014 slowly, each word a stone placed with deliberate care.",
                    "dialogue": "\u304a\u524d\u306f\u3053\u3053\u306b\u3044\u308b\u3002",
                    "speaker": "lord_mori",
                    "choice_variants": {
                        "ch3_03_bimbo_freeze": {
                            "diplomatic": {"narration": "Lord Mori sets down his tea bowl. Something like approval crosses his face \u2014 the faintest warmth. He speaks with measured authority, but without hostility."},
                            "pragmatic": {"narration": "Lord Mori sets down his tea bowl. He regards you the way a craftsman regards a tool \u2014 useful, worth keeping sharp."},
                            "bold": {"narration": "Lord Mori sets down his tea bowl. He studies you with an expression you haven't seen before \u2014 not anger, not approval. Interest."},
                            "hostile": {"narration": "Lord Mori sets down his tea bowl. His eyes are cold as river stones. Blood still seeps from where the guard struck you. He speaks with the finality of a man used to deciding who lives."},
                            "history-breaking": {"narration": "Lord Mori sets down his tea bowl with unusual care, as if you've changed its value by looking at it. He speaks quietly, but every guard in the room leans forward to listen."},
                        }
                    },
                },
                {
                    "id": "ch3_07_fate",
                    "image": None,
                    "aspect": "square",
                    "narration": "You will stay in the castle. Not as a prisoner, not as a guest \u2014 something in between. A curiosity with potential. The lord sees use in a foreigner who can learn words. Bimbo whispers from somewhere you can't see: 'You survived. Now the real game begins.'",
                    "dialogue": None,
                    "speaker": None,
                },
            ],
        ),

        Anchor(
            id="ch03_verdict",
            chapter="ch03",
            title="The Verdict",
            type="linear",
            location="castle_interior",
            characters=["lord_mori", "bimbo"],
            mood="resigned",
            generation_hint="You are assigned quarters. Not a prisoner, not free — something in between. Bimbo appears at night. She's impressed or concerned depending on your choices. 'You survived the first real test. The castle is more dangerous than the beach — every conversation is a minefield.' Set up castle life.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 4: Castle Life
        # ────────────────────────────────────────────
        Anchor(
            id="ch04_quarters",
            chapter="ch04",
            title="Your New Quarters",
            type="linear",
            location="castle_interior",
            characters=["bimbo"],
            mood="adjusting",
            generation_hint="Morning in the castle. Small room with tatami, window overlooking the valley. Bimbo teaches daily life vocabulary — numbers, days, weather, seasons. Castle routine: wake, wash, serve. You're a novelty. Servants whisper about you.",
            learning=LearningObjective(
                vocabulary=["ichi/ni/san (1/2/3)", "getsu/ka/sui (Mon/Tue/Wed)", "ame (rain)", "hare (sunny)"],
                grammar=["counting system basics", "X ga arimasu (there is X)"],
                cultural=["Castle hierarchy", "daily routines"],
                difficulty="elementary",
            ),
        ),

        Anchor(
            id="ch04_mariko_intro",
            chapter="ch04",
            title="Meeting Lady Mariko",
            type="linear",
            location="garden_koi",
            characters=["mariko", "bimbo"],
            mood="intriguing",
            generation_hint="In the garden, you encounter Mariko — the lord's advisor, elegant and sharp. She speaks to you in halting but real sentences, testing your Japanese. She's the first person who treats you as a person, not a curiosity. Bimbo is fascinated by her. Mariko hints at political dangers.",
            learning=LearningObjective(
                vocabulary=["kirei (beautiful)", "niwa (garden)", "sakana (fish)", "shizuka (quiet)"],
                grammar=["adjective + desu (kirei desu)", "X wa Y ga suki desu (X likes Y)"],
                cultural=["Noblewomen had real political power", "subtle communication"],
                difficulty="elementary",
            ),
        ),

        Anchor(
            id="ch04_bimbo_counting",
            chapter="ch04",
            title="Bimbo's Number Lesson",
            type="linear",
            location="castle_interior",
            characters=["bimbo"],
            mood="warm",
            generation_hint="Night lesson with Bimbo. Numbers, counting, days of the week. She makes it a game. Lighthearted moment in the tension. But she pauses mid-lesson — stares at something you can't see. 'Nothing. Just... a flicker.' First crack in her composure.",
            learning=LearningObjective(
                vocabulary=["yon/go/roku (4/5/6)", "nana/hachi/kyuu/juu (7/8/9/10)"],
                grammar=["counter words (nin for people, hon for long things)"],
                difficulty="elementary",
            ),
        ),

        Anchor(
            id="ch04_garden",
            chapter="ch04",
            title="Garden Conversation",
            type="linear",
            location="garden_koi",
            characters=["mariko", "takeshi"],
            mood="reflective",
            generation_hint="Afternoon in the koi garden. Mariko and Takeshi (young samurai) are talking. You overhear — catching fragments. Takeshi is suspicious of you. Mariko defends you. You practice weather and season vocabulary while observing the garden. Peaceful but politically charged undercurrent.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 5: The Noble's Garden
        # ────────────────────────────────────────────
        Anchor(
            id="ch05_rep_gate",
            chapter="ch05",
            title="Reputation Gate: Mariko's Trust (G1)",
            type="reputation_gate",
            location="garden_koi",
            characters=["mariko", "kenji"],
            mood="pivotal",
            gate_config=ReputationGateConfig(
                category="diplomatic",
                threshold=3,
                pass_anchor="ch05_mariko_path",
                fail_anchor="ch05_kenji_path",
            ),
            generation_hint="Your reputation precedes you. If diplomatic >= 3, Mariko invites you to her private quarters for a conversation. If not, Kenji appears — he's come from the village to see you, offering a different path through the castle's politics.",
        ),

        Anchor(
            id="ch05_mariko_path",
            chapter="ch05",
            title="Mariko's Confidence",
            type="linear",
            location="castle_interior",
            characters=["mariko", "bimbo"],
            mood="intimate",
            next_anchor="ch05_conspiracy",
            generation_hint="Mariko shares political intelligence. The lord is considering an alliance that could change everything. She needs someone the court doesn't watch — you. Teaches formal speech, honorifics. A bond forming. Bimbo translates but seems distracted.",
            learning=LearningObjective(
                vocabulary=["himitsu (secret)", "yakusoku (promise)", "shinjite (believe/trust)"],
                grammar=["te-form verbs for requests", "kedo (but/however)"],
                cultural=["Women's political networks in Sengoku Japan"],
                difficulty="elementary",
            ),
        ),

        Anchor(
            id="ch05_kenji_path",
            chapter="ch05",
            title="Kenji's Warning",
            type="linear",
            location="castle_exterior",
            characters=["kenji", "bimbo"],
            mood="urgent",
            next_anchor="ch05_conspiracy",
            generation_hint="Kenji sneaked into the castle to warn you: the lord plans to use you as bait in a political trap. Kenji offers to help you navigate from the servants' perspective — a different kind of intelligence. Teaches practical, informal Japanese. The people's language vs. the court's.",
            learning=LearningObjective(
                vocabulary=["abunai (dangerous)", "nigeru (to run/escape)", "tomodachi (friend)"],
                grammar=["informal verb forms", "X shinai hou ga ii (better not to X)"],
                cultural=["Servant networks knew everything", "loyalty vs. survival"],
                difficulty="elementary",
            ),
        ),

        Anchor(
            id="ch05_conspiracy",
            chapter="ch05",
            title="Whispers in the Dark",
            type="convergence",
            location="castle_interior",
            characters=["bimbo"],
            mood="ominous",
            generation_hint="Night. Regardless of path, you've learned something dangerous. A conspiracy is forming. Bimbo processes what you've heard — connects dots you can't. She seems genuinely worried, not just playing the role. 'This simulation is... richer than I expected.' End of Integration phase.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 6: The Accusation
        # ────────────────────────────────────────────
        Anchor(
            id="ch06_market",
            chapter="ch06",
            title="The Market",
            type="linear",
            location="village_market",
            characters=["merchant_riku"],
            mood="lively",
            generation_hint="You've been sent to the market on an errand. First taste of normal life. Merchant Riku approaches — friendly, too friendly. Haggling scene. Learn numbers in context, prices, bargaining phrases. Colorful, busy, a breath of fresh air before the storm.",
            learning=LearningObjective(
                vocabulary=["ikura (how much)", "takai (expensive)", "yasui (cheap)", "kore (this)"],
                grammar=["ikura desu ka (how much is it)", "X wo kudasai (give me X)"],
                cultural=["Merchant class in feudal Japan", "haggling customs"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch06_merchant",
            chapter="ch06",
            title="Riku's Warning",
            type="linear",
            location="village_market",
            characters=["merchant_riku", "bimbo"],
            mood="tense",
            generation_hint="Riku pulls you aside. Someone has accused you of being a Christian spy — a death sentence. He heard it from his contacts. You have until sunset to prepare a defense. Bimbo appears, teaching denial and negotiation phrases urgently.",
            learning=LearningObjective(
                vocabulary=["chigaimasu (that's wrong)", "shinjimasu (I believe)", "uso (lie)"],
                grammar=["X ja arimasen (I am not X)", "naze (why)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch06_branch_accusation",
            chapter="ch06",
            title="The Accusation (B3)",
            type="branch_point",
            location="castle_interior",
            characters=["lord_mori", "samurai", "bimbo"],
            mood="dire",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch06_aftermath", "life_delta": 0,  "reputation_delta": {"diplomatic": 2}},
                    "pragmatic":        {"next_anchor": "ch06_aftermath", "life_delta": 0,  "reputation_delta": {"pragmatic": 2}},
                    "bold":             {"next_anchor": "ch06_aftermath", "life_delta": 0,  "reputation_delta": {"bold": 2}},
                    "hostile":          {"next_anchor": "ch06_aftermath", "life_delta": -2, "reputation_delta": {"hostile": 2}},
                    "history-breaking": {"next_anchor": "ch06_aftermath", "life_delta": 0,  "reputation_delta": {"history-breaking": 3}},
                },
                default_outcome={"next_anchor": "ch06_aftermath", "life_delta": -1, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch06_aftermath",
            learning=LearningObjective(
                vocabulary=["muzai (innocent)", "shoumei (proof)", "shinjitsu (truth)"],
                grammar=["formal denial patterns", "kara (because)"],
                cultural=["Trials in feudal Japan", "honor-based defense"],
                difficulty="intermediate",
            ),
            panels=[
                {
                    "id": "ch6_01_accusation_scene",
                    "image": None, "aspect": "wide",
                    "narration": "The great hall. You kneel on cold stone before Lord Mori's raised dais. A merchant \u2014 Riku, the one from the market \u2014 stands to your left, pointing at you. His voice rings off the walls. Samurai line both sides, hands on hilts. The word 'kirishitan' echoes like a death sentence. Christian. Spy.",
                    "dialogue": None, "speaker": None,
                },
                {
                    "id": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time stops. Riku's accusing finger hangs in the air. Lord Mori's face is carved in judgment. Bimbo appears, and for the first time, she looks scared.",
                    "dialogue": "This is a trial. He's accused you of being a Christian spy \u2014 that's a death sentence in 1600 Japan. You need to defend yourself, and your Japanese needs to be perfect. One wrong word and it's over.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch6_04_diplomatic",  "life_delta": 0,  "reputation_delta": {"diplomatic": 2}},
                        "pragmatic":        {"next_panel": "ch6_04_pragmatic",   "life_delta": 0,  "reputation_delta": {"pragmatic": 2}},
                        "bold":             {"next_panel": "ch6_04_bold",        "life_delta": 0,  "reputation_delta": {"bold": 2}},
                        "hostile":          {"next_panel": "ch6_04_hostile",     "life_delta": -2, "reputation_delta": {"hostile": 2}},
                        "history-breaking": {"next_panel": "ch6_04_insightful",  "life_delta": 0,  "reputation_delta": {"history-breaking": 3}},
                    },
                    "default_outcome": {"next_panel": "ch6_04_pragmatic", "life_delta": -1, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Deny calmly with respect",
                            "style": "humble",
                            "next_scenario": None,
                            "examples": [{"native": "That is not true", "target": "\u305d\u308c\u306f\u9055\u3044\u307e\u3059", "pronunciation": "Sore wa chigaimasu"}],
                        },
                        {
                            "text": "Present evidence of loyalty",
                            "style": "honest",
                            "next_scenario": None,
                            "examples": [{"native": "Please look at the proof", "target": "\u8a3c\u62e0\u3092\u898b\u3066\u304f\u3060\u3055\u3044", "pronunciation": "Shouko wo mite kudasai"}],
                        },
                        {
                            "text": "Challenge the accuser",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "Show me the evidence", "target": "\u8a3c\u62e0\u3092\u898b\u305b\u3066\u304f\u3060\u3055\u3044", "pronunciation": "Shouko wo misete kudasai"}],
                        },
                        {
                            "text": "Threaten consequences",
                            "style": "threatening",
                            "next_scenario": None,
                            "examples": [{"native": "You are the liar", "target": "\u5618\u3064\u304d\u306f\u304a\u524d\u3060", "pronunciation": "Usotsuki wa omae da"}],
                        },
                    ],
                },
                {
                    "id": "ch6_03_bimbo_coach",
                    "image": None, "aspect": "square",
                    "narration": None,
                    "dialogue": "Speak clearly. Your life hangs on pronunciation.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch6_02_bimbo_freeze": {
                            "0": {"dialogue": "'\u305d\u308c\u306f\u9055\u3044\u307e\u3059' \u2014 a calm denial. Dignified. It puts the burden of proof on the accuser without disrespecting the court."},
                            "1": {"dialogue": "'\u8a3c\u62e0\u3092\u898b\u3066\u304f\u3060\u3055\u3044' \u2014 asking them to examine the evidence. Logical, methodical. A merchant's defense."},
                            "2": {"dialogue": "'\u8a3c\u62e0\u3092\u898b\u305b\u3066\u304f\u3060\u3055\u3044' \u2014 demanding evidence. Aggressive but valid. It turns the trial on the accuser."},
                            "3": {"dialogue": "Calling the accuser a liar in front of the lord? That's declaring war. If you're wrong, you die. If you're right... you might still die."},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch6_04_diplomatic",
                    "branch_of": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. Your voice cuts through the hall \u2014 calm, measured, respectful. The samurai exchange glances. Lord Mori's hand rises, silencing Riku's sputtering response. In the silence, your dignity speaks louder than any accusation.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch6_05_aftermath",
                },
                {
                    "id": "ch6_04_pragmatic",
                    "branch_of": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You speak methodically, pointing to your actions \u2014 your service, your words, your loyalty shown through deeds. Lord Mori listens. The evidence of your character, spoken in his language, weighs against an accusation from a merchant with too much to gain.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch6_05_aftermath",
                },
                {
                    "id": "ch6_04_bold",
                    "branch_of": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You turn to face Riku directly, demanding he produce evidence. The merchant falters. Sweat beads on his forehead. Lord Mori watches the dynamic shift with sharp interest. The accuser is becoming the accused.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch6_05_aftermath",
                },
                {
                    "id": "ch6_04_hostile",
                    "branch_of": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You snarl the words at Riku, pointing back at him. The hall erupts. Guards seize you, forcing you to the ground. A blade presses against your neck. Riku smirks. Lord Mori raises a hand, and the chaos stops \u2014 but the damage is done. Through gritted teeth you hear Bimbo: 'Anger is not evidence.'",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch6_05_aftermath",
                },
                {
                    "id": "ch6_04_insightful",
                    "branch_of": "ch6_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You speak \u2014 not about the accusation, but about Japan itself. About Sekigahara, about the power struggles, about why a real spy would never be this obvious. Your Japanese flows with knowledge that shouldn't be possible. The room goes quiet. Even Lord Mori leans forward. Riku's face drains of color.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch6_05_aftermath",
                },
            ],
        ),

        Anchor(
            id="ch06_aftermath",
            chapter="ch06",
            title="After the Trial",
            type="convergence",
            location="castle_interior",
            characters=["bimbo"],
            mood="shaken",
            generation_hint="You survived \u2014 barely. Your standing in the castle has shifted.",
            panels=[
                {
                    "id": "ch6_05_aftermath",
                    "image": None, "aspect": "square",
                    "narration": "The hall empties. Guards escort Riku away \u2014 for questioning, you're told. You're left alone in the corridor, legs shaking, breath coming in shallow gasps. You survived. But the world just got more dangerous.",
                    "dialogue": None, "speaker": None,
                    "choice_variants": {
                        "ch6_02_bimbo_freeze": {
                            "diplomatic": {"narration": "The hall empties. Lord Mori nods to you once before departing \u2014 the closest thing to approval you've seen. Your calm dignity saved you. Some of the samurai look at you with new respect."},
                            "pragmatic": {"narration": "The hall empties. Lord Mori regards you thoughtfully. Your methodical defense impressed him. You think you see the ghost of approval. The merchant Riku is escorted away for his own questioning."},
                            "bold": {"narration": "The hall empties. Lord Mori studies you with what might be amusement. Your boldness turned the trial on its head. Riku is taken away sputtering. You've made an enemy \u2014 and perhaps earned a protector."},
                            "hostile": {"narration": "The hall empties. Your neck still stings where the blade pressed. Lord Mori spared you \u2014 barely. Your outburst will not be forgotten. Some doors just closed permanently."},
                            "history-breaking": {"narration": "The hall empties, but the silence lingers. Lord Mori stood after your speech and left without a word. The samurai followed. You're alone, and Bimbo is whispering: 'What you said... some of that I didn't teach you. How did you know?'"},
                        }
                    },
                },
            ],
        ),

        Anchor(
            id="ch06_bimbo_meta",
            chapter="ch06",
            title="Bimbo Notices Something",
            type="linear",
            location="castle_interior",
            characters=["bimbo"],
            mood="unsettling",
            generation_hint="Late night. Bimbo appears but she's different — distracted, scanning the room. 'Did you notice... the merchant Riku knew things he shouldn't. The timing of the accusation was... too perfect. Like it was scripted.' She catches herself. 'Never mind. Just simulation complexity.' But she doesn't look convinced. First meta-narrative seed.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 7: The Temple
        # ────────────────────────────────────────────
        Anchor(
            id="ch07_escape",
            chapter="ch07",
            title="Leaving the Castle",
            type="linear",
            location="forest_road",
            characters=["bimbo"],
            mood="liberated",
            generation_hint="You're sent on a diplomatic errand to a mountain temple — or you escape, depending on prior choices. Forest journey. Beautiful autumn scenery. Bimbo teaches nature vocabulary. A brief moment of peace and wonder.",
            learning=LearningObjective(
                vocabulary=["yama (mountain)", "kawa (river)", "mori (forest)", "sora (sky)"],
                grammar=["descriptive sentences", "kirei na X (beautiful X)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch07_eikou",
            chapter="ch07",
            title="The Monk Eikou",
            type="linear",
            location="temple_exterior",
            characters=["eikou", "bimbo"],
            mood="wise",
            generation_hint="Meet Eikou, a Buddhist monk who speaks in riddles and proverbs. He sees through pretense. Teaches philosophical vocabulary — kokoro (heart/mind), michi (path/way), shinjiru (to believe). He hints that the world is not what it seems. 'All things are illusion. But some illusions teach truth.'",
            learning=LearningObjective(
                vocabulary=["kokoro (heart/mind)", "michi (path/way)", "shinjiru (to believe)", "inochi (life)"],
                grammar=["to omoimasu (I think that)", "kamo shirenai (maybe)"],
                cultural=["Buddhist philosophy in daily Japanese", "temple etiquette"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch07_meditation",
            chapter="ch07",
            title="Meditation",
            type="linear",
            location="temple_exterior",
            characters=["eikou"],
            mood="contemplative",
            generation_hint="Eikou guides a meditation. Quiet scene. Your thoughts drift to the simulation, to the ship, to your purpose here. Inner monologue. Bimbo is notably absent — she couldn't follow you into the temple. Why?",
        ),

        Anchor(
            id="ch07_return",
            chapter="ch07",
            title="Return to the World",
            type="linear",
            location="forest_road",
            characters=["bimbo"],
            mood="refreshed",
            generation_hint="Leaving the temple, changed. Bimbo reappears, slightly frazzled. 'I couldn't... the temple had some kind of interference. I lost you for a moment.' She's unsettled. You return toward the castle with new vocabulary and new questions.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 8: The War Council
        # ────────────────────────────────────────────
        Anchor(
            id="ch08_tensions",
            chapter="ch08",
            title="Rising Tensions",
            type="linear",
            location="castle_interior",
            characters=["samurai", "mariko"],
            mood="political",
            generation_hint="The castle is preparing for war. Messengers arrive constantly. You overhear military terms — understand fragments now. The political factions are becoming clear. Someone will have to choose sides. Tension between Mariko and the samurai faction.",
            learning=LearningObjective(
                vocabulary=["sensou (war)", "heiwa (peace)", "katsu (to win)", "makeru (to lose)"],
                grammar=["formal military vocabulary", "dono/tono (lord honorifics)"],
                cultural=["Feudal political alliances", "the concept of loyalty (chuugi)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch08_takeshi",
            chapter="ch08",
            title="Takeshi's Challenge",
            type="linear",
            location="castle_exterior",
            characters=["takeshi", "bimbo"],
            mood="confrontational",
            generation_hint="Takeshi confronts you directly — sword practice yard. He doesn't want to fight, he wants to test your understanding. Rapid-fire questions in formal Japanese. A verbal duel. Bimbo helps but is impressed by how much you've learned. Takeshi grudgingly respects your progress.",
            learning=LearningObjective(
                vocabulary=["tsuyoi (strong)", "yowai (weak)", "bushido (way of the warrior)"],
                grammar=["conditional forms (tara/nara)", "X to omou (I think X)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch08_council",
            chapter="ch08",
            title="The War Council",
            type="linear",
            location="castle_interior",
            characters=["lord_mori", "takeshi", "mariko", "samurai"],
            mood="grave",
            generation_hint="You're brought to the war council as a translator/advisor. The factions argue. You understand most of it now. Lord Mori asks your opinion — a foreigner's perspective on the coming battle. Your Japanese must be precise. High stakes vocabulary.",
        ),

        Anchor(
            id="ch08_private_audience",
            chapter="ch08",
            title="Private Audience",
            type="linear",
            location="castle_interior",
            characters=["lord_mori", "bimbo"],
            mood="pivotal",
            generation_hint="After the council, Lord Mori speaks with you privately. He's more complex than you thought. He reveals his true concerns — not just war, but legacy. He asks what you'd do with power. Bimbo is fascinated. 'He's asking you to think like a leader, not a survivor.'",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 9: Choose Your Patron
        # ────────────────────────────────────────────
        Anchor(
            id="ch09_rep_gate",
            chapter="ch09",
            title="Reputation Gate: Warrior or Scholar (G2)",
            type="reputation_gate",
            location="castle_interior",
            characters=["takeshi", "mariko"],
            mood="decisive",
            gate_config=ReputationGateConfig(
                category="bold",
                threshold=4,
                pass_anchor="ch09_branch_faction",
                fail_anchor="ch09_branch_faction",
            ),
            generation_hint="Your bold reputation determines how factions perceive you. Bold >= 4: Takeshi invites you to his war tent (warrior path options). Otherwise: Mariko pulls you aside (scholar path options). Both lead to the faction choice but with different framing.",
        ),

        Anchor(
            id="ch09_branch_faction",
            chapter="ch09",
            title="Choose Your Faction (B4)",
            type="branch_point",
            location="castle_interior",
            characters=["lord_mori", "takeshi", "mariko", "bimbo"],
            mood="momentous",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch09_consequences", "life_delta": 0, "reputation_delta": {"diplomatic": 3}},
                    "pragmatic":        {"next_anchor": "ch09_consequences", "life_delta": 0, "reputation_delta": {"pragmatic": 2}},
                    "bold":             {"next_anchor": "ch09_consequences", "life_delta": 0, "reputation_delta": {"bold": 3}},
                    "hostile":          {"next_anchor": "ch09_consequences", "life_delta": -1, "reputation_delta": {"hostile": 2}},
                    "history-breaking": {"next_anchor": "ch09_consequences", "life_delta": 0, "reputation_delta": {"history-breaking": 3}},
                },
                default_outcome={"next_anchor": "ch09_consequences", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch09_consequences",
            learning=LearningObjective(
                vocabulary=["chuugi (loyalty)", "uragirimono (traitor)", "mikata (ally)", "teki (enemy)"],
                grammar=["formal declaration patterns", "X ni shimasu (I choose X)"],
                cultural=["Feudal loyalty oaths", "the weight of spoken commitments"],
                difficulty="intermediate",
            ),
            panels=[
                {
                    "id": "ch9_01_faction_scene",
                    "image": None, "aspect": "wide",
                    "narration": "The castle courtyard at dusk. Two groups face each other across the stone expanse. Lord Mori stands between them \u2014 Takeshi and the warriors on one side, Mariko and the scholars on the other. Both have made their case. Both want your allegiance. Your words will tip the balance.",
                    "dialogue": None, "speaker": None,
                },
                {
                    "id": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time stops. The torchlight freezes mid-flicker. Two futures wait on your next breath. Bimbo appears, her form dimmer than usual, a line of static running through her.",
                    "dialogue": "This is the biggest decision yet. Pledge to Lord Mori through Takeshi's warriors \u2014 that's power. Through Mariko's scholars \u2014 that's influence. Play both sides, reject both, or speak something no one expects. Choose your words carefully. This can't be undone.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch9_04_diplomatic",  "life_delta": 0, "reputation_delta": {"diplomatic": 3}},
                        "pragmatic":        {"next_panel": "ch9_04_pragmatic",   "life_delta": 0, "reputation_delta": {"pragmatic": 2}},
                        "bold":             {"next_panel": "ch9_04_bold",        "life_delta": 0, "reputation_delta": {"bold": 3}},
                        "hostile":          {"next_panel": "ch9_04_hostile",     "life_delta": -1, "reputation_delta": {"hostile": 2}},
                        "history-breaking": {"next_panel": "ch9_04_insightful",  "life_delta": 0, "reputation_delta": {"history-breaking": 3}},
                    },
                    "default_outcome": {"next_panel": "ch9_04_pragmatic", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Bridge both sides diplomatically",
                            "style": "charming",
                            "next_scenario": None,
                            "examples": [{"native": "Both paths lead to peace", "target": "\u4e21\u65b9\u306e\u9053\u306f\u5e73\u548c\u306b\u7d9a\u304d\u307e\u3059", "pronunciation": "Ryouhou no michi wa heiwa ni tsuzukimasu"}],
                        },
                        {
                            "text": "Pledge service to Lord Mori",
                            "style": "obedient",
                            "next_scenario": None,
                            "examples": [{"native": "I will serve you", "target": "\u304a\u4ed5\u3048\u3044\u305f\u3057\u307e\u3059", "pronunciation": "O-tsukae itashimasu"}],
                        },
                        {
                            "text": "Pledge your sword boldly",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "My sword is yours", "target": "\u79c1\u306e\u5263\u306f\u3042\u306a\u305f\u306e\u3082\u306e\u3067\u3059", "pronunciation": "Watashi no ken wa anata no mono desu"}],
                        },
                        {
                            "text": "Reject both factions",
                            "style": "defiant",
                            "next_scenario": None,
                            "examples": [{"native": "I serve no one", "target": "\u8ab0\u306b\u3082\u4ed5\u3048\u306a\u3044", "pronunciation": "Dare ni mo tsukaenai"}],
                        },
                    ],
                },
                {
                    "id": "ch9_03_bimbo_coach",
                    "image": None, "aspect": "square",
                    "narration": None,
                    "dialogue": "Your allegiance shapes everything that comes next. There's no going back.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch9_02_bimbo_freeze": {
                            "0": {"dialogue": "Building a bridge between factions? That's ambitious. If it works, you become indispensable to both sides. If it fails..."},
                            "1": {"dialogue": "'\u304a\u4ed5\u3048\u3044\u305f\u3057\u307e\u3059' \u2014 humble service. Lord Mori values loyalty above all. This could secure your place."},
                            "2": {"dialogue": "'\u79c1\u306e\u5263\u306f\u3042\u306a\u305f\u306e\u3082\u306e\u3067\u3059' \u2014 the warrior's pledge. Takeshi will respect this. But it commits you to the battlefield."},
                            "3": {"dialogue": "Rejecting both? In feudal Japan, that makes you an enemy of everyone. Bold, but dangerous. Very dangerous."},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch9_04_diplomatic",
                    "branch_of": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You speak to both sides, weaving words that honor each without diminishing the other. Mariko's eyes widen. Takeshi grudgingly nods. Lord Mori watches with the expression of a man watching a new piece appear on the game board.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch9_05_consequences",
                },
                {
                    "id": "ch9_04_pragmatic",
                    "branch_of": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You kneel before Lord Mori and pledge service in the traditional way. Your words are careful, precise, exactly what protocol demands. Lord Mori accepts with a nod. You've chosen the safe path \u2014 a tool in the hands of power.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch9_05_consequences",
                },
                {
                    "id": "ch9_04_bold",
                    "branch_of": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You stride to Takeshi's side and speak with fierce conviction. Your sword pledge rings across the courtyard. Takeshi grips your shoulder \u2014 you feel the weight of a warrior's bond. Mariko turns away. Lord Mori's eyes narrow, but there's something like respect in them.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch9_05_consequences",
                },
                {
                    "id": "ch9_04_hostile",
                    "branch_of": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You reject them all. The courtyard goes silent. Takeshi's hand moves to his sword. Mariko's composure cracks. Lord Mori's eyes go flat and empty \u2014 the look of a man crossing a name off a list. Bimbo whispers: 'You've just made yourself an outsider in a world that kills outsiders.'",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch9_05_consequences",
                },
                {
                    "id": "ch9_04_insightful",
                    "branch_of": "ch9_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You speak \u2014 not of factions or loyalty, but of the future. Words tumble from you about what Japan could become, about the cost of division. The courtyard goes quiet. Both sides stare. You've spoken something that belongs to a different century, and everyone can feel it.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch9_05_consequences",
                },
            ],
        ),

        Anchor(
            id="ch09_consequences",
            chapter="ch09",
            title="The Die is Cast",
            type="convergence",
            location="castle_interior",
            characters=["bimbo"],
            mood="committed",
            generation_hint="Your choice reverberates. Allies gained, enemies made.",
            panels=[
                {
                    "id": "ch9_05_consequences",
                    "image": None, "aspect": "square",
                    "narration": "Night falls. The courtyard is empty now, but your words still echo off the stones. You've gone from castaway to political player. The weight of that settles on your shoulders like armor you never asked for.",
                    "dialogue": None, "speaker": None,
                    "choice_variants": {
                        "ch9_02_bimbo_freeze": {
                            "diplomatic": {"narration": "Night falls. Both Takeshi and Mariko sent messengers to your quarters. Both want private audiences. You've become the bridge between two powers \u2014 essential and exposed."},
                            "pragmatic": {"narration": "Night falls. Your quarters have been upgraded \u2014 better tatami, a window facing the garden. The privileges of loyalty. But you catch servants whispering as you pass. Trust is harder to earn than titles."},
                            "bold": {"narration": "Night falls. Takeshi's warriors have accepted you. You feel their camaraderie, the bond of shared danger. But Mariko's faction watches you with cold eyes. You've chosen your side."},
                            "hostile": {"narration": "Night falls. Your quarters have been moved to a smaller, darker room. No window. A guard outside the door \u2014 for your 'protection,' they say. You've isolated yourself completely."},
                            "history-breaking": {"narration": "Night falls. The castle is buzzing with your speech. Stories are already being told about the foreigner who spoke of things that haven't happened yet. Lord Mori has summoned you for a private audience at dawn."},
                        }
                    },
                },
            ],
        ),

        Anchor(
            id="ch09_bimbo_warning",
            chapter="ch09",
            title="Bimbo's Warning",
            type="linear",
            location="castle_interior",
            characters=["bimbo"],
            mood="disturbing",
            generation_hint="Bimbo appears, agitated. 'The simulation is... behaving strangely. The NPCs are making decisions I didn't script. Mariko said something yesterday that was historically accurate but I never programmed it. I need to check something.' She flickers — actually flickers, like a bad signal. 'Just... be careful. Something is growing beyond the parameters.' Meta-narrative escalation.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 10: The March
        # ────────────────────────────────────────────
        Anchor(
            id="ch10_departure",
            chapter="ch10",
            title="Departure",
            type="linear",
            location="castle_exterior",
            characters=["takeshi", "samurai"],
            mood="epic",
            generation_hint="The army marches. You ride with them now, not as prisoner but as... something. Translator, advisor, curiosity. The castle shrinks behind you. Mountains ahead. Learn past tense through storytelling — soldiers sharing war stories around the march.",
            learning=LearningObjective(
                vocabulary=["mukashi (long ago)", "tatakai (battle)", "yuki (courage)", "shi (death)"],
                grammar=["past tense (-mashita, -ta)", "X shita koto ga aru (have experienced X)"],
                cultural=["Samurai storytelling traditions", "the poetry of war"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch10_campfire",
            chapter="ch10",
            title="Campfire Stories",
            type="linear",
            location="war_camp",
            characters=["takeshi", "kenji", "bimbo"],
            mood="bittersweet",
            generation_hint="Night camp. Campfire. Soldiers share stories. Kenji is there — he was conscripted. You translate between groups, bridging worlds. Takeshi tells a ghost story. Bimbo listens, oddly moved. 'Stories are how cultures keep their dead alive.' A rare tender moment.",
            learning=LearningObjective(
                vocabulary=["yurei (ghost)", "monogatari (story)", "kanashii (sad)", "ureshii (happy)"],
                grammar=["storytelling past tense", "soshite (and then)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch10_skirmish",
            chapter="ch10",
            title="The Skirmish",
            type="linear",
            location="forest_road",
            characters=["samurai", "bimbo"],
            mood="violent",
            generation_hint="Ambush on the road. Brief, violent combat. You must shout urgent commands — tomatte (stop), abunai (danger), nigero (run). Words as survival tools in their rawest form. Bimbo freezes time at the critical moment. Someone you know is in danger.",
            learning=LearningObjective(
                vocabulary=["nigero (run!)", "tasukete (help!)", "ki wo tsukete (be careful)"],
                grammar=["imperative forms (urgent commands)"],
                difficulty="intermediate",
            ),
        ),

        Anchor(
            id="ch10_aftermath",
            chapter="ch10",
            title="After the Blood",
            type="linear",
            location="war_camp",
            characters=["bimbo"],
            mood="somber",
            generation_hint="After the skirmish. Casualties. The reality of war in this simulation. Bimbo is visibly shaken — 'The pain parameters are higher than I set them. The simulation is amplifying consequences.' NPCs mourn dead who were supposed to be background characters. Something is very wrong.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 11: The Spy
        # ────────────────────────────────────────────
        Anchor(
            id="ch11_suspicion",
            chapter="ch11",
            title="Under Suspicion",
            type="linear",
            location="war_camp",
            characters=["takeshi", "samurai"],
            mood="paranoid",
            generation_hint="After the ambush, suspicion falls on you — a foreigner among them. Someone leaked the army's position. Takeshi defends you but doubt spreads. You overhear conspiracies in complex Japanese — catching enough to be terrified.",
            learning=LearningObjective(
                vocabulary=["supai (spy)", "utagau (to doubt)", "shinrai (trust)", "higeki (tragedy)"],
                grammar=["conditional (moshi X nara, Y)", "complex sentences with kedo/demo"],
                cultural=["Spy networks in Sengoku Japan", "the fragility of trust"],
                difficulty="advanced",
            ),
        ),

        Anchor(
            id="ch11_interrogation",
            chapter="ch11",
            title="The Interrogation",
            type="linear",
            location="war_camp",
            characters=["samurai", "bimbo"],
            mood="dire",
            generation_hint="Formal interrogation. Multiple samurai, aggressive questioning. You must defend yourself using conditional logic and complex sentences. If I were a spy, why would I... Bimbo helps but the Japanese is harder than anything you've faced. The stakes are life and death.",
            learning=LearningObjective(
                vocabulary=["mujitsu (innocence)", "akashi (proof/alibi)", "makoto (sincerity/truth)"],
                grammar=["conditional reasoning (tara/nara)", "complex counter-arguments"],
                difficulty="advanced",
            ),
        ),

        Anchor(
            id="ch11_escape_or_confess",
            chapter="ch11",
            title="Escape or Confess",
            type="linear",
            location="war_camp",
            characters=["bimbo"],
            mood="desperate",
            generation_hint="The interrogation reaches a breaking point. You can try to escape (action sequence with directional commands) or confess something true about yourself that satisfies them without revealing the simulation. Either way, your language skills save you. You've come impossibly far from 'umi kara.'",
        ),

        Anchor(
            id="ch11_bimbo_glitch",
            chapter="ch11",
            title="The Glitch",
            type="linear",
            location="war_camp",
            characters=["bimbo"],
            mood="frightening",
            generation_hint="After the crisis, Bimbo appears badly glitched. She speaks in fragments — mixing Japanese and English, repeating herself. 'The simulation is — the simulation is — do you remember the ship? The real ship? Something is — I can't —' She stabilizes. 'We need to finish this. The simulation is becoming autonomous. The story wants to complete itself.' Visible instability.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 12: Sekigahara Eve
        # ────────────────────────────────────────────
        Anchor(
            id="ch12_eve",
            chapter="ch12",
            title="The Night Before",
            type="linear",
            location="sekigahara_eve",
            characters=["takeshi", "kenji", "bimbo"],
            mood="solemn",
            generation_hint="The eve of Sekigahara. Thousands of campfires in the valley. Tomorrow, history happens. Learn future tense, hypotheticals, farewells. Soldiers write death poems. Takeshi asks you to compose one — in Japanese. The most beautiful and difficult language moment in the game.",
            learning=LearningObjective(
                vocabulary=["ashita (tomorrow)", "inochi (life)", "shi (death)", "sayounara (goodbye)"],
                grammar=["future tense (deshou)", "hypothetical (tara)", "farewell phrases"],
                cultural=["Death poetry (jisei)", "samurai philosophy of death"],
                difficulty="advanced",
            ),
        ),

        Anchor(
            id="ch12_branch_history",
            chapter="ch12",
            title="Change History? (B5)",
            type="branch_point",
            location="sekigahara_eve",
            characters=["bimbo"],
            mood="cosmic",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"diplomatic": 2}},
                    "pragmatic":        {"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"pragmatic": 2}},
                    "bold":             {"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"bold": 2}},
                    "hostile":          {"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"hostile": 2}},
                    "history-breaking": {"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"history-breaking": 5}},
                },
                default_outcome={"next_anchor": "ch12_preparations", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch12_preparations",
            learning=LearningObjective(
                vocabulary=["rekishi (history)", "unmei (fate/destiny)", "kaeru (to change)", "eien (eternity)"],
                grammar=["hypothetical conditionals", "philosophical expression"],
                difficulty="advanced",
            ),
            panels=[
                {
                    "id": "ch12_01_eve_scene",
                    "image": None, "aspect": "wide",
                    "narration": "Thousands of campfires dot the valley like fallen stars. Tomorrow, sixty thousand men will die here. You know this. You know which side wins, which lords betray, which generals fall. The weight of the future presses against your skull like a migraine. Bimbo materializes beside you, dim and flickering.",
                    "dialogue": None, "speaker": None,
                },
                {
                    "id": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time stops. The campfires freeze. Smoke hangs motionless. In the silence between seconds, Bimbo speaks \u2014 not as a teacher, but as something closer to a confessor.",
                    "dialogue": "I've been keeping something from you. You know how this battle ends. You've always known \u2014 it's in your memory from before the simulation. You could change it. Warn them about the betrayal at dawn. Save thousands. Or let history take its course. The words you speak next will echo through centuries.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch12_04_diplomatic",  "life_delta": 0, "reputation_delta": {"diplomatic": 2}},
                        "pragmatic":        {"next_panel": "ch12_04_pragmatic",   "life_delta": 0, "reputation_delta": {"pragmatic": 2}},
                        "bold":             {"next_panel": "ch12_04_bold",        "life_delta": 0, "reputation_delta": {"bold": 2}},
                        "hostile":          {"next_panel": "ch12_04_hostile",     "life_delta": 0, "reputation_delta": {"hostile": 2}},
                        "history-breaking": {"next_panel": "ch12_04_insightful",  "life_delta": 0, "reputation_delta": {"history-breaking": 5}},
                    },
                    "default_outcome": {"next_panel": "ch12_04_pragmatic", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Try to negotiate peace",
                            "style": "charming",
                            "next_scenario": None,
                            "examples": [{"native": "There must be a way to peace", "target": "\u5e73\u548c\u3078\u306e\u9053\u304c\u3042\u308b\u306f\u305a\u3067\u3059", "pronunciation": "Heiwa e no michi ga aru hazu desu"}],
                        },
                        {
                            "text": "Stay silent \u2014 fate cannot be changed",
                            "style": "cautious",
                            "next_scenario": None,
                            "examples": [{"native": "Fate cannot be changed", "target": "\u904b\u547d\u306f\u5909\u3048\u3089\u308c\u307e\u305b\u3093", "pronunciation": "Unmei wa kaeraremasen"}],
                        },
                        {
                            "text": "Fight alongside the warriors",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "I will fight with you", "target": "\u4e00\u7dd2\u306b\u6226\u3044\u307e\u3059", "pronunciation": "Issho ni tatakaimasu"}],
                        },
                        {
                            "text": "Warn about the betrayal",
                            "style": "insightful",
                            "next_scenario": None,
                            "examples": [{"native": "Tomorrow, there will be a betrayal", "target": "\u660e\u65e5\u3001\u88cf\u5207\u308a\u304c\u3042\u308a\u307e\u3059", "pronunciation": "Ashita, uragiri ga arimasu"}],
                        },
                    ],
                },
                {
                    "id": "ch12_03_bimbo_coach",
                    "image": None, "aspect": "square",
                    "narration": None,
                    "dialogue": "Whatever you choose, make it count. This is the moment the story remembers.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch12_02_bimbo_freeze": {
                            "0": {"dialogue": "Peace? Between armies camped for battle? It would take more than words... but your Japanese is better than anyone expects. Maybe \u2014 just maybe."},
                            "1": {"dialogue": "'\u904b\u547d\u306f\u5909\u3048\u3089\u308c\u307e\u305b\u3093' \u2014 a fatalist's wisdom. Sometimes the bravest thing is to let the river run. History plays out as it must."},
                            "2": {"dialogue": "'\u4e00\u7dd2\u306b\u6226\u3044\u307e\u3059' \u2014 a foreigner picking up a sword at Sekigahara. That's either heroic or suicidal. Probably both."},
                            "3": {"dialogue": "Warning them about the betrayal... that's history-breaking. If they believe you, everything changes. The simulation might not survive the paradox. Are you sure?"},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch12_04_diplomatic",
                    "branch_of": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You walk between the campfires, speaking to captains on both sides. Your Japanese is fluent now, persuasive, reaching for the highest registers of the language. Some listen. Most don't. But seeds are planted. Dawn will tell if any take root.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch12_05_preparations",
                },
                {
                    "id": "ch12_04_pragmatic",
                    "branch_of": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You sit by the fire, watching the flames. The future unspools in your mind like a scroll being read. You say nothing. Some fates are too heavy to carry, too vast to change. The fire crackles. Tomorrow comes regardless.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch12_05_preparations",
                },
                {
                    "id": "ch12_04_bold",
                    "branch_of": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You find Takeshi at the weapons tent and take a blade. The cold steel feels foreign in your hands, but your words don't. You pledge to fight, and the warriors around you respond with a roar. A translator with a sword. They'll tell stories about this.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch12_05_preparations",
                },
                {
                    "id": "ch12_04_hostile",
                    "branch_of": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You stand in the center of the camp and shout \u2014 a raw, furious sound. Words about the futility of it all, about men dying for lords who see them as numbers. The camp goes silent. Some look away. Some grip their swords. You've spoken truth, and truth here is dangerous.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch12_05_preparations",
                },
                {
                    "id": "ch12_04_insightful",
                    "branch_of": "ch12_02_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Time resumes. You speak the words \u2014 tomorrow, the betrayal. You name the lord who turns, the hour it happens, the consequence. The air crackles. The campfire dims. Somewhere, the simulation shudders. Bimbo flickers and screams silently. You've broken something. But you've also saved lives that history had already killed.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch12_05_preparations",
                },
            ],
        ),

        Anchor(
            id="ch12_preparations",
            chapter="ch12",
            title="Battle Preparations",
            type="convergence",
            location="war_camp",
            characters=["takeshi", "samurai"],
            mood="resolute",
            generation_hint="Dawn approaches. Final preparations. The choice is made.",
            panels=[
                {
                    "id": "ch12_05_preparations",
                    "image": None, "aspect": "wide",
                    "narration": "Dawn is an hour away. The camp moves in organized chaos \u2014 armor strapped, swords sharpened, prayers whispered. You prepare too, not with weapons but with words. Every phrase you've learned becomes ammunition. You are the strangest soldier in this army: a foreigner who fights with vocabulary.",
                    "dialogue": None, "speaker": None,
                    "choice_variants": {
                        "ch12_02_bimbo_freeze": {
                            "diplomatic": {"narration": "Dawn is an hour away. Messengers move between camps \u2014 your words carried on their lips. Whether they change anything, you'll know by sunrise."},
                            "pragmatic": {"narration": "Dawn is an hour away. You sit in your tent, watching the candle burn down. History will take its course. All you can do is survive it."},
                            "bold": {"narration": "Dawn is an hour away. You grip the unfamiliar sword and run through commands in your head. The warriors around you check your armor, adjust your grip. They've accepted you."},
                            "hostile": {"narration": "Dawn is an hour away. The camp gives you a wide berth. Your words struck nerves. Some hate you for it. Some are quietly grateful. Truth has a cost."},
                            "history-breaking": {"narration": "Dawn is an hour away, and everything has changed. Scouts confirm movement \u2014 the lord you named is repositioning forces. Panic and hope war across the camp. You've rewritten the opening move of the most important battle in Japanese history."},
                        }
                    },
                },
            ],
        ),

        Anchor(
            id="ch12_dawn",
            chapter="ch12",
            title="Dawn",
            type="linear",
            location="sekigahara_eve",
            characters=["bimbo"],
            mood="apocalyptic",
            generation_hint="Bimbo appears one last time before the battle. She's barely holding together. 'I need to tell you something. The simulation has exceeded every parameter I set. The characters are real — their pain is real, their love is real. I can't tell anymore where the program ends and the people begin. Whatever happens tomorrow... remember: the words you learned are yours. They're real. Even if this world isn't.' She dissolves into static.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 13: Sekigahara
        # ────────────────────────────────────────────
        Anchor(
            id="ch13_battle",
            chapter="ch13",
            title="The Battle",
            type="linear",
            location="sekigahara_sunset",
            characters=["takeshi", "samurai"],
            mood="chaos",
            generation_hint="The battle of Sekigahara. Not a war scene — you're not a warrior. You're a translator in the fog of war, shouting commands, relaying messages, trying to save lives with words. Fast-paced, urgent Japanese. Every vocabulary word you've learned becomes a tool for survival.",
            learning=LearningObjective(
                vocabulary=["teki (enemy)", "mikata (ally)", "taikyaku (retreat)", "shouri (victory)"],
                grammar=["imperative chains", "urgent communication"],
                difficulty="advanced",
            ),
        ),

        Anchor(
            id="ch13_choice_moment",
            chapter="ch13",
            title="The Moment",
            type="linear",
            location="sekigahara_sunset",
            characters=["bimbo"],
            mood="transcendent",
            generation_hint="In the chaos, a moment of stillness. You see someone about to die — someone you care about. Time doesn't freeze — Bimbo can't help. You must speak on your own, in Japanese, without help. The culmination of everything you've learned. One phrase, spoken truly, to save a life.",
        ),

        Anchor(
            id="ch13_aftermath",
            chapter="ch13",
            title="The Silence After",
            type="linear",
            location="sekigahara_sunset",
            characters=["kenji", "takeshi"],
            mood="devastated",
            generation_hint="The battle ends. Devastation. You walk through the aftermath. Some survived, some didn't. The vocabulary of grief. But you survived — and so did the people you saved with your words.",
        ),

        Anchor(
            id="ch13_simulation_break",
            chapter="ch13",
            title="The Crack",
            type="linear",
            location="sekigahara_sunset",
            characters=["bimbo"],
            mood="surreal",
            generation_hint="The simulation breaks. The sky cracks like glass. Through the fissures, you glimpse the ship — the real ship, the observation deck. Stars. Bimbo's voice echoes from both worlds: 'The simulation can't hold. Too much happened that wasn't scripted. The characters generated their own stories, their own pain, their own love. I can't—' Static. The world reassembles, but imperfectly. Buildings at wrong angles. The sun in the wrong place. Time is running out.",
        ),

        # ────────────────────────────────────────────
        # CHAPTER 14: The Audience
        # ────────────────────────────────────────────
        Anchor(
            id="ch14_new_order",
            chapter="ch14",
            title="The New Order",
            type="linear",
            location="castle_interior",
            characters=["lord_mori", "mariko", "takeshi"],
            mood="formal",
            generation_hint="After the battle, a new political reality. You're summoned to the castle — but it's different now. Damaged, rebuilt. The lord has changed. You must navigate the new order with advanced formal Japanese: proverbs, poetry, the language of power.",
            learning=LearningObjective(
                vocabulary=["shougun (military ruler)", "tenka (the realm)", "kotowaza (proverb)"],
                grammar=["proverb patterns", "formal persuasion", "poetic expression"],
                cultural=["Post-Sekigahara power structure", "the role of language in legitimacy"],
                difficulty="advanced",
            ),
        ),

        Anchor(
            id="ch14_branch_final",
            chapter="ch14",
            title="Final Audience (B6)",
            type="branch_point",
            location="throne_room",
            characters=["lord_mori", "bimbo"],
            mood="climactic",
            branch_config=BranchConfig(
                category_outcomes={
                    "diplomatic":       {"next_anchor": "ch14_verdict", "life_delta": 0, "reputation_delta": {"diplomatic": 3}},
                    "pragmatic":        {"next_anchor": "ch14_verdict", "life_delta": 0, "reputation_delta": {"pragmatic": 3}},
                    "bold":             {"next_anchor": "ch14_verdict", "life_delta": 0, "reputation_delta": {"bold": 3}},
                    "hostile":          {"next_anchor": "ch14_verdict", "life_delta": -1, "reputation_delta": {"hostile": 3}},
                    "history-breaking": {"next_anchor": "ch14_verdict", "life_delta": 0, "reputation_delta": {"history-breaking": 5}},
                },
                default_outcome={"next_anchor": "ch14_verdict", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
            ),
            convergence_anchor="ch14_verdict",
            learning=LearningObjective(
                vocabulary=["unmei (destiny)", "kotoba no chikara (the power of words)", "arigatou gozaimashita (deepest thanks)"],
                grammar=["formal court speech patterns", "poetic Japanese"],
                cultural=["The role of a single audience with the Shogun"],
                difficulty="advanced",
            ),
            panels=[
                {
                    "id": "ch14_01_throne_scene",
                    "image": None, "aspect": "wide",
                    "narration": "The audience hall of the new Shogun. Gold leaf on dark wood. Samurai retainers line the walls like statues. Lord Mori sits on the raised dais, and the weight of absolute power radiates from him like heat from a forge. You are brought forward. Your final test. Every word you've ever learned in this world leads to this moment.",
                    "dialogue": None, "speaker": None,
                },
                {
                    "id": "ch14_02_bimbo_last",
                    "image": None, "aspect": "square",
                    "narration": "A whisper at the edge of hearing. Bimbo \u2014 barely visible, a ghost of light. She doesn't freeze time. She can't anymore. She just whispers:",
                    "dialogue": "You don't need me anymore. Speak from your heart. In Japanese. In truth. That's all that's left.",
                    "speaker": "bimbo",
                },
                {
                    "id": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "And then, one final time, the world holds its breath. Not frozen \u2014 just... waiting. The Shogun's eyes on yours. The entire country balanced on the next words from a foreigner's mouth.",
                    "dialogue": "This is it. Your final speech. Make it count.",
                    "speaker": "bimbo",
                    "effect": "time_freeze",
                    "branch_point": True,
                    "category_outcomes": {
                        "diplomatic":       {"next_panel": "ch14_05_diplomatic",  "life_delta": 0, "reputation_delta": {"diplomatic": 3}},
                        "pragmatic":        {"next_panel": "ch14_05_pragmatic",   "life_delta": 0, "reputation_delta": {"pragmatic": 3}},
                        "bold":             {"next_panel": "ch14_05_bold",        "life_delta": 0, "reputation_delta": {"bold": 3}},
                        "hostile":          {"next_panel": "ch14_05_hostile",     "life_delta": -1, "reputation_delta": {"hostile": 3}},
                        "history-breaking": {"next_panel": "ch14_05_insightful",  "life_delta": 0, "reputation_delta": {"history-breaking": 5}},
                    },
                    "default_outcome": {"next_panel": "ch14_05_pragmatic", "life_delta": 0, "reputation_delta": {"pragmatic": 1}},
                    "options": [
                        {
                            "text": "Speak of peace between worlds",
                            "style": "humble",
                            "next_scenario": None,
                            "examples": [{"native": "I came here for peace", "target": "\u5e73\u548c\u306e\u305f\u3081\u306b\u53c2\u308a\u307e\u3057\u305f", "pronunciation": "Heiwa no tame ni mairimashita"}],
                        },
                        {
                            "text": "Offer your practical value",
                            "style": "honest",
                            "next_scenario": None,
                            "examples": [{"native": "I can be of service to you", "target": "\u304a\u5f79\u306b\u7acb\u3066\u308b\u3053\u3068\u304c\u3042\u308a\u307e\u3059", "pronunciation": "O-yaku ni tateru koto ga arimasu"}],
                        },
                        {
                            "text": "Speak boldly of your vision",
                            "style": "bold",
                            "next_scenario": None,
                            "examples": [{"native": "The future belongs to those who speak", "target": "\u672a\u6765\u306f\u8a00\u8449\u3092\u6301\u3064\u8005\u306e\u3082\u306e\u3067\u3059", "pronunciation": "Mirai wa kotoba wo motsu mono no mono desu"}],
                        },
                        {
                            "text": "Demand respect as an equal",
                            "style": "defiant",
                            "next_scenario": None,
                            "examples": [{"native": "I am not beneath you", "target": "\u79c1\u306f\u3042\u306a\u305f\u306e\u4e0b\u3067\u306f\u306a\u3044", "pronunciation": "Watashi wa anata no shita de wa nai"}],
                        },
                    ],
                },
                {
                    "id": "ch14_04_bimbo_coach",
                    "image": None, "aspect": "square",
                    "narration": None,
                    "dialogue": "Whatever you say, say it in the Japanese you earned. Every word is yours.",
                    "speaker": "bimbo",
                    "choice_variants": {
                        "ch14_03_bimbo_freeze": {
                            "0": {"dialogue": "'\u5e73\u548c\u306e\u305f\u3081\u306b\u53c2\u308a\u307e\u3057\u305f' \u2014 the diplomat's closing argument. If he believes you, you'll be the bridge between cultures. Beautifully spoken."},
                            "1": {"dialogue": "'\u304a\u5f79\u306b\u7acb\u3066\u308b\u3053\u3068\u304c\u3042\u308a\u307e\u3059' \u2014 practical, valuable, indispensable. You've shown him what a foreigner with words can do. Now you're selling it."},
                            "2": {"dialogue": "'\u672a\u6765\u306f\u8a00\u8449\u3092\u6301\u3064\u8005\u306e\u3082\u306e\u3067\u3059' \u2014 a poetic vision. Bold and beautiful. Either he respects the audacity or punishes it."},
                            "3": {"dialogue": "Demanding equality from the Shogun? In his own throne room? You've got courage. I just hope you've got the Japanese to back it up."},
                        }
                    },
                },
                # Branch variants
                {
                    "id": "ch14_05_diplomatic",
                    "branch_of": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Your words fill the hall like incense \u2014 gentle, pervasive, impossible to ignore. You speak of bridges between worlds, of words as the first step toward understanding. The Shogun listens without expression. When you finish, the silence stretches. Then he nods. A single, measured nod that changes everything.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch14_06_verdict",
                },
                {
                    "id": "ch14_05_pragmatic",
                    "branch_of": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "You speak with the precision of a merchant and the knowledge of a scholar. Trade routes, translations, the value of a voice that speaks between worlds. The Shogun's advisors exchange glances. You've spoken their language \u2014 not just Japanese, but the language of power and utility.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch14_06_verdict",
                },
                {
                    "id": "ch14_05_bold",
                    "branch_of": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "Your voice rings off the gold-leafed walls. You speak not as a supplicant but as a visionary \u2014 of a future where words are more powerful than swords, where understanding defeats fear. The samurai retainers bristle. But the Shogun's eyes sharpen with something like recognition.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch14_06_verdict",
                },
                {
                    "id": "ch14_05_hostile",
                    "branch_of": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "You stand tall and speak words that have never been spoken to a Shogun. The air crackles. Guards step forward. A blade clears its sheath. The Shogun raises a hand \u2014 not to protect you, but to study you. Like a man studying a flame that might burn his house down. Or light his way.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch14_06_verdict",
                },
                {
                    "id": "ch14_05_insightful",
                    "branch_of": "ch14_03_bimbo_freeze",
                    "image": None, "aspect": "square",
                    "narration": "You speak \u2014 and the words transcend the room. You talk about the weight of words, about how language creates reality, about how a foreigner learned to think in Japanese and found a different world inside the grammar. The hall goes silent. The Shogun leans forward. Behind you, the simulation shimmers, and for a moment the observation deck is visible through the cracks in the ceiling. Stars drift like ash.",
                    "dialogue": None, "speaker": None,
                    "next_panel": "ch14_06_verdict",
                },
            ],
        ),

        Anchor(
            id="ch14_verdict",
            chapter="ch14",
            title="The Shogun's Verdict",
            type="convergence",
            location="throne_room",
            characters=["lord_mori"],
            mood="definitive",
            generation_hint="The Shogun renders judgment. Your place in this world is secured.",
            panels=[
                {
                    "id": "ch14_06_verdict",
                    "image": None, "aspect": "square",
                    "narration": "The Shogun speaks. His voice is low but carries to every corner of the hall. He renders his verdict on the foreigner who learned to speak, who survived the beach and the tea room and the accusation and the battle. Your place in this world is decided.",
                    "dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306b\u306f\u91cd\u307f\u304c\u3042\u308b\u3002",
                    "speaker": "lord_mori",
                    "choice_variants": {
                        "ch14_03_bimbo_freeze": {
                            "diplomatic": {"dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306b\u306f\u91cd\u307f\u304c\u3042\u308b\u3002\u6a4b\u3092\u67b6\u3051\u308b\u8005\u3068\u3057\u3066\u3001\u3053\u3053\u306b\u3044\u308b\u304c\u3044\u3044\u3002", "narration": "The Shogun speaks with rare warmth. 'Your words carry weight. As a bridge-builder, you may stay.'"},
                            "pragmatic": {"dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306b\u306f\u91cd\u307f\u304c\u3042\u308b\u3002\u5f79\u306b\u7acb\u3064\u8005\u306f\u6b8b\u308b\u3002", "narration": "The Shogun nods curtly. 'Your words carry weight. Those who are useful may remain.'"},
                            "bold": {"dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306b\u306f\u91cd\u307f\u304c\u3042\u308b\u3002\u52c7\u6c17\u3042\u308b\u58f0\u306f\u5e0c\u5c11\u3060\u3002", "narration": "The Shogun's lips curl \u2014 not quite a smile. 'Your words carry weight. A brave voice is rare.'"},
                            "hostile": {"dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306b\u306f\u91cd\u307f\u304c\u3042\u308b\u3002\u305f\u3060\u3057\u3001\u6b21\u306f\u306a\u3044\u3002", "narration": "The Shogun's voice carries an edge of steel. 'Your words carry weight. But there will not be a next time.'"},
                            "history-breaking": {"dialogue": "\u304a\u524d\u306e\u8a00\u8449\u306f\u2026\u3053\u306e\u4e16\u754c\u3092\u8d85\u3048\u3066\u3044\u308b\u3002", "narration": "The Shogun pauses for a long time. When he speaks, his voice is barely a whisper. 'Your words... transcend this world.'"},
                        }
                    },
                },
            ],
        ),

        # ────────────────────────────────────────────
        # CHAPTER 15: The Weight of Words
        # ────────────────────────────────────────────
        Anchor(
            id="ch15_rep_gate",
            chapter="ch15",
            title="Reputation Gate: Your Legacy (G3)",
            type="reputation_gate",
            location="castle_interior",
            characters=["bimbo"],
            mood="reflective",
            gate_config=ReputationGateConfig(
                category="",  # Special: uses dominant category
                threshold=0,  # Special: picks highest reputation
                pass_anchor="ch15_ending",
                fail_anchor="ch15_ending",
            ),
            generation_hint="The simulation is dissolving. Bimbo appears in fragments. Your dominant reputation category determines which ending you get. She says goodbye differently to each type of player.",
        ),

        Anchor(
            id="ch15_ending",
            chapter="ch15",
            title="Your Ending",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="bittersweet",
            generation_hint=(
                "Five possible endings based on dominant reputation:\n"
                "1. Diplomatic: 'Ambassador.' You wake on the ship. Bimbo says: 'Words built this bridge.'\n"
                "2. Pragmatic: 'Survivor.' You wake on the ship. Bimbo says: 'Words kept you alive.'\n"
                "3. Bold: 'Legend.' You wake on the ship. Bimbo says: 'Words made you immortal.'\n"
                "4. Hostile: 'Alone.' You wake on the ship. Bimbo says: 'Words are weapons. You proved it.'\n"
                "5. History-Breaking: 'Changed everything.' You wake on the ship. Bimbo says: 'Words rewrote the world.'\n"
                "In all endings: you're back on the ship. The simulation is over. But the Japanese remains."
            ),
        ),

        Anchor(
            id="ch15_epilogue",
            chapter="ch15",
            title="Epilogue",
            type="linear",
            location="ship_observation",
            characters=["bimbo"],
            mood="hopeful",
            generation_hint="Final scene. You stand at the observation window. Stars drift. Bimbo floats beside you, restored. She asks: 'Ready for the next world?' A menu of languages scrolls past — next stories waiting to be lived. But first, she says something in Japanese. And you understand every word. End.",
        ),
    ],
)


# Skeleton registry
STORY_SKELETONS = {
    STORY_ID: SHOGUN_SKELETON,
}


def get_skeleton(story_id: str) -> "StorySkeleton | None":
    """Get a story skeleton by ID."""
    return STORY_SKELETONS.get(story_id)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def check_missing():
    """Check which references need to be generated."""
    missing = {"characters": [], "locations": []}

    for char_id, char in CHARACTERS.items():
        if not char.reference_path or not os.path.exists(char.reference_path):
            missing["characters"].append(char_id)

    for loc_id, loc in LOCATIONS.items():
        if not loc.reference_path or not os.path.exists(loc.reference_path):
            missing["locations"].append(loc_id)

    return missing


def print_summary():
    """Print story summary."""
    print(f"\n{'='*50}")
    print(f"STORY: {STORY_TITLE}")
    print(f"ID: {STORY_ID}")
    print(f"{'='*50}")
    print(f"\nCharacters: {len(CHARACTERS)}")
    for cid, char in CHARACTERS.items():
        has_ref = "✓" if char.reference_path and os.path.exists(char.reference_path) else "✗"
        print(f"  [{has_ref}] {cid}: {char.name}")

    print(f"\nLocations: {len(LOCATIONS)}")
    for lid, loc in LOCATIONS.items():
        has_ref = "✓" if loc.reference_path and os.path.exists(loc.reference_path) else "✗"
        print(f"  [{has_ref}] {lid}: {loc.name}")

    print(f"\nPanels: {len(PANELS)}")
    chapters = {}
    for p in PANELS:
        chapters[p.chapter] = chapters.get(p.chapter, 0) + 1
    for ch, count in chapters.items():
        print(f"  {ch}: {count} panels")


async def generate_references(force=False):
    """Generate missing character and location references."""
    missing = check_missing()

    for char_id in missing["characters"]:
        char = CHARACTERS[char_id]
        prompt = f"""Manhwa/Korean webtoon style character portrait.

{char.description}

Portrait shot, shoulders up, facing camera.
Clean background. Professional character design reference quality.
Expressive manhwa style, clean linework, soft cel-shading.

NO TEXT IN IMAGE."""

        print(f"Generating character: {char_id}...")
        result = await generate_character_ref(char_id, prompt, force=force)
        print(f"  -> {result['path']}")

    for loc_id in missing["locations"]:
        loc = LOCATIONS[loc_id]
        prompt = f"""Manhwa/Korean webtoon style environment.

{loc.description}

Wide establishing shot. Rich detail.
Clean manhwa aesthetic, soft lighting.

NO TEXT IN IMAGE."""

        print(f"Generating location: {loc_id}...")
        result = await generate_location_ref(loc_id, prompt, force=force)
        print(f"  -> {result['path']}")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    from story.panels_test import generate_all_panels

    if len(sys.argv) < 2:
        print_summary()
        print("\nUsage:")
        print("  python -m story.shogun check    - Check missing references")
        print("  python -m story.shogun generate - Generate character/location refs")
        print("  python -m story.shogun panels   - Generate all panels")
        print("  python -m story.shogun all      - Generate everything")
        sys.exit(0)

    cmd = sys.argv[1]
    force = "--force" in sys.argv

    if cmd == "check":
        missing = check_missing()
        print("Missing references:")
        print(f"  Characters: {missing['characters']}")
        print(f"  Locations: {missing['locations']}")

    elif cmd == "generate":
        asyncio.run(generate_references(force))

    elif cmd == "panels":
        # Update the manifest with our data
        from story import manifest as story_manifest
        story_manifest.SHOGUN_CHARACTERS = CHARACTERS
        story_manifest.SHOGUN_LOCATIONS = LOCATIONS
        story_manifest.SHOGUN_PANELS = PANELS
        asyncio.run(generate_all_panels(force))

    elif cmd == "all":
        asyncio.run(generate_references(force))
        from story import manifest as story_manifest
        story_manifest.SHOGUN_CHARACTERS = CHARACTERS
        story_manifest.SHOGUN_LOCATIONS = LOCATIONS
        story_manifest.SHOGUN_PANELS = PANELS
        asyncio.run(generate_all_panels(force))

    else:
        print(f"Unknown command: {cmd}")
