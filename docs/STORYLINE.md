# Parallelwelten – Storyline & Format-Festlegungen

Stand: 22.10.2026 (Folgenplan: `docs/STORY_BIBEL.md`). Zusammengefasst aus den Chats „AI-Video-Kanal mit N8N automatisieren“
(17.–21.09.2026) und „Smartglasses mit Sehstärke für Thailand“ (bis 12.10.2026).
Die dort erstellten Dateien (`format-guide.md`, `ideas.md`, `anime-hybrid.md`, `style-bible.md`)
wurden nie in dieses Repo committet; diese Datei ersetzt sie als Referenz.

Legende: **FEST** = entschieden · **VORSCHLAG** = von Claude empfohlen, von Chris nicht bestätigt · **OFFEN**

---

## 1. Kanal & Geschichte

| Punkt | Stand |
|---|---|
| Name | **FEST:** „Parallelwelten“ (ersetzt den Arbeitstitel YouTube_Thailand_auswandern) |
| Plattformen | **FEST:** YouTube Shorts + Instagram. TikTok nur manuell (API-Audit fehlt) |
| Sprache | **FEST:** Deutsch, Zielgruppe Auswander-Interessierte |
| Erzählbogen | Familie (Vater, Mutter, zwei Kinder, Opa) wandert von Wolfsburg nach Krabi/Ao Nang aus (~Jan/Feb 2027), evtl. später weiter (Australien). Deshalb Name/Format länderneutral |
| Jetzt-Phase | Vorbereitung in Deutschland (Ausmisten, Behörden, Jobausstieg), ab 2027 Thailand-Alltag |
| Nordstern | buchartige Story mit Kapiteln → irgendwann echte Anime-Kurzserie. Manga-Seiten sind das erste „Kapitel-Format“ |

## 2. Kern-Idee „Parallelwelten“ (Hybrid, ein Kanal) – FEST

| Echt gefilmt | Anime |
|---|---|
| Chris selbst | **alles mit den Kindern** (Kinderschutz) |
| Zahlen / Säule B | Story- und Kapitel-Momente (Höhen, Tiefen, Wendepunkte) |
| POV-Alltag mit der Brille | emotionale Beats, schwer filmbare Szenen, Manga-Seiten aus Brillen-Fotos |

- Hauptlook der Pipeline: **Look B** – Kinder als Anime-Figuren in der echten Welt (siehe `PIPELINE.md`).
- Authentizitäts-Anker in beiden Welten: Chris' (geklonte) Stimme und echte Meinung.
- Formate nach Kosten: 1) Real-POV-Short (billig) · 2) Anime-Standbild/Manga-Seite (günstig) · 3) bewegtes Anime (teuer, nur Highlights).

## 3. Erzählweise / Dramaturgie

- **FEST – Kern-Mechanik:** Erwartung → harter Schnitt → Realität. Die Lücke ist der Gag
  (Referenzbeispiel: „Thai-Krankenhaus fühlt sich an wie ein Hotel“).
- **FEST – Zwei Säulen:**
  - **A Witzig/Kontrast** – Vorlagen: A1 „Alle denken … Realität …“, A2 „POV: …“, A3 „Niemand redet über …“, A4 „Ich dachte X – dann kam Y“, A5 „Deutschland vs. Thailand: [Alltagsding]“
  - **B Informativ** (Kosten, Steuer, Bürokratie DE ↔ TH) – B1 „3 Dinge, die keiner dir über … sagt“, B2 „Was kostet X in DE vs. TH?“, B3 How-to, B4 „Der teuerste Fehler …“, B5 Kosten-Aufschlüsselung
- **FEST – Länge:** 6–15 s pro Clip, 9:16.
- **FEST – Regel:** Das Format ist das Template, die KI füllt es nur aus, sie erfindet es nicht.
- Format-Vorbilder (fester Opener, gleiche Struktur jedes Mal): Dr. Michael Stoermer, Held der Steine.

## 4. Opener / Signature

> **Update 12.10.2026 (Chris):** Serien-Storytelling statt Begrüßungs-Opener. Jeder ~10-s-Clip ist eine
> **Folge** einer fortlaufenden Geschichte („wer alles sehen will, schaut Folge 1 bis 1000“). Kennung im Bild:
> **„PARALLELWELTEN · Folge N“**. Der Einstieg „Moin, Leute — wusstet ihr schon …?“ ist damit **verworfen**;
> die genaue Hook-Formel ist **OFFEN** (siehe Vorschläge im Chat, z. B. „Folge N: [Was passiert]“ als erster Satz).
> Story-Start: die Auswanderung beginnt mit **Ausweisen und DTV-Visum** (was man wissen muss).

- **Opener (von Chris favorisiert, final noch nicht ausdrücklich abgenickt):**
  „**Moin, Leute —**“ + zweiter Beat je Säule
  - Säule A: „**Wusstet ihr schon …?**“
  - Säule B: „**Habt ihr das mal durchgerechnet …?**“
  - Beispiel: „Moin, Leute — habt ihr schon mal durchgerechnet, was eine Wohnung in Thailand wirklich kostet?“
- Kein Name im Short-Opener (Name lebt in Bio/Trailer).
- **VORSCHLAG Persona (Bio/Trailer):** „Der Daten-Auswanderer“ – „Ich bin Chris, Datenanalyst – ich hab das Auswandern durchgerechnet. Hier sind die echten Zahlen.“ (Alternativen: „Der ehrliche Auswanderer“, „Tag X“). **OFFEN.**
- **FEST – Short-Signature in jedem Clip:** immer gleicher Untertitel-Stil · immer dieselbe Stimme · immer derselbe kurze Sound-Sting · optional 1-Sekunden-Tag/Logo.

## 5. Captions / Untertitel

> **Update 22.10.2026 (Chris) – FEST:** Manga-Stil (Textbox ohne Zipfel, Variante `manga` in
> `agents/05_short_template.py`). Captions müssen immer eindeutig sein: ein Satz pro Box,
> Text = exakt das ElevenLabs-Voiceover.


Festgelegt ist nur: **ein einziger, gleichbleibender Untertitel-Stil** als Wiedererkennungsmerkmal.
Schrift, Farbe, Position, Wort-für-Wort vs. Zeilen wurden nicht entschieden.
Vorschlag für die Vorlage: Bild-Look ist warm/malerisch (Abschnitt 7) → Caption so wählen, dass sie
zu beidem (echt + Anime) passt; als Variable in der Vorlage halten, bis Chris entscheidet.
Caption-Text + Hashtags schreibt ein LLM-Call (mit Trending-Hashtag-Lookup).

## 6. Stimme & Musik

- **Stimme – FEST (Richtung):** Chris' eigene Stimme, geklont mit **ElevenLabs** (DE, ~5 €/Monat).
  Konto/Stimmprobe noch nicht angelegt. Backup: Minimax (kostenlos).
  Ablauf: LLM schreibt Voiceover-Script → ElevenLabs → über den Clip.
- **Musik – OFFEN (nur Regeln fest):** lizenzierte Library, Auswahl als einfache Funktion (kein Agent);
  Lizenz immer separat prüfen. Eine Musikrichtung wurde nie festgelegt.
- **Sound-Sting – OFFEN:** fester kurzer Sting ist gesetzt, der konkrete Sound noch nicht.
  (Früher genannte Idee: „Willkommen back to Krabi“-Sting.)

## 7. Visueller Stil (Anime)

- **FEST:** warm, malerisch, Ghibli-nah (Chris' zwei Referenzbilder: Kind im Feld vor der Wolfsburger
  Industrie-Silhouette; Kind isst Ramen vor einem Wolfsburger Bus). Kontrast DE ↔ Asien steckt im Bild.
- Character Consistency ist Pflicht: jede Figur sieht in jedem Clip gleich aus
  → feste Referenzbilder je Figur (`input/style/`, `kaia_ref_1.png`, `luan_ref_1.png`).
- Gen-1-Brille: Motiv mittig halten (9:16-Zuschnitt), kurze Takes.

## 8. Leitplanken – FEST

- **Kinderschutz:** echte Fotos/Videos der Kinder nie posten, nur Anime-Version.
  **Keine echten Namen öffentlich** (Pseudonyme oder keine Namen), keine Schule/Adresse.
  → Die internen Namen in `PIPELINE.md` dürfen nicht in Captions, Voiceover oder Titeln landen.
- Arbeitgeber nie namentlich nennen. Erlaubt: „einer der größten Autobauer der Welt“ (FEST 22.10.2026).
  Ausstieg per Aufhebungsvertrag.
- Darstellung (FEST 22.10.2026): Erwachsene (Chris, Partnerin, Opa) **echt**, eigene Kinder **Anime**.
  Fremde Kinder später ebenfalls Anime, bis dahin nicht Hauptmotiv.
- Steuer/Recht nur als eigene Erfahrung/Recherche framen, nicht als Beratung.
- Nur eigenes Material, kein Repost fremder Videos.
- Rohmaterial archivieren, nicht löschen.
- Budget: gesamte Umgebung inkl. Claude unter ~50 €/Monat; bewegtes Anime sparsam.

## 9. Veröffentlichung (Zielbild)

Brille → Drive `01_raw` → Vorschnitt → Kurator (Gemini) → Script + Stimme → Caption/Hashtags/Musik →
`02_review` → Freigabe per Telegram → Kalender-Queue (jeden zweiten Tag) → Postiz/Blotato →
YouTube + Instagram. Puffer-Wächter: Telegram-Alarm bei < 4 Wochen Vorrat.

## 10. Erste Clip-Ideen (jetzt in Deutschland drehbar)

- A1 „Alle denken, Auswandern = Strand. Realität: Nummer ziehen im Bürgeramt.“
- A3 „Niemand sagt dir, dass Auswandern zu 80 % aus Papierkram besteht.“
- A4 „Ich dachte, Wohnung auflösen dauert ein Wochenende. Wir sind bei Woche drei.“
- B2 „Was kostet eine 3-Zimmer-Wohnung: Wolfsburg vs. Ao Nang?“
- Grauer Deutschland-Winter → harter Cut → der Grund, warum wir gehen.

## Offene Entscheidungen (für Chris)

1. Persona-Zeile für Bio/Trailer (Vorschlag: Daten-Auswanderer)
2. Hook-Formel für den Folgen-Einstieg (Opener „Moin, Leute“ verworfen, s. Abschnitt 4)
3. ~~Untertitel-Stil~~ → 22.10.2026: Manga-Stil
4. Musikrichtung und Sound-Sting (in der Vorlage: Platzhalter-Sting, leerer Musik-Slot)
5. ~~Kindernamen~~ → 22.10.2026: **keine Namen öffentlich**, nur „mein Sohn“ / „meine Tochter“;
   Partnerin = „meine Frau“. Leitplanke 8 bleibt.
