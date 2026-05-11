# Technische Dokumentation

## Überblick

`teleprompter.py` implementiert eine Teleprompter-Anwendung mit `tkinter`. Die Anwendung lädt eine Textdatei, zerlegt den Inhalt in Wörter, bricht diese Wörter abhängig von Font und Anzeigebreite in Zeilen um und stellt sie als mehrzeilige Prompter-Ansicht dar.

Zentrale Eigenschaften:

- feste Fokuszeile in der vertikalen Mitte
- mehrere sichtbare Vorschauzeilen darüber und darunter
- weiches Scrollen nach oben beim Zeilenwechsel
- wortweise Hervorhebung in der Fokuszeile
- zeitliche Steuerung pro Wort unter Berücksichtigung von Wortlänge und Satzzeichen

## Dateistruktur

Aktuell relevante Dateien:

- `teleprompter.py`: ausführbare Tkinter-Anwendung
- `anleitung.txt`: kurze Nutzungsanleitung
- `documentation.md`: technische Dokumentation

## Architektur

Die Anwendung besteht im Wesentlichen aus:

- `Line`:
  Datenklasse mit `start_word_index` und `words`. Sie beschreibt eine bereits umgebrochene Anzeigezeile.

- `TeleprompterApp`:
  zentrale UI- und Ablaufklasse.

## Zustandsmodell

`TeleprompterApp` verwaltet unter anderem folgende Zustände:

- `words`: flache Wortliste aus der geladenen Datei
- `lines`: Liste der umgebrochenen `Line`-Objekte
- `current_line_index`: aktuell aktive Zeile
- `current_word_index`: aktuell hervorgehobenes Wort innerhalb der Fokuszeile
- `scroll_offset`: vertikaler Pixel-Offset während der Scrollanimation
- `is_scrolling`: zeigt an, ob gerade ein Zeilenübergang animiert wird
- `job_id`: ID des laufenden `after()`-Timers

## Benutzeroberfläche

Die Oberfläche besteht aus drei Bereichen:

1. Kopfbereich mit Steuerelementen
   - Datei öffnen
   - Schriftgröße
   - Breite
   - Zeilen
   - Basis-WPM

2. Canvas als Anzeigefläche
   - zeichnet Hintergrund, Fokusbereich und Zeilen
   - rendert die Fokuszeile wortweise
   - rendert Nebenzeilen als komplette Textzeilen

3. Fußbereich mit Ablaufsteuerung
   - Start
   - Pause
   - Zurücksetzen
   - Statusanzeige

## Textverarbeitung

### Laden einer Datei

`load_text_file()` öffnet einen Dateidialog und versucht zuerst `utf-8`, danach `latin-1`.

Danach:

- wird der Text mit `split()` in Wörter zerlegt
- interner Zustand zurückgesetzt
- der Text über `_rebuild_lines()` neu umgebrochen

### Zeilenumbruch

`_wrap_words_into_lines()` erstellt aus der Wortliste Anzeigezeilen.

Vorgehen:

- Wörter werden nacheinander in eine Kandidatenzeile aufgenommen
- mit `font.measure()` wird geprüft, ob die Zeile noch in die eingestellte Breite passt
- sobald die Breite überschritten würde, wird eine neue Zeile begonnen

Damit orientiert sich der Zeilenumbruch an der realen Breite des gerenderten Texts und nicht an einer festen Zeichenanzahl.

## Ablaufsteuerung

### Start

`start()` startet entweder:

- die Worttaktung der aktuellen Fokuszeile oder
- eine laufende Scrollanimation erneut, falls genau dort pausiert wurde

### Wortweises Fortschreiten

`_schedule_current_word()` rendert die aktuelle Anzeige und setzt einen `after()`-Timer für das nächste Wort.

`_advance_word()`:

- erhöht den Wortindex innerhalb der aktuellen Zeile
- oder startet nach dem letzten Wort die Scrollanimation zur nächsten Zeile
- oder beendet den Ablauf am Textende

### Weiches Scrollen

`_start_scroll()` initialisiert den animierten Zeilenwechsel.

`_animate_scroll_step()`:

- reduziert `scroll_offset` in kleinen Schritten
- rendert nach jedem Schritt neu
- verwendet `after(16, ...)` für ungefähr 60 FPS
- setzt nach einer kompletten Zeilenhöhe auf die nächste Zeile um

Dadurch entsteht ein kontinuierliches Nach-oben-Scrollen ohne Sprünge.

## Rendering

### Gesamtaufbau

`_render()` zeichnet den kompletten Frame neu:

- Hintergrund
- Fokusrahmen in der Mitte
- Platzhaltertext, falls keine Datei geladen ist
- sichtbare Zeilen im relevanten Bereich

### Fokuszeile

Die Fokuszeile wird nicht als kompletter String, sondern wortweise gezeichnet:

- `_draw_focus_line()` berechnet die Gesamtbreite der Zeile
- jedes Wort wird einzeln auf dem Canvas positioniert
- das aktuelle Wort erhält eine hervorgehobene Farbe

### Nebenzeilen

Zeilen oberhalb und unterhalb der Fokuszeile werden als vollständiger Text gezeichnet. Ihre Farbe wird über `_shade_for_distance()` abhängig vom Abstand zur Mitte abgeschwächt.

## Timing-Logik

### Basisidee

Die Geschwindigkeit wird nicht rein zeilenweise, sondern wortweise gesteuert. Dadurch können kurze Wörter schneller und lange Wörter langsamer laufen.

### Wortdauer

`_word_duration_ms()` berechnet die Anzeigedauer eines Wortes.

Eingangsgrößen:

- `Basis-WPM` als Grundgeschwindigkeit
- Anzahl relevanter Zeichen im Wort
- Satzzeichen
- Bindestriche

Verhalten:

- längere Wörter erhalten einen größeren Zeitfaktor
- Komma, Semikolon und Doppelpunkt erzeugen kleine Zusatzpausen
- Punkt, Fragezeichen und Ausrufezeichen erzeugen größere Zusatzpausen

### Farbige Hervorhebung

`_highlight_color_for_word()` mappt die berechnete Wortdauer auf Farben:

- kurz: grün
- mittel: gelb
- lang: orange

Die Farbe ist damit nicht rein dekorativ, sondern spiegelt die geschätzte Sprechdauer wider.

## Reaktion auf Laufzeitänderungen

Bei Änderungen von Schriftgröße, Breite, Zeilenzahl oder Geschwindigkeit:

- wird ein laufender Timer gestoppt
- die Anzeige neu berechnet oder neu gerendert
- bei laufendem Betrieb der Ablauf anschließend wieder gestartet

So bleibt die Position im Text weitgehend erhalten und die Anzeige bleibt konsistent.

## Wichtige Methoden

- `load_text_file()`: Datei laden und Zustand initialisieren
- `start()`: Ablauf starten
- `pause()`: Timer stoppen
- `reset()`: Zustand auf Textanfang setzen
- `_rebuild_lines()`: Zeilen aus der Wortliste neu erzeugen
- `_wrap_words_into_lines()`: Umbruchlogik
- `_schedule_current_word()`: Timer für das aktuelle Wort
- `_advance_word()`: Wort- oder Zeilenfortschritt
- `_animate_scroll_step()`: Scrollanimation
- `_render()`: Canvas komplett neu zeichnen
- `_word_duration_ms()`: individuelle Sprechdauer pro Wort berechnen

## Erweiterungsmöglichkeiten

Sinnvolle nächste Schritte:

- Spiegelmodus für echten Prompter-Aufbau mit Spiegelglas
- Tastatur-Shortcuts für Start, Pause und Geschwindigkeitsänderung
- Markierungen für Absätze
- Speichern und Laden von Profileinstellungen
- Fortschrittsanzeige relativ zur Gesamtwortzahl
