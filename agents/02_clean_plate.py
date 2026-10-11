"""
Agent 2 — Background Inpainting: "leere Bühne" ohne die echten Kinder
(ProPainter via Replicate)

Entfernt alle echten Kinder aus dem Video und rekonstruiert den
Hintergrund über mehrere Frames hinweg (Flow-basiert: was in einem Frame
verdeckt ist, wird aus Nachbar-Frames geholt). Darauf setzt Agent 4 die
Anime-Kinder -- so kann vom echten Kind nichts mehr durchschimmern.

Maske = alle echten Kinder (SAM2, Agent 1), leicht vergrößert. Sehr
dunkle Pixel in der Maske von KEEP_DARK_FIGURES (das schwarze
Skateboard unter Kaia) werden NICHT entfernt, damit echte Gegenstände
erhalten bleiben.

Läuft lokal (Replicate ist aus der Cloud-Sandbox nicht erreichbar).

Ausführen:
    python agents/02_clean_plate.py <clip>
    python agents/02_clean_plate.py test_8s
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

for key in ("REPLICATE_API_TOKEN", "FAL_KEY"):
    if not os.environ.get(key):
        print(f"FEHLER: {key} nicht gefunden. Liegt die .env im Projekt-Root "
              f"und enthält sie {key}=...?")
        sys.exit(1)

import cv2  # noqa: E402
import fal_client  # noqa: E402
import numpy as np  # noqa: E402
import replicate  # noqa: E402
import requests  # noqa: E402

from runlog import log_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ISOLATION_DIR = ROOT / "intermediate" / "isolation"
OUTPUT_DIR = ROOT / "intermediate" / "cleanplate"

MODEL = "jd7h/propainter"
COST_HINT = "Replicate rechnet nach GPU-Zeit; laut Modellseite ca. 0,025 $ pro Lauf"

FIGURES = ["kaia", "luan"]
MASK_GROW_PX = 6  # zusätzlich zu ProPainters eigener mask_dilation
KEEP_DARK_BELOW = 55  # Helligkeit (0-255)
KEEP_DARK_FIGURES = {"kaia"}  # Kaia sitzt auf dem schwarzen Skateboard


def make_mask_video(clip, mask_path):
    """Weiß = entfernen. Alle echten Kinder, ohne dunkle Gegenstände."""
    video = cv2.VideoCapture(str(ISOLATION_DIR / f"{clip}_30fps.mp4"))
    caps = {f: cv2.VideoCapture(str(ISOLATION_DIR / f"{clip}_masked_{f}.mp4"))
            for f in FIGURES}
    fps = video.get(cv2.CAP_PROP_FPS)
    w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    grow = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * MASK_GROW_PX + 1, 2 * MASK_GROW_PX + 1))

    raw_path = OUTPUT_DIR / f"{mask_path.stem}_raw.mp4"
    writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    frames, share = 0, []
    while True:
        ok, frame = video.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        remove = np.zeros((h, w), bool)
        keep = np.zeros((h, w), bool)
        for f, cap in caps.items():
            ok_m, m = cap.read()
            if not ok_m:
                continue
            m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY) > 127
            remove |= m
            if f in KEEP_DARK_FIGURES:
                keep |= m & (gray < KEEP_DARK_BELOW)
        remove = (cv2.dilate(remove.astype(np.uint8), grow) > 0) & ~keep
        share.append(remove.mean())
        writer.write(cv2.cvtColor(remove.astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR))
        frames += 1
    writer.release()
    video.release()
    for c in caps.values():
        c.release()

    # verlustarm, damit die Maske binär bleibt
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", str(raw_path), "-c:v", "libx264",
         "-crf", "0", "-pix_fmt", "yuv420p", str(mask_path)],
        check=True, capture_output=True,
    )
    raw_path.unlink()
    print(f"Masken-Video erstellt: {mask_path} ({frames} Frames, "
          f"Ø {100 * np.mean(share):.1f} % des Bildes werden entfernt)")
    return frames, fps


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    clip = sys.argv[1]
    video_path = ISOLATION_DIR / f"{clip}_30fps.mp4"
    needed = [video_path] + [ISOLATION_DIR / f"{clip}_masked_{f}.mp4" for f in FIGURES]
    missing = [p for p in needed if not p.exists()]
    if missing:
        print("FEHLER: Dateien fehlen (erst Agent 1 laufen lassen):")
        for p in missing:
            print(f"  {p}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mask_path = OUTPUT_DIR / f"{clip}_remove_mask.mp4"
    frames, fps = make_mask_video(clip, mask_path)

    print(f"\nModell:    {MODEL} (Video-Inpainting)")
    print(f"Kosten:    {COST_HINT}")
    answer = input("\nStartet einen kostenpflichtigen Replicate-Call. Ok? [j/N] ")
    if answer.strip().lower() not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        sys.exit(0)

    started = time.monotonic()
    model = replicate.models.get(MODEL)
    print(f"Starte {MODEL} (Version {model.latest_version.id[:12]}) ...")
    # ProPainter prüft die Dateiendung der Maske (.mp4/.avi). Beim Upload
    # über den Replicate-Client geht der Dateiname verloren -> selbst
    # hochladen (fal.ai-Storage), die URLs enden dann auf .mp4.
    print("Lade Video und Maske hoch ...")
    video_url = fal_client.upload_file(str(video_path))
    mask_url = fal_client.upload_file(str(mask_path))
    prediction = replicate.predictions.create(
        version=model.latest_version.id,
        input={
            "video": video_url,
            "mask": mask_url,
            "mode": "video_inpainting",
            "save_fps": int(round(fps)),
            "mask_dilation": 4,
        },
    )
    prediction.wait()
    if prediction.status != "succeeded":
        print(f"FEHLER: Replicate-Status '{prediction.status}': {prediction.error}")
        sys.exit(1)

    # Reihenfolge wichtig: zuerst das bezahlte Ergebnis sichern
    outputs = prediction.output if isinstance(prediction.output, list) else [prediction.output]
    out_path = OUTPUT_DIR / f"{clip}_clean.mp4"
    r = requests.get(str(outputs[-1]), timeout=300)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    predict_time = (prediction.metrics or {}).get("predict_time")
    log_run(
        agent="02_clean_plate", model=MODEL, clip=clip, target="+".join(FIGURES),
        duration_s=time.monotonic() - started,
        cost_basis=COST_HINT,
        details={"frames": frames, "fps": fps, "gpu_predict_time_s": predict_time,
                 "replicate_prediction_id": prediction.id,
                 "outputs_returned": len(outputs)},
        outputs=[out_path],
    )
    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s "
          f"(GPU-Zeit {predict_time} s) ---")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()
