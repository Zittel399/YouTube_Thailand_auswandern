"""
Agent 4 — Compositing "Parallelwelten"-Look: Anime-Kinder in der echten Welt

Nimmt die Anime-Kinder aus der Kling-Version (Agent 3d) und setzt sie ins
echte Video. Alles andere bleibt fotorealistisch.

Eingaben (alle aus intermediate/isolation/, erzeugt von Agent 1):
  <clip>_30fps.mp4               echtes Video
  <clip>_masked_<figur>.mp4      Masken der ECHTEN Kinder
  <clip>_kling_30fps.mp4         Kling-Anime-Version (gleiche Bewegung)
  <clip>_kling_masked_<figur>.mp4  Masken der ANIME-Kinder

Optional (empfohlen): intermediate/cleanplate/<clip>_clean.mp4 von
Agent 2 = echtes Video ohne Kinder (ProPainter).

Die Anime-Figuren haben nicht exakt dieselbe Silhouette wie die echten
Kinder. Im Bereich der echten Kinder kommt der Hintergrund deshalb aus der
"leeren Bühne" von Agent 2 -- dort ist vom echten Kind nichts mehr übrig.
Überall sonst bleibt das echte Video (schärfer, original). Gibt es keine
leere Bühne, wird lokal per OpenCV aufgefüllt (sichtbare Schleier).
Gegenstände, mit denen die Kinder spielen (KEEP_OBJECTS, z.B. das
Skateboard), kommen immer aus dem echten Video -- pixelgenau über ihre
eigene SAM2-Maske (<clip>_masked_<objekt>.mp4), sonst grob über sehr dunkle
Pixel in Kaias Maske.

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
CLEANPLATE_DIR = ROOT / "intermediate" / "cleanplate"
OUTPUT_DIR = ROOT / "output"

FIGURES = ["kaia", "luan"]
OUT_WIDTH = 720  # Höhe ergibt sich aus dem Seitenverhältnis des echten Videos

REAL_MASK_GROW_PX = 10  # echte Kindermaske großzügig, damit nichts durchschaut
ANIME_FEATHER_PX = 3  # weicher Rand der Anime-Figuren
KEEP_DARK_BELOW = 55  # Helligkeit (0-255): so dunkle Pixel nicht auffüllen
# Nur bei diesen Figuren dunkle Pixel stehen lassen (Kaia sitzt auf dem
# schwarzen Skateboard). Bei Luan wäre das seine dunkle Jacke -> auffüllen.
KEEP_DARK_FIGURES = {"kaia"}  # Fallback, wenn es keine Objektmaske gibt
KEEP_OBJECTS = ["skateboard"]  # eigene SAM2-Masken, falls vorhanden
INPAINT_RADIUS = 6  # nur ohne leere Bühne (Fallback)
BLEND_PX = 4  # weicher Übergang zwischen echtem Video und leerer Bühne


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
    keep_paths = [ISOLATION_DIR / f"{clip}_masked_{o}.mp4" for o in KEEP_OBJECTS]
    keep_caps = [cv2.VideoCapture(str(p)) for p in keep_paths if p.exists()]
    print("Gegenstände aus echtem Video: " + (", ".join(p.stem for p in keep_paths if p.exists())
                                              or "dunkle Pixel (keine Objektmaske gefunden)"))
    plate_path = CLEANPLATE_DIR / f"{clip}_clean.mp4"
    plate_cap = cv2.VideoCapture(str(plate_path)) if plate_path.exists() else None
    print(f"Hintergrund: {'leere Bühne ' + plate_path.name if plate_cap else 'OpenCV-Auffüllen (keine leere Bühne gefunden)'}")
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
            if f in KEEP_DARK_FIGURES and not keep_caps:
                keep_dark |= real_f & (gray < KEEP_DARK_BELOW)
        for kc in keep_caps:
            keep_dark |= read_mask(kc, size)

        # Wo das echte Kind sichtbar bliebe -> Hintergrund ersetzen,
        # aber dunkle echte Gegenstände (Skateboard) stehen lassen
        real_grown = cv2.dilate(real_kids.astype(np.uint8), grow) > 0
        keep_dark = cv2.morphologyEx(keep_dark.astype(np.uint8), cv2.MORPH_CLOSE,
                                     np.ones((5, 5), np.uint8)) > 0
        hole = real_grown & ~keep_dark
        hole_share.append((hole & ~anime_kids).mean())
        if plate_cap is not None:
            ok_p, plate = plate_cap.read()
            plate = cv2.resize(plate, size, interpolation=cv2.INTER_LANCZOS4)
            k = 2 * BLEND_PX + 1
            w = cv2.GaussianBlur(hole.astype(np.float32), (k, k), 0)[..., None]
            background = (plate * w + real * (1 - w)).astype(np.uint8)
        else:
            hole_u8 = (hole & ~anime_kids).astype(np.uint8) * 255
            background = cv2.inpaint(real, hole_u8, INPAINT_RADIUS, cv2.INPAINT_TELEA)

        alpha = cv2.GaussianBlur(anime_kids.astype(np.float32), (feather, feather), 0)[..., None]
        frame = (anime * alpha + background * (1 - alpha)).astype(np.uint8)
        writer.write(frame)

        if frames % 56 == 0:
            samples.append((frames, real, frame))
        frames += 1
    writer.release()
    for c in caps.values():
        c.release()
    if plate_cap is not None:
        plate_cap.release()
    for kc in keep_caps:
        kc.release()

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
    print(f"  ersetzter Hintergrund (nicht von Anime verdeckt): Ø {100 * np.mean(hole_share):.1f} %, "
          f"max {100 * np.max(hole_share):.1f} %")
    print(f"  {out_path}")
    print(f"  {compare_path}")


if __name__ == "__main__":
    main()
