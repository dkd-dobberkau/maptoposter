"""
Command-line interface for MapToPoster.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import create_poster, list_themes


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate beautiful map posters for any city.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  maptoposter -c "Paris" -C "France" -t pastel_dream
  maptoposter -c "Tokyo" -C "Japan" -t japanese_ink -d 15000
  maptoposter --list-themes
        """
    )
    
    parser.add_argument(
        "-c", "--city",
        help="City name (required unless --list-themes)"
    )
    parser.add_argument(
        "-C", "--country",
        help="Country name (required unless --list-themes)"
    )
    parser.add_argument(
        "-t", "--theme",
        default="feature_based",
        help="Theme name (default: feature_based)"
    )
    parser.add_argument(
        "-d", "--distance",
        type=int,
        default=29000,
        help="Map radius in meters (default: 29000)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory (default: posters/)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output resolution (default: 300)"
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List all available themes"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    if args.list_themes:
        themes = list_themes()
        print("Available themes:")
        for theme in sorted(themes):
            print(f"  - {theme}")
        return 0
    
    if not args.city or not args.country:
        parser.error("--city and --country are required")
    
    try:
        output_path = create_poster(
            city=args.city,
            country=args.country,
            theme_name=args.theme,
            distance=args.distance,
            output_dir=args.output,
            dpi=args.dpi,
            show_progress=not args.quiet
        )
        print(f"\nPoster created: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
