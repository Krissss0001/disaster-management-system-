"""Geospatial map rendering helpers using 100% free OpenStreetMap and satellite layers."""
import folium
from folium.plugins import Fullscreen, MiniMap
from typing import List, Dict, Any, Optional


def create_emergency_map(
    disasters: List[Dict[str, Any]],
    resources: List[Dict[str, Any]],
    needs: List[Dict[str, Any]],
    height: int = 500
) -> folium.Map:
    """
    Build a rich interactive Folium map using 100% free public map tiles
    (OpenStreetMap, Free Satellite Imagery, CartoDB Positron).
    """
    # Collect coordinates to compute center
    lats, lons = [], []
    for d in disasters:
        lats.append(d["latitude"])
        lons.append(d["longitude"])
    for r in resources:
        lats.append(r["latitude"])
        lons.append(r["longitude"])
    for n in needs:
        lats.append(n["latitude"])
        lons.append(n["longitude"])

    default_center = [37.7749, -122.4194]
    zoom = 12 if lats else 5
    if lats and lons:
        default_center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    # 1. Base Map with free OpenStreetMap
    m = folium.Map(
        location=default_center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True
    )

    # 2. Add 100% Free Public Map Tiles
    # Layer 1: OpenStreetMap (Default free community street map)
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="🗺️ OpenStreetMap (Default)",
        control=True
    ).add_to(m)

    # Layer 2: Free Public Satellite Imagery (Esri World Imagery)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        name="🛰️ Satellite Imagery (Free)",
        control=True
    ).add_to(m)

    # Layer 3: Clean Light Positron
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="🏙️ Clean Street Canvas",
        control=True
    ).add_to(m)

    # 3. Create Feature Groups for toggling
    fg_disasters = folium.FeatureGroup(name="🚨 Active Disasters", show=True)
    fg_resources = folium.FeatureGroup(name="📦 Staged Resources", show=True)
    fg_needs = folium.FeatureGroup(name="⚠️ Critical Needs", show=True)

    # 4. Add Disasters (Pins + Danger Perimeter Radius)
    for d in disasters:
        sev = d.get("severity", 3)
        sev_color = "#e63946" if sev >= 4 else "#f4a261" if sev == 3 else "#2a9d8f"
        radius_meters = 600 * sev

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px; font-size: 13px; line-height: 1.4;">
            <h4 style="margin: 0 0 6px 0; color: #b91c1c;">🚨 {d['name']}</h4>
            <b>Type:</b> {d['type']}<br/>
            <b>Severity:</b> Level {sev}/5<br/>
            <b>Status:</b> <span style="font-weight:bold; color: #b91c1c; text-transform:uppercase;">{d['status']}</span><br/>
            <b>Location:</b> {d['latitude']:.4f}, {d['longitude']:.4f}<br/>
            <p style="margin: 6px 0 0 0; color: #475569; font-size: 12px;">{d.get('description') or 'No description logged.'}</p>
        </div>
        """

        folium.Marker(
            location=[d["latitude"], d["longitude"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"🚨 Disaster: {d['name']} (Severity {sev}/5)",
            icon=folium.Icon(color="red", icon="fire", prefix="fa")
        ).add_to(fg_disasters)

        # Draw danger zone radius circle
        folium.Circle(
            location=[d["latitude"], d["longitude"]],
            radius=radius_meters,
            color=sev_color,
            fill=True,
            fill_color=sev_color,
            fill_opacity=0.18,
            weight=2,
            tooltip=f"Threat Perimeter: {radius_meters}m"
        ).add_to(fg_disasters)

    # 5. Add Resources
    for r in resources:
        avail = r.get("available", 0)
        total = r.get("quantity", 0)
        icon_type = "medkit" if "Medical" in r["type"] else "truck"

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 200px; font-size: 13px; line-height: 1.4;">
            <h4 style="margin: 0 0 6px 0; color: #1d4ed8;">📦 {r['type']}</h4>
            <b>Provider:</b> {r['provider']}<br/>
            <b>Available:</b> <b style="color: #059669;">{avail}</b> / {total} units<br/>
            <b>Disaster:</b> {r.get('disaster_name', 'Linked')}<br/>
            <b>Location:</b> {r['latitude']:.4f}, {r['longitude']:.4f}
        </div>
        """

        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"📦 Resource: {r['type']} ({avail} avail) - {r['provider']}",
            icon=folium.Icon(color="blue", icon=icon_type, prefix="fa")
        ).add_to(fg_resources)

    # 6. Add Needs
    for n in needs:
        urg = n.get("urgency", 3)
        urg_color = "darkred" if urg == 5 else "red" if urg == 4 else "orange"

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 210px; font-size: 13px; line-height: 1.4;">
            <h4 style="margin: 0 0 6px 0; color: #d97706;">⚠️ Need: {n['type']}</h4>
            <b>Quantity Needed:</b> {n['quantity_needed']}<br/>
            <b>Urgency:</b> Level {urg}/5<br/>
            <b>Status:</b> <span style="font-weight:bold; text-transform:uppercase;">{n['status']}</span><br/>
            <b>Disaster:</b> {n.get('disaster_name', 'Linked')}<br/>
            <b>Location:</b> {n['latitude']:.4f}, {n['longitude']:.4f}
        </div>
        """

        folium.Marker(
            location=[n["latitude"], n["longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"⚠️ Need: {n['type']} (Urgency {urg}/5) - {n['status']}",
            icon=folium.Icon(color=urg_color, icon="exclamation", prefix="fa")
        ).add_to(fg_needs)

    fg_disasters.add_to(m)
    fg_resources.add_to(m)
    fg_needs.add_to(m)

    # Add Fullscreen toggle and Layer Switcher
    Fullscreen(position="topright").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m
