"""Octa Project Progress Tracker — Work Package Overview."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, format_month, DARK)
from modules.database import (get_project, get_work_packages,
                               get_tasks, get_deliverables, get_milestones,
                               get_project_partners)

st.set_page_config(page_title="Work Packages — Octa", page_icon="📦",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id", "")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj = get_project(sel_pid)
proj_start_raw = proj.get("project_start_date")
proj_start = date.fromisoformat(str(proj_start_raw)[:10]) if proj_start_raw else None
acronym = proj.get("acronym", "") or sel_pid

page_header("Work Package Overview",
            f"{acronym} — Leads, partners, timeline and completion per WP", "📦")
if st.button("← Dashboard"): st.switch_page("app.py")

D = DARK
muted = D["muted"]; acc = D["accent"]

wps      = get_work_packages(sel_pid)
tasks    = get_tasks(sel_pid)
dels     = get_deliverables(sel_pid)
mss      = get_milestones(sel_pid)
partners = get_project_partners(sel_pid)

partner_map = {p["id"]: p for p in partners}

if not wps:
    st.info("No work packages defined for this project yet.")
    st.stop()

# ── Summary KPIs ──────────────────────────────────────────────────────────────
section_label("📊 Overview")
k1, k2, k3, k4 = st.columns(4)
for col, label, val, color in [
    (k1, "Work Packages", len(wps),  acc),
    (k2, "Total Tasks",   len(tasks), D["accent2"]),
    (k3, "Deliverables",  len(dels),  D["success"]),
    (k4, "Milestones",    len(mss),   D["warning"]),
]:
    bg2 = D["bg2"]
    col.markdown(
        f"<div style='background:{bg2};border-top:3px solid {color};"
        f"border:1px solid {color}44;border-radius:10px;"
        f"padding:0.7rem;text-align:center'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:{color}'>{val}</div>"
        f"<div style='font-size:0.75rem;color:{muted}'>{label}</div></div>",
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── WP cards ──────────────────────────────────────────────────────────────────
section_label("📦 Work Packages")

WP_COLORS = ["#00BCD4","#FF6B35","#6fcf97","#f6cc52",
             "#9b59b6","#fc8181","#3498db","#e67e22",
             "#1abc9c","#e74c3c","#2ecc71","#8e44ad"]

for i, wp in enumerate(sorted(wps, key=lambda x: x.get("wp_number",""))):
    color   = WP_COLORS[i % len(WP_COLORS)]
    wp_id   = wp["wp_id"]
    wp_num  = wp.get("wp_number","")
    wp_title= wp.get("wp_title","")
    sm      = wp.get("start_month")
    em      = wp.get("end_month")

    # Lead partner
    lead_id   = wp.get("wp_lead_partner_id")
    lead_name = ""
    if lead_id and lead_id in partner_map:
        p = partner_map[lead_id]
        lead_name = p.get("full_name","") or p.get("short_name","")

    # Involved partners from work_package_partners
    try:
        from modules.database import db
        wpp = db().table("work_package_partners").select(
            "partner_id,role"
        ).eq("wp_id", wp_id).execute().data or []
        involved = []
        for row in wpp:
            pid = row.get("partner_id")
            if pid and pid in partner_map:
                p    = partner_map[pid]
                name = p.get("short_name","") or p.get("full_name","")
                role = row.get("role","")
                involved.append(f"{name}" + (f" ({role})" if role and role != "contributor" else ""))
    except Exception:
        involved = []

    # Task/deliverable stats for this WP
    wp_tasks = [t for t in tasks if t.get("wp_id") == wp_id]
    wp_dels  = [d for d in dels  if d.get("wp_id") == wp_id]
    wp_mss   = [m for m in mss   if m.get("wp_id") == wp_id]
    t_done   = sum(1 for t in wp_tasks if t.get("status") == "completed")
    d_done   = sum(1 for d in wp_dels  if d.get("status") in ("accepted","submitted"))
    m_done   = sum(1 for m in wp_mss   if m.get("status") == "achieved")

    bg2    = D["bg2"]; border = D["border"]; txt = D["text"]
    sm_str = format_month(proj_start, sm, short=True) if sm else "—"
    em_str = format_month(proj_start, em, short=True) if em else "—"

    with st.expander(
        f"📦 {wp_num}: {wp_title}  ·  {sm_str} → {em_str}",
        expanded=False
    ):
        wc1, wc2, wc3 = st.columns(3)

        with wc1:
            st.markdown(
                f"<div style='background:{bg2};border-left:4px solid {color};"
                f"border-radius:8px;padding:0.8rem 1rem'>"
                f"<div style='font-size:0.72rem;color:{muted};text-transform:uppercase;"
                f"font-weight:600;margin-bottom:0.3rem'>Timeline</div>"
                f"<div style='color:{txt}'>"
                f"<strong>Start:</strong> {sm_str}<br>"
                f"<strong>End:</strong> {em_str}"
                + (f"<br><strong>Duration:</strong> {int(em)-int(sm)+1} months"
                   if sm and em else "")
                + f"</div></div>", unsafe_allow_html=True)

        with wc2:
            st.markdown(
                f"<div style='background:{bg2};border-left:4px solid {color};"
                f"border-radius:8px;padding:0.8rem 1rem'>"
                f"<div style='font-size:0.72rem;color:{muted};text-transform:uppercase;"
                f"font-weight:600;margin-bottom:0.3rem'>Partners</div>"
                + (f"<div style='color:{color};font-weight:600'>⭐ Lead: {lead_name}</div>" if lead_name else "")
                + (f"<div style='color:{txt};font-size:0.82rem;margin-top:0.3rem'>"
                   + "<br>".join(f"• {n}" for n in involved[:6])
                   + ("</div>" if involved else "")
                   + (f"<span style='color:{muted};font-size:0.75rem'> +{len(involved)-6} more</span>" if len(involved)>6 else ""))
                + "</div>", unsafe_allow_html=True)

        with wc3:
            st.markdown(
                f"<div style='background:{bg2};border-left:4px solid {color};"
                f"border-radius:8px;padding:0.8rem 1rem'>"
                f"<div style='font-size:0.72rem;color:{muted};text-transform:uppercase;"
                f"font-weight:600;margin-bottom:0.4rem'>Completion</div>"
                f"<div style='color:{txt};font-size:0.85rem'>"
                f"⚙️ Tasks: <strong>{t_done}/{len(wp_tasks)}</strong> completed<br>"
                f"📄 Deliverables: <strong>{d_done}/{len(wp_dels)}</strong> submitted<br>"
                f"🏁 Milestones: <strong>{m_done}/{len(wp_mss)}</strong> achieved"
                f"</div></div>", unsafe_allow_html=True)

            # Progress bar (based on tasks)
            if wp_tasks:
                pct = round(t_done / len(wp_tasks) * 100)
                st.progress(pct / 100, text=f"Task completion: {pct}%")

        # Description
        if wp.get("wp_description"):
            st.markdown(
                f"<div style='color:{muted};font-size:0.83rem;padding:0.5rem 0'>"
                f"{wp['wp_description']}</div>", unsafe_allow_html=True)

        # Special type badges
        badges = []
        if wp.get("is_management_wp"):    badges.append("🏢 Management")
        if wp.get("is_communication_wp"): badges.append("📢 Communication")
        if wp.get("is_dissemination_wp"): badges.append("📡 Dissemination")
        if badges:
            st.markdown(
                " ".join(
                    f"<span style='background:{color}22;color:{color};"
                    f"padding:2px 9px;border-radius:10px;font-size:0.75rem'>{b}</span>"
                    for b in badges
                ), unsafe_allow_html=True)
