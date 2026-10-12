"""
Agent 5 — Short-Vorlage: fertiges Video -> 9:16-Short mit Serien-Signatur

Macht aus dem Ergebnis von Agent 4 (Look B) bzw. Look A einen Short in
1080x1920 mit:
  - Serien-Kennung "PARALLELWELTEN · Folge N" (jede Folge erweitert die Geschichte)
  - Untertiteln in einem festen Stil (zum Vergleich mehrere Varianten)
  - Ton: Original + Platzhalter-Sound-Sting am Anfang; Musik-Slot (MUSIC_PATH),
    solange keine Musik feststeht, bleibt er leer

Format: Das Video wird in voller Breite eingepasst, oben/unten füllt eine
unscharfe, abgedunkelte Version desselben Bildes auf. So wird nichts
abgeschnitten (Kinder am Bildrand bleiben drin), und die Untertitel haben
eigene Flächen, ohne die Figuren zu verdecken.

Läuft komplett lokal, keine API-Kosten.

Ausführen:
    python agents/05_short_template.py test_8s              # alle Varianten
    python agents/05_short_template.py test_8s klar         # nur eine Variante
"""

import math
import subprocess
import sys
import time
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
FONT_DIR = Path("C:/Windows/Fonts")

W, H = 1080, 1920
MUSIC_PATH = None  # Platzhalter: Pfad zu lizenzierter Musik, sobald entschieden
MUSIC_GAIN_DB = -18

SERIES = "PARALLELWELTEN"

# Inhalt je Clip: Folge, Titel, Untertitel (Start s, Ende s, Text).
# Platzhalter-Texte -- später schreibt sie ein LLM nach docs/STORYLINE.md.
EPISODES = {
    "test_8s": {
        "source": OUTPUT_DIR / "test_8s_parallelwelten.mp4",
        "folge": 1,
        "titel": "Das Skateboard",
        "zeilen": [
            (0.4, 3.2, "Luan hat das Skateboard entdeckt."),
            (3.2, 6.2, "Kaia will natürlich sofort mit."),
            (6.2, 9.3, "Wer am Ende oben sitzt? Na klar."),
        ],
    },
}


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


# ---------------------------------------------------------------------------
# Untertitel-Varianten
# ---------------------------------------------------------------------------

def badge(draw, folge, x, y, scale=1.0):
    """Serien-Kennung: kleines Label + Folgennummer."""
    f_small = font("seguibl.ttf", int(30 * scale))
    f_big = font("seguibl.ttf", int(54 * scale))
    label = f"{SERIES}"
    folge_txt = f"Folge {folge}"
    lw = draw.textlength(label, font=f_small)
    fw = draw.textlength(folge_txt, font=f_big)
    pad = int(18 * scale)
    bw = int(max(lw, fw) + 2 * pad)
    bh = int(30 * scale + 54 * scale + 2.6 * pad)
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=int(16 * scale),
                           fill=(0, 0, 0, 150))
    draw.text((x + pad, y + pad * 0.6), label, font=f_small, fill=(255, 214, 102, 255))
    draw.text((x + pad, y + pad * 0.6 + 30 * scale + 6), folge_txt, font=f_big,
              fill=(255, 255, 255, 255))


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if draw.textlength(test, font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def style_klar(draw, ep, t, line, word_idx):
    """V1 'klar': Kennung oben links, Zeilen-Untertitel unten, weiß mit Kontur."""
    badge(draw, ep["folge"], 48, 70)
    if line is None:
        return
    fnt = font("seguibl.ttf", 68)
    lines = wrap(draw, line, fnt, W - 160)
    y = H - 330 - (len(lines) - 1) * 84
    for ln in lines:
        lw = draw.textlength(ln, font=fnt)
        draw.text(((W - lw) / 2, y), ln, font=fnt, fill=(255, 255, 255, 255),
                  stroke_width=7, stroke_fill=(0, 0, 0, 255))
        y += 84


def style_wort(draw, ep, t, line, word_idx):
    """V2 'Wort für Wort': große Großbuchstaben, aktuelles Wort gelb (Trend-Stil)."""
    badge(draw, ep["folge"], 48, 70, scale=0.8)
    if line is None:
        return
    fnt = font("ariblk.ttf", 82)
    words = line.upper().split()
    lines = wrap(draw, " ".join(words), fnt, W - 140)
    y = H - 380 - (len(lines) - 1) * 100
    k = 0
    for ln in lines:
        lw = draw.textlength(ln, font=fnt)
        x = (W - lw) / 2
        for w_ in ln.split():
            active = k == word_idx
            color = (255, 214, 0, 255) if active else (255, 255, 255, 255)
            if k > word_idx:
                color = (255, 255, 255, 110)  # noch nicht gesprochen: blass
            draw.text((x, y), w_, font=fnt, fill=color, stroke_width=8,
                      stroke_fill=(0, 0, 0, 255))
            x += draw.textlength(w_ + " ", font=fnt)
            k += 1
        y += 100


def style_manga(draw, ep, t, line, word_idx):
    """V3 'Manga': Titelkarte am Anfang, danach Sprechbox unten, Kennung oben mittig."""
    if t < 1.3:  # Titelkarte "Folge N"
        a = 1.0 if t < 1.0 else max(0.0, (1.3 - t) / 0.3)
        draw.rectangle([0, 0, W, H], fill=(0, 0, 0, int(150 * a)))
        f1 = font("seguibl.ttf", 44)
        f2 = font("seguibl.ttf", 150)
        f3 = font("seguibl.ttf", 64)
        for txt, f_, y, col in ((SERIES, f1, 700, (255, 214, 102)),
                                (f"FOLGE {ep['folge']}", f2, 770, (255, 255, 255)),
                                (ep["titel"], f3, 960, (255, 255, 255))):
            lw = draw.textlength(txt, font=f_)
            draw.text(((W - lw) / 2, y), txt, font=f_, fill=(*col, int(255 * a)),
                      stroke_width=4, stroke_fill=(0, 0, 0, int(255 * a)))
        return
    f_top = font("seguibl.ttf", 36)
    top = f"{SERIES} · FOLGE {ep['folge']}"
    lw = draw.textlength(top, font=f_top)
    draw.text(((W - lw) / 2, 90), top, font=f_top, fill=(255, 255, 255, 230),
              stroke_width=3, stroke_fill=(0, 0, 0, 200))
    if line is None:
        return
    fnt = font("bahnschrift.ttf", 62)
    lines = wrap(draw, line, fnt, W - 260)
    box_h = 70 * len(lines) + 70
    x0, x1 = 90, W - 90
    y0 = H - 250 - box_h
    draw.rounded_rectangle([x0, y0, x1, y0 + box_h], radius=36, fill=(255, 255, 255, 240),
                           outline=(0, 0, 0, 255), width=6)
    # kleiner Sprechblasen-Zipfel
    draw.polygon([(x0 + 120, y0), (x0 + 170, y0), (x0 + 110, y0 - 50)],
                 fill=(255, 255, 255, 240), outline=(0, 0, 0, 255))
    draw.line([(x0 + 122, y0 + 3), (x0 + 168, y0 + 3)], fill=(255, 255, 255, 240), width=8)
    y = y0 + 35
    for ln in lines:
        lw = draw.textlength(ln, font=fnt)
        draw.text(((W - lw) / 2, y), ln, font=fnt, fill=(20, 20, 20, 255))
        y += 70


STYLES = {
    "klar": style_klar,
    "wort": style_wort,
    "manga": style_manga,
}


# ---------------------------------------------------------------------------
# Bild, Ton, Ausgabe
# ---------------------------------------------------------------------------

def frame_9x16(frame):
    """Volle Breite einpassen, oben/unten unscharfer Hintergrund."""
    h, w = frame.shape[:2]
    scale_cover = max(W / w, H / h)
    bg = cv2.resize(frame, (int(w * scale_cover), int(h * scale_cover)))
    by, bx = (bg.shape[0] - H) // 2, (bg.shape[1] - W) // 2
    bg = bg[by:by + H, bx:bx + W]
    bg = cv2.GaussianBlur(bg, (0, 0), 28)
    bg = (bg * 0.55).astype(np.uint8)
    fh = int(round(h * W / w))
    fg = cv2.resize(frame, (W, fh), interpolation=cv2.INTER_LANCZOS4)
    y = (H - fh) // 2
    bg[y:y + fh] = fg
    return bg


def current_line(ep, t):
    for start, end, text in ep["zeilen"]:
        if start <= t < end:
            n = len(text.split())
            idx = min(n - 1, int((t - start) / (end - start) * n))
            return text, idx
    return None, -1


def write_sting(path, sr=48000):
    """Platzhalter-Sound-Sting: zwei kurze, weiche Töne (wird später ersetzt)."""
    t = np.arange(int(0.55 * sr)) / sr
    sig = np.zeros_like(t)
    for f0, start in ((784.0, 0.0), (1175.0, 0.16)):
        tt = np.clip(t - start, 0, None)
        env = (t >= start) * np.exp(-tt * 7) * np.minimum(1, tt * 200)
        sig += 0.35 * env * np.sin(2 * math.pi * f0 * tt)
    pcm = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def render(clip, style_name, ep):
    src = ep["source"]
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS)
    silent = OUTPUT_DIR / f"{clip}_short_{style_name}_silent.mp4"
    out = OUTPUT_DIR / f"{clip}_short_{style_name}.mp4"
    writer = cv2.VideoWriter(str(silent), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    style = STYLES[style_name]
    cache = {}
    stills = []
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        line, widx = current_line(ep, t)
        # Overlay nur neu zeichnen, wenn sich Text/Zustand ändert
        key = (line, widx, round(t, 1) if t < 1.4 else None)
        if key not in cache:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            style(ImageDraw.Draw(ov), ep, t, line, widx)
            arr = np.array(ov).astype(np.float32)
            cache[key] = (arr[..., 2::-1], arr[..., 3:] / 255.0)  # RGB->BGR, Alpha
        rgb, a = cache[key]
        img = frame_9x16(frame).astype(np.float32)
        img = (rgb * a + img * (1 - a)).astype(np.uint8)
        writer.write(img)
        if i in (int(0.7 * fps), int(4.5 * fps)):
            stills.append(img)
        i += 1
    writer.release()
    cap.release()

    sting = OUTPUT_DIR / "_sting_platzhalter.wav"
    write_sting(sting)
    inputs = ["-i", str(silent), "-i", str(src), "-i", str(sting)]
    mix = "[1:a]volume=1.0[orig];[2:a]adelay=0|0,volume=0.9[st];[orig][st]amix=inputs=2:duration=first:normalize=0[a]"
    if MUSIC_PATH:
        inputs += ["-i", str(MUSIC_PATH)]
        mix = (f"[1:a]volume=1.0[orig];[2:a]volume=0.9[st];"
               f"[3:a]volume={MUSIC_GAIN_DB}dB[mu];"
               f"[orig][st][mu]amix=inputs=3:duration=first:normalize=0[a]")
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", *inputs, "-filter_complex", mix,
         "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
         "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )
    silent.unlink()
    sting.unlink()
    print(f"  {out}")
    return stills


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    clip = sys.argv[1]
    if clip not in EPISODES:
        print(f"FEHLER: Für Clip '{clip}' ist keine Folge hinterlegt (EPISODES).")
        sys.exit(1)
    ep = EPISODES[clip]
    if not ep["source"].exists():
        print(f"FEHLER: Quelle fehlt: {ep['source']} (erst Agent 4)")
        sys.exit(1)
    names = sys.argv[2:] or list(STYLES)
    started = time.monotonic()
    print(f"Short-Vorlage für {clip} (Folge {ep['folge']}), Varianten: {', '.join(names)}")
    sheet = []
    for name in names:
        stills = render(clip, name, ep)
        thumbs = [cv2.resize(s, (360, 640)) for s in stills]
        col = np.hstack(thumbs)
        cv2.putText(col, name, (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6)
        cv2.putText(col, name, (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 220, 255), 2)
        sheet.append(col)
    gap = np.full((640, 12, 3), 30, np.uint8)
    parts = []
    for c in sheet:
        parts += [c, gap]
    compare = OUTPUT_DIR / f"{clip}_short_varianten.png"
    cv2.imwrite(str(compare), np.hstack(parts[:-1]))
    print(f"  {compare}")
    print(f"Fertig nach {time.monotonic() - started:.0f} s")


if __name__ == "__main__":
    main()
