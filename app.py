"""
app.py — Overtone Explainability Widget
========================================
Run with:  streamlit run app.py

This is the UI layer only.
Data comes from data.py (placeholder) → swap
for BigQuery queries when access is ready.
"""

import streamlit as st
import plotly.graph_objects as go
from data import get_stories, score_to_label

# ── PAGE CONFIG ───────────────────────────────
st.set_page_config(
    page_title="Overtone · Insights",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── GLOBAL STYLES ─────────────────────────────
st.markdown("""
<style>
  /* Import font */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

  /* Base */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
  }
  .main .block-container {
    padding: 1.5rem 2rem 2rem;
    max-width: 1100px;
  }

  /* Hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }

  /* ── BRAND HEADER ── */
  .ovtn-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1rem;
    margin-bottom: 0.25rem;
    border-bottom: 1px solid #e4e4ea;
  }
  .ovtn-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 600;
    color: #1a1a2e;
  }
  .ovtn-logo-ring {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: conic-gradient(from 0deg, #a78bfa, #6c63e0, #38bdf8, #a78bfa);
    display: inline-block;
  }
  .ovtn-context {
    font-size: 12px;
    color: #9898b0;
    font-style: italic;
  }

  /* ── PAGE TITLE ── */
  .page-title {
    font-size: 26px;
    font-weight: 300;
    color: #1a1a2e;
    letter-spacing: -0.5px;
    margin: 0.75rem 0 1.25rem;
  }

  /* ── SCORE BADGE ── */
  .score-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.03em;
  }
  .score-high   { background: #eaf6f0; color: #1a7a4a; }
  .score-medium { background: #fef8e6; color: #8a6000; }
  .score-low    { background: #f4f4f6; color: #888;    }

  /* ── SIGNAL BADGE ── */
  .sig-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    white-space: nowrap;
  }
  .sig-green  { background: #eaf6f0; color: #1a7a4a; }
  .sig-amber  { background: #fef8e6; color: #8a6000; }
  .sig-red    { background: #fdecea; color: #c0392b; }
  .sig-purple { background: rgba(108,99,224,0.10); color: #5a52cc; }
  .sig-grey   { background: #f4f4f6; color: #888; border: 1px solid #e4e4ea; }

  /* ── SIGNAL ROW ── */
  .signal-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 7px;
    border: 1px solid #e4e4ea;
    background: #f7f7f9;
    margin-bottom: 6px;
  }
  .signal-icon { font-size: 14px; flex-shrink: 0; }
  .signal-text { flex: 1; min-width: 0; }
  .signal-name { font-size: 12px; font-weight: 500; color: #1a1a2e; }
  .signal-detail { font-size: 11px; color: #9898b0; }
  .signal-badge-wrap { flex-shrink: 0; }

  /* ── CONCEPT TAGS ── */
  .concepts-wrap { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
  .concept-tag {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    background: #f4f4f6;
    border: 1px solid #e4e4ea;
    color: #5a5a7a;
  }
  .concept-matched {
    background: rgba(108,99,224,0.09);
    border-color: rgba(108,99,224,0.25);
    color: #5a52cc;
    font-weight: 500;
  }

  /* ── VERDICT BOX ── */
  .verdict-box {
    padding: 10px 14px;
    border-left: 3px solid #6c63e0;
    border-radius: 0 7px 7px 0;
    background: rgba(108,99,224,0.06);
    font-size: 13px;
    line-height: 1.6;
    color: #3a3a5a;
    margin-bottom: 14px;
  }

  /* ── SELECTED STORY HEADER ── */
  .story-header {
    background: #6c63e0;
    border-radius: 8px 8px 0 0;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0;
  }
  .story-header-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.75);
  }
  .story-header-score {
    font-size: 13px;
    font-weight: 700;
    color: white;
    background: rgba(255,255,255,0.18);
    padding: 3px 10px;
    border-radius: 20px;
  }

  /* ── STORY PANEL BODY ── */
  .story-panel-body {
    border: 1px solid #e4e4ea;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 14px 16px;
    background: white;
    margin-bottom: 14px;
  }
  .story-source {
    font-size: 11px;
    color: #9898b0;
    margin-bottom: 4px;
  }
  .story-headline {
    font-size: 15px;
    font-weight: 500;
    color: #1a1a2e;
    line-height: 1.4;
    margin-bottom: 12px;
  }

  /* ── TABLE ROW STYLING ── */
  div[data-testid="stDataFrame"] table {
    font-size: 12px !important;
  }

  /* ── SECTION LABEL ── */
  .section-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #9898b0;
    margin-bottom: 8px;
    margin-top: 4px;
  }

  /* ── CTA BUTTONS ── */
  .stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-radius: 7px !important;
    padding: 6px 14px !important;
  }

  /* Divider */
  hr { border-color: #e4e4ea; margin: 1rem 0; }

  /* Plotly chart background */
  .js-plotly-plot { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── LOAD DATA ────────────────────────────────
stories = get_stories()

# ── SESSION STATE ─────────────────────────────
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None


# ── HELPERS ──────────────────────────────────
def score_class(score: float) -> str:
    if score >= 0.08: return "score-high"
    if score >= 0.04: return "score-medium"
    return "score-low"

def sig_class(color: str) -> str:
    return f"sig-{color}"

def render_badge(text: str, css_class: str) -> str:
    return f'<span class="sig-badge {css_class}">{text}</span>'

def render_score_badge(score: float) -> str:
    label, _ = score_to_label(score)
    css = score_class(score)
    return f'<span class="score-badge {css}">{label} · {score:.4f}</span>'


# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown("""
<div class="ovtn-header">
  <div class="ovtn-logo">
    <div class="ovtn-logo-ring"></div>
    Overtone
  </div>
  <div class="ovtn-context">Insights · Monitor · Brand: Coca-Cola · Market: Japan · 25 janv – 11 févr 2026</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Insights</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════
scores = [s["score"] for s in stories]
labels = [s["source"] for s in stories]
dates  = [s["date"]   for s in stories]
ids    = [s["id"]     for s in stories]

# Marker colors — highlight selected
marker_colors = []
marker_sizes  = []
for s in stories:
    if s["id"] == st.session_state.selected_id:
        marker_colors.append("#6c63e0")
        marker_sizes.append(12)
    elif s["score"] >= 0.08:
        marker_colors.append("#1a7a4a")
        marker_sizes.append(9)
    elif s["score"] >= 0.04:
        marker_colors.append("#6c63e0")
        marker_sizes.append(8)
    else:
        marker_colors.append("#b0b0c8")
        marker_sizes.append(7)

fig = go.Figure()

# Area fill
fig.add_trace(go.Scatter(
    x=list(range(len(stories))),
    y=scores,
    fill="tozeroy",
    fillcolor="rgba(108,99,224,0.08)",
    line=dict(color="#6c63e0", width=2),
    mode="lines+markers",
    marker=dict(
        color=marker_colors,
        size=marker_sizes,
        line=dict(color="white", width=2),
    ),
    customdata=[[s["id"], s["headline"][:55] + "…", s["source"]] for s in stories],
    hovertemplate=(
        "<b>%{customdata[1]}</b><br>"
        "%{customdata[2]}<br>"
        "Score: %{y:.4f}<br>"
        "<i>Click to see why →</i>"
        "<extra></extra>"
    ),
    name="Relevance Score",
))

fig.update_layout(
    height=210,
    margin=dict(l=40, r=20, t=20, b=40),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(
        tickmode="array",
        tickvals=list(range(len(stories))),
        ticktext=[s["date"].replace(" 2026", "") for s in stories],
        tickfont=dict(size=10, color="#9898b0"),
        gridcolor="#f0f0f4",
        showline=False,
    ),
    yaxis=dict(
        title=dict(text="recommendation_level", font=dict(size=10, color="#9898b0")),
        tickfont=dict(size=10, color="#9898b0"),
        gridcolor="#f0f0f4",
        showline=False,
        tickformat=".3f",
    ),
    showlegend=False,
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#6c63e0",
        font_size=12,
        font_family="Inter",
    ),
)

# Render chart — capture click via plotly_click event
chart_event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    key="main_chart",
    selection_mode="points",
)

# Handle graph point click
# st.plotly_chart returns an object (not dict) in Streamlit >= 1.33
try:
    points = chart_event.selection.points if chart_event else []
    if points:
        pt_idx = points[0]["point_index"]
        clicked_id = stories[pt_idx]["id"]
        if st.session_state.selected_id != clicked_id:
            st.session_state.selected_id = clicked_id
            st.rerun()
except Exception:
    pass


# ══════════════════════════════════════════════
# TWO COLUMNS: TABLE (left) + WIDGET (right)
# ══════════════════════════════════════════════
col_table, col_widget = st.columns([1.1, 1], gap="large")


# ── LEFT: ARTICLE TABLE ──────────────────────
with col_table:
    st.markdown('<div class="section-label">Articles · sorted by recommendation_level</div>',
                unsafe_allow_html=True)

    for s in stories:
        is_selected = (s["id"] == st.session_state.selected_id)
        label, _ = score_to_label(s["score"])
        badge_html = f'<span class="score-badge {score_class(s["score"])}">{label}</span>'

        # Build a clickable row
        with st.container():
            cols = st.columns([0.18, 1, 0.35])

            # Row number + score badge
            with cols[0]:
                st.markdown(
                    f'<div style="padding-top:10px;font-size:11px;color:#9898b0;">'
                    f'{stories.index(s)+1}.</div>',
                    unsafe_allow_html=True,
                )

            # Headline
            with cols[1]:
                # Highlight selected
                bg = "background:rgba(108,99,224,0.07);border-radius:6px;padding:6px 8px;border-left:3px solid #6c63e0;" if is_selected else "padding:6px 0;"
                st.markdown(
                    f'<div style="{bg}">'
                    f'<div style="font-size:12.5px;font-weight:{"500" if is_selected else "400"};'
                    f'color:{"#5a52cc" if is_selected else "#1a1a2e"};line-height:1.35;">'
                    f'{s["headline"]}</div>'
                    f'<div style="font-size:11px;color:#9898b0;margin-top:2px;">'
                    f'{s["source"]} · {s["date"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # Score + button
            with cols[2]:
                st.markdown(
                    f'<div style="padding-top:8px;">{badge_html}<br>'
                    f'<span style="font-size:10px;color:#b0b0c8;font-family:monospace;">'
                    f'{s["score"]:.7f}…</span></div>',
                    unsafe_allow_html=True,
                )

            # Click button — invisible label, full row feel
            if st.button(
                "Why this score →" if not is_selected else "✓ Selected",
                key=f"row_btn_{s['id']}",
                type="secondary" if not is_selected else "primary",
                use_container_width=True,
            ):
                st.session_state.selected_id = s["id"] if not is_selected else None
                st.rerun()

        st.divider()


# ── RIGHT: EXPLAINABILITY WIDGET ─────────────
with col_widget:
    st.markdown('<div class="section-label">Explainability</div>', unsafe_allow_html=True)

    if st.session_state.selected_id is None:
        # Empty state
        st.markdown("""
        <div style="
          border: 2px dashed #e4e4ea;
          border-radius: 10px;
          padding: 40px 24px;
          text-align: center;
          color: #9898b0;
          margin-top: 8px;
        ">
          <div style="font-size: 28px; margin-bottom: 10px;">⬡</div>
          <div style="font-size: 13px; font-weight: 500; margin-bottom: 6px; color: #5a5a7a;">
            Select a story to see why Overtone scored it
          </div>
          <div style="font-size: 12px; line-height: 1.6;">
            Click any row in the table<br>or any point on the graph above
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Find selected story
        story = next((s for s in stories if s["id"] == st.session_state.selected_id), None)

        if story:
            label, color_hex = score_to_label(story["score"])

            # ── Purple stripe header
            st.markdown(f"""
            <div class="story-header">
              <span class="story-header-label">Why this score</span>
              <span class="story-header-score">{label} · {story['score']:.4f}</span>
            </div>
            """, unsafe_allow_html=True)

            # ── Source + headline
            st.markdown(f"""
            <div class="story-panel-body">
              <div class="story-source">{story['source']} · {story['date']}</div>
              <div class="story-headline">{story['headline']}</div>
            """, unsafe_allow_html=True)

            # ── Verdict
            # Convert **bold** markdown to <strong> for HTML rendering
            verdict_html = story["verdict"].replace("**", "<|||>")
            parts = verdict_html.split("<|||>")
            verdict_rendered = ""
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    verdict_rendered += f"<strong>{part}</strong>"
                else:
                    verdict_rendered += part

            st.markdown(f"""
              <div class="verdict-box">{verdict_rendered}</div>
            """, unsafe_allow_html=True)

            # ── Signals
            st.markdown('<div class="section-label" style="margin-top:0;">Scoring signals</div>',
                        unsafe_allow_html=True)

            signals_html = ""
            for sig in story["signals"]:
                badge = render_badge(sig["badge"], sig_class(sig["color"]))
                signals_html += f"""
                <div class="signal-row">
                  <span class="signal-icon">{sig['icon']}</span>
                  <div class="signal-text">
                    <div class="signal-name">{sig['name']}</div>
                    <div class="signal-detail">{sig['detail']}</div>
                  </div>
                  <div class="signal-badge-wrap">{badge}</div>
                </div>
                """
            st.markdown(signals_html, unsafe_allow_html=True)

            # ── Concepts
            st.markdown('<div class="section-label">Concepts detected</div>',
                        unsafe_allow_html=True)

            concepts_html = '<div class="concepts-wrap">'
            for c in story["concepts"]:
                cls = "concept-matched" if c in story["matched"] else "concept-tag"
                concepts_html += f'<span class="concept-tag {cls}">{c}</span>'
            concepts_html += "</div>"
            st.markdown(concepts_html + "</div>", unsafe_allow_html=True)  # close story-panel-body

            # ── CTAs
            st.markdown("<br>", unsafe_allow_html=True)
            cta_col1, cta_col2 = st.columns(2)
            with cta_col1:
                st.link_button(
                    "Article Deepdive →",
                    url=story["url"],
                    use_container_width=True,
                    type="primary",
                )
            with cta_col2:
                if st.button(
                    "Did we get it wrong?",
                    key="feedback_btn",
                    use_container_width=True,
                ):
                    st.toast("Feedback recorded — thank you!", icon="✓")

            # ── Deselect
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back to all stories", key="deselect_btn"):
                st.session_state.selected_id = None
                st.rerun()
