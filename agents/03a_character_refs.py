"""
Agent 3a — Charakter-Referenzen (Vorstufe zu Asset-Generierung)
Erzeugt aus den Anime-Stilbildern in input/style/ saubere Ganzkörper-
Referenzen (neutraler Hintergrund, ganze Figur sichtbar). Die dienen
später als image_url für Wan-2.2 Animate Replace, das am besten mit
einer freigestellten Ganzkörper-Figur funktioniert.

Läuft lokal (fal.ai ist aus der Cloud-Sandbox nicht erreichbar).

Ausführen:
    python agents/03a_character_refs.py
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("FAL_KEY"):
    print("FEHLER: FAL_KEY nicht gefunden. Liegt die .env im Projekt-Root "
          "und enthält sie FAL_KEY=...?")
    sys.exit(1)

import fal_client  # noqa: E402  (nach dem FAL_KEY-Check importieren)
import requests  # noqa: E402

from runlog import log_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STYLE_DIR = ROOT / "input" / "style"
OUTPUT_DIR = ROOT / "intermediate" / "characters"

MODEL = "fal-ai/nano-banana/edit"
NUM_VARIANTS = 2  # pro Figur, damit du auswählen kannst
PRICE_PER_IMAGE = 0.039  # USD, Stand 2026-10, Angabe fal.ai

# Stilbild je Figur + was die Figur ausmacht (hilft, Details zu halten)
CHARACTERS = {
    "kaia": {
        "style_image": STYLE_DIR / "kaia_anime.jpeg",
        "description": "toddler girl, short messy blonde hair, big blue eyes, "
                       "light pink hooded jacket, blue pants",
    },
    "luan": {
        "style_image": STYLE_DIR / "luan_anime.jpeg",
        "description": "small child, blonde hair tied in a top bun, round black "
                       "glasses, blue eyes, mint green sweater",
    },
}

PROMPT_TEMPLATE = (
    "Full-body character reference of the exact same child as in the image "
    "({description}). Keep the face, hair, outfit and the soft watercolor "
    "anime art style exactly as in the image. Standing, front view, neutral "
    "relaxed pose, arms at the sides, the whole body visible from head to "
    "shoes, centered. Plain light grey background. No other people, no "
    "hands of adults, no objects, no text."
)


def main():
    missing = [c["style_image"] for c in CHARACTERS.values()
               if not c["style_image"].exists()]
    if missing:
        print("FEHLER: Stilbild(er) nicht gefunden:")
        for p in missing:
            print(f"  {p}")
        sys.exit(1)

    print(f"Modell: {MODEL}, {NUM_VARIANTS} Varianten je Figur")
    for name, c in CHARACTERS.items():
        print(f"\n[{name}] {c['style_image'].name}")
        print(f"  Prompt: {PROMPT_TEMPLATE.format(description=c['description'])}")

    total = NUM_VARIANTS * len(CHARACTERS)
    answer = input(f"\nStartet {len(CHARACTERS)} kostenpflichtige fal.ai-Calls "
                   f"({total} Bilder). Ok? [j/N] ").strip().lower()
    if answer not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    saved = []
    for name, c in CHARACTERS.items():
        print(f"\n[{name}] Lade Stilbild hoch ...")
        call_started = time.monotonic()
        call_saved = []
        image_url = fal_client.upload_file(str(c["style_image"]))

        print(f"[{name}] Generiere {NUM_VARIANTS} Referenzen ({MODEL}) ...")
        result = fal_client.subscribe(
            MODEL,
            arguments={
                "prompt": PROMPT_TEMPLATE.format(description=c["description"]),
                "image_urls": [image_url],
                "num_images": NUM_VARIANTS,
                "aspect_ratio": "9:16",
                "output_format": "png",
            },
        )

        for i, img in enumerate(result["images"], start=1):
            out_path = OUTPUT_DIR / f"{name}_ref_{i}.png"
            r = requests.get(img["url"], timeout=120)
            r.raise_for_status()
            out_path.write_bytes(r.content)
            print(f"  Gespeichert: {out_path}")
            saved.append(out_path)
            call_saved.append(out_path)

        log_run(
            agent="03a_character_refs", model=MODEL, clip=None, target=name,
            duration_s=time.monotonic() - call_started,
            cost_usd=len(call_saved) * PRICE_PER_IMAGE,
            cost_basis=f"{len(call_saved)} Bilder x {PRICE_PER_IMAGE} $",
            details={"num_images": len(call_saved), "aspect_ratio": "9:16",
                     "style_image": c["style_image"].name},
            outputs=call_saved,
        )

    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s ---")
    print("Such dir je Figur die beste Referenz aus. Kosten: fal.ai-Dashboard "
          "unter 'Usage'.")


if __name__ == "__main__":
    main()
