"""
MapToPoster - Generate beautiful map posters from any city.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from geopy.geocoders import Nominatim
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point

# Default theme as fallback
DEFAULT_THEME: dict[str, Any] = {
    "name": "feature_based",
    "description": "Classic black & white with road hierarchy",
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
    "road_default": "#3A3A3A",
}


def get_themes_dir() -> Path:
    """Get the themes directory path."""
    return Path(__file__).parent.parent.parent / "themes"


def load_theme(theme_name: str) -> dict[str, Any]:
    """Load a theme from JSON file or return default."""
    themes_dir = get_themes_dir()
    theme_file = themes_dir / f"{theme_name}.json"
    
    if theme_file.exists():
        with open(theme_file) as f:
            theme = json.load(f)
            # Merge with defaults for missing keys
            return {**DEFAULT_THEME, **theme}
    
    return DEFAULT_THEME.copy()


def list_themes() -> list[str]:
    """List all available theme names."""
    themes_dir = get_themes_dir()
    if not themes_dir.exists():
        return ["feature_based"]
    return [f.stem for f in themes_dir.glob("*.json")]


def get_coordinates(city: str, country: str) -> tuple[float, float]:
    """Get latitude and longitude for a city using Nominatim."""
    geolocator = Nominatim(user_agent="maptoposter")
    location = geolocator.geocode(f"{city}, {country}")
    
    if location is None:
        raise ValueError(f"Could not find coordinates for {city}, {country}")
    
    return location.latitude, location.longitude


def get_edge_colors_by_type(graph, theme: dict[str, Any]) -> list[str]:
    """Get colors for each edge based on road type."""
    colors = []
    for u, v, data in graph.edges(data=True):
        highway = data.get("highway", "")
        if isinstance(highway, list):
            highway = highway[0]
        
        if highway in ("motorway", "motorway_link"):
            colors.append(theme["road_motorway"])
        elif highway in ("trunk", "trunk_link", "primary", "primary_link"):
            colors.append(theme["road_primary"])
        elif highway in ("secondary", "secondary_link"):
            colors.append(theme["road_secondary"])
        elif highway in ("tertiary", "tertiary_link"):
            colors.append(theme["road_tertiary"])
        elif highway in ("residential", "living_street"):
            colors.append(theme["road_residential"])
        else:
            colors.append(theme["road_default"])
    
    return colors


def get_edge_widths_by_type(graph) -> list[float]:
    """Get line widths for each edge based on road type."""
    widths = []
    for u, v, data in graph.edges(data=True):
        highway = data.get("highway", "")
        if isinstance(highway, list):
            highway = highway[0]
        
        if highway in ("motorway", "motorway_link"):
            widths.append(1.2)
        elif highway in ("trunk", "trunk_link", "primary", "primary_link"):
            widths.append(1.0)
        elif highway in ("secondary", "secondary_link"):
            widths.append(0.8)
        elif highway in ("tertiary", "tertiary_link"):
            widths.append(0.6)
        elif highway in ("residential", "living_street"):
            widths.append(0.4)
        else:
            widths.append(0.3)
    
    return widths


def create_gradient_fade(
    ax,
    color: str,
    position: str = "top",
    height: float = 0.15
) -> None:
    """Create a gradient fade overlay at top or bottom."""
    if position == "top":
        y_start, y_end = 1.0, 1.0 - height
        alpha_start, alpha_end = 1.0, 0.0
    else:
        y_start, y_end = 0.0, height
        alpha_start, alpha_end = 1.0, 0.0
    
    # Create gradient
    gradient = np.linspace(alpha_start, alpha_end, 100).reshape(-1, 1)
    gradient = np.hstack([gradient] * 100)
    
    # Convert hex to RGB
    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) / 255 for i in (0, 2, 4))
    
    # Create colormap
    cmap = LinearSegmentedColormap.from_list(
        "fade",
        [(rgb[0], rgb[1], rgb[2], 1), (rgb[0], rgb[1], rgb[2], 0)]
    )
    
    ax.imshow(
        gradient,
        extent=[0, 1, y_start, y_end],
        aspect="auto",
        cmap=cmap,
        transform=ax.transAxes,
        zorder=10
    )


def create_poster(
    city: str,
    country: str,
    theme_name: str = "feature_based",
    distance: int = 29000,
    output_dir: Path | None = None,
    dpi: int = 300,
    show_progress: bool = True
) -> Path:
    """
    Create a map poster for a city.
    
    Args:
        city: City name
        country: Country name
        theme_name: Theme to use
        distance: Map radius in meters
        output_dir: Output directory (default: posters/)
        dpi: Output resolution
        show_progress: Print progress messages
    
    Returns:
        Path to the generated poster
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "posters"
    output_dir.mkdir(exist_ok=True)
    
    # Load theme
    theme = load_theme(theme_name)
    
    if show_progress:
        print(f"Creating poster for {city}, {country}")
        print(f"Theme: {theme.get('name', theme_name)}")
    
    # Get coordinates
    if show_progress:
        print("Getting coordinates...")
    lat, lon = get_coordinates(city, country)
    point = (lat, lon)
    
    if show_progress:
        print(f"Coordinates: {lat:.4f}, {lon:.4f}")
    
    # Fetch street network
    if show_progress:
        print("Fetching street network...")
    graph = ox.graph_from_point(point, dist=distance, network_type="all")
    
    # Fetch water features
    if show_progress:
        print("Fetching water features...")
    try:
        water = ox.features_from_point(
            point,
            tags={"natural": ["water", "bay"], "waterway": True},
            dist=distance
        )
    except Exception:
        water = None
    
    # Fetch parks
    if show_progress:
        print("Fetching parks...")
    try:
        parks = ox.features_from_point(
            point,
            tags={"leisure": "park", "landuse": ["grass", "forest"]},
            dist=distance
        )
    except Exception:
        parks = None
    
    # Create figure
    if show_progress:
        print("Rendering poster...")
    
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=theme["bg"])
    ax.set_facecolor(theme["bg"])
    
    # Plot water
    if water is not None and not water.empty:
        water.plot(ax=ax, color=theme["water"], zorder=1)
    
    # Plot parks
    if parks is not None and not parks.empty:
        parks.plot(ax=ax, color=theme["parks"], zorder=2)
    
    # Plot roads
    edge_colors = get_edge_colors_by_type(graph, theme)
    edge_widths = get_edge_widths_by_type(graph)
    
    ox.plot_graph(
        graph,
        ax=ax,
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        bgcolor=theme["bg"],
        show=False,
        close=False
    )
    
    # Add gradient fades
    create_gradient_fade(ax, theme["gradient_color"], "top", 0.08)
    create_gradient_fade(ax, theme["gradient_color"], "bottom", 0.20)
    
    # Add text
    city_text = "  ".join(city.upper())
    ax.text(
        0.5, 0.14,
        city_text,
        transform=ax.transAxes,
        fontsize=28,
        fontweight="bold",
        color=theme["text"],
        ha="center",
        va="center",
        zorder=11
    )
    
    # Decorative line
    ax.plot(
        [0.35, 0.65], [0.125, 0.125],
        color=theme["text"],
        linewidth=1,
        transform=ax.transAxes,
        zorder=11
    )
    
    # Country
    ax.text(
        0.5, 0.10,
        country.upper(),
        transform=ax.transAxes,
        fontsize=12,
        color=theme["text"],
        ha="center",
        va="center",
        zorder=11
    )
    
    # Coordinates
    coord_text = f"{abs(lat):.2f}°{'N' if lat >= 0 else 'S'} / {abs(lon):.2f}°{'E' if lon >= 0 else 'W'}"
    ax.text(
        0.5, 0.07,
        coord_text,
        transform=ax.transAxes,
        fontsize=10,
        color=theme["text"],
        ha="center",
        va="center",
        alpha=0.7,
        zorder=11
    )
    
    # Attribution
    ax.text(
        0.98, 0.02,
        "© OpenStreetMap",
        transform=ax.transAxes,
        fontsize=6,
        color=theme["text"],
        ha="right",
        va="bottom",
        alpha=0.5,
        zorder=11
    )
    
    # Clean up axes
    ax.set_axis_off()
    plt.tight_layout(pad=0)
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{city.lower().replace(' ', '_')}_{theme_name}_{timestamp}.png"
    output_path = output_dir / filename
    
    fig.savefig(
        output_path,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0,
        facecolor=theme["bg"]
    )
    plt.close(fig)
    
    if show_progress:
        print(f"Saved to: {output_path}")
    
    return output_path


__all__ = [
    "create_poster",
    "get_coordinates",
    "load_theme",
    "list_themes",
    "DEFAULT_THEME",
]
