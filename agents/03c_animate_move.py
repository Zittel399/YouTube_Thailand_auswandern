"""
Agent 3c — Anime-Figur mit der Bewegung eines Kindes animieren
(Wan-2.2 Animate Move)

1. Solo-Video (lokal): Mit der SAM2-Maske aus Agent 1 bleibt nur die
   gewählte Person sichtbar, alles andere wird neutral grau. So ist
   eindeutig, wessen Bewegung das Modell übernimmt -- auch wenn mehrere
   Kinder im Bild sind.
   - Fester Ausschnitt um den gesamten Bewegungsbereich der Person: sie
     ist größer im Bild (stabilere Pose/Gesicht), und die Position ist
     exakt bekannt (<..>_solo_crop.json) fürs spätere Zurücksetzen.
   - Auf MODEL_FPS reduziert: weniger Frames = weniger Drift über die
     Länge und günstiger. Agent 4 rechnet wieder auf 30 fps hoch.
2. Referenz auf das Seitenverhältnis des Ausschnitts auffüllen -- das
   Modell übernimmt das Format der Referenz, so passt das Ergebnis
   pixelgenau auf den Ausschnitt.
3. Animate Move (fal.ai): bewegt die Referenz wie die Person im
   Solo-Video. Ergebnis: Anime-Figur auf hellgrauem Hintergrund.

Läuft lokal (fal.ai ist aus der Cloud-Sandbox nicht erreichbar).

Ausführen:
    python agents/03c_animate_move.py <clip> <figur> [aufloesung]
    python agents/03c_animate_move.py test_8s kaia
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

import cv2  # noqa: E402
import fal_client  # noqa: E402  (nach dem FAL_KEY-Check importieren)
import numpy as np  # noqa: E402
import requests  # noqa: E402

from runlog import log_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ISOLATION_DIR = ROOT / "intermediate" / "isolation"
CHARACTER_DIR = ROOT / "intermediate" / "characters"
OUTPUT_DIR = ROOT / "intermediate" / "animate"

MODEL = "fal-ai/wan/v2.2-14b/animate/move"

CHARACTER_REFS = {
    "kaia": CHARACTER_DIR / "kaia_ref_1.png",
    "luan": CHARACTER_DIR / "luan_ref_1.png",
}

# fal.ai rechnet (Frames / 16) x Preis pro "Videosekunde"
PRICE_PER_16_FRAMES = {"480p": 0.04, "580p": 0.06, "720p": 0.08}

MODEL_FPS = 16  # Wan arbeitet nativ mit 16 fps
SOLO_BG = (232, 232, 232)  # BGR, ähnlich dem Hintergrund der Referenzen
MASK_GROW_PX = 6  # Maske leicht vergrößern, damit Haare/Ränder drin bleiben
CROP_MARGIN_PX = 12  # Rand um den Bewegungsbereich


def read_masks(mask_path):
    cap = cv2.VideoCapture(str(mask_path))
    masks = []
    while True:
        ok, m = cap.read()
        if not ok:
            break
        masks.append(cv2.cvtColor(m, cv2.COLOR_BGR2GRAY) > 127)
    cap.release()
    return masks


def motion_box(masks, w, h):
    """Rechteck um alle Maskenpixel über den ganzen Clip, mit Rand, gerade Maße."""
    union = np.logical_or.reduce(masks)
    ys, xs = np.nonzero(union)
    x0 = max(int(xs.min()) - CROP_MARGIN_PX, 0)
    y0 = max(int(ys.min()) - CROP_MARGIN_PX, 0)
    x1 = min(int(xs.max()) + CROP_MARGIN_PX + 1, w)
    y1 = min(int(ys.max()) + CROP_MARGIN_PX + 1, h)
    # libx264 braucht gerade Breite/Höhe
    x1 -= (x1 - x0) % 2
    y1 -= (y1 - y0) % 2
    return x0, y0, x1, y1


def make_solo_video(clip, character, solo_path, crop_path):
    """Nur die gewählte Person, Rest grau, fester Ausschnitt, MODEL_FPS."""
    video_path = ISOLATION_DIR / f"{clip}_30fps.mp4"
    mask_path = ISOLATION_DIR / f"{clip}_masked_{character}.mp4"
    for p in (video_path, mask_path):
        if not p.exists():
            print(f"FEHLER: Datei nicht gefunden: {p} (erst Agent 1 laufen lassen)")
            sys.exit(1)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    masks = read_masks(mask_path)
    x0, y0, x1, y1 = motion_box(masks, w, h)
    cw, ch = x1 - x0, y1 - y0

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * MASK_GROW_PX + 1, 2 * MASK_GROW_PX + 1))
    bg = np.full((ch, cw, 3), SOLO_BG, np.uint8)
    silent_path = OUTPUT_DIR / f"{solo_path.stem}_silent.mp4"
    writer = cv2.VideoWriter(str(silent_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (cw, ch))
    for m in masks:
        ok, frame = cap.read()
        if not ok:
            break
        m = cv2.dilate(m[y0:y1, x0:x1].astype(np.uint8) * 255, kernel)
        alpha = cv2.GaussianBlur(m, (5, 5), 0).astype(np.float32)[..., None] / 255
        crop = frame[y0:y1, x0:x1]
        writer.write((crop * alpha + bg * (1 - alpha)).astype(np.uint8))
    writer.release()
    cap.release()

    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", str(silent_path), "-vf", f"fps={MODEL_FPS}",
         "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(solo_path)],
        check=True, capture_output=True,
    )
    silent_path.unlink()

    frames = int(cv2.VideoCapture(str(solo_path)).get(cv2.CAP_PROP_FRAME_COUNT))
    crop_path.write_text(json.dumps({
        "clip": clip, "character": character, "source_size": [w, h],
        "box_xyxy": [x0, y0, x1, y1], "source_fps": fps,
        "solo_fps": MODEL_FPS, "solo_frames": frames,
    }, indent=2), encoding="utf-8")
    print(f"Solo-Video erstellt: {solo_path}")
    print(f"  Ausschnitt x {x0}-{x1}, y {y0}-{y1} ({cw}x{ch} von {w}x{h}), "
          f"{frames} Frames @ {MODEL_FPS} fps")
    return frames, cw / ch


def pad_reference(ref_path, aspect, out_path):
    """Referenz mit ihrer eigenen Hintergrundfarbe auf Seitenverhältnis 'aspect' auffüllen."""
    img = cv2.imread(str(ref_path))
    h, w = img.shape[:2]
    fill = [int(v) for v in np.median(np.concatenate([img[:8].reshape(-1, 3),
                                                      img[:, :8].reshape(-1, 3)]), axis=0)]
    if w / h < aspect:  # zu schmal -> links/rechts auffüllen
        pad = int(round(h * aspect)) - w
        img = cv2.copyMakeBorder(img, 0, 0, pad // 2, pad - pad // 2,
                                 cv2.BORDER_CONSTANT, value=fill)
    else:  # zu breit -> oben/unten auffüllen
        pad = int(round(w / aspect)) - h
        img = cv2.copyMakeBorder(img, pad // 2, pad - pad // 2, 0, 0,
                                 cv2.BORDER_CONSTANT, value=fill)
    cv2.imwrite(str(out_path), img)
    print(f"Referenz aufgefüllt: {out_path} ({img.shape[1]}x{img.shape[0]})")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    clip, character = sys.argv[1], sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "480p"
    if character not in CHARACTER_REFS:
        print(f"FEHLER: Unbekannte Figur '{character}'. "
              f"Möglich: {', '.join(CHARACTER_REFS)}")
        sys.exit(1)
    if resolution not in PRICE_PER_16_FRAMES:
        print(f"FEHLER: Auflösung muss eine von {', '.join(PRICE_PER_16_FRAMES)} sein.")
        sys.exit(1)
    ref_path = CHARACTER_REFS[character]
    if not ref_path.exists():
        print(f"FEHLER: Referenz nicht gefunden: {ref_path} (erst Agent 3a)")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    solo_path = OUTPUT_DIR / f"{clip}_{character}_solo.mp4"
    crop_path = OUTPUT_DIR / f"{clip}_{character}_solo_crop.json"
    frames, aspect = make_solo_video(clip, character, solo_path, crop_path)
    ref_padded = OUTPUT_DIR / f"{clip}_{character}_ref_padded.png"
    pad_reference(ref_path, aspect, ref_padded)

    cost = frames / 16 * PRICE_PER_16_FRAMES[resolution]
    print(f"\nFigur:     {character} -> {ref_path.name} (aufgefüllt)")
    print(f"Modell:    {MODEL}, {resolution}")
    print(f"Kosten:    ca. {cost:.2f} $ (laut fal.ai-Preisangabe)")
    print(f"-> Prüfe vorher {solo_path.name}: ist nur {character} zu sehen?")

    answer = input("\nStartet einen kostenpflichtigen fal.ai-Call. Ok? [j/N] ")
    if answer.strip().lower() not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        sys.exit(0)

    started = time.monotonic()
    print("\nLade Solo-Video und Referenz hoch ...")
    video_url = fal_client.upload_file(str(solo_path))
    image_url = fal_client.upload_file(str(ref_padded))

    print(f"Starte {MODEL} (dauert erfahrungsgemäß 5-10 Minuten) ...")
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

    # Reihenfolge wichtig: zuerst das bezahlte Ergebnis sichern
    stem = f"{clip}_{character}_move_{resolution}"
    out_path = OUTPUT_DIR / f"{stem}.mp4"
    r = requests.get(result["video"]["url"], timeout=300)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    log_run(
        agent="03c_animate_move", model=MODEL, clip=clip, target=character,
        duration_s=time.monotonic() - started, cost_usd=cost,
        cost_basis=f"{frames} Frames / 16 x {PRICE_PER_16_FRAMES[resolution]} $ ({resolution})",
        details={"resolution": resolution, "frames": frames, "fps": MODEL_FPS,
                 "crop": json.loads(crop_path.read_text(encoding="utf-8"))["box_xyxy"],
                 "input_video": solo_path.name, "reference": ref_path.name},
        outputs=[out_path],
    )
    (OUTPUT_DIR / f"{stem}_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s ---")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()
