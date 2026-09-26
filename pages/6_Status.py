import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Setup project root import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from logic.disasters import get_all_disasters
from logic.resources import get_all_resources
from logic.needs import get_all_needs
from logic.allocations import get_all_allocations
from database.connection import get_db
from database.models import Disaster, Resource, ResourceNeed, Allocation
from sqlalchemy import func
from utils.ui_helpers import apply_custom_styles, render_hero

st.set_page_config(
    page_title="Status | Disaster Response",
    page_icon="📊",
    layout="wide"
)
apply_custom_styles()

render_hero(
    title="Live Operational Disaster Status",
    subtitle="Unified per-disaster logistics view combining supply staging, field demand, and fulfillment balance.",
    icon="📊"
)

disasters = get_all_disasters()

if not disasters:
    st.info("No disasters found in the system. Use 'Manage Disasters' to declare an incident.")
else:
    disaster_options = {
        f"{d['name']} ({d['type']} — {d['status'].upper()} — Sev: {d['severity']}/5)": d["id"]
        for d in disasters
    }
    selected_label = st.selectbox("Select Disaster Incident for In-Depth Assessment", list(disaster_options.keys()))
    disaster_id = disaster_options[selected_label]
    d = next(dis for dis in disasters if dis["id"] == disaster_id)

    # -------------------------------------------------------------
    # 1. INCIDENT HEADER & METRICS
    # -------------------------------------------------------------
    resources = get_all_resources(disaster_id=disaster_id)
    needs = get_all_needs(disaster_id=disaster_id)
    allocations = get_all_allocations(disaster_id=disaster_id)

    total_res_qty = sum(r["quantity"] for r in resources)
    avail_res_qty = sum(r["available"] for r in resources)
    total_need_qty = sum(n["quantity_needed"] for n in needs)
    open_needs_count = sum(1 for n in needs if n["status"] in ["pending", "partial"])
    fulfilled_needs_count = sum(1 for n in needs if n["status"] == "fulfilled")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Incident Status</div>
            <div class="metric-val" style="font-size: 1.4rem;">
                <span class="badge badge-{d['status']}">{d['status'].upper()}</span>
            </div>
            <div class="metric-sub">Severity Level {d['severity']}/5</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Staged Supplies</div>
            <div class="metric-val" style="color: #2a9d8f;">{avail_res_qty:,}</div>
            <div class="metric-sub">{total_res_qty:,} total ({len(resources)} batches)</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Demand Deficit / Open Needs</div>
            <div class="metric-val" style="color: #e63946;">{open_needs_count}</div>
            <div class="metric-sub">{total_need_qty:,} units requested</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Fulfilled Needs</div>
            <div class="metric-val" style="color: #457b9d;">{fulfilled_needs_count} / {len(needs)}</div>
            <div class="metric-sub">{len(allocations)} total allocations logged</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # -------------------------------------------------------------
    # 2. CATEGORY-BY-CATEGORY SUPPLY VS DEMAND BALANCE
    # -------------------------------------------------------------
    st.subheader("⚖️ Supply vs Demand Balance Analysis")

    # Aggregate by type
    all_categories = sorted(list(set([r["type"] for r in resources] + [n["type"] for n in needs])))

    balance_rows = []
    for cat in all_categories:
        avail_units = sum(r["available"] for r in resources if r["type"] == cat)
        needed_units = sum(n["quantity_needed"] for n in needs if n["type"] == cat)
        net_diff = avail_units - needed_units

        if needed_units == 0:
            status_tag = "Surplus Available"
        elif net_diff >= 0:
            status_tag = "Sufficient Supply"
        else:
            status_tag = "Deficit / Shortage"

        balance_rows.append({
            "Resource Category": cat,
            "Available Units": avail_units,
            "Units Needed": needed_units,
            "Net Balance": f"{'+' if net_diff > 0 else ''}{net_diff}",
            "Operational Balance": status_tag
        })

    if balance_rows:
        df_balance = pd.DataFrame(balance_rows)
        st.dataframe(df_balance, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -------------------------------------------------------------
    # 3. DETAILED BREAKDOWNS (RESOURCES, NEEDS, ALLOCATIONS)
    # -------------------------------------------------------------
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📦 Linked Resources", "⚠️ Open & Fulfilled Needs", "📜 Committed Allocations"])

    with sub_tab1:
        if not resources:
            st.info("No resources currently assigned to this disaster.")
        else:
            df_r = pd.DataFrame([
                {
                    "Type": r["type"],
                    "Available": r["available"],
                    "Total Quantity": r["quantity"],
                    "Allocated": r["allocated"],
                    "Provider": r["provider"],
                    "Location": f"{r['latitude']:.4f}, {r['longitude']:.4f}"
                }
                for r in resources
            ])
            st.dataframe(df_r, use_container_width=True, hide_index=True)

    with sub_tab2:
        if not needs:
            st.info("No needs currently recorded for this disaster.")
        else:
            df_n = pd.DataFrame([
                {
                    "Need Type": n["type"],
                    "Quantity Needed": n["quantity_needed"],
                    "Urgency": f"Level {n['urgency']}/5",
                    "Status": n["status"].upper(),
                    "Location": f"{n['latitude']:.4f}, {n['longitude']:.4f}",
                    "Logged Time": n["created_at"].strftime("%Y-%m-%d %H:%M") if n["created_at"] else "N/A"
                }
                for n in needs
            ])
            st.dataframe(df_n, use_container_width=True, hide_index=True)

    with sub_tab3:
        if not allocations:
            st.info("No allocations have been dispatched for this disaster yet.")
        else:
            df_a = pd.DataFrame([
                {
                    "Item Dispatched": a["need_type"],
                    "Quantity Allocated": a["quantity_allocated"],
                    "Source Provider": a["provider"],
                    "Timestamp": a["created_at"].strftime("%Y-%m-%d %H:%M:%S") if a["created_at"] else "N/A",
                    "Allocation ID": a["id"]
                }
                for a in allocations
            ])
            st.dataframe(df_a, use_container_width=True, hide_index=True)
