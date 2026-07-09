"""
Journey to the West story data: characters, locations, and panel specifications.

Separated from journey.py to keep the main skeleton module searchable.
"""

import os
from story.manifest import Character, Location, PanelSpec

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
