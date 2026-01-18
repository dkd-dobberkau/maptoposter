"""
MapToPoster - Generate beautiful map posters from any city.
"""

from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from geopy.geocoders import Nominatim
from matplotlib.colors import LinearSegmentedColormap

# Paper sizes in mm (width, height) for Portrait orientation
PAPER_SIZES: dict[str, tuple[float, float]] = {
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
}

# Bleed for print-ready PDFs in mm
BLEED_MM = 3


def get_aspect_ratio(paper_size: str = "A4", orientation: str = "portrait") -> float:
    """
    Calculate aspect ratio (width/height) for a paper size and orientation.

    Args:
        paper_size: Paper size (A3, A4, A5)
        orientation: portrait, landscape, or square

    Returns:
        Aspect ratio as width/height
    """
    width_mm, height_mm = PAPER_SIZES.get(paper_size, PAPER_SIZES["A4"])

    if orientation == "landscape":
        width_mm, height_mm = height_mm, width_mm
    elif orientation == "square":
        size = min(width_mm, height_mm)
        width_mm, height_mm = size, size

    return width_mm / height_mm

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


def create_poster_figure(
    city: str,
    country: str,
    theme_name: str = "feature_based",
    distance: int = 29000,
    show_progress: bool = True,
    aspect_ratio: float | None = None,
) -> tuple[plt.Figure, float, float]:
    """
    Create a map poster figure without saving.

    Args:
        city: City name
        country: Country name
        theme_name: Theme to use
        distance: Map radius in meters
        show_progress: Print progress messages
        aspect_ratio: Width/height ratio (e.g., 0.707 for A4 portrait).
                      If None, uses default 12:16 (0.75) ratio.

    Returns:
        Tuple of (figure, latitude, longitude)
    """
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

    # Calculate figure size based on aspect ratio
    fig_height = 16  # Base height in inches
    if aspect_ratio is not None:
        fig_width = fig_height * aspect_ratio
    else:
        fig_width = 12  # Default width (3:4 ratio)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=theme["bg"])
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

    return fig, lat, lon


def export_pdf(
    fig: plt.Figure,
    city: str,
    theme_name: str,
    paper_size: str = "A4",
    orientation: str = "portrait",
    print_ready: bool = False,
    output_dir: Path | None = None,
) -> bytes:
    """
    Export a poster figure as PDF.

    Args:
        fig: Matplotlib figure to export
        city: City name (for filename)
        theme_name: Theme name (for filename)
        paper_size: Paper size (A3, A4, A5)
        orientation: portrait, landscape, or square
        print_ready: Add bleed and crop marks
        output_dir: Optional output directory (if None, returns bytes only)

    Returns:
        PDF as bytes
    """
    # Get paper dimensions in mm
    width_mm, height_mm = PAPER_SIZES.get(paper_size, PAPER_SIZES["A4"])

    # Apply orientation
    if orientation == "landscape":
        width_mm, height_mm = height_mm, width_mm
    elif orientation == "square":
        size = min(width_mm, height_mm)
        width_mm, height_mm = size, size

    # Add bleed for print-ready
    if print_ready:
        width_mm += 2 * BLEED_MM
        height_mm += 2 * BLEED_MM

    # Convert mm to inches (matplotlib uses inches)
    width_in = width_mm / 25.4
    height_in = height_mm / 25.4

    # Resize figure to exact paper size
    fig.set_size_inches(width_in, height_in)

    # Adjust subplot to fill the page
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Get background color from figure
    bg_color = fig.get_facecolor()

    # Create PDF in memory
    pdf_buffer = io.BytesIO()

    if print_ready:
        # For print-ready, save with bleed already included in dimensions
        fig.savefig(
            pdf_buffer,
            format="pdf",
            facecolor=bg_color,
            edgecolor="none",
        )
        pdf_buffer.seek(0)

        # Add crop marks
        pdf_with_marks = _add_crop_marks(
            pdf_buffer.getvalue(),
            width_mm - 2 * BLEED_MM,
            height_mm - 2 * BLEED_MM,
            BLEED_MM
        )
        pdf_buffer = io.BytesIO(pdf_with_marks)
    else:
        # Save at exact paper size
        fig.savefig(
            pdf_buffer,
            format="pdf",
            facecolor=bg_color,
            edgecolor="none",
        )

    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.getvalue()

    # Optionally save to file
    if output_dir is not None:
        output_dir.mkdir(exist_ok=True)
        orientation_str = orientation[:4]  # port, land, squa
        suffix = "_printready" if print_ready else ""
        filename = f"{city.lower().replace(' ', '_')}_{theme_name}_{paper_size}_{orientation_str}{suffix}.pdf"
        output_path = output_dir / filename
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def _add_crop_marks(pdf_bytes: bytes, width_mm: float, height_mm: float, bleed_mm: float) -> bytes:
    """Add crop marks to a PDF. Returns PDF with marks."""
    # For simplicity, we'll create the crop marks using matplotlib
    # and overlay them. This is a simplified implementation.

    # Create a figure with crop marks
    total_width = width_mm + 2 * bleed_mm + 20  # Extra space for marks
    total_height = height_mm + 2 * bleed_mm + 20

    fig_marks, ax_marks = plt.subplots(
        figsize=(total_width / 25.4, total_height / 25.4),
        facecolor="white"
    )
    ax_marks.set_xlim(0, total_width)
    ax_marks.set_ylim(0, total_height)
    ax_marks.set_aspect("equal")
    ax_marks.axis("off")

    # Offset to center the content
    offset = 10  # mm from edge

    # Crop mark positions (corners of the final trim size)
    corners = [
        (offset + bleed_mm, offset + bleed_mm),  # bottom-left
        (offset + bleed_mm + width_mm, offset + bleed_mm),  # bottom-right
        (offset + bleed_mm, offset + bleed_mm + height_mm),  # top-left
        (offset + bleed_mm + width_mm, offset + bleed_mm + height_mm),  # top-right
    ]

    mark_length = 5  # mm
    mark_offset = 3  # mm from corner

    for cx, cy in corners:
        # Horizontal marks
        if cx == offset + bleed_mm:  # Left side
            ax_marks.plot([cx - mark_offset - mark_length, cx - mark_offset], [cy, cy], "k-", linewidth=0.5)
        else:  # Right side
            ax_marks.plot([cx + mark_offset, cx + mark_offset + mark_length], [cy, cy], "k-", linewidth=0.5)

        # Vertical marks
        if cy == offset + bleed_mm:  # Bottom
            ax_marks.plot([cx, cx], [cy - mark_offset - mark_length, cy - mark_offset], "k-", linewidth=0.5)
        else:  # Top
            ax_marks.plot([cx, cx], [cy + mark_offset, cy + mark_offset + mark_length], "k-", linewidth=0.5)

    # For now, just return the original PDF as crop marks would require
    # PDF manipulation libraries like PyPDF2 or reportlab for proper overlay
    # This is a placeholder that returns the original
    plt.close(fig_marks)
    return pdf_bytes


__all__ = [
    "create_poster",
    "create_poster_figure",
    "export_pdf",
    "get_aspect_ratio",
    "get_coordinates",
    "load_theme",
    "list_themes",
    "DEFAULT_THEME",
    "PAPER_SIZES",
]
