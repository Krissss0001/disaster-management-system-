"""UI Helpers and Shared CSS styling for the Disaster Response Coordination Platform."""
import streamlit as st

CUSTOM_CSS = """
<style>
    /* Global Font & Theme Polish */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 60%, #415a77 100%);
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 6px solid #e63946;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        margin: 0.35rem 0 0 0;
        color: #e0e1dd;
        font-size: 0.95rem;
    }

    /* Metric Card */
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.1rem 1.25rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 0.3rem;
    }
    .metric-val {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-ongoing { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
    .badge-contained { background-color: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .badge-resolved { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-pending { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
    .badge-partial { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }
    .badge-fulfilled { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }

    /* Map Card Container */
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
</style>
"""


def apply_custom_styles():
    """Inject custom CSS across pages."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, icon: str = "🚨"):
    """Render a unified aesthetic hero header."""
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
