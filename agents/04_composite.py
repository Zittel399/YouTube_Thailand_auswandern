"""
Agent 4 — Compositing "Parallelwelten"-Look: Anime-Kinder in der echten Welt

Nimmt die Anime-Kinder aus der Kling-Version (Agent 3d) und setzt sie ins
echte Video. Alles andere bleibt fotorealistisch.

Eingaben (alle aus intermediate/isolation/, erzeugt von Agent 1):
  <clip>_30fps.mp4               echtes Video
  <clip>_masked_<figur>.mp4      Masken der ECHTEN Kinder
  <clip>_kling_30fps.mp4         Kling-Anime-Version (gleiche Bewegung)
  <clip>_kling_masked_<figur>.mp4  Masken der ANIME-Kinder

Die Anime-Figuren haben nicht exakt dieselbe Silhouette wie die echten
Kinder. Wo ein echtes Kind hinter der Anime-Figur hervorschauen würde,
wird der Hintergrund aufgefüllt (OpenCV-Inpainting, lokal, kostenlos).
Sehr dunkle Pixel (z.B. das schwarze Skateboard) werden dabei nicht
aufgefüllt, damit echte Gegenstände, die in der Kindermaske stecken,
erhalten bleiben.

Ausgabe: output/<clip>_parallelwelten.mp4 und ein Vergleichsbild.
Läuft komplett lokal, keine API-Kosten.

Ausführen:
    python agents/04_composite.py test_8s
"""

import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ISOLATION_DIR = ROOT / "intermediate" / "isolation"
OUTPUT_DIR = ROOT / "output"

FIGURES = ["kaia", "luan"]
OUT_WIDTH = 720  # Höhe ergibt sich aus dem Seitenverhältnis des echten Videos

REAL_MASK_GROW_PX = 10  # echte Kindermaske großzügig, damit nichts durchschaut
ANIME_FEATHER_PX = 3  # weicher Rand der Anime-Figuren
KEEP_DARK_BELOW = 55  # Helligkeit (0-255): so dunkle Pixel nicht auffüllen
# Nur bei diesen Figuren dunkle Pixel stehen lassen (Kaia sitzt auf dem
# schwarzen Skateboard). Bei Luan wäre das seine dunkle Jacke -> auffüllen.
KEEP_DARK_FIGURES = {"kaia"}
INPAINT_RADIUS = 6


def open_videos(clip):
    paths = {
        "real": ISOLATION_DIR / f"{clip}_30fps.mp4",
        "anime": ISOLATION_DIR / f"{clip}_kling_30fps.mp4",
    }
    for f in FIGURES:
        paths[f"real_{f}"] = ISOLATION_DIR / f"{clip}_masked_{f}.mp4"
        paths[f"anime_{f}"] = ISOLATION_DIR / f"{clip}_kling_masked_{f}.mp4"
    missing = [p for p in paths.values() if not p.exists()]
    if missing:
        print("FEHLER: Dateien fehlen (erst Agent 1 auf <clip> und <clip>_kling):")
        for p in missing:
            print(f"  {p}")
        sys.exit(1)
    return {k: cv2.VideoCapture(str(p)) for k, p in paths.items()}


def read_mask(cap, size):
    ok, m = cap.read()
    if not ok:
        return None
    m = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    return cv2.resize(m, size, interpolation=cv2.INTER_LINEAR) > 127


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    clip = sys.argv[1]
    caps = open_videos(clip)
    started = time.monotonic()

    rw = int(caps["real"].get(cv2.CAP_PROP_FRAME_WIDTH))
    rh = int(caps["real"].get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = caps["real"].get(cv2.CAP_PROP_FPS)
    ow = OUT_WIDTH
    oh = int(round(rh * ow / rw / 2)) * 2
    size = (ow, oh)

    grow = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * REAL_MASK_GROW_PX + 1, 2 * REAL_MASK_GROW_PX + 1))
    feather = 2 * ANIME_FEATHER_PX + 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    silent_path = OUTPUT_DIR / f"{clip}_parallelwelten_silent.mp4"
    out_path = OUTPUT_DIR / f"{clip}_parallelwelten.mp4"
    writer = cv2.VideoWriter(str(silent_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)

    samples = []
    frames = 0
    hole_share = []
    while True:
        ok_r, real = caps["real"].read()
        ok_a, anime = caps["anime"].read()
        if not (ok_r and ok_a):
            break
        real = cv2.resize(real, size, interpolation=cv2.INTER_LANCZOS4)
        anime = cv2.resize(anime, size, interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(real, cv2.COLOR_BGR2GRAY)
        real_kids = np.zeros((oh, ow), bool)
        anime_kids = np.zeros((oh, ow), bool)
        keep_dark = np.zeros((oh, ow), bool)
        for f in FIGURES:
            real_f = read_mask(caps[f"real_{f}"], size)
            real_kids |= real_f
            anime_kids |= read_mask(caps[f"anime_{f}"], size)
            if f in KEEP_DARK_FIGURES:
                keep_dark |= real_f & (gray < KEEP_DARK_BELOW)

        # Wo das echte Kind sichtbar bliebe -> Hintergrund auffüllen,
        # aber dunkle echte Gegenstände (Skateboard) stehen lassen
        real_grown = cv2.dilate(real_kids.astype(np.uint8), grow) > 0
        hole = real_grown & ~anime_kids & ~keep_dark
        hole_u8 = hole.astype(np.uint8) * 255
        background = cv2.inpaint(real, hole_u8, INPAINT_RADIUS, cv2.INPAINT_TELEA)
        hole_share.append(hole.mean())

        alpha = cv2.GaussianBlur(anime_kids.astype(np.float32), (feather, feather), 0)[..., None]
        frame = (anime * alpha + background * (1 - alpha)).astype(np.uint8)
        writer.write(frame)

        if frames % 56 == 0:
            samples.append((frames, real, frame))
        frames += 1
    writer.release()
    for c in caps.values():
        c.release()

    # H.264 + Originalton (Kling-Version ist etwas kürzer -> -shortest)
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", str(silent_path),
         "-i", str(ISOLATION_DIR / f"{clip}_30fps.mp4"),
         "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
         str(out_path)],
        check=True, capture_output=True,
    )
    silent_path.unlink()

    # Vergleichsbild: oben echt, unten Parallelwelten
    tiles = []
    for idx, real, comp in samples:
        th = (int(oh * 240 / ow), 240)
        col = np.vstack([cv2.resize(real, (240, th[0])),
                         np.full((4, 240, 3), 40, np.uint8),
                         cv2.resize(comp, (240, th[0]))])
        label = f"{idx / fps:.1f}s"
        cv2.putText(col, label, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(col, label, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        tiles.append(col)
    compare_path = OUTPUT_DIR / f"{clip}_parallelwelten_vergleich.png"
    cv2.imwrite(str(compare_path), np.hstack(tiles))

    print(f"Fertig nach {time.monotonic() - started:.0f} s: {frames} Frames, {ow}x{oh}")
    print(f"  aufgefüllter Anteil pro Frame: Ø {100 * np.mean(hole_share):.1f} %, "
          f"max {100 * np.max(hole_share):.1f} %")
    print(f"  {out_path}")
    print(f"  {compare_path}")


if __name__ == "__main__":
    main()
