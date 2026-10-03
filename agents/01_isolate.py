"""
Agent 1 — Isolation & Tracking (Phase 2)
Segmentiert eine Person im Testvideo mit SAM2 (via fal.ai) und liefert
eine Maskensequenz als Video zurück.

WICHTIG: Dieses Skript läuft NICHT in der Cloud-Sandbox (dort ist fal.ai
aktuell durch einen Anthropic-seitigen Netzwerk-Bug blockiert), sondern
lokal bei dir in VS Code.

Setup (einmalig):
    pip install fal-client python-dotenv requests
    # .env im Projekt-Root mit FAL_KEY=... anlegen (siehe .env.example)

Ausführen:
    python agents/01_isolate.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("FAL_KEY"):
    print("FEHLER: FAL_KEY nicht gefunden. Liegt die .env im Projekt-Root "
          "und enthält sie FAL_KEY=...?")
    sys.exit(1)

import fal_client  # noqa: E402  (nach dem FAL_KEY-Check importieren)
import requests  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = ROOT / "input" / "test_clips" / "test_15s.mp4"
OUTPUT_DIR = ROOT / "intermediate" / "isolation"
PREVIEW_PATH = OUTPUT_DIR / "frame0_preview.png"

# ---------------------------------------------------------------------
# Foreground-Punkt für SAM2: sagt dem Modell, WELCHE Person/Objekt es
# auf Frame 0 tracken soll. (x, y) in Pixeln, Ursprung oben links.
# Video ist 368x480 (Hochformat). Grobe Schätzung anhand des ersten
# Frames: Kind im Kinderstuhl rechts im Bild.
# -> PRÜFE frame0_preview.png (wird unten erzeugt) und passe die Werte
#    bei Bedarf an, bevor du den fal.ai-Call startest!
# ---------------------------------------------------------------------
PROMPT_X = 300
PROMPT_Y = 330
PROMPT_FRAME_INDEX = 0
PROMPT_LABEL = 1  # 1 = Vordergrund (das willst du maskieren), 0 = Hintergrund


def extract_preview_frame():
    """Frame 0 lokal extrahieren, damit der Prompt-Punkt geprüft werden kann."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(VIDEO_PATH),
            "-vf", "select=eq(n\\,0)", "-vframes", "1",
            "-update", "1", str(PREVIEW_PATH),
        ],
        check=True,
        capture_output=True,
    )
    print(f"Vorschau-Frame gespeichert: {PREVIEW_PATH}")
    print(f"  -> Öffne das Bild und prüfe, ob der Punkt ({PROMPT_X}, {PROMPT_Y}) "
          f"wirklich auf der gewünschten Person liegt. Falls nicht: PROMPT_X / "
          f"PROMPT_Y im Skript anpassen und neu starten.")


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"  [fal.ai] {log['message']}")


def main():
    if not VIDEO_PATH.exists():
        print(f"FEHLER: Testvideo nicht gefunden unter {VIDEO_PATH}")
        print("Leg die 15-Sekunden-Testdatei dort ab (siehe Chat-Anleitung).")
        sys.exit(1)

    extract_preview_frame()

    answer = input("\nPrompt-Punkt geprüft und ok? [j/N] ").strip().lower()
    if answer not in ("j", "ja", "y", "yes"):
        print("Abgebrochen. Passe PROMPT_X/PROMPT_Y an und starte erneut.")
        sys.exit(0)

    print(f"\nLade Video zu fal.ai hoch: {VIDEO_PATH}")
    video_url = fal_client.upload_file(str(VIDEO_PATH))
    print(f"Hochgeladen: {video_url}")

    print("\nStarte SAM2-Segmentierung (fal-ai/sam2/video) ...")
    result = fal_client.subscribe(
        "fal-ai/sam2/video",
        arguments={
            "video_url": video_url,
            "prompts": [
                {
                    "x": PROMPT_X,
                    "y": PROMPT_Y,
                    "frame_index": PROMPT_FRAME_INDEX,
                    "label": PROMPT_LABEL,
                }
            ],
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result_json_path = OUTPUT_DIR / "result.json"
    result_json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nRoh-Ergebnis gespeichert: {result_json_path}")

    out_video_url = result["video"]["url"]
    out_path = OUTPUT_DIR / "test_15s_masked.mp4"
    print(f"Lade maskiertes Video herunter von {out_video_url} ...")
    r = requests.get(out_video_url, timeout=120)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    print(f"Gespeichert: {out_path}")

    print("\n--- Fertig ---")
    print(f"Schau dir {out_path} an. Passt die Maske auf die Person über die")
    print("gesamten 15 Sekunden? Falls nicht: Prompt-Punkt anpassen oder")
    print("mehrere Punkte/Frames angeben, dann neu starten.")
    print("\nKosten: fal.ai rechnet nach Rechenzeit ab — Stand prüfst du im")
    print("fal.ai-Dashboard unter 'Billing/Usage', ich habe darauf keinen Zugriff.")


if __name__ == "__main__":
    main()
