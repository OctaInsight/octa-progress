"""Octa Project Progress Tracker — Partner Map (with HTML export for website)."""
import streamlit as st

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, DARK)
from modules.database import get_project, get_project_partners
from modules.charts import chart_partner_map, fig_to_html
from config import DARK as D

st.set_page_config(page_title="Partner Map — Octa", page_icon="🌍",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj    = get_project(sel_pid)
acronym = proj.get("acronym","") or sel_pid
muted   = D["muted"]; acc = D["accent"]

page_header("Partner Map",
            f"{acronym} — Interactive partner country map, embeddable in your website",
            "🌍")
if st.button("← Dashboard"): st.switch_page("app.py")

partners = get_project_partners(sel_pid)

if not partners:
    st.info("No partner data found. Make sure partners are linked to this proposal "
            "and have country information in the Partner Network app.")
    st.stop()

# ── Partner list ──────────────────────────────────────────────────────────────
section_label(f"👥 Project Partners ({len(partners)})")

pc_cols = st.columns(4)
for i, p in enumerate(partners):
    with pc_cols[i % 4]:
        is_coord = p.get("is_coordinator", False)
        name     = p.get("full_name","") or p.get("short_name","")
        country  = p.get("country","")
        ptype    = p.get("partner_type","")
        logo     = p.get("logo_url","")
        border_c = acc if is_coord else D["success"]
        bg2      = D["bg2"]; border = D["border"]; txt = D["text"]

        st.markdown(
            f"<div style='background:{bg2};border:1px solid {border};"
            f"border-top:3px solid {border_c};border-radius:10px;"
            f"padding:0.8rem;margin-bottom:0.6rem;text-align:center'>"
            + (f"<img src='{logo}' style='height:32px;object-fit:contain;margin-bottom:0.3rem'><br>" if logo else "")
            + (f"<span style='background:{acc}22;color:{acc};padding:1px 7px;"
               f"border-radius:8px;font-size:0.7rem;font-weight:600'>⭐ Coordinator</span><br>" if is_coord else "")
            + f"<strong style='color:{txt};font-size:0.85rem'>{name}</strong><br>"
            f"<span style='color:{muted};font-size:0.75rem'>{country} · {ptype}</span>"
            f"</div>", unsafe_allow_html=True)

# ── Maps ──────────────────────────────────────────────────────────────────────
section_label("🗺️ Interactive Maps")

# Map scope selector
scope_opts = {"World": "world", "Europe": "europe", "Africa": "africa",
              "Asia": "asia", "North America": "north america",
              "South America": "south america"}
mc1, mc2 = st.columns([2,5])
with mc1:
    scope_label = st.selectbox("Map Scope", list(scope_opts.keys()),
                                index=1 if any(
                                    p.get("country","") in (
                                        "Germany","France","Italy","Spain","Netherlands",
                                        "Belgium","Austria","Poland","Greece","Romania",
                                        "Portugal","Czech Republic","Hungary","Sweden",
                                        "Denmark","Finland","Norway","Switzerland"
                                    ) for p in partners
                                ) else 0,
                                key="map_scope")
    scope = scope_opts[scope_label]

    st.markdown(
        f"<div style='background:{D["bg2"]};border:1px solid {D["border"]};"
        f"border-radius:8px;padding:0.8rem;font-size:0.82rem;color:{muted}'>"
        f"<strong style='color:{D["accent"]}'>Map legend:</strong><br>"
        f"<span style='color:{D["accent"]}'>■</span> Coordinator country<br>"
        f"<span style='color:{D["success"]}'>■</span> Partner countries"
        f"</div>", unsafe_allow_html=True)

with mc2:
    fig_map = chart_partner_map(partners, acronym, scope=scope)
    st.plotly_chart(fig_map, use_container_width=True)

# ── Export section ────────────────────────────────────────────────────────────
section_label("📥 Export for Project Website")

acc = D["accent"]
st.markdown(
    f"<div style='background:{D["bg2"]};border-left:4px solid {acc};"
    f"border-radius:10px;padding:1rem 1.3rem;margin-bottom:1rem'>"
    f"<strong style='color:{acc}'>How to embed this map in your website</strong><br>"
    f"<ol style='color:{muted};font-size:0.85rem;margin:0.5rem 0 0;padding-left:1.2rem'>"
    f"<li>Download the HTML file below</li>"
    f"<li>Upload it to your web server or Google Drive</li>"
    f"<li>Embed using an <code>&lt;iframe&gt;</code> tag:<br>"
    f"<code style='font-size:0.78rem'>&lt;iframe src=\"partner_map.html\" "
    f"width=\"100%\" height=\"500\" frameborder=\"0\"&gt;&lt;/iframe&gt;</code></li>"
    f"<li>Or open directly in any browser — fully interactive with zoom and hover</li>"
    f"</ol></div>", unsafe_allow_html=True)

ec1, ec2 = st.columns(2)

with ec1:
    html_world = fig_to_html(
        chart_partner_map(partners, acronym, scope="world"),
        f"{acronym} — Project Partner Countries"
    )
    st.download_button(
        "🌍 Download World Map (HTML)",
        data=html_world.encode("utf-8"),
        file_name=f"{acronym}_partner_map_world.html",
        mime="text/html",
        use_container_width=True,
        key="dl_world"
    )

with ec2:
    html_eu = fig_to_html(
        chart_partner_map(partners, acronym, scope="europe"),
        f"{acronym} — Project Partners in Europe"
    )
    st.download_button(
        "🇪🇺 Download Europe Map (HTML)",
        data=html_eu.encode("utf-8"),
        file_name=f"{acronym}_partner_map_europe.html",
        mime="text/html",
        use_container_width=True,
        key="dl_eu"
    )

# ── Full dashboard export ─────────────────────────────────────────────────────
section_label("📊 Export Full Dashboard as HTML")

st.markdown(
    f"<p style='color:{muted};font-size:0.85rem'>"
    f"Download all project charts as a single interactive HTML dashboard "
    f"— ready to embed in your project website or share with stakeholders.</p>",
    unsafe_allow_html=True)

if st.button("🖥️ Generate Full Dashboard HTML", type="primary"):
    from modules.database import (get_tasks, get_deliverables, get_milestones,
                                   get_work_packages, get_task_stats,
                                   get_deliverable_stats, get_milestone_stats,
                                   get_budget_summary, get_snapshots)
    from modules.charts import (chart_task_status, chart_deliverable_status,
                                chart_milestone_timeline, chart_budget_gauge,
                                chart_wp_completion, chart_progress_over_time)
    from datetime import date as _date

    with st.spinner("Building interactive dashboard…"):
        tasks  = get_tasks(sel_pid)
        dels   = get_deliverables(sel_pid)
        mss    = get_milestones(sel_pid)
        wps    = get_work_packages(sel_pid)
        budget = get_budget_summary(sel_pid)
        snaps  = get_snapshots(sel_pid)
        proj_start_raw = proj.get("project_start_date")
        proj_start_dt  = _date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None

        # Build individual chart HTMLs (without full_html wrapper)
        def _chart_div(fig, title):
            return fig.to_html(full_html=False, include_plotlyjs=False,
                               div_id=title.lower().replace(" ","_"))

        charts_html = "".join([
            _chart_div(chart_task_status(tasks),           "Task Status"),
            _chart_div(chart_deliverable_status(dels),     "Deliverable Status"),
            _chart_div(chart_milestone_timeline(mss, proj_start_dt), "Milestone Timeline"),
            _chart_div(chart_budget_gauge(budget["planned"], budget["spent"]), "Budget"),
            _chart_div(chart_wp_completion(wps, tasks, dels), "WP Completion"),
            _chart_div(chart_partner_map(partners, acronym, "world"), "Partner Map"),
        ] + ([_chart_div(chart_progress_over_time(snaps), "Progress Over Time")] if snaps else []))

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{acronym} — Project Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body {{ background:#0f1421; color:#e2e8f0; font-family:Calibri,sans-serif; margin:0; padding:1rem 2rem; }}
    h1   {{ color:#00BCD4; font-size:1.8rem; margin-bottom:0.3rem; }}
    p    {{ color:#8899b0; font-size:0.9rem; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-top:1.5rem; }}
    .chart {{ background:#1a2235; border-radius:12px; padding:1rem;
              border:1px solid rgba(255,255,255,0.09); }}
    .chart.full {{ grid-column:1/-1; }}
    footer {{ margin-top:2rem; color:#8899b0; font-size:0.78rem; text-align:center; }}
  </style>
</head>
<body>
  <h1>🏗️ {acronym} — Project Progress Dashboard</h1>
  <p>{proj.get('proposal_title','')} · Generated {_date.today().isoformat()}</p>
  <div class="grid">
    <div class="chart">{_chart_div(chart_task_status(tasks),'ts')}</div>
    <div class="chart">{_chart_div(chart_deliverable_status(dels),'ds')}</div>
    <div class="chart">{_chart_div(chart_budget_gauge(budget['planned'],budget['spent']),'bg')}</div>
    <div class="chart">{_chart_div(chart_wp_completion(wps,tasks,dels),'wpc')}</div>
    <div class="chart full">{_chart_div(chart_milestone_timeline(mss,proj_start_dt),'mst')}</div>
    <div class="chart full">{_chart_div(chart_partner_map(partners,acronym,'world'),'pm')}</div>
    {'<div class="chart full">' + _chart_div(chart_progress_over_time(snaps),'pot') + '</div>' if snaps else ''}
  </div>
  <footer>Generated by Octa Platform · {acronym}</footer>
</body>
</html>"""

    st.download_button(
        f"📥 Download {acronym}_Dashboard.html",
        data=full_html.encode("utf-8"),
        file_name=f"{acronym}_Dashboard.html",
        mime="text/html",
        key="dl_dashboard"
    )
    st.success("✅ Dashboard ready — open in any browser or embed with an <iframe>.")
