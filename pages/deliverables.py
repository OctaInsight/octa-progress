"""Octa Project Progress Tracker — Deliverable Tracking."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (format_month, format_month_range,inject_css, sidebar_nav, page_header,
                                 section_label, kpi_card, DARK)
from modules.database import (get_deliverables, update_deliverable_progress,
                               get_project, get_deliverable_stats,
                               get_work_packages, month_to_date)
from modules.charts import chart_deliverable_status, chart_delay_analysis, fig_to_html
from config import DELIVERABLE_STATUS_COLORS, DARK as D

st.set_page_config(page_title="Deliverables — Octa", page_icon="📄",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id","")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj = get_project(sel_pid)
proj_start_raw = proj.get("project_start_date")
proj_start = date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None
acronym = proj.get("acronym","") or sel_pid

page_header("Deliverables",
            f"{acronym} — Track submission and acceptance against planned delivery", "📄")
if st.button("← Dashboard"): st.switch_page("app.py")

wps  = get_work_packages(sel_pid)
wp_map = {w["wp_id"]: w.get("wp_number","") for w in wps}
dels = get_deliverables(sel_pid)
stats= get_deliverable_stats(dels, proj_start)
muted= D["muted"]

# ── KPI row ───────────────────────────────────────────────────────────────────
section_label("📊 Deliverable Summary")
k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_card(k1,"Total",      stats["total"],       D["accent"])
kpi_card(k2,"Accepted",   stats["accepted"],    D["success"])
kpi_card(k3,"Submitted",  stats["submitted"],   D["accent"])
kpi_card(k4,"In Progress",stats["in_progress"], D["warning"])
kpi_card(k5,"Overdue",    len(stats["overdue"]),D["danger"] if stats["overdue"] else D["success"])
pct = round((stats["accepted"]+stats["submitted"])/stats["total"]*100) if stats["total"] else 0
kpi_card(k6,"Submitted %",f"{pct}%",D["accent"] if pct>=50 else D["warning"])

# ── Charts ────────────────────────────────────────────────────────────────────
section_label("📈 Charts")
cc1, cc2 = st.columns(2)

with cc1:
    fig1 = chart_deliverable_status(dels)
    st.plotly_chart(fig1, use_container_width=True)
    if st.button("📥 Export", key="exp_del_pie"):
        st.download_button("⬇ Download HTML",
                           fig_to_html(fig1,"Deliverable Status").encode("utf-8"),
                           f"{acronym}_del_status.html","text/html", key="dl_dp")

with cc2:
    # Delay analysis: compare planned vs actual delivery month
    delay_items = []
    for d in dels:
        if d.get("actual_submission_date") and (d.get("planned_delivery_month") or d.get("delivery_month")):
            if proj_start:
                ad = date.fromisoformat(str(d["actual_submission_date"])[:10])
                actual_month = max(1, (ad - proj_start).days // 30 + 1)
                delay_items.append({
                    **d,
                    "actual_month": actual_month,
                })
    if delay_items:
        fig2 = chart_delay_analysis(
            delay_items,
            number_col="deliverable_number", title_col="deliverable_title",
            planned_col="planned_delivery_month", actual_col="actual_month",
            title="Delivery Delay (months)"
        )
        st.plotly_chart(fig2, use_container_width=True)
        if st.button("📥 Export", key="exp_del_delay"):
            st.download_button("⬇ Download HTML",
                               fig_to_html(fig2,"Delivery Delays").encode("utf-8"),
                               f"{acronym}_del_delay.html","text/html", key="dl_dd")
    else:
        st.info("Delay analysis available after actual submission dates are entered.")

# ── Overdue ───────────────────────────────────────────────────────────────────
if stats["overdue"]:
    section_label(f"⚠️ Overdue Deliverables ({len(stats['overdue'])})")
    for d in stats["overdue"]:
        danger = D["danger"]; bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
        st.markdown(
            f"<div style='background:{bg2};border-left:4px solid {danger};"
            f"border-radius:10px;padding:0.7rem 1rem;margin-bottom:0.4rem'>"
            f"<strong style='color:{danger}'>{d.get('deliverable_number','')}: "
            f"{d.get('deliverable_title','')}</strong>"
            f"<span style='color:{muted};font-size:0.8rem'> · Planned M{d.get('delivery_month','?')} "
            f"· <strong style='color:{danger}'>{d.get('delay_days',0)} days overdue</strong></span>"
            f"</div>", unsafe_allow_html=True)

# ── Deliverable list by WP ────────────────────────────────────────────────────
section_label(f"📄 All Deliverables ({len(dels)})")

status_opts = ["planned","in_progress","submitted","accepted","delayed","cancelled"]
diss_labels = {"public":"🌐 Public","sensitive":"🔒 Sensitive",
               "confidential":"🔐 Confidential","internal":"🏢 Internal"}

wp_dels = {}
for d in sorted(dels, key=lambda x: x.get("delivery_month",0) or 0):
    wnum = wp_map.get(d.get("wp_id"),"No WP")
    if wnum not in wp_dels: wp_dels[wnum] = []
    wp_dels[wnum].append(d)

for wp_num, d_list in sorted(wp_dels.items()):
    acc2 = D["accent"]
    st.markdown(
        f"<div style='font-size:0.82rem;font-weight:700;color:{acc2};"
        f"margin:0.8rem 0 0.3rem'>📦 {wp_num}</div>",
        unsafe_allow_html=True)

    for d in d_list:
        did    = d["deliverable_id"]
        dnum   = d.get("deliverable_number","")
        dtitle = d.get("deliverable_title","")
        status = d.get("status","planned")
        s_color= DELIVERABLE_STATUS_COLORS.get(status, D["muted"])
        prog   = int(d.get("progress_percentage",0) or 0)
        plan_m = d.get("planned_delivery_month") or d.get("delivery_month")
        dtype  = d.get("deliverable_type","").replace("_"," ").title()
        diss   = diss_labels.get(d.get("dissemination_level",""),"")

        with st.expander(
            f"📄 {dnum}: {dtitle}  ·  {format_month(proj_start, plan_m, short=True)}  ·  {status.replace('_',' ').title()}",
            expanded=(status in ("in_progress","delayed"))
        ):
            dc1, dc2 = st.columns([3,2])
            with dc1:
                bg2 = D["bg2"]; border = D["border"]; txt = D["text"]
                st.markdown(
                    f"<div style='background:{bg2};border-left:4px solid {s_color};"
                    f"border-radius:8px;padding:0.8rem 1rem'>"
                    f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.4rem'>"
                    f"<span style='background:{s_color}22;color:{s_color};"
                    f"padding:2px 8px;border-radius:10px;font-size:0.75rem;font-weight:600'>"
                    f"{status.replace('_',' ').title()}</span>"
                    + (f"<span style='color:{muted};font-size:0.78rem'>{dtype}</span>" if dtype else "")
                    + (f"<span style='color:{muted};font-size:0.78rem'>{diss}</span>" if diss else "")
                    + f"</div>"
                    + (f"<div style='color:{txt};font-size:0.84rem'>{d.get('deliverable_description','')}</div>" if d.get("deliverable_description") else "")
                    + f"<div style='color:{muted};font-size:0.8rem;margin-top:0.3rem'>"
                    f"Planned delivery: {format_month(proj_start, plan_m)}"
                    + (f" · Submitted: {d['actual_submission_date']}" if d.get("actual_submission_date") else "")
                    + (f" · Accepted: {d['acceptance_date']}" if d.get("acceptance_date") else "")
                    + f"</div></div>", unsafe_allow_html=True)

                if prog:
                    st.progress(prog/100, text=f"Progress: {prog}%")

                if d.get("submission_link"):
                    acc3 = D["accent"]
                    st.markdown(
                        f"🔗 [View submission]({d['submission_link']})",
                        unsafe_allow_html=False)

            with dc2:
                with st.form(f"del_update_{did}"):
                    new_s = st.selectbox("Status", status_opts,
                        index=status_opts.index(status) if status in status_opts else 0,
                        format_func=lambda s: s.replace("_"," ").title(),
                        key=f"ds_{did}")
                    new_prog = st.slider("Progress %", 0, 100, prog, 5, key=f"dp_{did}")
                    new_sub  = None
                    new_acc  = None
                    if new_s in ("submitted","accepted"):
                        new_sub = st.date_input("Submission Date",
                            value=date.fromisoformat(str(d["actual_submission_date"])[:10])
                                  if d.get("actual_submission_date") else date.today(),
                            key=f"dsub_{did}")
                    if new_s == "accepted":
                        new_acc = st.date_input("Acceptance Date",
                            value=date.fromisoformat(str(d["acceptance_date"])[:10])
                                  if d.get("acceptance_date") else date.today(),
                            key=f"dacc_{did}")
                    new_link = st.text_input("Link to submission",
                        value=d.get("submission_link",""),
                        placeholder="https://…", key=f"dlink_{did}")
                    new_note = st.text_area("Reviewer comments",
                        value=d.get("reviewer_comment",""),
                        height=60, key=f"dnote_{did}")

                    if st.form_submit_button("💾 Save", type="primary",
                                             use_container_width=True):
                        if update_deliverable_progress(
                            did, new_s, new_prog, new_sub, new_acc, new_link, new_note
                        ):
                            st.success("✅ Saved!"); st.rerun()
