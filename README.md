# Prompter Tool

Ein einfaches Teleprompter-Programm mit `tkinter` für lokale Textdateien.

Die Anwendung orientiert sich am Verhalten eines echten Prompters:

- feste Fokuszeile in der Mitte
- mehrere sichtbare Zeilen über und unter der Fokuszeile
- weiches Scrollen nach oben statt sprunghafter Wechsel
- wortweise Hervorhebung in der Fokuszeile
- variable Wortdauer abhängig von Wortlänge und Satzzeichen

## Funktionen

- Textdatei per Dateidialog auswählen
- Schriftgröße anpassen
- Zeilenbreite anpassen
- Anzahl sichtbarer Zeilen anpassen
- Grundgeschwindigkeit in Wörtern pro Minute einstellen
- Start, Pause und Zurücksetzen

## Voraussetzungen

- Python 3
- `tkinter` muss verfügbar sein

Unter vielen Python-Installationen ist `tkinter` bereits enthalten.

## Start

Projektordner öffnen und ausführen:

```bash
python3 teleprompter.py
```

## Bedienung

1. Auf `Textdatei öffnen` klicken.
2. Eine `.txt`, `.md` oder andere Textdatei auswählen.
3. Anzeige über die Regler einstellen:
   - `Schriftgröße`
   - `Breite`
   - `Zeilen`
   - `Basis-WPM`
4. Mit `Start` den Prompter starten.
5. Mit `Pause` anhalten.
6. Mit `Zurücksetzen` wieder an den Anfang springen.

## Wortbasierte Geschwindigkeit

Die Anzeige läuft nicht mit einer starren Zeit pro Wort. Stattdessen wird die Dauer pro Wort dynamisch berechnet:

- kurze Wörter werden schneller angezeigt
- lange Wörter werden länger angezeigt
- Satzzeichen erzeugen kleine zusätzliche Pausen

Die Hervorhebungsfarbe des aktuellen Worts orientiert sich ebenfalls an der berechneten Dauer:

- grün: kurz
- gelb: mittel
- orange: lang

## Projektdateien

- `teleprompter.py`: Hauptprogramm
- `anleitung.txt`: kurze Benutzungsanleitung
- `documentation.md`: technische Dokumentation
- `text.txt`: Beispiel- oder Testtext

## Technische Hinweise

Die Anwendung rendert die Anzeige auf einem `tkinter.Canvas`. Der Text wird zunächst abhängig von Font und verfügbarer Breite in Zeilen umgebrochen. Die Fokuszeile wird wortweise gezeichnet, damit einzelne Wörter farblich hervorgehoben werden können. Der Zeilenwechsel wird über eine weiche vertikale Scrollanimation umgesetzt.

## Lizenz

Die Lizenz findest du in [LICENSE](LICENSE).
