"""
Streamlit WebApp for MapToPoster.

Run with: streamlit run src/maptoposter/webapp.py
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from maptoposter import create_poster, get_coordinates, list_themes, load_theme


def get_theme_preview(theme: dict) -> str:
    """Generate CSS preview for a theme."""
    return f"""
    <div style="
        background: {theme['bg']};
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
    ">
        <div style="color: {theme['text']}; font-size: 18px; font-weight: bold; letter-spacing: 3px;">
            CITY NAME
        </div>
        <div style="
            width: 60%;
            height: 2px;
            background: {theme['text']};
            margin: 8px auto;
        "></div>
        <div style="color: {theme['text']}; font-size: 12px; opacity: 0.8;">
            COUNTRY
        </div>
        <div style="display: flex; justify-content: center; gap: 4px; margin-top: 12px;">
            <div style="width: 20px; height: 4px; background: {theme['road_motorway']};"></div>
            <div style="width: 20px; height: 3px; background: {theme['road_primary']};"></div>
            <div style="width: 20px; height: 2px; background: {theme['road_secondary']};"></div>
        </div>
        <div style="display: flex; justify-content: center; gap: 8px; margin-top: 8px;">
            <div style="width: 20px; height: 20px; background: {theme['water']}; border-radius: 4px;" title="Water"></div>
            <div style="width: 20px; height: 20px; background: {theme['parks']}; border-radius: 4px;" title="Parks"></div>
        </div>
    </div>
    """


def main():
    st.set_page_config(
        page_title="MapToPoster",
        page_icon="🗺️",
        layout="wide"
    )
    
    st.title("🗺️ MapToPoster")
    st.markdown("*Create beautiful, minimalist map posters for any city*")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # City input
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", value="Frankfurt", placeholder="e.g., Paris")
        with col2:
            country = st.text_input("Country", value="Germany", placeholder="e.g., France")
        
        # Theme selection
        st.subheader("🎨 Theme")
        themes = list_themes()
        theme_name = st.selectbox(
            "Select theme",
            options=themes,
            index=themes.index("feature_based") if "feature_based" in themes else 0
        )
        
        # Theme preview
        theme = load_theme(theme_name)
        st.markdown(get_theme_preview(theme), unsafe_allow_html=True)
        
        # Distance slider
        st.subheader("📏 Map Size")
        distance = st.slider(
            "Radius (meters)",
            min_value=2000,
            max_value=30000,
            value=12000,
            step=1000,
            help="Smaller values show more detail, larger values show more area"
        )
        
        # Distance guide
        with st.expander("📐 Distance Guide"):
            st.markdown("""
            | Distance | Best for |
            |----------|----------|
            | 4000-6000m | Small/dense cities (Venice, Amsterdam) |
            | 8000-12000m | Medium cities (Paris, Barcelona) |
            | 15000-20000m | Large metros (Tokyo, Mumbai) |
            """)
        
        # Quality settings
        st.subheader("📊 Quality")
        dpi = st.select_slider(
            "Resolution (DPI)",
            options=[150, 200, 300],
            value=300,
            help="Higher DPI = better quality but slower"
        )
    
    # Main content area
    col_map, col_preview = st.columns([1, 1])
    
    with col_map:
        st.subheader("📍 Location Preview")
        
        # Get coordinates and show map
        if city and country:
            try:
                with st.spinner("Finding location..."):
                    lat, lon = get_coordinates(city, country)
                
                st.success(f"Found: {lat:.4f}°N, {lon:.4f}°E")
                
                # Create folium map
                m = folium.Map(
                    location=[lat, lon],
                    zoom_start=12,
                    tiles="CartoDB positron"
                )
                
                # Add marker
                folium.Marker(
                    [lat, lon],
                    popup=f"{city}, {country}",
                    tooltip="Center point"
                ).add_to(m)
                
                # Add circle for distance
                folium.Circle(
                    [lat, lon],
                    radius=distance,
                    color="#FF6B6B",
                    fill=True,
                    fillOpacity=0.1,
                    weight=2
                ).add_to(m)
                
                st_folium(m, width=None, height=400)
                
            except Exception as e:
                st.error(f"Could not find location: {e}")
                lat, lon = None, None
        else:
            st.info("Enter a city and country to see the location")
            lat, lon = None, None
    
    with col_preview:
        st.subheader("🖼️ Generate Poster")
        
        if lat and lon:
            if st.button("🎨 Create Poster", type="primary", use_container_width=True):
                with st.spinner("Generating poster... This may take a minute."):
                    try:
                        # Create poster
                        output_path = create_poster(
                            city=city,
                            country=country,
                            theme_name=theme_name,
                            distance=distance,
                            dpi=dpi,
                            show_progress=False
                        )
                        
                        # Display result
                        st.image(str(output_path), caption=f"{city}, {country}")
                        
                        # Download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Poster",
                                data=f,
                                file_name=output_path.name,
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error creating poster: {e}")
        else:
            st.info("Enter a valid location to generate a poster")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; opacity: 0.6; font-size: 12px;">
            Made with ❤️ using OpenStreetMap data • 
            <a href="https://github.com/originalankur/maptoposter">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
