"""
MANUELA SÁENZ — Quito, 16 June 1822

Spanish-language immersion. The player is Manuela Sáenz on the night of the
victory ball for the Liberator. Roberto, a Spanish-speaking guide, narrates.

Panel-driven: each anchor supplies a full-screen image as the backdrop, with
dialogue overlaid. Scenarios 1000-1007 remain the branching gameplay beats.

Characters, locations and panel assets are reused from story.manifest's
MANUELA_* dicts so the manifest pipeline (scripts/gen_roberto.py) is the
single source of truth for images.
"""

import os

from story.manifest import MANUELA_CHARACTERS, MANUELA_LOCATIONS
from story.skeleton import (
    StorySkeleton, Anchor, ChapterDef, LearningObjective, StoryCategory,
)

IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "image_cache")
CHARACTER_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "characters")
LOCATION_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "locations")

STORY_ID = "manuela"
STORY_TITLE = "Manuela Sáenz: La Libertadora"
STORY_SUBTITLE = "Quito, 16 de junio de 1822"

CHARACTERS = MANUELA_CHARACTERS
LOCATIONS = MANUELA_LOCATIONS


# ============================================================
# STORY SKELETON
# ============================================================

IMAGE_BASE_URL = "/images/generated"

MANUELA_CATEGORIES = [
    StoryCategory(key="elegant",     label="Elegante",   color="#f5d0fe", icon="🌹", description="Palabras con porte"),
    StoryCategory(key="coy",         label="Coqueta",    color="#fbcfe8", icon="💫", description="Palabras que insinúan"),
    StoryCategory(key="bold",        label="Osada",      color="#fdba74", icon="⚡", description="Palabras que desafían"),
    StoryCategory(key="diplomatic",  label="Diplomática", color="#86efac", icon="🕊", description="Palabras que calman"),
    StoryCategory(key="defiant",     label="Rebelde",    color="#fca5a5", icon="🔥", description="Palabras que rompen"),
]

MANUELA_STYLE_TO_CATEGORY = {
    "elegant": "elegant", "polite": "elegant", "playful": "coy", "coy": "coy",
    "flirtatious": "coy", "intimate": "coy", "demure": "coy",
    "firm": "bold", "bold": "bold", "passionate": "bold", "warning": "bold",
    "cool": "diplomatic", "diplomatic": "diplomatic", "evasive": "diplomatic",
    "defiant": "defiant", "mischievous": "defiant", "poetic": "defiant", "obedient": "diplomatic",
    "honest": "diplomatic", "curious": "coy",
}

# ============================================================
# ANCHORS — each with ONE panel used as the full-screen backdrop.
#
# Panel.image points at image_cache/panels/manuela_*.png when generated.
# Until each panel is generated, the frontend falls back to the location
# reference or a mood gradient (handled by StoryOrchestrator).
#
# The first anchor — roberto_hello — intentionally uses the ALREADY-GENERATED
# roberto.png portrait as the main backdrop so the user sees him big and
# centered during his opening monologue.
# ============================================================

MANUELA_SKELETON = StorySkeleton(
    id=STORY_ID,
    title=STORY_TITLE,
    subtitle=STORY_SUBTITLE,
    setting="Quito, Ecuador, 16 de junio de 1822 — the night of the victory ball for Simón Bolívar",
    target_language="Spanish",
    tone="Romantic, dramatic, period-authentic. Candlelight, torchlight, silk, laurel. Every word is a choice history will remember.",
    categories=MANUELA_CATEGORIES,
    style_to_category=MANUELA_STYLE_TO_CATEGORY,
    character_ids=list(CHARACTERS.keys()),
    location_ids=list(LOCATIONS.keys()),
    meta_narrative=(
        "Prologue: Roberto introduces the player to Manuela and the night of 16 June 1822. "
        "Chapter 4: The ball — gossip, flirtation, the laurel wreath, the first dance with Bolívar."
    ),

    chapters=[
        ChapterDef(
            id="prologue",
            title="Prólogo: Roberto",
            anchor_ids=["manuela_pro_hello", "manuela_pro_setting", "manuela_pro_drop"],
        ),
        ChapterDef(
            id="ch04",
            title="Capítulo 4: El baile de Quito",
            anchor_ids=["manuela_ch4_balcon", "manuela_ch4_corona", "manuela_ch4_mirada"],
        ),
    ],

    anchors=[
        # ────────────────────────── PROLOGUE ──────────────────────────
        Anchor(
            id="manuela_pro_hello",
            chapter="prologue",
            title="Hola, soy Roberto",
            type="linear",
            location="salon_candelabra",
            characters=["roberto"],
            mood="warm",
            panels=[
                {
                    "id": "manuela_pro_01_roberto",
                    # Reuse the already-generated HUD portrait as a full-screen backdrop.
                    # The frontend will object-fit cover it, so it reads as a dramatic hero shot.
                    "image": f"{IMAGE_BASE_URL}/characters/roberto.png",
                    "aspect": "tall",
                    "narration": "Hola. Soy Roberto, tu guía.",
                    "dialogue": {
                        "speaker": "roberto",
                        "text": "Hola. Soy Roberto, tu guía.",
                        "translation": "Hi. I'm Roberto, your guide.",
                    },
                },
            ],
            next_anchor="manuela_pro_setting",
        ),

        Anchor(
            id="manuela_pro_setting",
            chapter="prologue",
            title="Quito, 1822",
            type="linear",
            location="quito_balcony_night",
            characters=["roberto"],
            mood="electric",
            panels=[
                {
                    "id": "manuela_pro_02_quito",
                    "image": f"{IMAGE_BASE_URL}/panels/manuela_prologue/manuela_pro_02_quito.png",
                    "aspect": "wide",
                    "narration": (
                        "Quito. 16 de junio de 1822. "
                        "Los españoles han sido vencidos. El Libertador entra victorioso."
                    ),
                    "dialogue": {
                        "speaker": "roberto",
                        "text": "Vamos a 1822. A Quito. A una noche que la historia nunca olvidó.",
                        "translation": "We're going to 1822. To Quito. To a night history never forgot.",
                    },
                },
            ],
            next_anchor="manuela_pro_drop",
        ),

        Anchor(
            id="manuela_pro_drop",
            chapter="prologue",
            title="Abriendo el portal",
            type="linear",
            location="quito_balcony_night",
            characters=["roberto"],
            mood="decisive",
            panels=[
                {
                    "id": "manuela_pro_03_drop",
                    "image": f"{IMAGE_BASE_URL}/panels/manuela_prologue/manuela_pro_03_drop.png",
                    "aspect": "wide",
                    "narration": "Buena suerte, Doña Manuela.",
                    "dialogue": {
                        "speaker": "roberto",
                        "text": "Abriendo el portal. Buena suerte, Doña Manuela.",
                        "translation": "Opening the portal. Good luck, Doña Manuela.",
                    },
                },
            ],
            next_anchor="manuela_ch4_balcon",
        ),

        # ────────────────────────── CHAPTER 4 ──────────────────────────
        Anchor(
            id="manuela_ch4_balcon",
            chapter="ch04",
            title="El balcón de los Aguirre",
            type="linear",
            location="quito_balcony_night",
            characters=["manuela", "maria_josefa"],
            mood="electric",
            panels=[
                {
                    "id": "manuela_ch4_01_balcon",
                    "image": f"{IMAGE_BASE_URL}/panels/manuela_ch4/manuela_ch4_01_balcon.png",
                    "aspect": "wide",
                    "narration": "Luz de velas. Aroma de jazmín. La música sube desde la plaza.",
                    "dialogue": {
                        "speaker": "maria_josefa",
                        "text": "¡Manuela, por fin llegaste!",
                        "translation": "Manuela, you're finally here!",
                    },
                    "options": [
                        {
                            "text": "Say you went looking for a worthy dress",
                            "style": "coy",
                            "examples": [{
                                "native": "I went to find a dress worthy of tonight.",
                                "target": "Fui a buscar un vestido digno de esta noche.",
                            }],
                        },
                        {
                            "text": "Admit you were watching the soldiers",
                            "style": "honest",
                            "examples": [{
                                "native": "I stayed to watch the soldiers come in.",
                                "target": "Me quedé viendo entrar a los soldados.",
                            }],
                        },
                        {
                            "text": "Tease about the occasion",
                            "style": "playful",
                            "examples": [{
                                "native": "It's not every day we welcome the Liberator.",
                                "target": "No todos los días se recibe al Libertador.",
                            }],
                        },
                    ],
                },
            ],
            next_anchor="manuela_ch4_corona",
        ),

        Anchor(
            id="manuela_ch4_corona",
            chapter="ch04",
            title="La corona de laurel",
            type="linear",
            location="plaza_torches",
            characters=["manuela", "bolivar"],
            mood="decisive",
            panels=[
                {
                    "id": "manuela_ch4_06_corona",
                    "image": f"{IMAGE_BASE_URL}/panels/manuela_ch4/manuela_ch4_06_corona.png",
                    "aspect": "tall",
                    "narration": "El Libertador se acerca. La corona está en tus manos. ¿Qué haces?",
                    "dialogue": None,
                    "options": [
                        {
                            "text": "Throw the crown hard, like a challenge",
                            "style": "bold",
                            "examples": [{
                                "native": "Let him receive it on my behalf!",
                                "target": "¡Que la reciba de mi parte!",
                            }],
                        },
                        {
                            "text": "Let it fall softly, like a flower",
                            "style": "poetic",
                            "examples": [{
                                "native": "May it fall upon him like a flower.",
                                "target": "Que caiga como una flor sobre él.",
                            }],
                        },
                        {
                            "text": "Aim directly at his head",
                            "style": "mischievous",
                            "examples": [{
                                "native": "I'll aim straight for his head.",
                                "target": "Apuntaré directo a su cabeza.",
                            }],
                        },
                    ],
                },
            ],
            next_anchor="manuela_ch4_mirada",
        ),

        Anchor(
            id="manuela_ch4_mirada",
            chapter="ch04",
            title="La mirada del Libertador",
            type="linear",
            location="plaza_torches",
            characters=["bolivar"],
            mood="electric",
            panels=[
                {
                    "id": "manuela_ch4_07_mirada",
                    "image": f"{IMAGE_BASE_URL}/panels/manuela_ch4/manuela_ch4_07_mirada.png",
                    "aspect": "square",
                    "narration": "Bolívar levanta la vista. Sus ojos encuentran los tuyos.",
                    "dialogue": {
                        "speaker": "bolivar",
                        "text": "¿Y a quién debo tan dulce agresión, señora?",
                        "translation": "And to whom do I owe such a sweet assault, madam?",
                    },
                    "options": [
                        {
                            "text": "Smile mysteriously",
                            "style": "coy",
                            "examples": [{
                                "native": "Let you guess that for yourself, General.",
                                "target": "Que lo adivine usted, General.",
                            }],
                        },
                        {
                            "text": "Introduce yourself boldly",
                            "style": "bold",
                            "examples": [{
                                "native": "Manuela Sáenz, at your service, General.",
                                "target": "Manuela Sáenz, para servirle, General.",
                            }],
                        },
                        {
                            "text": "Feign innocence",
                            "style": "demure",
                            "examples": [{
                                "native": "Forgive me, General, the wind betrayed me.",
                                "target": "Perdón, General, el viento me traicionó.",
                            }],
                        },
                    ],
                },
            ],
        ),
    ],
)


# ============================================================
# REGISTRY — exposed to story_panels router
# ============================================================

STORY_SKELETONS = {STORY_ID: MANUELA_SKELETON}
