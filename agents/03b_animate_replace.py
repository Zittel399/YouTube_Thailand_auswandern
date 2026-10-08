"""
Agent 3b — Person im Video durch Anime-Figur ersetzen (Wan-2.2 Animate Replace)
Nimmt das 30-fps-Video aus Agent 1 und eine Charakter-Referenz aus
Agent 3a und ersetzt eine Person durch die Figur. Bewegung, Mimik, Licht
und Farbton der Szene werden übernommen.

Achtung: Das Modell hat kein Masken-Feld -- welche Person es bei mehreren
Personen ersetzt, entscheidet es selbst. Ergebnis also immer prüfen.

Läuft lokal (fal.ai ist aus der Cloud-Sandbox nicht erreichbar).

Ausführen:
    python agents/03b_animate_replace.py <clip> <figur> [aufloesung] [eingabevideo]
    python agents/03b_animate_replace.py test_8s kaia
    python agents/03b_animate_replace.py test_8s luan 480p intermediate/animate/test_8s_kaia_480p.mp4
"""

import json
import os
import subprocess
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
ISOLATION_DIR = ROOT / "intermediate" / "isolation"
CHARACTER_DIR = ROOT / "intermediate" / "characters"
OUTPUT_DIR = ROOT / "intermediate" / "animate"

MODEL = "fal-ai/wan/v2.2-14b/animate/replace"

# Ausgewählte Referenz je Figur (aus Agent 3a)
CHARACTER_REFS = {
    "kaia": CHARACTER_DIR / "kaia_ref_1.png",
    "luan": CHARACTER_DIR / "luan_ref_1.png",
}

# fal.ai rechnet (Frames / 16) x Preis pro "Videosekunde"
PRICE_PER_16_FRAMES = {"480p": 0.04, "580p": 0.06, "720p": 0.08}


def count_frames(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return int(out.stdout.strip())


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    clip, character = sys.argv[1], sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "480p"
    video_path = (ROOT / sys.argv[4] if len(sys.argv) > 4
                  else ISOLATION_DIR / f"{clip}_30fps.mp4")

    if character not in CHARACTER_REFS:
        print(f"FEHLER: Unbekannte Figur '{character}'. "
              f"Möglich: {', '.join(CHARACTER_REFS)}")
        sys.exit(1)
    if resolution not in PRICE_PER_16_FRAMES:
        print(f"FEHLER: Auflösung muss eine von {', '.join(PRICE_PER_16_FRAMES)} sein.")
        sys.exit(1)
    ref_path = CHARACTER_REFS[character]
    for p in (video_path, ref_path):
        if not p.exists():
            print(f"FEHLER: Datei nicht gefunden: {p}")
            sys.exit(1)

    frames = count_frames(video_path)
    cost = frames / 16 * PRICE_PER_16_FRAMES[resolution]
    print(f"Video:     {video_path} ({frames} Frames)")
    print(f"Figur:     {character} -> {ref_path.name}")
    print(f"Modell:    {MODEL}, {resolution}")
    print(f"Kosten:    ca. {cost:.2f} $ (laut fal.ai-Preisangabe)")

    answer = input("\nStartet einen kostenpflichtigen fal.ai-Call. Ok? [j/N] ")
    if answer.strip().lower() not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    print("\nLade Video und Referenz hoch ...")
    video_url = fal_client.upload_file(str(video_path))
    image_url = fal_client.upload_file(str(ref_path))

    print(f"Starte {MODEL} (kann einige Minuten dauern) ...")
    result = fal_client.subscribe(
        MODEL,
        arguments={
            "video_url": video_url,
            "image_url": image_url,
            "resolution": resolution,
            "video_quality": "high",
        },
        with_logs=True,
        on_queue_update=lambda u: [print(f"  [fal.ai] {log['message']}")
                                   for log in getattr(u, "logs", None) or []],
    )

    # Reihenfolge wichtig: zuerst das bezahlte Ergebnis sichern, dann alles
    # andere -- ein Fehler danach darf das Video nicht mehr kosten.
    stem = f"{video_path.stem.removesuffix('_30fps')}_{character}_{resolution}"
    out_path = OUTPUT_DIR / f"{stem}.mp4"
    r = requests.get(result["video"]["url"], timeout=300)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    log_run(
        agent="03b_animate_replace", model=MODEL, clip=clip, target=character,
        duration_s=time.monotonic() - started, cost_usd=cost,
        cost_basis=f"{frames} Frames / 16 x {PRICE_PER_16_FRAMES[resolution]} $ ({resolution})",
        details={"resolution": resolution, "frames": frames,
                 "input_video": video_path.name, "reference": ref_path.name},
        outputs=[out_path],
    )
    # fal.ai liefert u.a. einen chinesischen Default-Prompt -> utf-8 nötig
    (OUTPUT_DIR / f"{stem}_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s ---")
    print(f"  {out_path}")
    print("Prüfen: Wurde die richtige Person ersetzt? Kosten: fal.ai-Dashboard "
          "unter 'Usage'.")


if __name__ == "__main__":
    main()
