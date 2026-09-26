import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters
from logic.resources import get_all_resources, register_resource, get_resource_metrics
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Resources | Disaster Response",
    page_icon="📦",
    layout="wide"
)
apply_custom_styles()

render_hero(
    title="Emergency Resource Inventory",
    subtitle="Register emergency supplies, track provider staging, and monitor per-disaster availability.",
    icon="📦"
)

# Quick Metrics
metrics = get_resource_metrics()
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Supply Units", f"{metrics['total_resources']:,}")
with m2:
    st.metric("Available for Dispatch", f"{metrics['available_resources']:,}")
with m3:
    st.metric("Currently Allocated", f"{metrics['allocated_resources']:,}")
with m4:
    st.metric("Distinct Resource Types", f"{metrics['resource_types_count']}")

st.write("")

tab_register, tab_list = st.tabs(["➕ Register Resource", "📋 Resources by Disaster"])

disasters = get_all_disasters()

# -------------------------------------------------------------
# TAB 1: REGISTER RESOURCE FORM
# -------------------------------------------------------------
with tab_register:
    st.subheader("Register Emergency Resource")
    st.caption("Stage new supplies, rescue personnel, or equipment designated for a disaster zone.")

    if not disasters:
        st.warning("⚠️ No disasters found. Please create a disaster in 'Manage Disasters' before registering resources.")
    else:
        disaster_options = {
            f"{d['name']} ({d['type']} - {d['status'].upper()})": d["id"]
            for d in disasters
        }
        selected_disaster_label = st.selectbox("Assign to Disaster Incident *", list(disaster_options.keys()))
        selected_disaster_id = disaster_options[selected_disaster_label]
        target_disaster = next(d for d in disasters if d["id"] == selected_disaster_id)

        with st.form("register_resource_form", clear_on_submit=True):
            r_col1, r_col2 = st.columns(2)

            with r_col1:
                resource_type = st.selectbox(
                    "Resource Type *",
                    [
                        "Medical Supplies",
                        "Food & Water",
                        "Rescue Team",
                        "Shelter Kits",
                        "Heavy Machinery",
                        "Power Generators",
                        "Fuel & Energy",
                        "Blankets & Clothing"
                    ]
                )
                quantity = st.number_input("Total Quantity *", min_value=1, value=50, step=1)
                provider = st.text_input("Provider / Organization *", placeholder="e.g. Red Cross, FEMA, Local Fire Dept")

            with r_col2:
                st.caption(f"Defaulting coordinates to disaster epicenter ({target_disaster['name']}):")
                lat = st.number_input(
                    "Staging Latitude *",
                    value=float(target_disaster["latitude"]),
                    format="%.5f",
                    min_value=-90.0,
                    max_value=90.0
                )
                lon = st.number_input(
                    "Staging Longitude *",
                    value=float(target_disaster["longitude"]),
                    format="%.5f",
                    min_value=-180.0,
                    max_value=180.0
                )

            submit_res = st.form_submit_button("📦 Register Resource", use_container_width=True)

            if submit_res:
                if not provider or not provider.strip():
                    st.error("❌ Provider organization is required.")
                else:
                    try:
                        res = register_resource(
                            disaster_id=selected_disaster_id,
                            resource_type=resource_type,
                            quantity=int(quantity),
                            latitude=lat,
                            longitude=lon,
                            provider=provider.strip()
                        )
                        st.success(f"✅ Successfully registered **{quantity} units of {resource_type}** by **{provider}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error registering resource: {str(e)}")

# -------------------------------------------------------------
# TAB 2: RESOURCES LIST VIEW PER DISASTER
# -------------------------------------------------------------
with tab_list:
    st.subheader("Resources Directory")

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        d_filter_options = ["All Disasters"] + list(disaster_options.keys()) if disasters else ["All Disasters"]
        selected_d_filter = st.selectbox("Filter by Disaster Incident", d_filter_options)
        filter_d_id = None
        if selected_d_filter != "All Disasters":
            filter_d_id = disaster_options[selected_d_filter]

    with f_col2:
        all_res_raw = get_all_resources()
        type_options = ["All Types"] + sorted(list({r["type"] for r in all_res_raw})) if all_res_raw else ["All Types"]
        selected_type_filter = st.selectbox("Filter by Resource Type", type_options)
        filter_type = None if selected_type_filter == "All Types" else selected_type_filter

    resources_list = get_all_resources(disaster_id=filter_d_id, resource_type=filter_type)

    if not resources_list:
        st.info("No resources found matching the specified filters.")
    else:
        df_rows = []
        for r in resources_list:
            avail_pct = (r["available"] / r["quantity"] * 100) if r["quantity"] > 0 else 0
            df_rows.append({
                "Resource Type": r["type"],
                "Available": r["available"],
                "Total Quantity": r["quantity"],
                "Allocated": r["allocated"],
                "Availability %": f"{avail_pct:.0f}%",
                "Disaster": r["disaster_name"],
                "Provider": r["provider"],
                "Latitude": round(r["latitude"], 4),
                "Longitude": round(r["longitude"], 4),
                "Registered": r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else "N/A"
            })
        df_resources = pd.DataFrame(df_rows)
        st.dataframe(df_resources, use_container_width=True, hide_index=True)
