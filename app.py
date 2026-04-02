"""
Real-Time Industry Insights Dashboard
=======================================
Production-level Streamlit app powered by FastMCP + SerpAPI.

Architecture:
  User → Streamlit UI → FastMCP Client → MCP Server → SerpAPI
       → Data Processing → AI Engine → Visualisation → PDF Export
"""

import streamlit as st
import asyncio
import json
import sys
import os

# ── Path & env setup ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastmcp import Client
import plotly.express as px
import plotly.graph_objects as go

# Local modules (same directory)
from ai_engine import (
    compute_stats,
    compute_brand_intelligence_score,
    detect_market_momentum,
    generate_predictions,
    generate_smart_alerts,
    generate_market_summary,
    explain_decision,
)
from pdf_report import generate_pdf_report

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Industry Insights · AI Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
#  CSS — Premium dark glassmorphism theme
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & Global ────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: linear-gradient(145deg, #05051a 0%, #0a0a2e 30%, #0f1035 60%, #130f30 100%);
}

/* ── Scrollbar ─────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(146,141,255,.3); border-radius: 3px; }

/* ── Hero ──────────────────────────────────────── */
.hero { text-align: center; padding: 1.8rem 0 .8rem; }
.hero h1 {
    font-size: 2.6rem; font-weight: 900; margin-bottom: .2rem;
    background: linear-gradient(90deg, #00d2ff 0%, #928dff 40%, #ff6ec4 80%, #ffc53d 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 6s ease-in-out infinite alternate;
}
@keyframes shimmer { 0%{filter:hue-rotate(0deg)} 100%{filter:hue-rotate(25deg)} }
.hero-sub { color: #6c7a96; font-size: .95rem; letter-spacing: .02em; }

/* ── Glass card ────────────────────────────────── */
.glass {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 16px; padding: 1.4rem;
    backdrop-filter: blur(14px);
    margin-bottom: 1rem;
    transition: transform .22s, box-shadow .22s;
}
.glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 44px rgba(0,210,255,.1);
}
.glass h3 { color:#e6f1ff; margin:0 0 .7rem; font-weight:700; }

/* ── Metric blocks ─────────────────────────────── */
.metric-card {
    text-align: center; padding: 1.1rem .8rem;
    border-radius: 14px;
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.06);
}
.metric-val {
    font-size: 1.55rem; font-weight: 800; color: #e6f1ff;
    line-height: 1.2;
}
.metric-lbl {
    font-size: .72rem; color: #6c7a96; text-transform: uppercase;
    letter-spacing: .06em; margin-top: .3rem;
}

/* ── Product rows ──────────────────────────────── */
.prod-row {
    display: flex; align-items: center; gap: .8rem;
    padding: .65rem .9rem; border-radius: 10px;
    background: rgba(255,255,255,.025);
    border: 1px solid rgba(255,255,255,.05);
    margin-bottom: .45rem; transition: background .18s;
}
.prod-row:hover { background: rgba(255,255,255,.06); }
.prod-name { flex:1; color:#ccd6f6; font-weight:500; font-size:.88rem; }
.badge {
    display: inline-block; padding: .2rem .6rem;
    border-radius: 999px; font-size: .78rem; font-weight: 600;
}
.b-price { background:rgba(0,210,255,.12); color:#00d2ff; }
.b-rating { background:rgba(255,199,0,.12); color:#ffc700; }
.b-na     { background:rgba(255,255,255,.05); color:#6c7a96; }

/* ── Alert cards ───────────────────────────────── */
.alert-card {
    padding: 1rem 1.2rem; border-radius: 12px;
    margin-bottom: .7rem;
    border-left: 4px solid;
}
.alert-positive { background:rgba(0,255,136,.06); border-color:#00ff88; }
.alert-warning  { background:rgba(255,71,87,.06); border-color:#ff4757; }
.alert-caution  { background:rgba(255,199,0,.06); border-color:#ffc700; }
.alert-info     { background:rgba(0,210,255,.06); border-color:#00d2ff; }
.alert-title { color:#e6f1ff; font-weight:700; font-size:.92rem; margin-bottom:.25rem; }
.alert-msg { color:#8892b0; font-size:.84rem; line-height:1.5; }

/* ── Chips ─────────────────────────────────────── */
.chip {
    display:inline-flex; align-items:center; gap:.35rem;
    padding:.3rem .75rem; border-radius:999px;
    font-size:.78rem; font-weight:600; margin-bottom:1rem;
}
.chip-ok  { background:rgba(0,255,136,.1); color:#00ff88; border:1px solid rgba(0,255,136,.2); }
.chip-err { background:rgba(255,71,87,.1); color:#ff4757; border:1px solid rgba(255,71,87,.2); }

/* ── Divider ───────────────────────────────────── */
.glow-div {
    height:2px; border:none; margin:1.4rem 0;
    background: linear-gradient(90deg, transparent, #928dff, transparent);
}

/* ── Score bar ─────────────────────────────────── */
.score-outer {
    height: 10px; border-radius: 5px;
    background: rgba(255,255,255,.06);
    overflow: hidden; margin: .3rem 0 .15rem;
}
.score-inner {
    height: 100%; border-radius: 5px;
    background: linear-gradient(90deg, #00d2ff, #928dff, #ff6ec4);
    transition: width .6s ease;
}

/* ── Hide defaults ─────────────────────────────── */
#MainMenu, footer { visibility: hidden; }

/* ── Tab styling ───────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,.03) !important;
    border-radius: 10px 10px 0 0 !important;
    border: 1px solid rgba(255,255,255,.06) !important;
    color: #8892b0 !important;
    font-weight: 600 !important; font-size: .85rem !important;
    padding: .5rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,210,255,.08) !important;
    color: #00d2ff !important;
    border-bottom: 2px solid #00d2ff !important;
}

/* ── Forms & Plotly ────────────────────────────── */
[data-testid="stForm"] { border-color: rgba(255,255,255,.1) !important; }
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* ── Global Text Visibility Overrides ─────────────────── */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #f8f9fa;
}
[data-testid="stMarkdownContainer"] blockquote p,
[data-testid="stMarkdownContainer"] blockquote span {
    color: #a0aabf !important;
}
[data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid #00d2ff !important;
    background: rgba(0, 210, 255, 0.05) !important;
    padding: 0.6rem 1rem !important;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
}

/* ── Chat Visibility Overrides ─────────────────── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    color: #f8f9fa !important;
}
[data-testid="stChatInput"] {
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    color: #111827 !important;
}


/* ── Sidebar ───────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(10,10,30,.92) !important;
    border-right: 1px solid rgba(255,255,255,.06) !important;
}
section[data-testid="stSidebar"] .stTextInput>div>div>input {
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    color: #ccd6f6 !important;
    border-radius: 10px !important;
}

/* ── Buttons ───────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #00d2ff, #928dff) !important;
    color: #050520 !important; font-weight: 700 !important;
    border: none !important; border-radius: 12px !important;
    padding: .6rem 1.8rem !important; font-size: .92rem !important;
    transition: transform .15s, box-shadow .15s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,210,255,.22) !important;
}

/* ── Download button ───────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #ff6ec4, #ffc53d) !important;
    color: #050520 !important; font-weight: 700 !important;
    border: none !important; border-radius: 12px !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(255,110,196,.22) !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  Hero
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <h1>🔬 Industry Insights</h1>
    <p class="hero-sub">AI-Powered Market Intelligence · MCP Architecture · Real-Time SerpAPI Data</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def parse_tool_result(result):
    """Extract Python object from FastMCP CallToolResult."""
    content_list = getattr(result, "content", None)
    if content_list is None:
        content_list = result if isinstance(result, list) else [result]
    for item in content_list:
        text = getattr(item, "text", None)
        if text is None and isinstance(item, dict):
            text = item.get("text")
        if text:
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
    return content_list


# Plotly dark theme
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#8892b0"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,.05)"),
)

BRAND_COLORS = [
    "#00d2ff", "#928dff", "#ff6ec4", "#ffc53d", "#00ff88",
    "#ff4757", "#70a1ff", "#7bed9f", "#eccc68", "#a29bfe",
]


# ═══════════════════════════════════════════════════════════════════════════
#  MCP Communication
# ═══════════════════════════════════════════════════════════════════════════

async def _fetch_multi_brand(client, brands_csv: str, product_type: str):
    raw = await client.call_tool("get_multi_brand_data", {
        "brand_names_csv": brands_csv,
        "product_type": product_type,
        "num_results": 6,
    })
    return parse_tool_result(raw)


async def _fetch_trends(client, query: str):
    raw = await client.call_tool("get_market_trends", {
        "query": query,
        "num_results": 20,
    })
    return parse_tool_result(raw)


async def run_full_analysis(brands: list[str], product_type: str):
    """Single MCP session → fetch brands + trends."""
    server = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    async with Client(server) as client:
        brand_task = _fetch_multi_brand(client, ",".join(brands), product_type)
        trend_task = _fetch_trends(client, f"best {product_type} brands")
        brand_data, trend_data = await asyncio.gather(brand_task, trend_task)
    return brand_data, trend_data


# ═══════════════════════════════════════════════════════════════════════════
#  Configuration Form
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("### 🎯 Analysis Configuration")
with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        brand_input = st.text_input(
            "Brands (comma-separated, 2–5)",
            value="Nike, Puma, Adidas",
            placeholder="e.g. Nike, Adidas, Puma",
        )
    with col2:
        product_type = st.text_input(
            "Product Category",
            value="shoes",
            placeholder="e.g. shoes, watches, laptops",
        )
    with col3:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        analyse_btn = st.button("🚀  Analyse Market", use_container_width=True)

st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  Execute analysis
# ═══════════════════════════════════════════════════════════════════════════
if analyse_btn:
    brands = [b.strip() for b in brand_input.split(",") if b.strip()]
    if len(brands) < 2:
        st.error("Enter at least 2 brands separated by commas.")
    elif len(brands) > 5:
        st.error("Maximum 5 brands allowed.")
    else:
        with st.spinner("⚡ Connecting to MCP server · Fetching live market data …"):
            try:
                brand_data, trend_raw = asyncio.run(
                    run_full_analysis(brands, product_type.strip())
                )

                # ── Compute derived analytics ────────────────────────
                trend_freq = trend_raw.get("brand_frequency", {}) if isinstance(trend_raw, dict) else {}
                trend_results = trend_raw.get("results", []) if isinstance(trend_raw, dict) else []

                b_stats = {}
                for b in brands:
                    prods = brand_data.get(b, []) if isinstance(brand_data, dict) else []
                    b_stats[b] = compute_stats(prods)

                max_t = max(trend_freq.values()) if trend_freq else 1
                b_scores = {}
                for b in brands:
                    tf = trend_freq.get(b, 0)
                    # Try case-insensitive match
                    if tf == 0:
                        for tk, tv in trend_freq.items():
                            if tk.lower() == b.lower():
                                tf = tv
                                break
                    b_scores[b] = compute_brand_intelligence_score(b_stats[b], tf, max_t)

                momentum = detect_market_momentum(trend_freq)
                preds = generate_predictions(b_scores, {b: trend_freq.get(b, 0) for b in brands})
                alerts = generate_smart_alerts(
                    brand_data if isinstance(brand_data, dict) else {},
                    b_stats,
                )
                mkt_summary = generate_market_summary(b_stats, trend_freq, b_scores, preds, alerts)

                # ── Persist to session ────────────────────────────────
                st.session_state.update({
                    "brands": brands,
                    "product_type": product_type.strip(),
                    "brand_data": brand_data,
                    "trend_freq": trend_freq,
                    "trend_results": trend_results,
                    "b_stats": b_stats,
                    "b_scores": b_scores,
                    "momentum": momentum,
                    "preds": preds,
                    "alerts": alerts,
                    "mkt_summary": mkt_summary,
                    "ok": True,
                })
            except Exception as exc:
                st.session_state["ok"] = False
                st.session_state["err"] = str(exc)


# ═══════════════════════════════════════════════════════════════════════════
#  Render dashboard (from session state)
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.get("ok"):
    brands       = st.session_state["brands"]
    brand_data   = st.session_state["brand_data"]
    trend_freq   = st.session_state["trend_freq"]
    trend_results = st.session_state["trend_results"]
    b_stats      = st.session_state["b_stats"]
    b_scores     = st.session_state["b_scores"]
    momentum     = st.session_state["momentum"]
    preds        = st.session_state["preds"]
    alerts       = st.session_state["alerts"]
    mkt_summary  = st.session_state["mkt_summary"]
    prod_type    = st.session_state["product_type"]

    st.markdown('<div class="chip chip-ok">● Connected to MCP Server — Live Data</div>', unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Brand Comparison",
        "📈 Market Trends",
        "🤖 AI Insights",
        "📊 Advanced Analytics",
        "🔮 Predictions & Alerts",
        "📄 Export Report",
        "💬 AI Chat Analyst",
    ])

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 1 — Brand Comparison
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 🏷️ Multi-Brand Product Comparison")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        # ── Stat cards ───────────────────────────────────────────────
        cols = st.columns(len(brands))
        for i, b in enumerate(brands):
            s = b_stats[b]
            score = b_scores[b]
            with cols[i]:
                ap = f"${s['avg_price']:.2f}" if s.get("avg_price") else "N/A"
                ar = f"{s['avg_rating']:.1f} ⭐" if s.get("avg_rating") else "N/A"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val" style="font-size:1.1rem; color:{BRAND_COLORS[i % len(BRAND_COLORS)]}">{b}</div>
                    <div class="metric-lbl" style="margin-top:.6rem;">Avg Price</div>
                    <div class="metric-val" style="font-size:1.3rem;">{ap}</div>
                    <div class="metric-lbl" style="margin-top:.5rem;">Avg Rating</div>
                    <div class="metric-val" style="font-size:1.3rem;">{ar}</div>
                    <div class="metric-lbl" style="margin-top:.5rem;">Intelligence</div>
                    <div class="metric-val" style="font-size:1.3rem; color:{BRAND_COLORS[i % len(BRAND_COLORS)]}">{score['total_score']}/100 ({score['grade']})</div>
                    <div class="score-outer"><div class="score-inner" style="width:{score['total_score']}%"></div></div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        # ── Product cards per brand ──────────────────────────────────
        prod_cols = st.columns(min(len(brands), 3))
        for i, b in enumerate(brands):
            with prod_cols[i % len(prod_cols)]:
                st.markdown(f'<div class="glass"><h3>🛍️ {b}</h3>', unsafe_allow_html=True)
                prods = brand_data.get(b, []) if isinstance(brand_data, dict) else []
                if prods:
                    for p in prods:
                        price = p.get("price", "")
                        rating = p.get("rating")
                        pb = f'<span class="badge b-price">{price}</span>' if price and price != "N/A" else '<span class="badge b-na">—</span>'
                        rb = f'<span class="badge b-rating">⭐ {rating}</span>' if rating else '<span class="badge b-na">—</span>'
                        st.markdown(f"""
                        <div class="prod-row">
                            <span class="prod-name">{p.get("title","Untitled")}</span>
                            {pb} {rb}
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("No products found.")
                st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 2 — Market Trends
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📈 Market Trend Analysis")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        if trend_freq:
            # Bar chart
            sorted_items = sorted(trend_freq.items(), key=lambda x: x[1], reverse=True)
            chart_brands = [x[0] for x in sorted_items]
            chart_counts = [x[1] for x in sorted_items]
            fig_bar = go.Figure(go.Bar(
                x=chart_brands, y=chart_counts,
                marker=dict(
                    color=chart_counts,
                    colorscale=[[0, "#0ea5e9"], [0.5, "#928dff"], [1, "#ff6ec4"]],
                    line=dict(width=0),
                    cornerradius=6,
                ),
                text=chart_counts, textposition="outside",
                textfont=dict(color="#ccd6f6", size=12, family="Inter"),
            ))
            fig_bar.update_layout(
                title="Brand Search Frequency",
                **PLOTLY_LAYOUT,
                yaxis_title="Mentions",
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Pie chart
            total = sum(chart_counts)
            fig_pie = go.Figure(go.Pie(
                labels=chart_brands, values=chart_counts,
                hole=0.5,
                marker=dict(colors=BRAND_COLORS[:len(chart_brands)]),
                textinfo="label+percent",
                textfont=dict(size=11, family="Inter"),
            ))
            fig_pie.update_layout(
                title="Market Share Distribution",
                **PLOTLY_LAYOUT,
                height=400,
                showlegend=True,
                legend=dict(font=dict(color="#8892b0")),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Momentum table
        if momentum:
            st.markdown("#### 🚀 Market Momentum")
            for m in momentum:
                st.markdown(f"""
                <div class="prod-row">
                    <span class="prod-name" style="font-weight:700;">{m['brand']}</span>
                    <span class="badge b-price">{m['status']}</span>
                    <span class="badge b-rating">Strength: {m['strength']}%</span>
                </div>""", unsafe_allow_html=True)

        # Top search results
        if trend_results:
            st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)
            st.markdown("#### 🔗 Top Organic Results")
            for tr in trend_results[:8]:
                link = tr.get('link', '#')
                st.markdown(f"""
                <div class="prod-row">
                    <a href="{link}" target="_blank" class="prod-name" style="text-decoration:none;">{tr.get('title','')}</a>
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 3 — AI Insights
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🤖 AI Market Analyst")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        # Confidence gauge
        conf = mkt_summary.get("confidence", 0)
        st.markdown(f"""
        <div class="glass" style="text-align:center; padding:1.5rem;">
            <div class="metric-lbl">Analysis Confidence</div>
            <div class="metric-val" style="font-size:2.2rem;
                 background:linear-gradient(90deg,#00d2ff,#928dff);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                {conf:.0f}%
            </div>
            <div class="score-outer" style="max-width:300px; margin:.5rem auto;">
                <div class="score-inner" style="width:{conf}%"></div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Summary
        st.markdown(f"""
        <div class="glass">
            <h3>📋 Market Summary</h3>
            <p style="color:#8892b0; line-height:1.7; font-size:.9rem;">{mkt_summary.get('summary','')}</p>
        </div>""", unsafe_allow_html=True)

        # Recommendation
        best = mkt_summary.get("best_brand")
        st.markdown(f"""
        <div class="glass">
            <h3>💡 Recommendation</h3>
            <p style="color:#8892b0; line-height:1.7; font-size:.9rem;">{mkt_summary.get('recommendation','')}</p>
        </div>""", unsafe_allow_html=True)

        # Strategic Insight
        st.markdown(f"""
        <div class="glass">
            <h3>🎯 Strategic Insight</h3>
            <p style="color:#8892b0; line-height:1.7; font-size:.9rem;">{mkt_summary.get('strategic_insight','')}</p>
        </div>""", unsafe_allow_html=True)

        # XAI explanations
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)
        st.markdown("### 🧠 Explainable AI — Score Breakdown")
        xai_tabs = st.tabs([f"🔍 {b}" for b in brands])
        for i, b in enumerate(brands):
            with xai_tabs[i]:
                explanation = explain_decision(b_scores[b], b)
                st.markdown(explanation)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 4 — Advanced Analytics
    # ══════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 📊 Advanced Visualisations")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        # ── Price vs Rating Scatter ──────────────────────────────────
        scatter_data = []
        for b in brands:
            prods = brand_data.get(b, []) if isinstance(brand_data, dict) else []
            for p in prods:
                from ai_engine import parse_price
                pv = parse_price(p.get("price"))
                rv = p.get("rating")
                if pv and rv:
                    scatter_data.append({
                        "Brand": b, "Price": pv,
                        "Rating": float(rv), "Product": p.get("title", "")[:40],
                    })

        if scatter_data:
            import pandas as pd
            df_scatter = pd.DataFrame(scatter_data)
            fig_scat = px.scatter(
                df_scatter, x="Price", y="Rating", color="Brand",
                hover_data=["Product"],
                color_discrete_sequence=BRAND_COLORS,
                title="Price vs Rating — All Products",
            )
            fig_scat.update_layout(**PLOTLY_LAYOUT, height=450)
            fig_scat.update_traces(marker=dict(size=12, line=dict(width=1, color="#0a0a2e")))
            st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.info("Not enough product data for scatter plot.")

        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        # ── Brand Intelligence Radar ─────────────────────────────────
        st.markdown("#### 🕸️ Brand Intelligence Radar")
        categories = ["Rating", "Price", "Trend", "Value"]
        fig_radar = go.Figure()
        for i, b in enumerate(brands):
            bd = b_scores[b].get("breakdown", {})
            vals = [
                (bd.get("rating", {}).get("score", 0) / 35) * 100,
                (bd.get("price", {}).get("score", 0) / 25) * 100,
                (bd.get("trend", {}).get("score", 0) / 25) * 100,
                (bd.get("value", {}).get("score", 0) / 15) * 100,
            ]
            vals.append(vals[0])  # close the polygon
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=categories + [categories[0]],
                fill="toself", name=b,
                fillcolor=f"rgba({int(BRAND_COLORS[i % len(BRAND_COLORS)][1:3],16)},"
                          f"{int(BRAND_COLORS[i % len(BRAND_COLORS)][3:5],16)},"
                          f"{int(BRAND_COLORS[i % len(BRAND_COLORS)][5:7],16)},0.15)",
                line=dict(color=BRAND_COLORS[i % len(BRAND_COLORS)], width=2),
            ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,.06)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,.06)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            height=450, showlegend=True,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # ── Score comparison bar ─────────────────────────────────────
        st.markdown("#### 🏅 Brand Intelligence Score Ranking")
        sorted_brands = sorted(brands, key=lambda b: b_scores[b]["total_score"], reverse=True)
        fig_rank = go.Figure(go.Bar(
            y=sorted_brands,
            x=[b_scores[b]["total_score"] for b in sorted_brands],
            orientation="h",
            marker=dict(
                color=[b_scores[b]["total_score"] for b in sorted_brands],
                colorscale=[[0, "#ff4757"], [0.5, "#ffc53d"], [1, "#00ff88"]],
                cornerradius=6,
            ),
            text=[f'{b_scores[b]["total_score"]} ({b_scores[b]["grade"]})' for b in sorted_brands],
            textposition="outside",
            textfont=dict(color="#ccd6f6", size=12, family="Inter"),
        ))
        fig_rank.update_layout(
            **PLOTLY_LAYOUT, height=50 + len(brands) * 55,
            xaxis_title="Intelligence Score (0-100)",
            xaxis_range=[0, 110],
            showlegend=False,
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 5 — Predictions & Alerts
    # ══════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown("### 🔮 Market Prediction Engine")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        if preds:
            # Prediction chart
            fig_pred = go.Figure(go.Bar(
                x=[p["brand"] for p in preds],
                y=[p["prediction_score"] for p in preds],
                marker=dict(
                    color=[p["prediction_score"] for p in preds],
                    colorscale=[[0, "#ff4757"], [0.5, "#ffc53d"], [1, "#00ff88"]],
                    cornerradius=6,
                ),
                text=[p["outlook"] for p in preds],
                textposition="outside",
                textfont=dict(color="#ccd6f6", size=10, family="Inter"),
            ))
            fig_pred.update_layout(
                title="Predicted Market Performance",
                **PLOTLY_LAYOUT,
                yaxis_title="Prediction Score",
                yaxis_range=[0, 110],
                height=400,
                showlegend=False,
            )
            st.plotly_chart(fig_pred, use_container_width=True)

            # Prediction details
            pred_cols = st.columns(min(len(preds), 3))
            for i, p in enumerate(preds):
                with pred_cols[i % len(pred_cols)]:
                    pcolor = "#00ff88" if p["prediction_score"] > 70 else "#ffc53d" if p["prediction_score"] > 50 else "#ff4757"
                    st.markdown(f"""
                    <div class="glass" style="text-align:center;">
                        <div class="metric-val" style="color:{pcolor}; font-size:1.2rem;">{p['brand']}</div>
                        <div class="metric-val" style="font-size:2rem; color:{pcolor};">{p['prediction_score']}</div>
                        <div class="metric-lbl">Prediction Score</div>
                        <div style="color:#8892b0; font-size:.82rem; margin-top:.5rem;">{p['outlook']}</div>
                        <div class="score-outer" style="margin-top:.5rem;">
                            <div class="score-inner" style="width:{p['prediction_score']}%"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)
        st.markdown("### ⚠️ Smart Insight Alerts")

        if alerts:
            for a in alerts:
                sev = a.get("severity", "info")
                css_class = f"alert-{sev}" if sev in ("positive", "warning", "caution", "info") else "alert-info"
                st.markdown(f"""
                <div class="alert-card {css_class}">
                    <div class="alert-title">{a.get('icon','')} {a.get('title','')}</div>
                    <div class="alert-msg">{a.get('message','')}</div>
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 6 — Export Report
    # ══════════════════════════════════════════════════════════════════════
    with tab6:
        st.markdown("### 📄 Export Market Analysis Report")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="glass" style="text-align:center; padding:2rem;">
            <h3 style="font-size:1.4rem;">📑 Professional PDF Report</h3>
            <p style="color:#8892b0; font-size:.9rem; max-width:500px; margin:.5rem auto;">
                Download a comprehensive market analysis report containing brand
                comparisons, trend data, intelligence scores, AI insights,
                predictions, and smart alerts — ready for presentations.
            </p>
        </div>""", unsafe_allow_html=True)

        # Report preview summary
        prevc1, prevc2, prevc3 = st.columns(3)
        with prevc1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{len(brands)}</div>
                <div class="metric-lbl">Brands Analysed</div>
            </div>""", unsafe_allow_html=True)
        with prevc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{prod_type.title()}</div>
                <div class="metric-lbl">Product Category</div>
            </div>""", unsafe_allow_html=True)
        with prevc3:
            best_b = mkt_summary.get("best_brand", "—")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color:#00ff88;">{best_b}</div>
                <div class="metric-lbl">Top Pick</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        try:
            pdf_bytes = generate_pdf_report(
                brands=brands,
                product_type=prod_type,
                brand_stats=b_stats,
                trend_data=trend_freq,
                brand_scores=b_scores,
                predictions=preds,
                alerts=alerts,
                market_summary=mkt_summary,
            )
            st.download_button(
                label="⬇️  Download Full Analysis (PDF)",
                data=pdf_bytes,
                file_name=f"industry_report_{prod_type}_{'-'.join(brands)}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

        st.markdown("""
        <div style="color:#6c7a96; font-size:.78rem; text-align:center; margin-top:1rem;">
            Report includes: Brand Comparison · Market Trends · AI Insights · Intelligence Scores · Predictions · Alerts
        </div>""", unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════
    #  TAB 7 — AI Chat Analyst
    # ══════════════════════════════════════════════════════════════════════
    with tab7:
        st.markdown("### 💬 AI Chat Analyst")
        st.markdown('<div class="glow-div"></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background:rgba(0,210,255,.08); padding:1rem; border-radius:12px; margin-bottom:1.5rem; text-align:center;">
            This bot operates using a deterministic NLP engine. It uses <b>only</b> the live computations from your SerpAPI crawl. No LLM hallucinations!
        </div>""", unsafe_allow_html=True)

        from chat_module import ChatAnalyst
        analyst = ChatAnalyst(
            brands, b_stats, trend_freq, b_scores, preds, alerts, mkt_summary
        )

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Hello! I am your AI Market Analyst. I only use real-time, mathematically computed data—no hallucinations. How can I help you today?", "confidence": "High"}
            ]
            st.session_state.chat_context = {}

        # Display suggested questions
        st.markdown("**Suggested Questions:**")
        
        def trigger_chat(q):
            st.session_state.submit_q = q
            
        sc1, sc2, sc3 = st.columns(3)
        sc1.button("🏆 Which brand is best?", on_click=trigger_chat, args=("Which brand is best?",), use_container_width=True)
        sc2.button("⚠️ Any overpriced?", on_click=trigger_chat, args=("Overpriced brands?",), use_container_width=True)
        sc3.button("🔮 Predict leader", on_click=trigger_chat, args=("Predict future leader",), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Display chat history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and "confidence" in msg:
                    st.markdown(f"<div style='font-size:0.75rem; color:#6c7a96;'>Confidence Level: {msg['confidence']}</div>", unsafe_allow_html=True)

        # Input gathering logic
        query = st.chat_input("Ask about rankings, reasons, or trends...")
        
        # Override with button click
        if "submit_q" in st.session_state and st.session_state.submit_q:
            query = st.session_state.submit_q
            del st.session_state.submit_q

        if query:
            # Add user msg instantly
            st.session_state.chat_messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            
            # Generate and stream response
            with st.chat_message("assistant"):
                resp, new_ctx = analyst.respond(query, st.session_state.chat_context)
                st.session_state.chat_context = new_ctx
                st.markdown(resp)
                st.markdown(f"<div style='font-size:0.75rem; color:#6c7a96;'>Confidence Level: {analyst.confidence}</div>", unsafe_allow_html=True)
                st.session_state.chat_messages.append({"role": "assistant", "content": resp, "confidence": analyst.confidence})


# ═══════════════════════════════════════════════════════════════════════════
#  Error / Landing state
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.get("ok") is False:
    st.markdown('<div class="chip chip-err">✕ Connection Failed</div>', unsafe_allow_html=True)
    st.error(f"Error: {st.session_state.get('err', 'Unknown')}")
else:
    st.markdown("""
    <div class="glass" style="text-align:center; padding:3rem 2rem;">
        <h3 style="font-size:1.4rem; color:#e6f1ff;">
            👈 Configure brands in the sidebar and hit <span style="color:#00d2ff;">Analyse Market</span>
        </h3>
        <p style="color:#6c7a96; margin-top:.6rem; line-height:1.6; max-width:550px; margin-left:auto; margin-right:auto;">
            The dashboard connects to the <b>FastMCP server</b>, fetches real-time
            Google Shopping and Search data via <b>SerpAPI</b>, runs AI-powered
            analysis, and presents comprehensive market intelligence — including
            brand scoring, trend momentum, predictions, and a downloadable PDF report.
        </p>
    </div>
    """, unsafe_allow_html=True)
