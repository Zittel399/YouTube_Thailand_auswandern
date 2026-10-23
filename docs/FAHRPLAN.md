# Parallelwelten – Fahrplan bis zum Start am 01.12.2026

Stand: 23.10.2026. **Die eine Übersicht**: was wann fertig sein muss und wer es macht.
Abhaken, wenn erledigt. Details stehen in den verlinkten Dateien.

**Ziel am 01.12.:** Kanal steht, **14 Folgen fertig** (= 4 Wochen Puffer), Dashboard online,
Freigabe per Telegram läuft. Ab dann alle 2 Tage eine Folge.

## Woche 1 · 23.–31.10. – Fundament

| ✓ | Aufgabe | Wer |
|---|---|---|
| ☐ | GitHub-Repo auf **privat** stellen | Chris |
| ☐ | YouTube-Kanal **„Parallelwelten“** anlegen, Handle sichern (`@parallelwelten…`) | Chris |
| ☐ | Instagram-Konto anlegen, auf **Creator-Konto** umstellen, gleicher Handle | Chris |
| ☐ | **ElevenLabs**-Konto (Starter, ~5 €) + **Stimmprobe** 1–3 min, ruhiger Raum | Chris |
| ☐ | **Telegram-Bot** bei @BotFather anlegen (`/newbot`) | Chris |
| ☐ | **Hostinger**: Subdomain für das Dashboard (z. B. `studio.<domain>`) + FTP-Zugang | Chris |
| ☐ | Alle Schlüssel als **GitHub Secrets** eintragen (Anleitung kommt von Claude) | Chris |
| ☐ | Kanal-Auftritt: Profilbild + Banner (Anime-Familie), Bio, Persona-Zeile | Claude entwirft, Chris wählt |

## Woche 2 · 01.–09.11. – Produktion von A bis Z (eine Folge komplett)

| ✓ | Aufgabe | Wer |
|---|---|---|
| ☐ | Clips für **Folge 1–5** auf Drive `40_Medien/01_raw` (`F01_….mp4` usw.) | Chris |
| ☐ | **Voiceover-Agent**: Text aus Story-Bibel → ElevenLabs → Audio | Claude |
| ☐ | Short-Vorlage (Manga-Captions) + Voiceover + Musik → **Folge 1 fertig** | Claude |
| ☐ | Folge 1 abnehmen: Stil, Stimme, Länge passen? | Chris |
| ☐ | **Dashboard online** auf Hostinger (Passwortschutz) | Claude |

## Woche 3 · 10.–16.11. – Automatik

| ✓ | Aufgabe | Wer |
|---|---|---|
| ☐ | **Telegram-Freigabe**: fertige Folge kommt aufs Handy → ✅ / ❌ / ✏️ | Claude |
| ☐ | **Tages-Agent** (GitHub Action): Drive prüfen, Vorauswahl, 3–5 Vorschläge | Claude |
| ☐ | Clips für **Folge 6–14** hochladen | Chris |

## Woche 4 · 17.–30.11. – Puffer & Marketing

| ✓ | Aufgabe | Wer |
|---|---|---|
| ☐ | **Folge 1–14 fertig** und freigegeben (bewegtes Anime nur Folge 5 + 20) | Claude + Chris |
| ☐ | **Trailer** (30–45 s): „Eine Familie verlässt Deutschland. Folge 1 am 1. Dezember.“ | Claude |
| ☐ | **3 Teaser-Posts** ab ~24.11. (Countdown), Kanal-Trailer auf YouTube | Claude + Chris |
| ☐ | **Posting** einrichten: YouTube geplant veröffentlichen, Instagram (Graph API oder Postiz) | Claude |
| ☐ | Generalprobe: eine Folge läuft komplett automatisch bis „eingeplant“ | Claude |

## Ab 01.12. – Laufender Betrieb

- Alle 2 Tage eine Folge (Zeitplan im Dashboard)
- Täglich: Vorschläge per Telegram, Chris gibt frei
- Analytics täglich ins Dashboard (Follower, Aufrufe, was gut/schlecht ankommt)
- Puffer-Alarm unter 4 Wochen
- 17.01.2027: Folge 11 „Das Visum ist da“ · Feb/März: Abschied & Abflug

## Wo was steht

| Datei | Inhalt |
|---|---|
| `docs/FAHRPLAN.md` | **diese Übersicht** |
| `docs/STORY_BIBEL.md` | Warum, Figuren, Staffeln, Folgenplan mit Voiceover |
| `docs/STORYLINE.md` | Format, Stil, Leitplanken |
| `docs/AUTOMATION.md` | Tages-Agent, Telegram, Dashboard, Kosten |
| `PIPELINE.md` | Video-Technik (Anime-Look B), Einstellungen, Kosten pro Clip |
| `dashboard/index.html` | Dashboard (lokal per Doppelklick öffnen) |
