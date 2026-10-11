# Parallelwelten-Pipeline: Vorgehen, Einstellungen, Kosten

Stand: 11.10.2026, getestet mit `test_8s` (9,5 s, 368×496, Wohnzimmer, Kaia + Luan, Skateboard).

Ziel: 5–15-s-Shorts, in denen Kaia und Luan als Anime-Figuren erscheinen. Zwei Looks:

| Look | Beschreibung | Ergebnis test_8s |
|---|---|---|
| **A – komplett animiert** | ganze Szene im Anime-Stil | `output/test_8s_anime_komplett.mp4` |
| **B – Parallelwelten** (Hauptlook) | nur die Kinder Anime, Welt bleibt echt | `output/test_8s_parallelwelten.mp4` |

Alle Medien (`input/`, `intermediate/`, `output/`) sind gitignored und liegen nur lokal.

## Ablauf für einen neuen Clip

Voraussetzungen: `.venv` mit `requirements.txt`, ffmpeg, `.env` mit `FAL_KEY` und `REPLICATE_API_TOKEN`
(Guthaben auf **beiden** Konten). Alle Skripte fragen vor jedem bezahlten Call nach (`j/N`) und
protokollieren Dauer und geschätzte Kosten in `logs/runs.jsonl`.

| # | Schritt | Befehl | Dienst | Look |
|---|---|---|---|---|
| 0 | Clip ablegen | `input/test_clips/<clip>.mp4`, 3–10 s | – | A, B |
| 0 | Figuren-Referenzen (einmalig je Figur) | `python agents/03a_character_refs.py` | fal: nano-banana/edit | A, B |
| 1 | Echte Kinder (+ Spielzeug) maskieren | `python agents/01_isolate.py <clip>` | fal: SAM2 video | B |
| 2 | Kinder → Anime (beide in einem Call) | `python agents/03d_kling_edit.py <clip>` | fal: Kling O1 Edit | A, B |
| 3 | Anime-Kinder maskieren | `python agents/01_isolate.py <clip>_kling` | fal: SAM2 video | B |
| 4 | Leere Bühne (echte Kinder entfernen) | `python agents/02_clean_plate.py <clip>` | Replicate: ProPainter | B |
| 5 | Zusammensetzen | `python agents/04_composite.py <clip>` | lokal | B |

Pro neuem Clip im Code eintragen:
- `agents/01_isolate.py` → `TARGETS_BY_CLIP["<clip>"]` und `["<clip>_kling"]` (Prompt-Punkte), bei
  `<clip>_kling` zusätzlich `SOURCES`
- `agents/03d_kling_edit.py` → `PROMPTS_BY_CLIP["<clip>"]` (wer ist wer im Video)

### Einstellungen, die sich bewährt haben

**Agent 1 – SAM2 (`fal-ai/sam2/video`)**
- Quellvideo vorher auf **30 fps** reduzieren (Handyclips: 120 fps oder variable Bildrate)
- Pro Person ein eigener Call (das Modell hat keine Objekt-IDs; alle Punkte eines Calls = eine Maske)
- Je Person **2 Punkte** (Kopf + Oberkörper), Label 1
- Schwenkt die Kamera weg und zurück: zusätzliche Punkte in den Frames, in denen die Person wieder auftaucht
- Gegenstände, mit denen gespielt wird (Skateboard), als **eigenes Objekt** maskieren und
  **Ausschlusspunkte (Label 0)** auf das Kind setzen, das darauf sitzt. Sonst nimmt SAM2 das Kind mit.
- Einzelne Objekte neu maskieren: `python agents/01_isolate.py <clip> skateboard`

**Agent 3a – Figuren-Referenzen (`fal-ai/nano-banana/edit`)**
- Eingabe: Anime-Stilbild je Kind (`input/style/kaia_anime.jpeg`, `luan_anime.jpeg`)
- Prompt: Ganzkörper, frontal, neutrale Pose, hellgrauer Hintergrund, Stil und Outfit exakt beibehalten,
  dazu eine kurze Beschreibung der Figur
- 2 Varianten je Figur, 9:16. Gewählt: `kaia_ref_1.png`, `luan_ref_1.png`

**Agent 3d – Kling O1 Edit (`fal-ai/kling-video/o1/video-to-video/edit`)**
- Clip auf **≥ 720 px** (kürzere Seite) hochskalieren; erlaubt sind 3–10,05 s und 24–60 fps
- Referenzen als `image_urls`, im Prompt über `@Image1` (Kaia) und `@Image2` (Luan)
- Prompt beschreibt, **wer wer im Video ist** (Kleidung, Position), und verlangt exakt gleiche
  Bewegungen und Interaktionen. Der Wunsch „Hintergrund fotorealistisch lassen“ wird **ignoriert**:
  Kling stilisiert die ganze Szene. Deshalb ist für Look B das Compositing nötig.
- Ausgabe: 24 fps, höhere Auflösung (1240×1668), ca. 0,15 s kürzer als das Original

**Agent 2 – Leere Bühne (`jd7h/propainter` auf Replicate)**
- Maske = alle echten Kinder, um 6 px vergrößert, **ohne** die Gegenstands-Masken
- `save_fps` = Bildrate des Clips (Standard wäre 24!), `mask_dilation` 4
- `fp16` = true: Replicate-Instanzen laufen teils noch im fp16-Modus eines anderen Auftrags,
  mit fp32 stürzt das Modell dann ab („FloatTensor vs HalfTensor“)
- Video und Maske über den fal-Storage hochladen und als URL übergeben. ProPainter prüft die
  Dateiendung `.mp4`, und der Replicate-Client verliert beim eigenen Upload den Dateinamen.

**Agent 4 – Compositing (lokal)**
- Ausgabe 720 px breit, Anime-Kinder mit 3 px weichem Rand
- Im Bereich der echten Kinder (+10 px) kommt der Hintergrund aus der leeren Bühne, sonst aus dem echten Video
- Gegenstände (Skateboard) immer pixelgenau aus dem echten Video
- Ton aus dem Original, auf die Länge der Kling-Version gekürzt

### Was nicht funktioniert hat (nicht wiederholen)

| Ansatz | Problem |
|---|---|
| Wan 2.2 Animate **Replace** | sucht sich die Person selbst aus (hat Luan statt Kaia genommen), kein Anime-Look |
| Wan 2.2 Animate **Move** (Solo-Video je Kind) | Anime-Look ok, aber Drift/Glühen nach ca. 5 s, erfindet Objekte (Skateboard → Einkaufswagen) |
| Lokales OpenCV-Auffüllen statt ProPainter | sichtbarer Schleier (Jacke des echten Kindes) |
| Skateboard über „dunkle Pixel“ statt eigener Maske | verschmierte Brettkanten |
| Testclip mit schnellen Kameraschwenks | Kinder sind die meiste Zeit nicht im Bild, SAM2 verliert sie |

## Kosten und Laufzeit pro Video

Preise laut Anbieter, Stand Oktober 2026. Für SAM2 (fal) und ProPainter (Replicate) wird nach
GPU-Zeit abgerechnet, einen festen Preis veröffentlichen die Anbieter nicht. Die echten Beträge
stehen in den Dashboards (fal: Usage, Replicate: Billing).

**Ein Clip von ca. 10 s:**

| Schritt | Kosten | Dauer |
|---|---|---|
| SAM2 echte Kinder (2 Calls) + Skateboard (1 Call) | wenige Cent | ca. 0,5–1 min |
| Kling O1 Edit (0,168 $/s × 9,5 s) | **ca. 1,60 $** | ca. 6–7 min |
| SAM2 Anime-Kinder (2 Calls) | wenige Cent | ca. 1–1,5 min |
| ProPainter | ca. 0,03 $ | ca. 1 min |
| Compositing | 0 $ | < 1 min |
| **Look B gesamt** | **ca. 1,70 $** (≈ 0,17 $/s) | **ca. 10–12 min** |
| **Look A gesamt** (nur Kling) | **ca. 1,60 $** | ca. 7 min |

- **15-s-Short:** Kling erlaubt max. 10,05 s pro Call → 2 Abschnitte, **ca. 2,60 $** (Look B)
- **Einmalig je neuer Figur:** Referenzen ca. 0,08 $ (2 Varianten)
- **Ausgaben in der Testphase bisher:** ca. 3,60 $ laut Protokoll, plus SAM2/ProPainter (Cent-Beträge).
  Details: `logs/runs.jsonl`

Kling macht über 90 % der Kosten aus. Wer sparen will, muss dort ansetzen (kürzere Clips,
günstigeres Edit-Modell testen).

## Nächster Schritt: echte Videos mit der Meta Ray-Ban

Die Testclips waren Handyvideos mit niedriger Auflösung. Mit der Ray-Ban zu klären bzw. anzupassen:
- **Auflösung:** Die Brille filmt deutlich höher aufgelöst. Kling nimmt max. 2160 px. SAM2 und
  ProPainter rechnen nach GPU-Zeit, also kostet hohe Auflösung dort mehr → für Masken und leere
  Bühne verkleinert arbeiten, Kling und Compositing in hoher Auflösung
- **Ich-Perspektive mit Kopfbewegung:** mehr Kamerabewegung als beim Handy → eventuell mehr
  Prompt-Punkte (siehe test_15s) und Clips mit ruhigeren Passagen wählen
- **Länge:** 5–10-s-Abschnitte schneiden (Kling-Limit), für 15 s zwei Abschnitte
- Danach: Short-Format 1080×1920, Musik, Hook, Untertitel
