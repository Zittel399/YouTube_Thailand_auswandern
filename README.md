# YouTube_Thailand_auswandern (Parallelwelten)

Automatisierte Anime-Pipeline: echtes Rohmaterial (Handy/Brille) →
Person wird durch eine Anime-Figur ersetzt → fertiger Short-Form-Clip
für Instagram/YouTube.

## Architektur (4 Agenten)
1. **Isolation & Tracking** (SAM2, via fal.ai) — Person im Video maskieren/tracken
2. **Background Inpainting** (ProPainter/E2FGVI) — Hintergrund ohne Person rekonstruieren
3. **Asset-Generierung** (Wan-2.2 Animate Move) — Anime-Figur passend zur Bewegung generieren
4. **Compositing & Blending** — Figur + Hintergrund zusammenfügen, glätten, farblich angleichen

## Wichtig: Wo läuft was?

Die eigentlichen GPU-Calls (fal.ai/Replicate) laufen **lokal**, nicht in
der Cloud-Sandbox — dort ist der Netzwerkzugriff auf Drittanbieter-APIs
aktuell durch einen bekannten Anthropic-Bug blockiert
([#93512](https://github.com/anthropics/claude-code/issues/93512)).
Code, Projektstruktur und Git bleiben in der Cloud-Sandbox/im Chat.

## Lokales Setup (VS Code)

1. Repo klonen (falls noch nicht geschehen):
   ```
   git clone https://github.com/zittel399/youtube_thailand_auswandern.git
   cd youtube_thailand_auswandern
   ```
2. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
3. `.env` im Projekt-Root anlegen (siehe `.env.example`), mit deinem
   echten `FAL_KEY` und `REPLICATE_API_TOKEN` — **niemals committen**,
   ist in `.gitignore` ausgeschlossen.
4. Testvideo ablegen: `input/test_clips/test_15s.mp4` (siehe Chat —
   wird dir als Datei geschickt).
5. Agent 1 starten:
   ```
   python agents/01_isolate.py
   ```
   Das Skript zeigt dir zuerst den ersten Frame zur Kontrolle des
   SAM2-Prompt-Punkts, bevor es den kostenpflichtigen fal.ai-Call
   auslöst.

## Ordnerstruktur
- `input/` — Rohmaterial (gitignored, nur lokal/Cloud)
- `intermediate/` — Zwischenergebnisse je Agent (gitignored)
- `output/` — fertige Clips (gitignored)
- `agents/` — Pipeline-Code je Stufe

## Kosten
fal.ai/Replicate rechnen pay-per-use ab. Aktuellen Stand im jeweiligen
Dashboard prüfen — kein automatischer Kosten-Tracker in diesem Repo.
