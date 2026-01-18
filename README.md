# MapToPoster

Generate beautiful, minimalist map posters for any city in the world.

> **Fork Info:** Dieses Projekt basiert auf [originalankur/maptoposter](https://github.com/originalankur/maptoposter).
> Erweitert um PDF-Export (Raster/Vektor), EPS-Export, Docker-Support und Streamlit WebApp.

## Installation mit UV

```bash
# Repository klonen
git clone https://github.com/dkd-dobberkau/maptoposter.git
cd maptoposter

# Mit UV installieren
uv sync

# Oder mit optionalen Web-Dependencies
uv sync --extra web
```

## Verwendung

### CLI

```bash
# Poster erstellen
uv run maptoposter -c "Frankfurt" -C "Germany" -t noir -d 12000

# Themes auflisten
uv run maptoposter --list-themes

# Mit allen Optionen
uv run maptoposter \
  --city "Paris" \
  --country "France" \
  --theme pastel_dream \
  --distance 10000 \
  --dpi 300 \
  --output ./my-posters
```

### WebApp (Streamlit)

```bash
# Web-Dependencies installieren falls noch nicht geschehen
uv sync --extra web

# WebApp starten
uv run streamlit run src/maptoposter/webapp.py
```

Die App öffnet sich unter http://localhost:8501

### Python API

```python
from maptoposter import create_poster, list_themes, get_coordinates

# Verfügbare Themes
print(list_themes())

# Koordinaten einer Stadt
lat, lon = get_coordinates("Frankfurt", "Germany")
print(f"Frankfurt: {lat}, {lon}")

# Poster erstellen
output = create_poster(
    city="Frankfurt",
    country="Germany",
    theme_name="noir",
    distance=12000,
    dpi=300
)
print(f"Gespeichert: {output}")
```

## Themes

| Theme | Beschreibung |
|-------|-------------|
| `feature_based` | Klassisch schwarz-weiß |
| `noir` | Schwarzer Hintergrund, weiße Straßen |
| `midnight_blue` | Navy mit goldenen Straßen |
| `japanese_ink` | Minimalistischer Tusche-Stil |
| `neon_cyberpunk` | Dunkel mit Pink/Cyan |
| `sunset` | Warme Orange- und Pinktöne |
| `warm_beige` | Vintage Sepia |
| `terracotta` | Mediterrane Wärme |
| `blueprint` | Architektur-Blaupause |

## Eigene Themes erstellen

Erstelle eine JSON-Datei in `themes/`:

```json
{
  "name": "mein_theme",
  "description": "Beschreibung",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

## Distanz-Empfehlungen

| Distanz | Ideal für |
|---------|-----------|
| 4000-6000m | Kleine/dichte Städte (Venedig, Amsterdam-Zentrum) |
| 8000-12000m | Mittelgroße Städte (Paris, Barcelona) |
| 15000-20000m | Große Metropolen (Tokyo, Mumbai) |

## Projektstruktur

```
maptoposter/
├── pyproject.toml          # UV/Projekt-Konfiguration
├── src/
│   └── maptoposter/
│       ├── __init__.py     # Hauptmodul
│       ├── cli.py          # Kommandozeile
│       └── webapp.py       # Streamlit WebApp
├── themes/                 # Theme JSON-Dateien
├── posters/                # Generierte Poster
└── README.md
```

## Entwicklung

```bash
# Dev-Dependencies installieren
uv sync --extra dev

# Tests ausführen
uv run pytest

# Code formatieren
uv run ruff format .

# Linting
uv run ruff check .
```

## Credits

Basiert auf [maptoposter](https://github.com/originalankur/maptoposter) von [@originalankur](https://github.com/originalankur).

## Lizenz

MIT License
