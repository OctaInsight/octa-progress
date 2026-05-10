"""Octa Project Progress Tracker — Milestone Tracking."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (format_month, format_month_range,inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, deviation_badge, DARK)
from modules.database import (get_milestones, update_milestone, get_project,
                               get_milestone_stats, get_work_packages,
                               month_to_date)
from modules.charts import chart_milestone_timeline, fig_to_html
from config import MILESTONE_STATUS_COLORS, DARK as D

st.set_page_config(page_title="Milestones — Octa", page_icon="🏁",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid:
    st.warning("No project selected."); st.switch_page("app.py"); st.stop()

proj = get_project(sel_pid)
proj_start_raw = proj.get("project_start_date")
proj_start = date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None
acronym = proj.get("acronym","") or sel_pid

page_header("Milestones", f"{acronym} — Track milestone achievement against plan", "🏁")
if st.button("← Dashboard"): st.switch_page("app.py")

wps       = get_work_packages(sel_pid)
wp_map    = {w["wp_id"]: w.get("wp_number","") for w in wps}
milestones= get_milestones(sel_pid)
stats     = get_milestone_stats(milestones, proj_start)
muted     = D["muted"]; acc = D["accent"]

# ── KPI row ───────────────────────────────────────────────────────────────────
section_label("📊 Milestone Summary")
k1,k2,k3,k4,k5 = st.columns(5)
kpi_card(k1,"Total",             stats["total"],             acc)
kpi_card(k2,"Achieved",          stats["achieved"],           D["success"])
kpi_card(k3,"Partially Achieved",stats.get("partially_achieved",0),D["warning"])
kpi_card(k4,"Delayed / Overdue", len(stats["overdue"]),       D["danger"] if stats["overdue"] else D["success"])
kpi_card(k5,"Planned",           stats["planned"],            D["muted"])

pct = round(stats["achieved"]/stats["total"]*100) if stats["total"] else 0
st.progress(pct/100, text=f"Achievement rate: {pct}%")

# ── Timeline chart ────────────────────────────────────────────────────────────
section_label("📅 Milestone Timeline — Planned vs Achieved")
fig = chart_milestone_timeline(milestones, proj_start)
st.plotly_chart(fig, use_container_width=True)
ec1, ec2 = st.columns(2)
with ec1:
    html = fig_to_html(fig, f"{acronym} — Milestone Timeline")
    st.download_button("📥 Download chart as HTML",
                       html.encode("utf-8"), f"{acronym}_milestones.html",
                       "text/html", use_container_width=True, key="dl_ms_chart")
with ec2:
    st.caption("💡 Open HTML in any browser — fully interactive, ready for your project website")

# ── Overdue alerts ────────────────────────────────────────────────────────────
if stats["overdue"]:
    section_label(f"⚠️ Overdue Milestones ({len(stats['overdue'])})")
    for m in stats["overdue"]:
        danger = D["danger"]; bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
        st.markdown(
            f"<div style='background:{bg2};border:1px solid {danger}44;"
            f"border-left:4px solid {danger};border-radius:10px;"
            f"padding:0.7rem 1rem;margin-bottom:0.4rem'>"
            f"<strong style='color:{danger}'>{m.get('milestone_number','')}: "
            f"{m.get('milestone_title','')}</strong>"
            f"<span style='color:{muted};font-size:0.8rem'> · Planned M{m.get('due_month','?')} "
            f"· <strong style='color:{danger}'>{m.get('delay_days',0)} days overdue</strong></span>"
            f"</div>", unsafe_allow_html=True)

# ── Milestone list with update forms ─────────────────────────────────────────
section_label(f"🏁 All Milestones ({len(milestones)})")

status_opts = ["planned","achieved","partially_achieved","delayed","not_achieved"]

# Group by WP
wp_milestones = {}
for m in sorted(milestones, key=lambda x: x.get("due_month",0) or 0):
    wid = m.get("wp_id")
    wnum= wp_map.get(wid,"No WP")
    if wnum not in wp_milestones:
        wp_milestones[wnum] = []
    wp_milestones[wnum].append(m)

for wp_num, ms_list in sorted(wp_milestones.items()):
    acc2 = D["accent"]
    st.markdown(
        f"<div style='font-size:0.82rem;font-weight:700;color:{acc2};"
        f"margin:0.8rem 0 0.3rem'>📦 {wp_num}</div>",
        unsafe_allow_html=True)

    for m in ms_list:
        mid    = m["milestone_id"]
        mnum   = m.get("milestone_number","")
        mtitle = m.get("milestone_title","")
        status = m.get("status","planned")
        s_color= MILESTONE_STATUS_COLORS.get(status, D["muted"])
        due_m  = m.get("planned_due_month") or m.get("due_month")

        # Deviation
        dev_html = ""
        if m.get("achieved_date") and due_m and proj_start:
            planned_dt = month_to_date(proj_start, int(due_m))
            achieved_dt= date.fromisoformat(str(m["achieved_date"])[:10])
            delay      = (achieved_dt - planned_dt).days if planned_dt else 0
            if delay > 0:
                dev_html = f"<span style='color:{D["danger"]};font-size:0.75rem'> +{delay}d late</span>"
            elif delay < 0:
                dev_html = f"<span style='color:{D["success"]};font-size:0.75rem'> {abs(delay)}d early</span>"
            else:
                dev_html = f"<span style='color:{D["success"]};font-size:0.75rem'> On time</span>"

        with st.expander(
            f"🏁 {mnum}: {mtitle}  ·  {format_month(proj_start, due_m, short=True)}  ·  {status.replace('_',' ').title()}",
            expanded=(status in ("planned","delayed"))
        ):
            ec1, ec2 = st.columns([3,2])
            with ec1:
                bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
                st.markdown(
                    f"<div style='background:{bg2};border-left:4px solid {s_color};"
                    f"border-radius:8px;padding:0.7rem 1rem'>"
                    f"<span style='background:{s_color}22;color:{s_color};"
                    f"padding:2px 9px;border-radius:10px;font-size:0.75rem;font-weight:600'>"
                    f"{status.replace('_',' ').title()}</span>"
                    f"{dev_html}"
                    f"<div style='color:{muted};font-size:0.82rem;margin-top:0.4rem'>"
                    f"Planned: {format_month(proj_start, due_m)}"
                    + (f" · Achieved: {m['achieved_date']}" if m.get("achieved_date") else "")
                    + f"</div>"
                    + (f"<div style='color:{txt};font-size:0.85rem;margin-top:0.3rem'>{m.get('milestone_description','')}</div>" if m.get("milestone_description") else "")
                    + (f"<div style='color:{D["success"]};font-size:0.82rem;margin-top:0.3rem'>📝 {m['achievement_notes']}</div>" if m.get("achievement_notes") else "")
                    + "</div>", unsafe_allow_html=True)

                if m.get("means_of_verification"):
                    warn = D["warning"]
                    st.markdown(
                        f"<div style='background:{warn}11;border-left:3px solid {warn};"
                        f"border-radius:6px;padding:0.3rem 0.7rem;margin-top:0.3rem;"
                        f"font-size:0.8rem;color:{warn}'>"
                        f"✔ MoV: {m['means_of_verification']}</div>",
                        unsafe_allow_html=True)

            with ec2:
                with st.form(f"ms_update_{mid}"):
                    new_status = st.selectbox("Status", status_opts,
                        index=status_opts.index(status) if status in status_opts else 0,
                        format_func=lambda s: s.replace("_"," ").title(),
                        key=f"ms_sel_{mid}")
                    new_date = None
                    if new_status == "achieved":
                        new_date = st.date_input("Achieved Date",
                            value=date.fromisoformat(str(m["achieved_date"])[:10])
                                  if m.get("achieved_date") else date.today(),
                            key=f"ms_dt_{mid}")
                    notes = st.text_area("Achievement Notes",
                        value=m.get("achievement_notes",""),
                        height=70, key=f"ms_notes_{mid}",
                        placeholder="Describe how this milestone was achieved…")

                    if st.form_submit_button("💾 Save", type="primary",
                                             use_container_width=True):
                        if update_milestone(mid, new_status, new_date, notes):
                            st.success("✅ Saved!"); st.rerun()
