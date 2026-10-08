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
    python agents/01_isolate.py                 # Default: test_15s
    python agents/01_isolate.py test_8s         # anderer Clip aus input/test_clips/
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
CLIP = sys.argv[1] if len(sys.argv) > 1 else "test_15s"
SOURCE_PATH = ROOT / "input" / "test_clips" / f"{CLIP}.mp4"
OUTPUT_DIR = ROOT / "intermediate" / "isolation"
PREVIEW_PATH = OUTPUT_DIR / f"{CLIP}_frame0_preview.png"

# Handyclips sind oft 120 fps oder haben variable Bildrate -> SAM2 würde 1800 Frames tracken (fal.ai rechnet
# nach Rechenzeit ab). Daher vorher lokal auf TARGET_FPS reduzieren und
# diese Kopie an SAM2 schicken. Das Original in input/ bleibt unverändert.
TARGET_FPS = 30
VIDEO_PATH = OUTPUT_DIR / f"{CLIP}_{TARGET_FPS}fps.mp4"

# ---------------------------------------------------------------------
# Foreground-Punkte für SAM2: sagen dem Modell, WELCHE Person es tracken
# soll. Je Punkt (frame, x, y): Frame-Index im 30-fps-Video, (x, y) in
# Pixeln, Ursprung oben links. Punkte gelten je Clip (TARGETS_BY_CLIP).
# fal-ai/sam2/video kennt keine Objekt-IDs (alle Punkte eines Calls
# ergeben EINE Maske) -> pro Person ein eigener Call, eigene Maske.
# Je Person zwei Punkte (Kopf + Oberkörper), damit SAM2 die ganze
# Person nimmt und nicht nur den Kopf. Schwenkt die Kamera weg und
# wieder zurück, zusätzliche Punkte in den Frames setzen, in denen die
# Person wieder auftaucht -- sonst findet SAM2 sie oft nicht wieder.
# -> PRÜFE prompts_preview_marked.png (wird unten erzeugt) und passe die
#    Werte bei Bedarf an, bevor du den fal.ai-Call startest!
# ---------------------------------------------------------------------
TARGETS_BY_CLIP = {
    "test_15s": {  # 368x480, Frühstück am Pool, Kamera schwenkt viel
        "kaia": [  # Kind im Kinderstuhl rechts
            (0, 300, 330), (0, 295, 370),
            (45, 215, 305), (45, 225, 345),
            (90, 264, 310), (90, 265, 360),
            (330, 224, 310), (330, 230, 355),
        ],
        "luan": [  # stehendes Kind Mitte, vor der Säule
            (0, 188, 255), (0, 185, 310),
            (15, 280, 265), (15, 280, 305),
            (105, 165, 250),  # nur Kopf, darunter verdeckt der Plüsch-Dino
        ],
    },
    "test_8s": {  # 368x496, Wohnzimmer mit Skateboard, ruhige Kamera
        "kaia": [  # kleines Kind im hellen Outfit auf dem Skateboard
            (0, 178, 215), (0, 175, 240),
        ],
        "luan": [  # stehendes Kind in blau-grüner Jacke, links
            (0, 92, 70), (0, 78, 160),
        ],
    },
}
if CLIP not in TARGETS_BY_CLIP:
    print(f"FEHLER: Für Clip '{CLIP}' sind keine Prompt-Punkte hinterlegt "
          f"(TARGETS_BY_CLIP).")
    sys.exit(1)
TARGETS = TARGETS_BY_CLIP[CLIP]
PROMPT_LABEL = 1  # 1 = Vordergrund (das willst du maskieren), 0 = Hintergrund
MARKED_PREVIEW_PATH = OUTPUT_DIR / f"{CLIP}_prompts_preview_marked.png"
OVERLAY_PATH = OUTPUT_DIR / f"{CLIP}_overlay.mp4"
COLORS = {"kaia": (0, 255, 0), "luan": (255, 160, 0)}  # BGR


def reduce_framerate():
    """Quellvideo lokal auf TARGET_FPS herunterrechnen (Audio unverändert)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y", "-i", str(SOURCE_PATH),
            "-vf", f"fps={TARGET_FPS}",
            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(VIDEO_PATH),
        ],
        check=True,
        capture_output=True,
    )
    print(f"{TARGET_FPS}-fps-Kopie erstellt: {VIDEO_PATH}")


def extract_preview_frame():
    """Frame 0 lokal extrahieren, damit der Prompt-Punkt geprüft werden kann."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y", "-i", str(VIDEO_PATH),
            "-vf", "select=eq(n\\,0)", "-vframes", "1",
            "-update", "1", str(PREVIEW_PATH),
        ],
        check=True,
        capture_output=True,
    )
    print(f"Vorschau-Frame gespeichert: {PREVIEW_PATH}")

    # Alle Frames mit Prompt-Punkten nebeneinander, Punkte eingezeichnet
    prompt_frames = sorted({f for pts in TARGETS.values() for f, _, _ in pts})
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    tiles = []
    for frame_idx in prompt_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, img = cap.read()
        if not ok:
            print(f"FEHLER: Frame {frame_idx} lässt sich nicht lesen.")
            sys.exit(1)
        for name, points in TARGETS.items():
            color = COLORS.get(name, (0, 200, 255))
            pts = [(x, y) for f, x, y in points if f == frame_idx]
            for x, y in pts:
                cv2.circle(img, (x, y), 8, (0, 0, 0), 3)
                cv2.circle(img, (x, y), 8, color, 2)
                cv2.circle(img, (x, y), 2, (0, 0, 255), -1)
            if pts:
                x, y = pts[0]
                cv2.putText(img, name, (x + 11, y + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(img, name, (x + 11, y + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(img, f"Frame {frame_idx}", (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(img, f"Frame {frame_idx}", (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        tiles.append(img)
    cap.release()
    cv2.imwrite(str(MARKED_PREVIEW_PATH), cv2.hconcat(tiles))
    print(f"Vorschau mit Prompt-Punkten: {MARKED_PREVIEW_PATH}")
    print("  -> Öffne das Bild und prüfe, ob die Punkte wirklich auf den "
          "gewünschten Personen liegen. Falls nicht: TARGETS im Skript "
          "anpassen und neu starten.")


def write_overlay():
    """Alle Masken halbtransparent über das Video legen (mit Originalton)."""
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    mask_caps = {name: cv2.VideoCapture(str(OUTPUT_DIR / f"{CLIP}_masked_{name}.mp4"))
                 for name in TARGETS}
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    silent_path = OUTPUT_DIR / "overlay_silent.mp4"
    writer = cv2.VideoWriter(str(silent_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        for name, mcap in mask_caps.items():
            ok, mask = mcap.read()
            if not ok:
                continue
            m = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY) > 127
            color = COLORS.get(name, (0, 200, 255))
            frame[m] = (0.5 * frame[m] + 0.5 * np.array(color)).astype(np.uint8)
        writer.write(frame)
    writer.release()
    cap.release()
    for mcap in mask_caps.values():
        mcap.release()

    # H.264 + Originalton, damit es in jedem Player läuft
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y", "-i", str(silent_path), "-i", str(VIDEO_PATH),
            "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "copy", str(OVERLAY_PATH),
        ],
        check=True,
        capture_output=True,
    )
    silent_path.unlink()
    print(f"Overlay-Video erstellt: {OVERLAY_PATH}")


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"  [fal.ai] {log['message']}")


def main():
    if not SOURCE_PATH.exists():
        print(f"FEHLER: Testvideo nicht gefunden unter {SOURCE_PATH}")
        print("Leg die 15-Sekunden-Testdatei dort ab (siehe Chat-Anleitung).")
        sys.exit(1)

    reduce_framerate()
    extract_preview_frame()

    answer = input(f"\nPrompt-Punkte für {', '.join(TARGETS)} geprüft und ok? "
                   f"Startet {len(TARGETS)} kostenpflichtige fal.ai-Calls. [j/N] ")
    answer = answer.strip().lower()
    if answer not in ("j", "ja", "y", "yes"):
        print("Abgebrochen. Passe TARGETS an und starte erneut.")
        sys.exit(0)

    started = time.monotonic()
    print(f"\nLade Video zu fal.ai hoch: {VIDEO_PATH}")
    video_url = fal_client.upload_file(str(VIDEO_PATH))
    print(f"Hochgeladen: {video_url}")

    out_paths = []
    for name, points in TARGETS.items():
        print(f"\nStarte SAM2-Segmentierung für '{name}' (fal-ai/sam2/video) ...")
        call_started = time.monotonic()
        result = fal_client.subscribe(
            "fal-ai/sam2/video",
            arguments={
                "video_url": video_url,
                "prompts": [
                    {
                        "x": x,
                        "y": y,
                        "frame_index": frame_idx,
                        "label": PROMPT_LABEL,
                    }
                    for frame_idx, x, y in points
                ],
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        result_json_path = OUTPUT_DIR / f"{CLIP}_result_{name}.json"
        result_json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
        print(f"Roh-Ergebnis gespeichert: {result_json_path}")

        out_video_url = result["video"]["url"]
        out_path = OUTPUT_DIR / f"{CLIP}_masked_{name}.mp4"
        print(f"Lade maskiertes Video herunter von {out_video_url} ...")
        r = requests.get(out_video_url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        print(f"Gespeichert: {out_path}")
        out_paths.append(out_path)
        log_run(
            agent="01_isolate", model="fal-ai/sam2/video", clip=CLIP, target=name,
            duration_s=time.monotonic() - call_started,
            cost_basis="nach GPU-Rechenzeit, Preis von fal.ai nicht veröffentlicht",
            details={"fps": TARGET_FPS, "prompt_points": len(points),
                     "prompt_frames": sorted({f for f, _, _ in points})},
            outputs=[out_path],
        )

    write_overlay()
    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s ---")
    for out_path in out_paths:
        print(f"  {out_path}")
    print(f"  {OVERLAY_PATH}  (Masken farbig über dem Original, zum Anschauen)")
    print("Passt jede Maske über den gesamten Clip auf die jeweilige")
    print("Person? Falls nicht: TARGETS anpassen (mehr Punkte, ggf. Label 0")
    print("für Hintergrund), dann neu starten.")
    print("\nKosten: fal.ai rechnet nach Rechenzeit ab — Stand prüfst du im")
    print("fal.ai-Dashboard unter 'Billing/Usage', ich habe darauf keinen Zugriff.")


if __name__ == "__main__":
    main()
