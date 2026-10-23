# Parallelwelten – Story-Bibel

Stand: 22.10.2026 (2. Fassung). Grundlage: Chris' Input vom 22.10.2026 + `docs/STORYLINE.md`.
Status: **ENTWURF** – Folgenplan ist ein Vorschlag, Reihenfolge und Texte darf Chris frei ändern.

---

## 1. Worum es geht (die eine Frage der Serie)

> **Kann eine ganz normale deutsche Familie alles hinter sich lassen – und es besser machen?**

Jede Folge beantwortet ein kleines Stück davon. Wer alles sehen will, schaut Folge 1 bis 1000.

## 2. Das Warum (FEST, aus Chris' Worten)

| # | Grund | Wie er in der Serie vorkommt |
|---|---|---|
| 1 | **Bildung** – das deutsche Schulsystem gefällt uns nicht mehr; in Thailand können wir unserem Sohn eine gute Bildung geben | **Hauptmotiv, roter Faden.** Taucht in jeder Staffel wieder auf (Entscheidung → Schulsuche → erster Schultag in Krabi) |
| 2 | **Systembrüchigkeit** in Deutschland | Kontrast-Gags (Säule A): Bürokratie, Wartezeiten, Dinge, die nicht mehr funktionieren – nie wütend, immer mit Augenzwinkern |
| 3 | **Veränderung, etwas Neues erleben** als Familie | Emotionale Beats, Anime-Momente |
| 4 | **Das Unbekannte, Herausforderungen annehmen** | Jede Hürde (Visum, Steuer, Kündigung) ist eine „Prüfung“ – Abenteuer-Rahmen statt Jammern |

**Leitsatz für Voiceover:** Wir laufen nicht weg, wir laufen auf etwas zu.

## 3. Figuren & Darstellung (FEST)

| Figur | Darstellung | Hinweise |
|---|---|---|
| **Chris** (Erzähler) | **echt** | Stimme = ElevenLabs-Klon, erzählt jede Folge in Ich-Form |
| **Partnerin** | **echt** | Im Voiceover immer „meine Frau“ (FEST 22.10.) |
| **Opa** | **echt** | |
| **Sohn** | **Anime** | Öffentlich nur „mein Sohn“. Zentrale Figur des Bildungs-Fadens |
| **Tochter** | **Anime** | Öffentlich nur „meine Tochter“ / „die Kleine“. Sorgt für die lustigen Momente |
| Fremde Kinder | vorerst: nicht Hauptmotiv / unkenntlich | später ebenfalls Anime (eigener Schritt, noch nicht gebaut) |
| Fremde Erwachsene | nicht Hauptmotiv / unkenntlich | Recht am eigenen Bild |

**Keine Kindernamen öffentlich (FEST 22.10.)** – nicht in Voiceover, Captions, Titeln, Hashtags.
Die internen Namen in `PIPELINE.md`/Code (Referenzbilder, Masken) bleiben intern.

Arbeitgeber: **nie namentlich.** Formulierung: „einer der größten Autobauer der Welt“ / „der Konzern“.

## 4. Stil jeder Folge (FEST)

- **~10 s, 9:16**, Kennung **„PARALLELWELTEN · Folge N“** oben.
- **Captions im Manga-Stil** (Textbox ohne Zipfel, `agents/05_short_template.py` → Variante `manga`),
  immer eindeutig: **ein Satz pro Box**, max. 2 Zeilen, Text = exakt das gesprochene Voiceover.
- **Ton:** ElevenLabs-Stimme erzählt; Musik leise darunter; Originalton höchstens 10–15 % als Atmosphäre.
- **Mechanik:** Erwartung → harter Schnitt → Realität (Säule A) oder klare Info (Säule B).
- **Jede Folge endet mit einem Haken** zur nächsten (letzter Satz = offene Frage oder Ankündigung).
- Voiceover-Länge: **20–25 Wörter** pro 10 s.

Formate (nach Kosten, siehe `PIPELINE.md`): **R** = Real-POV (billig) · **M** = Manga-Standbild (günstig) ·
**A** = bewegtes Anime Look B (ca. 1,70 $, nur Höhepunkte).

## 5. Staffeln

| Staffel | Titel | Zeitraum | Bogen |
|---|---|---|---|
| 1 | **Der Ausstieg** | jetzt bis Abflug (~Jan/Feb 2027) | Entscheidung → Papiere → Steuer/Geld → Job → Ausmisten → Abschied → Abflug |
| 2 | **Ankommen** | ab Ankunft Krabi | erste Tage, Wohnung, **Schule**, Alltag, Rückschläge |
| 3 | **Neues Normal** | später | Vergleich DE ↔ TH nach Monaten, Bildung zahlt sich aus? |

## 6. Staffel 1 „Der Ausstieg“ – Folgenplan (Entwurf, 28 Folgen = 8 Wochen Vorrat)

Kapitel und Meilensteine aus Chris' Input: **Reisepässe → Visum → Steuer → Finanzen → Aufhebungsvertrag**.

### Echte Zeitachse (FEST 22.10.2026)

| Meilenstein | Datum |
|---|---|
| Reisepässe | **erledigt** (kürzlich erneuert) |
| Visum | **17.01.2027** |
| Abflug | **zwischen 15.02. und 15.03.2027** |

**Start der Serie: 01.12.2026 (FEST 23.10.)** – bis dahin müssen Kanal und Puffer stehen (siehe `docs/FAHRPLAN.md`).

**Regel: Die Serie überholt nie die Wirklichkeit.** Bei einer Folge alle 2 Tage ab 01.12.2026 sind
die Folgen 1–10 und 12–24 am 14.01.2027 aufgebraucht – Visum und Abflug kommen erst danach. Deshalb:

| Zeitraum | Folgen | Inhalt |
|---|---|---|
| 01.12. – 14.01. | 1–10, 12–24 | Entscheidung, Pässe (Rückblick), Steuer/Geld, Job, Ausmisten |
| Lücken füllen | Zwischenfolgen | Säule A/B-Folgen ohne Zeitbezug („Deutschland vs. Thailand: …“), Bildung |
| ab 17.01.2027 | 11 | Visum ist da |
| Feb – März 2027 | 25–28 | Abschied, Abflug, Staffelfinale |

Vom 01.12. bis zum Abflug (~01.03.) sind das ca. **45 Posts** → zu den 28 Folgen kommen ca. **17 Zwischenfolgen**. Die Zwischenfolgen schlägt der
Tages-Agent aus dem hochgeladenen Material vor (siehe `docs/AUTOMATION.md`).

### Kapitel 1 – Die Entscheidung (Folge 1–5)

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 1 | Der Satz am Küchentisch | grauer Wolfsburger Morgen, Kaffee | „Folge 1. Eines Abends sagte ich: Wir gehen. Nicht in den Urlaub. Für immer. Meine Frau schaute mich nur an …“ | R |
| 2 | Warum eigentlich? | Kinder (Anime) mit Schulranzen | „Der wichtigste Grund sitzt hier. Mein Sohn. Und eine Frage, die mich nicht mehr loslässt: Welche Schule hat er verdient?“ | M |
| 3 | Bildung | Anime-Sohn vor Schulgebäude, Regen | „Ich will, dass er neugierig bleibt. In Thailand haben wir eine Schule gefunden, die genau das kann. Dazu später mehr.“ | M |
| 4 | Es knirscht | Real: Baustelle/Bahnhof, Anzeigetafel „Verspätung“ | „Grund Nummer zwei: Vieles in Deutschland fühlt sich an, als würde es langsam auseinanderfallen. Ihr kennt das.“ | R |
| 5 | Das Unbekannte | Anime: beide Kinder auf Feldweg, Industrie-Silhouette | „Und ehrlich? Wir wollen nochmal was erleben. Als Familie. Das Unbekannte. Ziel: Krabi, Thailand. Aber erst kommt der Papierkram …“ | A |

### Kapitel 2 – Papiere (Folge 6–11)

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 6 | Reisepässe | Real: Bürgeramt, Wartenummer | „Erste Prüfung: Reisepässe für vier. Ich dachte, ein Termin. Realität: Nummer 247. Aber: erledigt.“ | R |
| 7 | Passfotos mit Kleinkind | Anime: Tochter zappelt vor Kamera | „Biometrisches Passfoto mit meiner Tochter. Versuch eins bis neun: lassen wir das.“ | M |
| 8 | Welches Visum? | Real: Laptop, Tabs | „Touristenvisum? Rentnervisum? Für uns passt das DTV. Was das ist – in 10 Sekunden. Nächste Folge.“ | R |
| 9 | DTV erklärt (B) | Text-Karten | „DTV: Destination Thailand Visa. Bis zu fünf Jahre, Familie kann mit. Was du dafür brauchst …“ | R |
| 10 | Die Unterlagen | Real: Papierstapel | „Kontoauszüge, Nachweise, Übersetzungen. Mein Schreibtisch sieht aus wie ein Finanzamt. Apropos Finanzamt …“ | R |

*(Folge 11 verschoben – siehe Zeitachse. Nach Folge 10 geht es direkt mit Kapitel 3 weiter.)*
| 11 | Das Visum ist da *(erst ab 17.01.2027)* | Anime: Kinder halten Pässe hoch | „17. Januar. Das Visum ist da. Jetzt gibt es kein Zurück mehr. Nächster Schritt: Flug buchen.“ | A |

### Kapitel 3 – Steuer & Geld (Folge 12–17)

Rahmen: **eigene Erfahrung/Recherche, keine Beratung** (Leitplanke).

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 12 | Wer will mein Geld? | Real: zwei Flaggen auf dem Tisch | „Wenn du auswanderst, fragen plötzlich zwei Länder: Wo zahlst du eigentlich Steuern? Ich wusste es nicht.“ | R |
| 13 | Abmelden reicht nicht | Text-Karten | „Abmelden heißt nicht automatisch steuerfrei in Deutschland. Was wirklich zählt, hab ich gelernt …“ | R |
| 14 | Das Abkommen (B) | Text-Karten DE ↔ TH | „Deutschland und Thailand haben ein Doppelbesteuerungsabkommen. Was das für uns bedeutet …“ | R |
| 15 | Konto, Karte, Versicherung | Real: Karten auf Tisch | „Welches Konto? Welche Kreditkarte? Welche Krankenversicherung für vier? Unsere Liste wurde lang.“ | R |
| 16 | Was kostet das Leben? (B2) | Split: Wolfsburg vs. Ao Nang | „3-Zimmer-Wohnung: Wolfsburg gegen Ao Nang. Ich hab's durchgerechnet. Das Ergebnis hat mich überrascht.“ | R |
| 17 | Die Rechnung geht auf | Anime: Kinder stapeln Münzen | „Die Zahlen passen. Jetzt fehlt nur noch eins: Ich muss meinem Arbeitgeber Tschüss sagen.“ | M |

### Kapitel 4 – Der Job (Folge 18–20)

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 18 | Der sichere Job | Real: Werkstor von weitem, keine Logos | „Jahrelang bei einem der größten Autobauer der Welt. Sicherer geht's nicht. Und genau das war das Problem.“ | R |
| 19 | Aufhebungsvertrag | Real: Stift, Unterschrift (Dokument unscharf) | „Kein Streit, keine Kündigung. Ein Aufhebungsvertrag. Eine Unterschrift – und alles ist anders.“ | R |
| 20 | Der letzte Arbeitstag | Anime: Kinder warten am Tor | „Letzter Arbeitstag. Draußen warten zwei, die gar nicht verstehen, warum Papa so grinst.“ | A |

### Kapitel 5 – Ausmisten (Folge 21–24)

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 21 | Ein Wochenende | Real: volle Garage | „Ich dachte: Wohnung auflösen, ein Wochenende. Wir sind bei Woche drei.“ | R |
| 22 | Was kommt mit? | Anime: Tochter hält Kuscheltier fest | „Regel: Jeder darf einen Koffer füllen. Die Kleine hat ihren schon gepackt. Nur Kuscheltiere.“ | M |
| 23 | Kleinanzeigen | Real: Handy, Nachrichten | „Ist das noch da? Letzter Preis? Kann ich in drei Wochen abholen? Kleinanzeigen ist ein eigenes Abenteuer.“ | R |
| 24 | Leere Wohnung | Real: leerer Raum, Echo | „Leere Wohnung. Komisch, wie laut es plötzlich ist. Jetzt kommt der schwerste Teil.“ | R |

### Kapitel 6 – Abschied & Abflug (Folge 25–28)

| # | Titel | Bild | Voiceover (Entwurf) | Fmt |
|---|---|---|---|---|
| 25 | Opa | Real: Opa (echt), Kinder Anime daneben | „Opa. Der Abschied, vor dem ich am meisten Angst hatte. Aber er hat einen Plan …“ | A |
| 26 | Die letzte Bratwurst | Real: Imbiss, Winter | „Letzte Bratwurst, letzter Winter. Ich werde das hier vermissen. Ein bisschen.“ | R |
| 27 | Flughafen | Real: Abflugtafel | „Vier Pässe, vier Visa, acht Koffer. Es ist wirklich passiert.“ | R |
| 28 | Staffelfinale | Anime: Kinder am Flugzeugfenster, Wolken | „Unter uns wird Deutschland kleiner. Mein Sohn fragt: Papa, wie ist die neue Schule? Staffel 2: Ankommen.“ | A |

**Kostenschätzung Staffel 1:** 6 × A (≈ 10 $) + Rest R/M (Cent-Beträge + Stimme) → **ca. 12–15 $**.

## 7. Material, das Chris liefern muss

| Für | Material | Ablage |
|---|---|---|
| Alle R-Folgen | kurze Brillen-/Handyclips der Szenen oben (5–15 s, ruhig) | Drive `40_Medien/01_raw` |
| A-Folgen | Clips, in denen die Kinder gut sichtbar sind, ruhige Kamera | Drive `40_Medien/01_raw` |
| Stimme | ElevenLabs-Konto + API-Key in `.env` (`ELEVENLABS_API_KEY`), 1–3 min Stimmprobe | lokal |

**Tipp:** Beim Hochladen Dateien sprechend benennen, z. B. `F06_buergeramt.mp4`, dann kann die
Vorauswahl sie direkt einer Folge zuordnen.

## 8. Offen

1. ~~Name der Partnerin~~ → „meine Frau“
2. ~~Kindernamen öffentlich~~ → nein, „mein Sohn“ / „meine Tochter“
3. Datum des Aufhebungsvertrags / letzter Arbeitstag (für Folge 18–20)
4. Hook-Formel: Vorschlag = erster Satz „Folge N.“ + Kernsatz (wie oben)
