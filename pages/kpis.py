"""Octa Project Progress Tracker — KPI Progress Update."""
import streamlit as st
from datetime import date

from modules.auth import require_auth
from modules.sso import auto_login_from_url
from modules.ui_helpers import (inject_css, sidebar_nav, page_header,
                                 section_label, DARK)
from modules.database import get_project, get_kpis, db
from modules.charts import chart_kpi_achievement, fig_to_html

st.set_page_config(page_title="KPIs — Octa", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")
inject_css(); auto_login_from_url(); require_auth(); sidebar_nav()

sel_pid = st.session_state.get("selected_project_id", "")
if not sel_pid:
    st.switch_page("app.py"); st.stop()

proj    = get_project(sel_pid)
acronym = proj.get("acronym", "") or sel_pid

page_header("KPI Progress", f"{acronym} — Update achieved values against targets", "📊")
if st.button("← Dashboard"): st.switch_page("app.py")

D = DARK; muted = D["muted"]; acc = D["accent"]

kpis_short = get_kpis(sel_pid, "short_term")
kpis_long  = get_kpis(sel_pid, "long_term")


def _update_kpi(kpi_id, achieved_val, status, notes):
    try:
        db().table("kpis").update({
            "achieved_value":    achieved_val,
            "status":            status,
            "measurement_notes": notes,
            "last_measured_date": date.today().isoformat(),
        }).eq("kpi_id", kpi_id).execute()
        return True
    except Exception:
        return False


STATUS_OPTS = ["planned","on_track","achieved","partially_achieved","delayed","not_achieved"]
STATUS_COLORS = {
    "planned":"#8899b0","on_track":"#00BCD4","achieved":"#6fcf97",
    "partially_achieved":"#f6cc52","delayed":"#fc8181","not_achieved":"#e74c3c",
}


def _render_kpis(kpi_list, tab_key):
    if not kpi_list:
        st.info("No KPIs defined for this project.")
        return

    # Chart: baseline vs target vs achieved
    if any(k.get("target_value") for k in kpi_list):
        fig = chart_kpi_achievement(kpi_list)
        st.plotly_chart(fig, use_container_width=True)
        if st.button("📥 Export chart as HTML", key=f"exp_{tab_key}"):
            html = fig_to_html(fig, f"{acronym} — KPI Achievement")
            st.download_button("⬇ Download", html.encode("utf-8"),
                               f"{acronym}_kpi_{tab_key}.html", "text/html",
                               key=f"dl_{tab_key}")

    section_label(f"📋 Update KPIs ({len(kpi_list)})")

    for k in kpi_list:
        kid     = k["kpi_id"]
        knum    = k.get("kpi_number","")
        ktitle  = k.get("kpi_title","")
        status  = k.get("status","planned")
        s_color = STATUS_COLORS.get(status, D["muted"])

        try:    baseline = float(k.get("baseline_value","0") or 0)
        except: baseline = 0.0
        try:    target   = float(k.get("target_value","0")  or 0)
        except: target   = 0.0
        try:    achieved = float(k.get("achieved_value","0") or 0)
        except: achieved = 0.0

        # Progress %  relative to target
        pct = round(achieved / target * 100, 1) if target else 0
        pct = min(pct, 100)

        with st.expander(
            f"📊 {knum}: {ktitle}  ·  {status.replace('_',' ').title()}",
            expanded=(status in ("planned","on_track","delayed"))
        ):
            ec1, ec2 = st.columns([3, 2])

            with ec1:
                bg2 = D["bg2"]; txt = D["text"]
                st.markdown(
                    f"<div style='background:{bg2};border-left:4px solid {s_color};"
                    f"border-radius:8px;padding:0.9rem 1rem;margin-bottom:0.5rem'>"
                    f"<span style='background:{s_color}22;color:{s_color};"
                    f"padding:2px 9px;border-radius:10px;font-size:0.75rem;font-weight:600'>"
                    f"{status.replace('_',' ').title()}</span>"
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;"
                    f"gap:0.5rem;margin-top:0.6rem'>"
                    f"<div style='text-align:center;background:{D["bg3"]};"
                    f"border-radius:8px;padding:0.4rem'>"
                    f"<div style='font-size:1.2rem;font-weight:700;color:{muted}'>{baseline}</div>"
                    f"<div style='font-size:0.7rem;color:{muted}'>Baseline</div></div>"
                    f"<div style='text-align:center;background:{D["bg3"]};"
                    f"border-radius:8px;padding:0.4rem'>"
                    f"<div style='font-size:1.2rem;font-weight:700;color:{acc}'>{target}</div>"
                    f"<div style='font-size:0.7rem;color:{muted}'>Target</div></div>"
                    f"<div style='text-align:center;background:{D["bg3"]};"
                    f"border-radius:8px;padding:0.4rem'>"
                    f"<div style='font-size:1.2rem;font-weight:700;color:{D["success"]}'>{achieved if achieved else '—'}</div>"
                    f"<div style='font-size:0.7rem;color:{muted}'>Achieved</div></div>"
                    f"</div>"
                    f"<div style='font-size:0.78rem;color:{muted};margin-top:0.5rem'>"
                    f"Unit: <strong style='color:{txt}'>{k.get('unit','')}</strong>"
                    + (f" · Method: {k.get('measurement_method','')}" if k.get("measurement_method") else "")
                    + (f" · Last measured: {k.get('last_measured_date','')[:10]}" if k.get("last_measured_date") else "")
                    + f"</div></div>",
                    unsafe_allow_html=True)

                if pct > 0:
                    bar_color = D["success"] if pct >= 100 else (D["warning"] if pct >= 50 else D["danger"])
                    st.progress(pct / 100,
                                text=f"Achievement: {pct}% of target")

                if k.get("kpi_description"):
                    st.caption(k["kpi_description"])

                if k.get("measurement_notes"):
                    suc = D["success"]
                    st.markdown(
                        f"<div style='background:{suc}11;border-left:3px solid {suc};"
                        f"border-radius:6px;padding:0.3rem 0.7rem;font-size:0.8rem;color:{suc}'>"
                        f"📝 {k['measurement_notes']}</div>",
                        unsafe_allow_html=True)

            with ec2:
                with st.form(f"kpi_update_{kid}_{tab_key}"):
                    new_val = st.text_input(
                        "Achieved Value",
                        value=k.get("achieved_value","") or "",
                        placeholder=f"Target: {target} {k.get('unit','')}",
                        key=f"kv_{kid}"
                    )
                    new_status = st.selectbox(
                        "Status", STATUS_OPTS,
                        index=STATUS_OPTS.index(status) if status in STATUS_OPTS else 0,
                        format_func=lambda s: s.replace("_"," ").title(),
                        key=f"ks_{kid}"
                    )
                    new_notes = st.text_area(
                        "Measurement Notes",
                        value=k.get("measurement_notes","") or "",
                        height=80, key=f"kn_{kid}",
                        placeholder="Evidence, data source, context…"
                    )
                    if st.form_submit_button("💾 Save", type="primary",
                                             use_container_width=True):
                        if _update_kpi(kid, new_val.strip(), new_status, new_notes.strip()):
                            st.success("✅ Saved!"); st.rerun()
                        else:
                            st.error("Save failed.")


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_short, tab_long = st.tabs([
    f"⏱️ Short-Term KPIs ({len(kpis_short)})",
    f"🔭 Long-Term KPIs / Impact ({len(kpis_long)})",
])

with tab_short:
    st.markdown(
        f"<p style='color:{muted};font-size:0.85rem'>"
        f"Short-term KPIs are measured <strong>during the project</strong>. "
        f"Enter the latest achieved value and update the status.</p>",
        unsafe_allow_html=True)
    _render_kpis(kpis_short, "short")

with tab_long:
    st.markdown(
        f"<p style='color:{muted};font-size:0.85rem'>"
        f"Long-term KPIs measure <strong>post-project impact</strong>. "
        f"Update as post-project data becomes available.</p>",
        unsafe_allow_html=True)
    _render_kpis(kpis_long, "long")
