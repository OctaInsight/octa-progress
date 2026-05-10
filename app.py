"""Octa Project Progress Tracker — Dashboard."""
import streamlit as st
import plotly.graph_objects as go
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url, set_token_in_url, get_token_from_url
from modules.ui_helpers import (format_month, format_month_range,inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, DARK)
from modules.database import (get_funded_projects, get_project,
                               get_tasks, get_deliverables, get_milestones,
                               get_kpis, get_work_packages,
                               get_task_stats, get_deliverable_stats,
                               get_milestone_stats, get_budget_summary,
                               get_snapshots, get_project_partners,
                               month_to_date)
from modules.charts import (chart_task_status, chart_deliverable_status,
                             chart_milestone_timeline, chart_progress_over_time,
                             chart_wp_completion, chart_budget_gauge,
                             chart_partner_map, fig_to_html)
from config import DARK as D

st.set_page_config(page_title="Project Progress Tracker — Octa",
                   page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
auto_login_from_url()
require_auth()

token = st.session_state.get("sso_token","") or get_token_from_url()
if token: set_token_in_url(token)

sidebar_nav()

user_id  = st.session_state.get("user_id")
is_admin = st.session_state.get("role") == "admin"
org      = st.session_state.get("organisation","")
muted    = D["muted"]

page_header("Project Progress Tracker",
            "Monitor milestones, deliverables and tasks for funded projects", "🏗️")

# ── Project selector ──────────────────────────────────────────────────────────
projects, db_error = get_funded_projects(organisation=org, is_admin=is_admin)
if db_error:
    st.error(f"❌ Database error: {db_error}")
    st.stop()

if not projects:
    st.warning(
        "⚠️ No funded projects visible. "
        "Make sure a proposal status is set to **Funded** in the Proposal Tracker."
    )
    st.stop()

proj_opts = {}
for p in projects:
    acr    = p.get("acronym","").strip() or p["proposal_id"]
    status = p.get("lifecycle_status","").replace("_"," ").title()
    proj_opts[f"{acr} — {p.get('proposal_title','')[:45]} [{status}]"] = p["proposal_id"]

current_pid = st.session_state.get("selected_project_id","")
cur_label   = next((l for l,v in proj_opts.items() if v==current_pid), None)
def_idx     = list(proj_opts.keys()).index(cur_label) if cur_label else 0

sel_label = st.selectbox("Select Project", list(proj_opts.keys()),
                          index=def_idx, key="proj_selector")
sel_pid   = proj_opts[sel_label]

if sel_pid != current_pid:
    st.session_state["selected_project_id"] = sel_pid
    st.rerun()

if not sel_pid:
    st.stop()

# ── Load project data ─────────────────────────────────────────────────────────
proj        = get_project(sel_pid)
wps         = get_work_packages(sel_pid)
tasks       = get_tasks(sel_pid)
deliverables= get_deliverables(sel_pid)
milestones  = get_milestones(sel_pid)
kpis_short  = get_kpis(sel_pid, "short_term")
budget      = get_budget_summary(sel_pid)
snapshots   = get_snapshots(sel_pid)
partners    = get_project_partners(sel_pid)

proj_start_raw = proj.get("project_start_date")
proj_start     = date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None
# Read duration from whichever field is populated
_dur_raw = (proj.get("project_duration_months") or
            proj.get("duration_months") or
            proj.get("proposal_duration") or
            proj.get("duration") or None)
if _dur_raw:
    try:    proj_dur = int(_dur_raw)
    except: proj_dur = None
elif proj_start and proj.get("project_end_date"):
    try:
        from dateutil.relativedelta import relativedelta as _rd
        _end = date.fromisoformat(str(proj.get("project_end_date"))[:10])
        _d   = _rd(_end, proj_start)
        proj_dur = _d.years * 12 + _d.months + 1
    except: proj_dur = None
else:
    proj_dur = None
acronym        = proj.get("acronym","") or sel_pid

# Current month of project
current_proj_month = None
if proj_start:
    elapsed = (date.today() - proj_start).days
    current_proj_month = max(1, elapsed // 30 + 1)

task_stats= get_task_stats(tasks, proj_start)
del_stats = get_deliverable_stats(deliverables, proj_start)
ms_stats  = get_milestone_stats(milestones, proj_start)

# ── Project info bar ──────────────────────────────────────────────────────────
pi1, pi2, pi3, pi4 = st.columns(4)
# Use lifecycle_status if meaningful, otherwise fall back to original status field
_ls = (proj.get("lifecycle_status") or "").strip()
_st = (proj.get("status") or "").strip()
lifecycle   = _ls.replace("_"," ").title() if _ls and _ls not in ("","draft_proposal") else _st
lc_color    = (D["success"] if any(w in _ls.lower() for w in ("ongoing","ended"))
               else D["accent"] if any(w in (_ls+_st).lower() for w in ("funded","project"))
               else D["muted"])

for col, label, val in [
    (pi1, "Status",     lifecycle),
    (pi2, "Start Date", str(proj_start) if proj_start else "—"),
    (pi3, "Duration",   f"{proj_dur} months" if proj_dur else "—"),
    (pi4, "Current Month", f"M{current_proj_month}" if current_proj_month else "—"),
]:
    bg2 = D["bg2"]
    col.markdown(
        f"<div style='background:{bg2};border-radius:8px;padding:0.6rem 0.9rem;"
        f"border:1px solid {D["border"]}'>"
        f"<div style='font-size:0.72rem;color:{muted}'>{label}</div>"
        f"<div style='font-weight:700;color:{D["text"]}'>{val}</div>"
        f"</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Project Settings ─────────────────────────────────────────────────────────
with st.expander("⚙️ Project Settings — Start Date, Duration, Status", expanded=not proj_start):
    ps1, ps2, ps3, ps4 = st.columns(4)
    with ps1:
        new_start = st.date_input(
            "Project Start Date",
            value=proj_start if proj_start else date.today(),
            key="proj_start_input"
        )
    with ps2:
        new_dur = st.number_input(
            "Duration (months)", min_value=1, max_value=120,
            value=int(proj_dur) if proj_dur else 24, key="proj_dur_input"
        )
    with ps3:
        status_choices = ["Funded","ongoing_project","ended_project"]
        cur_status = (proj.get("lifecycle_status") or proj.get("status") or "Funded")
        cur_idx    = next((i for i,s in enumerate(status_choices) if s.lower() in cur_status.lower()), 0)
        new_status_sel = st.selectbox("Project Status", status_choices, index=cur_idx,
                                       key="proj_status_sel")
    with ps4:
        new_grant = st.text_input("Grant Agreement No.",
                                   value=proj.get("grant_agreement_number","") or "",
                                   key="proj_grant")
    if st.button("💾 Save Project Settings", type="primary"):
        from modules.database import update_project_status
        ok = update_project_status(sel_pid, {
            "project_start_date":      new_start.isoformat(),
            "project_duration_months": new_dur,
            "lifecycle_status":        new_status_sel,
            "grant_agreement_number":  new_grant.strip(),
        })
        if ok:
            st.success("✅ Project settings saved! Reloading…")
            st.rerun()
        else:
            st.error("Save failed — check your Supabase permissions.")

# ── KPI row ───────────────────────────────────────────────────────────────────
section_label("📊 At a Glance")
k1,k2,k3,k4,k5,k6,k7 = st.columns(7)

ms_pct  = round(ms_stats["achieved"]/ms_stats["total"]*100) if ms_stats["total"] else 0
del_pct = round((del_stats["accepted"]+del_stats["submitted"])/del_stats["total"]*100) if del_stats["total"] else 0
t_pct   = round(task_stats["completed"]/task_stats["total"]*100) if task_stats["total"] else 0

kpi_card(k1,"Milestones",  f"{ms_stats['achieved']}/{ms_stats['total']}",  D["accent"],  f"{ms_pct}%")
kpi_card(k2,"Deliverables",f"{del_stats['accepted']}/{del_stats['total']}",D["accent"],  f"{del_pct}% accepted")
kpi_card(k3,"Tasks",       f"{task_stats['completed']}/{task_stats['total']}",D["accent"],f"{t_pct}% done")
kpi_card(k4,"MS Overdue",  ms_stats["overdue"].__len__(),  D["danger"]  if ms_stats["overdue"]  else D["success"], "milestones")
kpi_card(k5,"Del. Overdue",del_stats["overdue"].__len__(), D["danger"]  if del_stats["overdue"] else D["success"], "deliverables")
kpi_card(k6,"Task Avg",    f"{task_stats['avg_progress']}%",D["warning"], "avg progress")
kpi_card(k7,"Budget Used", f"{budget['pct_spent']}%",
         D["danger"] if budget["pct_spent"]>90 else (D["warning"] if budget["pct_spent"]>75 else D["success"]),
         f"€{budget['spent']:,.0f}")

# ── Quick access cards ───────────────────────────────────────────────────────
section_label("🔗 Quick Access")
qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)
for col, icon, label, page in [
    (qa1, "📦", "WP Overview",  "pages/work_packages.py"),
    (qa2, "🏁", "Milestones",   "pages/milestones.py"),
    (qa3, "📄", "Deliverables", "pages/deliverables.py"),
    (qa4, "⚙️",  "Tasks",       "pages/tasks.py"),
    (qa5, "📊", "KPIs",         "pages/kpis.py"),
    (qa6, "🌍", "Partner Map",  "pages/partner_map.py"),
]:
    bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
    col.markdown(
        f"<div style='background:{bg2};border:1px solid {border};border-radius:10px;"
        f"padding:0.7rem;text-align:center'>"
        f"<div style='font-size:1.5rem'>{icon}</div>"
        f"<div style='font-size:0.78rem;color:{txt}'>{label}</div></div>",
        unsafe_allow_html=True)
    if col.button(f"Open", key=f"qa_{label}", use_container_width=True):
        st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
section_label("📈 Progress Charts")

c1, c2, c3 = st.columns(3)

with c1:
    fig = chart_task_status(tasks)
    st.plotly_chart(fig, use_container_width=True)
    if st.button("📥 Export chart", key="exp_task_status"):
        st.download_button("⬇ Download HTML", fig_to_html(fig, "Tasks by Status"),
                           "task_status.html","text/html", key="dl_ts")

with c2:
    fig = chart_deliverable_status(deliverables)
    st.plotly_chart(fig, use_container_width=True)
    if st.button("📥 Export chart", key="exp_del_status"):
        st.download_button("⬇ Download HTML", fig_to_html(fig, "Deliverables by Status"),
                           "deliverable_status.html","text/html", key="dl_ds")

with c3:
    fig = chart_budget_gauge(budget["planned"], budget["spent"])
    st.plotly_chart(fig, use_container_width=True)
    if st.button("📥 Export chart", key="exp_budget"):
        st.download_button("⬇ Download HTML", fig_to_html(fig, "Budget Consumption"),
                           "budget_gauge.html","text/html", key="dl_bg")

c4, c5 = st.columns(2)

with c4:
    fig = chart_wp_completion(wps, tasks, deliverables)
    st.plotly_chart(fig, use_container_width=True)
    if st.button("📥 Export chart", key="exp_wp"):
        st.download_button("⬇ Download HTML", fig_to_html(fig, "Completion by WP"),
                           "wp_completion.html","text/html", key="dl_wp")

with c5:
    if snapshots:
        fig = chart_progress_over_time(snapshots)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("📥 Export chart", key="exp_progress"):
            st.download_button("⬇ Download HTML", fig_to_html(fig, "Progress Over Time"),
                               "progress_over_time.html","text/html", key="dl_pr")
    else:
        acc2 = D["accent"]
        st.markdown(
            f"<div style='background:{D["bg2"]};border-radius:10px;padding:2rem;"
            f"text-align:center;border:1px solid {D["border"]}'>"
            f"<div style='color:{muted};font-size:0.88rem'>"
            f"Progress over time chart will appear once snapshots are saved.<br>"
            f"Go to <strong style='color:{acc2}'>Milestones</strong> or "
            f"<strong style='color:{acc2}'>Deliverables</strong> pages to save a snapshot.</div>"
            f"</div>", unsafe_allow_html=True)

# ── KPI progress chart ───────────────────────────────────────────────────────
if kpis_short:
    section_label("📊 KPI Achievement — Short-Term")
    from modules.charts import chart_kpi_achievement
    fig_kpi = chart_kpi_achievement(kpis_short, "Short-Term KPI Progress (Baseline → Target → Achieved)")
    st.plotly_chart(fig_kpi, use_container_width=True)
    kc1, kc2 = st.columns(2)
    with kc1:
        if st.button("📥 Export KPI chart", key="exp_kpi_dash"):
            html_kpi = fig_to_html(fig_kpi, f"{acronym} — KPI Progress")
            st.download_button("⬇ Download HTML", html_kpi.encode("utf-8"),
                               f"{acronym}_kpi_progress.html","text/html", key="dl_kpi_dash")
    with kc2:
        if st.button("📊 Update KPI Values →", key="goto_kpi"):
            st.switch_page("pages/kpis.py")

# ── Milestone timeline ────────────────────────────────────────────────────────
section_label("🏁 Milestone Timeline")
fig_ms = chart_milestone_timeline(milestones, proj_start)
st.plotly_chart(fig_ms, use_container_width=True)
if st.button("📥 Export Milestone Timeline", key="exp_ms_tl"):
    st.download_button("⬇ Download HTML", fig_to_html(fig_ms, "Milestone Timeline"),
                       "milestone_timeline.html","text/html", key="dl_ms_tl")

# ── Partner map (mini preview) ────────────────────────────────────────────────
section_label("🌍 Partner Map")
if partners:
    fig_map = chart_partner_map(partners, acronym, scope="world")
    st.plotly_chart(fig_map, use_container_width=True)
    mc1, mc2 = st.columns(2)
    with mc1:
        if st.button("🌍 Open Full Map Page", use_container_width=True):
            st.switch_page("pages/partner_map.py")
    with mc2:
        html_map = fig_to_html(fig_map, f"{acronym} — Partner Countries")
        st.download_button(
            "📥 Download Map as HTML",
            data=html_map.encode("utf-8"),
            file_name=f"{acronym}_partner_map.html",
            mime="text/html",
            use_container_width=True,
            key="dl_map_dash"
        )
else:
    st.info("No partners with country data found for this project.")

# ── Save Progress Snapshot ───────────────────────────────────────────────────
section_label("📸 Save Progress Snapshot")
st.markdown(
    f"<p style='color:{muted};font-size:0.84rem'>"
    f"Snapshots record the current project state (task/deliverable/milestone counts "
    f"and budget) for a given reporting period. They power the "
    f"<strong>Progress Over Time</strong> chart.</p>",
    unsafe_allow_html=True)

with st.form("snapshot_form"):
    sn1, sn2 = st.columns([1, 3])
    with sn1:
        snap_period = st.number_input(
            "Reporting Period", min_value=1, max_value=20,
            value=len(snapshots) + 1,
            help="e.g. 1 = first year, 2 = second year (or quarter 1, 2, 3…)"
        )
    with sn2:
        snap_notes = st.text_input(
            "Notes", placeholder="e.g. End of Year 1 / Mid-term review"
        )
    if st.form_submit_button("📸 Save Snapshot", type="primary", use_container_width=True):
        from modules.database import save_snapshot as _save_snap
        _b  = budget   # already loaded above
        ok  = _save_snap(sel_pid, snap_period, tasks, deliverables, milestones,
                         _b["planned"], _b["spent"], snap_notes)
        if ok:
            st.success(f"✅ Snapshot for Period {snap_period} saved!")
            st.rerun()
        else:
            st.error("❌ Save failed — check Supabase permissions.")

if snapshots:
    with st.expander(f"📋 Saved Snapshots ({len(snapshots)})", expanded=False):
        for s in reversed(snapshots):
            bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
            st.markdown(
                f"<div style='background:{bg2};border:1px solid {border};"
                f"border-radius:8px;padding:0.5rem 0.9rem;margin-bottom:0.3rem;"
                f"font-size:0.83rem;display:flex;gap:1.5rem;flex-wrap:wrap'>"
                f"<strong style='color:{txt}'>Period {s['reporting_period']}</strong>"
                f"<span style='color:{muted}'>{s.get('snapshot_date','')[:10]}</span>"
                f"<span style='color:{D["accent"]}'>Progress: {s.get('overall_progress_pct',0):.1f}%</span>"
                f"<span style='color:{D["success"]}'>Tasks: {s.get('tasks_completed',0)}/{s.get('tasks_total',0)}</span>"
                f"<span style='color:{D["warning"]}'>Deliverables: {s.get('deliverables_accepted',0)}/{s.get('deliverables_total',0)}</span>"
                + (f"<span style='color:{muted}'>{s.get('notes','')}</span>" if s.get("notes") else "")
                + "</div>", unsafe_allow_html=True)

# ── Upcoming deadlines ────────────────────────────────────────────────────────
if current_proj_month:
    section_label("📅 Next 3 Months — Upcoming Deadlines")
    horizon = current_proj_month + 3
    upcoming = []
    for m in milestones:
        dm = m.get("planned_due_month") or m.get("due_month")
        if dm and current_proj_month <= int(dm) <= horizon and m.get("status") != "achieved":
            upcoming.append({"type":"🏁 Milestone","num":m.get("milestone_number",""),
                             "title":m.get("milestone_title",""),"month":int(dm)})
    for d in deliverables:
        dm = d.get("planned_delivery_month") or d.get("delivery_month")
        if dm and current_proj_month <= int(dm) <= horizon and d.get("status") not in ("accepted","cancelled"):
            upcoming.append({"type":"📄 Deliverable","num":d.get("deliverable_number",""),
                             "title":d.get("deliverable_title",""),"month":int(dm)})

    upcoming.sort(key=lambda x: x["month"])
    if upcoming:
        for u in upcoming:
            diff = u["month"] - current_proj_month
            col  = D["danger"] if diff==0 else (D["warning"] if diff==1 else D["accent"])
            bg2  = D["bg2"]; border = D["border"]; txt = D["text"]
            st.markdown(
                f"<div style='background:{bg2};border:1px solid {border};"
                f"border-left:4px solid {col};border-radius:8px;"
                f"padding:0.6rem 1rem;margin-bottom:0.3rem;"
                f"display:flex;align-items:center;gap:1rem'>"
                f"<span style='background:{col}22;color:{col};padding:2px 8px;"
                f"border-radius:8px;font-size:0.78rem;white-space:nowrap'>"
                f"{format_month(proj_start, u['month'], short=True)}"
                + (f" — this month" if diff==0 else f" — {diff} month(s)")
                + f"</span>"
                f"<span style='color:{D["muted"]};font-size:0.8rem'>{u['type']}</span>"
                f"<strong style='color:{txt}'>{u['num']}: {u['title'][:60]}</strong>"
                f"</div>", unsafe_allow_html=True)
    else:
        st.success("No deadlines in the next 3 months. 🎉")
