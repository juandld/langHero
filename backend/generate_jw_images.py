"""Generate Journey to the West character/location/panel images via OpenAI gpt-image-1."""
import os, base64, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

IMAGE_CACHE = os.path.join(os.path.dirname(__file__), "image_cache")
CHAR_DIR = os.path.join(IMAGE_CACHE, "characters")
LOC_DIR = os.path.join(IMAGE_CACHE, "locations")
PANEL_DIR = os.path.join(IMAGE_CACHE, "panels")

STYLE = "Manhwa/webtoon anime art style, detailed, vivid colors, cinematic lighting. "

CHARACTERS = {
    "wukong": "The Monkey King Sun Wukong. Lean muscular figure with golden-furred monkey features but humanoid body. Wild golden eyes, sharp canines in a grin. Golden chainmail over red silk. Golden phoenix-feather cap with headband. Red-tasseled iron staff across shoulders. Mischievous and dangerous. Full body character reference sheet, simple background.",
    "sanzang": "Tang Sanzang, Buddhist monk. Serene handsome face, shaved head. Elaborate golden kasaya robe over white robes. Prayer beads and monk staff with rings. Gentle resolute expression. Tang Dynasty. Full body character reference, simple background.",
    "bajie": "Zhu Bajie, half-pig half-man. Heavyset round body. Pig snout, floppy ears, wearing loose monk robes. Nine-toothed rake weapon. Lazy grin, comic relief character. Full body character reference, simple background.",
    "wujing": "Sha Wujing, river spirit monk. Tall, blue-tinged skin, calm stoic expression. Nine skull prayer beads as necklace. Brown monk robes. Crescent-moon spade weapon. Quiet dependable. Full body character reference, simple background.",
    "innkeeper_chen": "Chinese innkeeper, Tang Dynasty. Round face, shrewd eyes, ready smile. Simple merchant clothes with apron. Warm but calculating. Full body character reference, simple background.",
    "bandit_chief": "Mountain bandit leader, 40s. Scarred face, missing ear. Leather armor over rough clothes. Two swords crossed on back. Dangerous smile. Full body character reference, simple background.",
    "jade_spirit": "Beautiful female spirit. Semi-transparent, glowing pale green jade light. Long flowing black hair moves like water. White and jade green Tang Dynasty hanfu dress. Ethereal mysterious. Full body character reference, simple background.",
    "magistrate_wang": "Tang Dynasty magistrate. Black gauze cap. Formal green official robes. Thin mustache, sharp eyes. Holds folding fan. Powerful cautious. Full body character reference, simple background.",
    "tea_master_lu": "Old tea master, 70s. Wispy white beard, calm ancient eyes. Simple gray Taoist robes. Weathered precise hands. Perpetual stillness. Full body character reference, simple background.",
}

LOCATIONS = {
    "jw_mountain_pass": "Narrow mountain pass in Tang Dynasty China. Steep cliff one side, drop on the other. Mist swirling below. Ancient worn stone path. Silk Road atmosphere. Dramatic landscape, no people.",
    "jw_roadside_inn": "Tang Dynasty roadside inn at dusk. Warm lantern light from wooden doors. Red paper lanterns on eaves. Horses tied outside. Smoke from kitchen. Inviting but isolated. No people.",
    "jw_bamboo_forest": "Dense bamboo forest. Tall green stalks creating cathedral of green light. Narrow winding path. Mist and filtered sunlight. Peaceful but mysterious. No people.",
    "jw_river_crossing": "Wide river with ancient wooden ferry. Mountains reflected in still water. Tang Dynasty boats with square sails. Dawn light. No people.",
    "jw_temple_mountain": "Buddhist temple perched on mountain cliff. Red and gold pagoda. Incense smoke. Stone steps carved into mountain. Clouds below. Serene ancient. No people.",
    "jw_market_town": "Bustling Tang Dynasty Silk Road market town. Merchants from many lands. Silk spices pottery. Camels horses. Colorful awnings. Multicultural. Wide establishing shot.",
    "jw_bandit_camp": "Hidden camp in mountain valley. Rough tents, stolen goods. Campfire smoke. Lookout posts on ridges. Dangerous organized. No people.",
    "jw_spirit_cave": "Luminous cave interior. Jade-green light from walls. Underground pool reflecting strange stars. Ancient Chinese characters carved in stone. Otherworldly beautiful. No people.",
    "jw_tea_house": "Small tea house on cliff edge above clouds. Simple wooden structure, open sides. Low tables, ceramic tea sets. Wind chimes. Peace above the world. No people.",
}

PANELS = {
    "jw_prologue/jw_pro_01_stars": "POV looking out through curved spaceship observation window. Infinite void of space, stars drifting. Purple and cyan ambient lighting. Contemplative mood. Wide cinematic shot.",
    "jw_prologue/jw_pro_02_bimbo": "Young woman AI hologram with purple-to-cyan gradient hair floating in spaceship. Excited expression, particles spinning around her. Stars visible behind. Manhwa style, warm glow.",
    "jw_prologue/jw_pro_03_china": "Holographic projection of ancient China materializing in a spaceship. Mountains, rivers, the Silk Road glowing golden. A woman AI hologram gestures at it. Wonder and excitement.",
    "jw_ch01/jw_ch1_01_wake": "POV waking on a narrow mountain path in Tang Dynasty China. Clouds below, peaks above. Rough cotton traveler clothes visible. Blue sky. Cold thin mountain air feeling. Wide shot.",
    "jw_ch01/jw_ch1_02_wukong": "The Monkey King Sun Wukong crouched on a boulder above, looking down at viewer. Golden fur, golden eyes, sharp-toothed grin. Iron staff across shoulders, red tassel swinging. Backlit by sunrise. Magnificent and terrifying. Tall dramatic composition.",
    "jw_ch01/jw_ch1_03_freeze": "Mountain scene FROZEN in time. The Monkey King frozen mid-leap with blue desaturated tint. Clouds stopped. A glowing purple-cyan hologram woman appears as only warm-colored element. Time freeze effect.",
    "jw_ch01/jw_ch1_04_teach": "Young woman AI hologram in teaching pose. Holographic Chinese characters 你好 and 我是 float around her hands. Frozen mountain background with blue tint. Patient encouraging expression. Time freeze scene.",
    "jw_ch01/jw_ch1_05_speak": "The Monkey King reacting with surprised amusement. His grin shifts from predatory to delighted. He tilts his head like a curious animal. Mountain pass background. Dynamic expression.",
    "jw_ch01/jw_ch1_06_group": "Wide shot of the Journey to the West pilgrimage group on a mountain path. A monk in golden robes leading, a pig-man creature, a tall blue-skinned figure, and the golden Monkey King bounding ahead. Mountains and clouds. Epic adventure composition.",
}

def gen(prompt, path, label):
    if os.path.exists(path):
        print(f"  SKIP {label} (exists)")
        return True
    print(f"  Generating {label}...", flush=True)
    try:
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=STYLE + prompt,
            size="1024x1024",
            n=1,
        )
        img_b64 = resp.data[0].b64_json
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        print(f"  OK: {label}")
        return True
    except Exception as e:
        print(f"  FAILED {label}: {e}")
        return False

what = sys.argv[1] if len(sys.argv) > 1 else "all"

if what in ("chars", "all"):
    print("=== CHARACTERS ===")
    for cid, desc in CHARACTERS.items():
        gen(desc, os.path.join(CHAR_DIR, f"{cid}.png"), cid)

if what in ("locs", "all"):
    print("\n=== LOCATIONS ===")
    for lid, desc in LOCATIONS.items():
        gen(desc, os.path.join(LOC_DIR, f"{lid}.png"), lid)

if what in ("panels", "all"):
    print("\n=== PANELS ===")
    for pid, desc in PANELS.items():
        gen(desc, os.path.join(PANEL_DIR, f"{pid}.png"), pid)

print("\nDone!")
