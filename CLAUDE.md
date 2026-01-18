# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MapToPoster generates minimalist map posters for any city using OpenStreetMap data. It provides three interfaces: CLI, Streamlit web app, and Python API.

## Commands

```bash
# Install dependencies
uv sync                      # Base installation
uv sync --extra web          # With Streamlit web app
uv sync --extra dev          # With pytest, ruff, mypy

# Run CLI
uv run maptoposter -c "Frankfurt" -C "Germany" -t noir -d 12000
uv run maptoposter --list-themes

# Run web app
uv run streamlit run src/maptoposter/webapp.py

# Docker
docker compose up -d         # Start container (builds if needed)
docker compose down          # Stop container
docker compose logs -f       # View logs

# Development
uv run pytest                # Run tests
uv run ruff format .         # Format code
uv run ruff check .          # Lint
uv run mypy src/             # Type check
```

## Architecture

```
src/maptoposter/
├── __init__.py    # Core API: create_poster(), get_coordinates(), load_theme()
├── cli.py         # ArgParse CLI wrapping the API
└── webapp.py      # Streamlit UI with Folium map preview
themes/            # JSON theme definitions (9 built-in themes)
posters/           # Generated output directory
```

**Rendering Pipeline** (`create_poster()` in `__init__.py`):
1. Geocode city → coordinates (geopy/Nominatim)
2. Fetch street network + water/parks within radius (osmnx)
3. Render with matplotlib: water (zorder=1) → parks (zorder=2) → roads (zorder=3+)
4. Apply theme colors and road type styling (motorway/primary/secondary/etc.)
5. Add gradient fades and typography
6. Save PNG to `posters/`

**Theme JSON Structure**:
```json
{
  "name": "theme_id",
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

## Code Style

- Line length: 100 characters
- Python 3.10+ target
- Ruff rules: E, F, I, W
