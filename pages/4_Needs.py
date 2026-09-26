import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters
from logic.needs import get_all_needs, post_resource_need, get_need_metrics
from logic.alerts import dispatch_emergency_alert
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Needs | Disaster Response",
    page_icon="⚠️",
    layout="wide"
)
apply_custom_styles()

render_hero(
    title="Emergency Resource Needs",
    subtitle="Log urgent ground supply shortages, triage urgency levels, and track fulfillment status.",
    icon="⚠️"
)

# Need Metrics Row
metrics = get_need_metrics()
n1, n2, n3, n4 = st.columns(4)
with n1:
    st.metric("Total Open Needs", f"{metrics['total_open_needs']}")
with n2:
    st.metric("Pending Dispatch", f"{metrics['pending_needs']}")
with n3:
    st.metric("Partially Fulfilled", f"{metrics['partial_needs']}")
with n4:
    st.metric("Total Units Requested", f"{metrics['total_needed_qty']:,}")

st.write("")

tab_post, tab_list = st.tabs(["➕ Post Resource Need", "📋 Needs Directory (Urgency Ranked)"])

disasters = get_all_disasters()

# -------------------------------------------------------------
# TAB 1: POST RESOURCE NEED FORM
# -------------------------------------------------------------
with tab_post:
    st.subheader("Post Emergency Supply or Personnel Need")
    st.caption("Submit critical shortages reported by field teams, hospitals, or evacuation shelters.")

    if not disasters:
        st.warning("⚠️ No disasters found. Please create a disaster in 'Manage Disasters' before posting needs.")
    else:
        disaster_options = {
            f"{d['name']} ({d['type']} - {d['status'].upper()})": d["id"]
            for d in disasters
        }
        selected_disaster_label = st.selectbox("Assign to Disaster Incident *", list(disaster_options.keys()))
        selected_disaster_id = disaster_options[selected_disaster_label]
        target_disaster = next(d for d in disasters if d["id"] == selected_disaster_id)

        with st.form("post_need_form", clear_on_submit=True):
            n_col1, n_col2 = st.columns(2)

            with n_col1:
                need_type = st.selectbox(
                    "Resource Need Type *",
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
                quantity_needed = st.number_input("Quantity Needed *", min_value=1, value=25, step=1)
                urgency = st.slider(
                    "Urgency Level (1 = Low, 5 = Critical/Life Threatening) *",
                    min_value=1,
                    max_value=5,
                    value=4,
                    help="Urgency 4 and 5 immediately trigger emergency dispatch alerts."
                )

            with n_col2:
                st.caption(f"Coordinates pre-set to incident epicenter ({target_disaster['name']}):")
                lat = st.number_input(
                    "Request Latitude *",
                    value=float(target_disaster["latitude"]),
                    format="%.5f",
                    min_value=-90.0,
                    max_value=90.0
                )
                lon = st.number_input(
                    "Request Longitude *",
                    value=float(target_disaster["longitude"]),
                    format="%.5f",
                    min_value=-180.0,
                    max_value=180.0
                )

            submit_need = st.form_submit_button("🚨 Post Urgent Need", use_container_width=True)

            if submit_need:
                try:
                    new_need = post_resource_need(
                        disaster_id=selected_disaster_id,
                        need_type=need_type,
                        quantity_needed=int(quantity_needed),
                        latitude=lat,
                        longitude=lon,
                        urgency=int(urgency)
                    )
                    st.success(f"✅ Successfully posted need for **{quantity_needed} units of {need_type}** (Urgency: {urgency}/5)!")

                    # Automatic Emergency Dispatch Alert on Urgency 4-5
                    if urgency >= 4:
                        alert = dispatch_emergency_alert(
                            event_type="CRITICAL_NEED_ALERT",
                            title=f"Critical {need_type} Needed",
                            urgency_or_severity=urgency,
                            details=f"Incident: {target_disaster['name']}. Quantity required: {quantity_needed} units.",
                            location_str=f"{lat:.4f}, {lon:.4f}"
                        )
                        st.warning(f"📞 **Emergency Dispatch Alert Triggered:** {alert['summary']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error posting resource need: {str(e)}")

# -------------------------------------------------------------
# TAB 2: NEEDS LIST VIEW (COLOR CODED BY URGENCY)
# -------------------------------------------------------------
with tab_list:
    st.subheader("Field Needs Directory")

    f1, f2, f3 = st.columns(3)
    with f1:
        d_options = ["All Disasters"] + list(disaster_options.keys()) if disasters else ["All Disasters"]
        selected_d = st.selectbox("Filter by Disaster Incident", d_options, key="filter_d_need")
        filter_d_id = None if selected_d == "All Disasters" else disaster_options[selected_d]
    with f2:
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "partial", "fulfilled"])
    with f3:
        urgency_filter = st.selectbox("Filter by Urgency", ["All", "5 - Critical", "4 - High", "3 - Moderate", "2 - Low", "1 - Minimal"])
        urgency_val = None if urgency_filter == "All" else int(urgency_filter.split(" - ")[0])

    needs_list = get_all_needs(
        disaster_id=filter_d_id,
        status_filter=status_filter if status_filter != "All" else None,
        urgency_filter=urgency_val
    )

    if not needs_list:
        st.info("No needs match the specified filter criteria.")
    else:
        # Display cards with clear visual color-coding
        for n in needs_list:
            urg = n["urgency"]
            if urg == 5:
                border_color = "#dc2626"
                bg_color = "#fef2f2"
                urg_badge = "🔴 Level 5 - CRITICAL"
            elif urg == 4:
                border_color = "#ea580c"
                bg_color = "#fff7ed"
                urg_badge = "🟠 Level 4 - HIGH"
            elif urg == 3:
                border_color = "#d97706"
                bg_color = "#fffbeb"
                urg_badge = "🟡 Level 3 - MODERATE"
            else:
                border_color = "#0284c7"
                bg_color = "#f0f9ff"
                urg_badge = f"🟢 Level {urg} - LOW"

            status_style = {
                "pending": "background-color: #fee2e2; color: #b91c1c;",
                "partial": "background-color: #ffedd5; color: #c2410c;",
                "fulfilled": "background-color: #dcfce7; color: #15803d;"
            }.get(n["status"], "")

            card_html = f"""
            <div style="
                border-left: 6px solid {border_color};
                background: {bg_color};
                border-radius: 8px;
                padding: 12px 18px;
                margin-bottom: 12px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">
                        📦 {n['type']} — <span style="color: #2563eb;">{n['quantity_needed']} units needed</span>
                    </span>
                    <div>
                        <span style="font-weight: 600; font-size: 0.8rem; margin-right: 8px;">{urg_badge}</span>
                        <span style="display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; {status_style}">
                            {n['status']}
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #475569;">
                    <b>Disaster:</b> {n['disaster_name']} &nbsp;|&nbsp;
                    <b>Location:</b> {n['latitude']:.4f}, {n['longitude']:.4f} &nbsp;|&nbsp;
                    <b>Logged:</b> {n['created_at'].strftime('%Y-%m-%d %H:%M') if n['created_at'] else 'N/A'}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
