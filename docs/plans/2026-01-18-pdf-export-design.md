# PDF Export Design

## Übersicht

PDF-Export mit A3/A4/A5 Formaten in der Streamlit Web-App.

**Features:**
- Drei Papiergrößen: A3, A4, A5
- Drei Ausrichtungen: Portrait, Landscape, Quadrat
- Zwei Export-Varianten: Home (sauber) und Print-Ready (mit Bleed + Schnittmarken)

## Papiergrößen

| Format | Portrait (mm) | Landscape (mm) |
|--------|---------------|----------------|
| A3     | 297 × 420     | 420 × 297      |
| A4     | 210 × 297     | 297 × 210      |
| A5     | 148 × 210     | 210 × 148      |

**Quadrat:** Kleinere Seite × Kleinere Seite, zentriert auf Seite.

## Print-Ready Variante

- 3mm Bleed auf allen Seiten
- Schnittmarken an den Ecken (5mm lang, 3mm Abstand vom Endformat)
- Karte/Hintergrund läuft über Endformat hinaus

## Technische Umsetzung

**Neue Funktion in `__init__.py`:**
```python
def export_pdf(
    fig,
    output_path: Path,
    paper_size: str = "A4",      # A3, A4, A5
    orientation: str = "portrait", # portrait, landscape, square
    print_ready: bool = False
) -> Path
```

**Abhängigkeiten:**
- Keine neuen - matplotlib kann bereits PDF (`matplotlib.backends.backend_pdf`)

**Bestehender Code:**
- `create_poster()` bleibt unverändert, erzeugt weiterhin die Figure
- Neue Funktion übernimmt Figure und exportiert als PDF

## Web-App UI

**Sidebar-Erweiterung:**
```
Format:        [PNG / PDF]  (radio, horizontal)

Bei PDF:
  Papiergröße: [A4 ▼]       (selectbox: A3, A4, A5)
  Ausrichtung: [Portrait ▼] (selectbox: Portrait, Landscape, Quadrat)
```

**Download-Buttons:**
- PNG: Ein Button "Download PNG"
- PDF: Zwei Buttons "PDF (Home)" und "PDF (Print-Ready)"

## Dateinamen

- PNG: `{city}_{theme}_{timestamp}.png` (unverändert)
- PDF Home: `{city}_{theme}_{size}_{orientation}.pdf`
- PDF Print-Ready: `{city}_{theme}_{size}_{orientation}_printready.pdf`

## Scope

- Nur Web-App (CLI und Python API später bei Bedarf)
