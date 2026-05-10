"""Octa Project Progress Tracker — Task Tracking."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (format_month, format_month_range,inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, DARK)
from modules.database import (get_tasks, update_task_progress, get_project,
                               get_task_stats, get_work_packages, month_to_date)
from modules.charts import (chart_task_status, chart_delay_analysis,
                             chart_wp_completion, fig_to_html)
from modules.database import get_deliverables
from config import TASK_STATUS_COLORS, DARK as D

st.set_page_config(page_title="Tasks — Octa", page_icon="⚙️",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj = get_project(sel_pid)
proj_start_raw = proj.get("project_start_date")
proj_start = date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None
acronym = proj.get("acronym","") or sel_pid

page_header("Tasks", f"{acronym} — Track task progress, status and delays", "⚙️")
if st.button("← Dashboard"): st.switch_page("app.py")

wps   = get_work_packages(sel_pid)
wp_map= {w["wp_id"]: w.get("wp_number","") for w in wps}
tasks = get_tasks(sel_pid)
stats = get_task_stats(tasks, proj_start)
dels  = get_deliverables(sel_pid)
muted = D["muted"]

# ── KPI row ───────────────────────────────────────────────────────────────────
section_label("📊 Task Summary")
k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_card(k1,"Total",       stats["total"],             D["accent"])
kpi_card(k2,"Completed",   stats["completed"],          D["success"])
kpi_card(k3,"Ongoing",     stats.get("ongoing",0),      D["accent"])
kpi_card(k4,"Planned",     stats.get("planned",0),      D["muted"])
kpi_card(k5,"Overdue",     len(stats["overdue"]),        D["danger"] if stats["overdue"] else D["success"])
kpi_card(k6,"Avg Progress",f"{stats['avg_progress']}%", D["warning"])

# ── Charts ────────────────────────────────────────────────────────────────────
section_label("📈 Charts")
cc1, cc2 = st.columns(2)

with cc1:
    fig1 = chart_task_status(tasks)
    st.plotly_chart(fig1, use_container_width=True)
    if st.button("📥 Export", key="exp_t_pie"):
        st.download_button("⬇ Download HTML",
                           fig_to_html(fig1,"Task Status").encode("utf-8"),
                           f"{acronym}_task_status.html","text/html", key="dl_tp")

with cc2:
    fig2 = chart_wp_completion(wps, tasks, dels)
    st.plotly_chart(fig2, use_container_width=True)
    if st.button("📥 Export", key="exp_t_wp"):
        st.download_button("⬇ Download HTML",
                           fig_to_html(fig2,"WP Completion").encode("utf-8"),
                           f"{acronym}_wp_completion.html","text/html", key="dl_tw")

# Delay analysis
delay_tasks = []
for t in tasks:
    if t.get("actual_end_date") and proj_start and (t.get("planned_end_month") or t.get("end_month")):
        ad = date.fromisoformat(str(t["actual_end_date"])[:10])
        actual_month = max(1, (ad - proj_start).days // 30 + 1)
        delay_tasks.append({**t, "actual_end_month": actual_month})

if delay_tasks:
    section_label("⏱️ Delay Analysis")
    fig3 = chart_delay_analysis(
        delay_tasks, "task_number","task_title",
        "planned_end_month","actual_end_month",
        "Task Completion Delay (months)"
    )
    st.plotly_chart(fig3, use_container_width=True)
    if st.button("📥 Export delay chart", key="exp_t_delay"):
        st.download_button("⬇ Download HTML",
                           fig_to_html(fig3,"Task Delays").encode("utf-8"),
                           f"{acronym}_task_delay.html","text/html", key="dl_td")

# ── Overdue ───────────────────────────────────────────────────────────────────
if stats["overdue"]:
    section_label(f"⚠️ Overdue Tasks ({len(stats['overdue'])})")
    for t in stats["overdue"]:
        danger = D["danger"]; bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
        st.markdown(
            f"<div style='background:{bg2};border-left:4px solid {danger};"
            f"border-radius:10px;padding:0.7rem 1rem;margin-bottom:0.4rem'>"
            f"<strong style='color:{danger}'>{t.get('task_number','')}: "
            f"{t.get('task_title','')}</strong>"
            f"<span style='color:{muted};font-size:0.8rem'>"
            f" · Planned end M{t.get('end_month','?')}"
            f" · <strong style='color:{danger}'>{t.get('delay_days',0)} days overdue</strong>"
            f"</span></div>", unsafe_allow_html=True)

# ── Task list by WP ───────────────────────────────────────────────────────────
section_label(f"⚙️ All Tasks ({len(tasks)})")

status_opts = ["planned","ongoing","completed","delayed","cancelled"]

wp_tasks = {}
for t in sorted(tasks, key=lambda x: x.get("task_number","")):
    wnum = wp_map.get(t.get("wp_id"),"No WP")
    if wnum not in wp_tasks: wp_tasks[wnum] = []
    wp_tasks[wnum].append(t)

for wp_num, t_list in sorted(wp_tasks.items()):
    acc2 = D["accent"]
    st.markdown(
        f"<div style='font-size:0.82rem;font-weight:700;color:{acc2};"
        f"margin:0.8rem 0 0.3rem'>📦 {wp_num}</div>",
        unsafe_allow_html=True)

    for t in t_list:
        tid    = t["task_id"]
        tnum   = t.get("task_number","")
        ttitle = t.get("task_title","")
        status = t.get("status","planned")
        s_color= TASK_STATUS_COLORS.get(status, D["muted"])
        prog   = float(t.get("progress_percentage",0) or 0)
        plan_sm= t.get("planned_start_month") or t.get("start_month")
        plan_em= t.get("planned_end_month")   or t.get("end_month")

        with st.expander(
            f"⚙️ {tnum}: {ttitle}  ·  {format_month(proj_start,plan_sm,short=True)}–{format_month(proj_start,plan_em,short=True)}  ·  {status.replace('_',' ').title()}",
            expanded=(status in ("ongoing","delayed"))
        ):
            tc1, tc2 = st.columns([3,2])
            with tc1:
                bg2 = D["bg2"]; txt = D["text"]
                st.markdown(
                    f"<div style='background:{bg2};border-left:4px solid {s_color};"
                    f"border-radius:8px;padding:0.8rem 1rem'>"
                    f"<span style='background:{s_color}22;color:{s_color};"
                    f"padding:2px 8px;border-radius:10px;font-size:0.75rem;font-weight:600'>"
                    f"{status.replace('_',' ').title()}</span><br>"
                    + (f"<div style='color:{txt};font-size:0.84rem;margin-top:0.3rem'>{t.get('task_description','')}</div>" if t.get("task_description") else "")
                    + f"<div style='color:{muted};font-size:0.8rem;margin-top:0.4rem'>"
                    f"Planned: {format_month(proj_start,plan_sm,short=True)}–{format_month(proj_start,plan_em,short=True)}"
                    + (f" · Actual start: {t['actual_start_date']}" if t.get("actual_start_date") else "")
                    + (f" · Actual end: {t['actual_end_date']}"     if t.get("actual_end_date")   else "")
                    + f"</div></div>", unsafe_allow_html=True)

                if prog:
                    st.progress(prog/100, text=f"Progress: {prog:.0f}%")

                if t.get("implementation_notes"):
                    suc = D["success"]
                    st.markdown(
                        f"<div style='color:{suc};font-size:0.8rem;margin-top:0.3rem'>"
                        f"📝 {t['implementation_notes']}</div>",
                        unsafe_allow_html=True)

            with tc2:
                with st.form(f"task_update_{tid}"):
                    new_s    = st.selectbox("Status", status_opts,
                        index=status_opts.index(status) if status in status_opts else 0,
                        format_func=lambda s: s.replace("_"," ").title(),
                        key=f"ts_{tid}")
                    new_prog = st.slider("Progress %", 0, 100,
                                          int(prog), 5, key=f"tprog_{tid}")
                    new_start= st.date_input("Actual Start",
                        value=date.fromisoformat(str(t["actual_start_date"])[:10])
                              if t.get("actual_start_date") else None,
                        key=f"tstart_{tid}")
                    new_end  = st.date_input("Actual End",
                        value=date.fromisoformat(str(t["actual_end_date"])[:10])
                              if t.get("actual_end_date") else None,
                        key=f"tend_{tid}")
                    new_notes= st.text_area("Progress Notes",
                        value=t.get("implementation_notes",""),
                        height=60, key=f"tnotes_{tid}")

                    if st.form_submit_button("💾 Save", type="primary",
                                             use_container_width=True):
                        if update_task_progress(
                            tid, new_s, new_prog,
                            new_start if new_start else None,
                            new_end   if new_end   else None,
                            new_notes,
                            st.session_state.get("user_id")
                        ):
                            st.success("✅ Saved!"); st.rerun()
