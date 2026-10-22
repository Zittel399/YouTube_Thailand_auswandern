# Parallelwelten – Automatisierung: Tages-Agent, Telegram, Dashboard

Stand: 22.10.2026 · Status: **KONZEPT** (noch nichts davon läuft)

## Zielbild in einem Satz

Chris lädt Rohmaterial auf Drive → ein Agent prüft es **jeden Tag**, gleicht es mit Story-Bibel und
Trends ab → schickt **3–5 Vorschläge per Telegram** → was Chris freigibt, wird gerendert, eingeplant
und gepostet → ein **Dashboard** zeigt Zeitlinie, Puffer, Storyline und Reichweite.

```
Drive 40_Medien/01_raw ──► Tages-Agent (täglich 06:00) ──► Telegram: 3–5 Vorschläge
                                │                                │ ✅ / ❌ / ✏️
                                ▼                                ▼
                     Trends + Story-Bibel            Freigabe → Render → 02_review
                                                                 │
Dashboard ◄── data/*.json ◄── Analytics (täglich) ◄── Posting (YouTube/Instagram, alle 2 Tage)
```

## 1. Tages-Agent (läuft ohne Laptop)

Läuft als **GitHub Action mit Zeitplan** (kostenlos, Laptop muss nicht an sein). Alle Bezahl-Dienste
(fal, Replicate, ElevenLabs, Claude) sind Cloud-APIs, ffmpeg läuft im Runner.

| Schritt | Was | Kosten |
|---|---|---|
| 1. Neues Material | Drive `01_raw` auf neue Dateien prüfen (Service-Account mit Lesezugriff nur auf `40_Medien`) | 0 |
| 2. Vorauswahl (Agent 0) | in 8–15-s-Kandidaten schneiden; Wackeln, Schärfe, Kinder im Bild, Lacher/laute Momente; Transkript (Whisper) | Cent |
| 3. Trends | YouTube: beliebte Shorts DE (Data API), eigene Top-Clips (Analytics), Google Trends zu Auswandern/Thailand | 0 |
| 4. Vorschläge | Claude gleicht Material × Story-Bibel × Trends ab → **3–5 Vorschläge**: Folge N oder Zwischenfolge, Titel, Voiceover, Format (R/M/A), Kosten, Begründung („passt zu Trend X“) | ~0,05 $ |
| 5. Vorschau | billige Vorschau (Standbild + Text), **kein** teures Anime vor der Freigabe | 0 |
| 6. Telegram | Vorschläge mit Buttons ✅ Freigeben · ❌ Verwerfen · ✏️ Text ändern | 0 |

**Leitplanken im Agenten fest eingebaut** (aus `STORYLINE.md`): keine Kindernamen, Kinder nur als
Anime, kein Arbeitgebername, Steuer nur als eigene Erfahrung, keine erkennbaren Fremden als Hauptmotiv,
keine Folge, die der echten Zeitachse vorgreift (Visum erst ab 17.01.2027).

## 2. Nach der Freigabe

1. Status → `freigegeben`, nächster freier Slot im Kalender (jeden 2. Tag)
2. Rendern: Voiceover (ElevenLabs) → ggf. Look B (Pipeline) → Short-Vorlage Manga → `02_review`
3. Telegram: fertiges Video zur **Endabnahme** → ✅ → `03_final` + eingeplant
4. Posting zum Slot: YouTube (Data API, geplante Veröffentlichung), Instagram (Graph API, braucht
   Creator-/Business-Konto mit verknüpfter Facebook-Seite). Alternative: Postiz/Blotato.

**Puffer-Wächter:** Telegram-Alarm, wenn weniger als **4 Wochen** fertige Folgen in der Queue sind.

## 3. Dashboard

Prototyp: `dashboard/index.html` (öffnet sich auch lokal per Doppelklick). Daten kommen aus
`dashboard/data.js`; später schreibt der Agent sie täglich neu.

| Bereich | Inhalt |
|---|---|
| Kennzahlen | Puffer in Tagen, nächster Post, Follower gesamt, Veränderung 7 Tage |
| Zeitlinie | was wann gepostet wurde / wird, in Reihenfolge, mit Status |
| Storyline | Staffeln → Kapitel → Folgen, **anklickbar**: Voiceover, Format, abgelegt unter (Drive-Dateiname), Status |
| Reichweite | Follower je Plattform über Zeit, Aufrufe je Folge, was gut/schlecht ankommt |
| Vorschläge | offene Vorschläge des Tages-Agenten |

### Hosting – Empfehlung

| Option | Bewertung |
|---|---|
| **Hostinger** (vorhanden?) | **empfohlen**: statische Seite, GitHub Action lädt sie täglich hoch, **Passwortschutz** per `.htaccess` |
| Google Workspace | Google Sites kann keine eigene Seite mit Skript einbinden; ginge nur über Apps Script – umständlicher |
| GitHub Pages | nur sinnvoll mit privatem Repo + bezahltem Plan, sonst öffentlich |

Das Dashboard enthält Familien-Infos und Zahlen → **immer mit Passwort**.

## 4. Was Chris einrichten muss (einmalig)

| # | Was | Wofür |
|---|---|---|
| 1 | **Repo auf privat stellen** | Story-Bibel, Zeitplan und Agent-Daten sind sonst öffentlich |
| 2 | Telegram-Bot bei @BotFather anlegen → Token + eigene Chat-ID | Vorschläge, Freigaben, Alarme |
| 3 | Google-Cloud-Service-Account, Ordner `40_Medien` für ihn freigeben | Agent liest Drive |
| 4 | YouTube-Kanal „Parallelwelten“ + API-Zugang (OAuth) | Upload, Statistiken |
| 5 | Instagram als Creator-/Business-Konto | Posting, Statistiken |
| 6 | ElevenLabs-Konto + Stimmprobe | Voiceover |
| 7 | Hostinger-Zugang (FTP) | Dashboard hosten |
| 8 | Alle Schlüssel als **GitHub Secrets** (nie in Chat oder Repo) | Agent |

## 5. Laufende Kosten (Schätzung)

| Posten | pro Monat |
|---|---|
| GitHub Actions, Telegram, YouTube/Instagram-APIs, Drive | 0 € |
| Claude für Vorschläge (täglich) | ~2 € |
| ElevenLabs | ~5 € |
| Videos (15 Folgen, Mix R/M/A) | ~5–10 € |
| Hostinger | vorhandenes Paket |
| **Summe** | **~12–17 €** (Budget ~50 €) |

## 6. Reihenfolge der Umsetzung

1. Dashboard-Prototyp mit Beispieldaten ✔ (dieser Stand)
2. Datenmodell `data/episodes.json` aus der Story-Bibel befüllen → Dashboard zeigt echte Folgen
3. Telegram-Bot + Freigabe-Logik
4. Tages-Agent: Drive lesen + Vorauswahl + Vorschläge
5. Render-Kette nach Freigabe (Voiceover + Manga-Vorlage)
6. Posting + Analytics → Dashboard mit echten Zahlen
