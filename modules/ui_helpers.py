"""Octa Project Progress Tracker — UI helpers."""
import streamlit as st
from config import DARK, APP_NAME, APP_VERSION

GLOBAL_CSS = f"""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="block-container"] {{
    background-color: {DARK['bg']} !important;
    color: {DARK['text']} !important;
}}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],
[data-testid="column"],.element-container,.stMarkdown {{
    background: transparent !important;
}}
h1,h2,h3,h4 {{ color: {DARK['text']} !important; }}
p, li {{ color: {DARK['text']}; }}
label,.stTextInput label,.stSelectbox label,.stMultiselect label,
.stTextArea label,.stNumberInput label,.stDateInput label {{
    color: {DARK['muted']} !important; font-size:0.85rem !important;
}}
[data-testid="stSidebar"] {{
    background: {DARK['sidebar']} !important;
    border-right: 3px solid {DARK['accent']} !important;
    box-shadow: 4px 0 20px rgba(0,188,212,0.1) !important;
}}
[data-testid="stSidebar"] * {{ color: {DARK['text']} !important; }}
[data-testid="stSidebarNav"] {{ display: none !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important; width: 100% !important;
    color: {DARK['text']} !important; font-size: 0.87rem !important;
    text-align: left !important; margin-bottom: 2px !important;
    transition: all 0.18s !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {DARK['accent']}22 !important;
    border-color: {DARK['accent']}66 !important;
    color: {DARK['accent']} !important;
}}
input,textarea {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    border-radius: 8px !important; color: {DARK['text']} !important;
}}
div[data-baseweb="select"] > div {{
    background: {DARK['bg3']} !important;
    border-color: {DARK['border']} !important; color: {DARK['text']} !important;
}}
div[data-baseweb="select"] * {{ color: {DARK['text']} !important; }}
div[data-baseweb="popover"] {{
    background: {DARK['bg2']} !important;
    border: 1px solid {DARK['border']} !important;
}}
div[data-baseweb="popover"] li:hover {{ background: {DARK['bg3']} !important; }}
[data-testid="stTabs"] [role="tablist"] {{
    background: {DARK['bg2']}; border-radius: 10px;
    padding: 4px; border: 1px solid {DARK['border']};
}}
[data-testid="stTabs"] [role="tab"] {{
    color: {DARK['muted']} !important; border-radius: 8px;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {DARK['accent']} !important; color: white !important;
}}
[data-testid="stButton"] > button {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    color: {DARK['text']} !important; border-radius: 8px !important;
    transition: all 0.2s !important;
}}
[data-testid="stButton"] > button:hover {{
    border-color: {DARK['accent']} !important; color: {DARK['accent']} !important;
}}
[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg,{DARK['accent']},#0097A7) !important;
    border: none !important; color: white !important; font-weight: 600 !important;
}}
[data-testid="stExpander"] {{
    background: {DARK['bg2']} !important;
    border: 1px solid {DARK['border']} !important; border-radius: 10px !important;
}}
[data-testid="stExpander"] summary {{ color: {DARK['text']} !important; }}
hr {{ border-color: {DARK['border']} !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {DARK['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {DARK['bg3']}; border-radius: 3px; }}
.page-header {{
    background: linear-gradient(135deg,{DARK['sidebar']} 0%,#2d4a7a 100%);
    padding: 1.2rem 1.8rem; border-radius: 12px;
    border-left: 4px solid {DARK['accent']}; margin-bottom: 1.4rem;
}}
.page-header h1 {{ margin:0; font-size:1.6rem; font-weight:700; color:white !important; }}
.page-header p  {{ margin:0.2rem 0 0; color:rgba(255,255,255,0.65)!important; font-size:0.88rem; }}
.section-label {{
    font-size:0.72rem; font-weight:600; letter-spacing:0.08em;
    text-transform:uppercase; color:{DARK['accent']};
    margin:1.2rem 0 0.5rem; padding-bottom:0.3rem;
    border-bottom:1px solid {DARK['border']};
}}
</style>
"""

def inject_css(): st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def page_header(title, subtitle="", icon=""):
    st.markdown(
        f"<div class='page-header'>"
        f"<h1>{icon+' ' if icon else ''}{title}</h1>"
        f"{'<p>'+subtitle+'</p>' if subtitle else ''}"
        f"</div>", unsafe_allow_html=True
    )

def section_label(text):
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)

def _hr():
    st.markdown(
        "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);margin:0.5rem 0'>",
        unsafe_allow_html=True)

def _nav_section(text):
    muted = DARK["muted"]
    st.markdown(
        f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;"
        f"text-transform:uppercase;color:{muted};margin-bottom:0.3rem'>{text}</div>",
        unsafe_allow_html=True)



def format_month(project_start, month_num, short: bool = False) -> str:
    """
    Convert a relative project month number to a human-readable calendar month.
    project_start: datetime.date or None
    month_num:     int (1-based) or None
    short:         True → "Feb 2028", False → "February 2028"

    Returns:
      "February 2028"  when project_start is known
      "Month 5"        when project_start is unknown (fallback)
      "—"              when month_num is None
    """
    if not month_num:
        return "—"
    try:
        month_num = int(month_num)
    except (TypeError, ValueError):
        return "—"

    if not project_start:
        return f"M{month_num}"

    try:
        from dateutil.relativedelta import relativedelta
        from datetime import date
        if isinstance(project_start, str):
            project_start = date.fromisoformat(project_start[:10])
        target = project_start + relativedelta(months=month_num - 1)
        fmt    = "%b %Y" if short else "%B %Y"
        return target.strftime(fmt)           # e.g. "February 2028"
    except Exception:
        return f"M{month_num}"


def format_month_range(project_start, start_month, end_month,
                        short: bool = False) -> str:
    """Format a month range, e.g. 'February 2027 – August 2028'."""
    s = format_month(project_start, start_month, short)
    e = format_month(project_start, end_month,   short)
    if s == "—" and e == "—":
        return "—"
    return f"{s} – {e}"


def sidebar_nav():
    is_auth       = st.session_state.get("authenticated", False)
    is_admin_user = st.session_state.get("role") == "admin"
    uname         = st.session_state.get("first_name") or st.session_state.get("username","")
    pid           = st.session_state.get("selected_project_id","")

    with st.sidebar:
        txt = DARK["text"]; muted = DARK["muted"]
        st.markdown(f"""
<div style="text-align:center;padding:0.8rem 0 0.6rem">
<div style="font-size:1.9rem">🏗️</div>
<div style="font-weight:700;font-size:0.88rem;color:{txt};line-height:1.3">{APP_NAME}</div>
<div style="color:{muted};font-size:0.65rem">v{APP_VERSION}</div>
</div>""", unsafe_allow_html=True)

        if is_auth and uname:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.07);"
                f"border:1px solid rgba(255,255,255,0.12);border-radius:8px;"
                f"padding:0.35rem 0.7rem;font-size:0.8rem;margin-bottom:0.3rem'>"
                f"👤 <strong style='color:{txt}'>{uname}</strong></div>",
                unsafe_allow_html=True)

        if pid:
            acc = DARK["accent"]
            st.markdown(
                f"<div style='background:{acc}15;border:1px solid {acc}44;"
                f"border-radius:6px;padding:0.3rem 0.6rem;font-size:0.75rem;"
                f"color:{acc};margin-bottom:0.3rem'>📋 {pid}</div>",
                unsafe_allow_html=True)

        _hr()

        # ── Monitoring ────────────────────────────────────────────────────────
        _nav_section("Monitoring")
        if st.button("🏠  Dashboard",           key="nav_dash",  use_container_width=True):
            st.switch_page("app.py")
        if st.button("📦  WP Overview",         key="nav_wp",    use_container_width=True):
            st.switch_page("pages/work_packages.py")
        if st.button("🏁  Milestones",          key="nav_ms",    use_container_width=True):
            st.switch_page("pages/milestones.py")
        if st.button("📄  Deliverables",        key="nav_del",   use_container_width=True):
            st.switch_page("pages/deliverables.py")
        if st.button("⚙️  Tasks",               key="nav_task",  use_container_width=True):
            st.switch_page("pages/tasks.py")
        if st.button("📊  KPIs",                key="nav_kpi",   use_container_width=True):
            st.switch_page("pages/kpis.py")
        if st.button("🌍  Partner Map",         key="nav_map",   use_container_width=True):
            st.switch_page("pages/partner_map.py")

        _hr()

        # ── Administration ────────────────────────────────────────────────────
        if is_admin_user:
            _nav_section("Administration")
            if st.button("🛡️  Admin Panel", key="nav_admin", use_container_width=True):
                st.switch_page("pages/admin.py")
            _hr()

        # ── Account ───────────────────────────────────────────────────────────
        _nav_section("Account")
        if is_auth:
            if st.button("🚪  Sign Out", use_container_width=True, key="nav_signout"):
                try:
                    from modules.sso import logout
                    logout()
                except Exception:
                    pass
                st.switch_page("pages/login.py")
        else:
            if st.button("🔑  Login", use_container_width=True, key="nav_login"):
                st.switch_page("pages/login.py")

        st.markdown(
            f"<div style='color:{muted};font-size:0.62rem;text-align:center;"
            f"margin-top:1rem'>Octa Platform · "
            f"{__import__('datetime').date.today().year}</div>",
            unsafe_allow_html=True)


def kpi_card(col, label: str, value, color: str, subtitle: str = ""):
    bg2 = DARK["bg2"]; muted = DARK["muted"]
    col.markdown(
        f"<div style='background:{bg2};border-top:3px solid {color};"
        f"border:1px solid {color}44;border-radius:10px;"
        f"padding:0.8rem;text-align:center'>"
        f"<div style='font-size:1.6rem;font-weight:700;color:{color}'>{value}</div>"
        f"<div style='font-size:0.78rem;color:{muted}'>{label}</div>"
        + (f"<div style='font-size:0.72rem;color:{muted};margin-top:2px'>{subtitle}</div>" if subtitle else "")
        + "</div>", unsafe_allow_html=True)


def deviation_badge(planned, actual, unit: str = "months") -> str:
    """Return coloured HTML badge showing deviation."""
    D = DARK
    if planned is None or actual is None:
        return ""
    try:
        delta = int(actual) - int(planned)
    except Exception:
        return ""
    if delta == 0:
        return f"<span style='color:{D["success"]};font-size:0.75rem'>✓ On time</span>"
    elif delta > 0:
        return (f"<span style='color:{D["danger"]};font-size:0.75rem'>"
                f"⚠ +{delta} {unit} late</span>")
    else:
        return (f"<span style='color:{D["success"]};font-size:0.75rem'>"
                f"↑ {abs(delta)} {unit} early</span>")
