"""
Agent 3d — Beide Kinder in einem Schritt durch Anime-Figuren ersetzen
(Kling O1 Edit, Video-zu-Video per Textanweisung)

Kling O1 Edit bearbeitet ein bestehendes Video per Prompt, behält die
originale Bewegung und den Bildaufbau und nimmt bis zu 4 Referenzbilder
(@Image1, @Image2 ...). Damit lassen sich mehrere Personen in einem Call
tauschen -- inkl. Interaktionen (Hände auf dem Skateboard, Nähe).

Vorbereitung (lokal): Kling braucht 720-2160 px und 3-10,05 s. Der Clip
wird auf mindestens 720 px (kürzere Seite) hochskaliert.

Läuft lokal (fal.ai ist aus der Cloud-Sandbox nicht erreichbar).

Ausführen:
    python agents/03d_kling_edit.py <clip>
    python agents/03d_kling_edit.py test_8s
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
OUTPUT_DIR = ROOT / "intermediate" / "kling"

MODEL = "fal-ai/kling-video/o1/video-to-video/edit"
PRICE_PER_SECOND = 0.168  # USD, Stand 2026-10, Angabe fal.ai
MIN_SIDE_PX = 720
MAX_DURATION_S = 10.05

# Reihenfolge = @Image1, @Image2, ...
REFERENCES = [
    CHARACTER_DIR / "kaia_ref_1.png",
    CHARACTER_DIR / "luan_ref_1.png",
]

# Je Clip: wer ist wer (Beschreibung, wie die Kinder im Video aussehen)
PROMPTS_BY_CLIP = {
    "test_8s": (
        "Replace the small toddler girl in the light pink and white outfit who "
        "crawls on the skateboard with the anime girl from @Image1, and replace "
        "the older child with the blonde hair bun in the blue and green jacket "
        "with the anime child from @Image2. Both children become hand-drawn "
        "characters in the soft watercolor anime style of the reference images, "
        "with exactly the same movements, poses, positions and interactions as "
        "in the original video, including the hands on the skateboard. Keep "
        "the room, the floor, the skateboard, the furniture and the toys "
        "photorealistic and unchanged. Keep the camera movement unchanged."
    ),
}


def prepare_video(clip, out_path):
    """30-fps-Video so hochskalieren, dass die kürzere Seite >= MIN_SIDE_PX ist."""
    src = ISOLATION_DIR / f"{clip}_30fps.mp4"
    if not src.exists():
        print(f"FEHLER: Datei nicht gefunden: {src} (erst Agent 1 laufen lassen)")
        sys.exit(1)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:format=duration", "-of", "json", str(src)],
        check=True, capture_output=True, text=True,
    )
    info = json.loads(probe.stdout)
    w, h = info["streams"][0]["width"], info["streams"][0]["height"]
    duration = float(info["format"]["duration"])
    if not 3.0 <= duration <= MAX_DURATION_S:
        print(f"FEHLER: Clip ist {duration:.2f} s lang, Kling erlaubt 3-{MAX_DURATION_S} s.")
        sys.exit(1)

    scale = max(1.0, MIN_SIDE_PX / min(w, h))
    nw, nh = int(round(w * scale / 2)) * 2, int(round(h * scale / 2)) * 2
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", str(src),
         "-vf", f"scale={nw}:{nh}:flags=lanczos",
         "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", str(out_path)],
        check=True, capture_output=True,
    )
    print(f"Eingabe vorbereitet: {out_path} ({w}x{h} -> {nw}x{nh}, {duration:.2f} s)")
    return duration, (nw, nh)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    clip = sys.argv[1]
    if clip not in PROMPTS_BY_CLIP:
        print(f"FEHLER: Für Clip '{clip}' ist kein Prompt hinterlegt (PROMPTS_BY_CLIP).")
        sys.exit(1)
    for p in REFERENCES:
        if not p.exists():
            print(f"FEHLER: Referenz nicht gefunden: {p} (erst Agent 3a)")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / f"{clip}_kling_input.mp4"
    duration, size = prepare_video(clip, input_path)
    prompt = PROMPTS_BY_CLIP[clip]
    cost = duration * PRICE_PER_SECOND

    print(f"\nModell:    {MODEL}")
    for i, p in enumerate(REFERENCES, start=1):
        print(f"@Image{i}:   {p.name}")
    print(f"Prompt:    {prompt}")
    print(f"Kosten:    ca. {cost:.2f} $ ({duration:.2f} s x {PRICE_PER_SECOND} $)")

    answer = input("\nStartet einen kostenpflichtigen fal.ai-Call. Ok? [j/N] ")
    if answer.strip().lower() not in ("j", "ja", "y", "yes"):
        print("Abgebrochen.")
        sys.exit(0)

    started = time.monotonic()
    print("\nLade Video und Referenzen hoch ...")
    video_url = fal_client.upload_file(str(input_path))
    image_urls = [fal_client.upload_file(str(p)) for p in REFERENCES]

    print(f"Starte {MODEL} (kann einige Minuten dauern) ...")
    result = fal_client.subscribe(
        MODEL,
        arguments={
            "prompt": prompt,
            "video_url": video_url,
            "image_urls": image_urls,
            "keep_audio": True,
        },
        with_logs=True,
        on_queue_update=lambda u: [print(f"  [fal.ai] {log['message']}")
                                   for log in getattr(u, "logs", None) or []],
    )

    # Reihenfolge wichtig: zuerst das bezahlte Ergebnis sichern
    stem = f"{clip}_kling_edit"
    out_path = OUTPUT_DIR / f"{stem}.mp4"
    r = requests.get(result["video"]["url"], timeout=300)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    log_run(
        agent="03d_kling_edit", model=MODEL, clip=clip, target="kaia+luan",
        duration_s=time.monotonic() - started, cost_usd=cost,
        cost_basis=f"{duration:.2f} s x {PRICE_PER_SECOND} $",
        details={"input_size": list(size), "references": [p.name for p in REFERENCES],
                 "prompt": prompt},
        outputs=[out_path],
    )
    (OUTPUT_DIR / f"{stem}_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n--- Fertig nach {time.monotonic() - started:.0f} s ---")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()
