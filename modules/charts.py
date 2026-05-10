"""
Octa Project Progress Tracker — Reusable Plotly Charts
All colours defined inline. No external module dependencies at import time.
"""
import plotly.graph_objects as go
from datetime import date

# ── Inline colour palette ─────────────────────────────────────────────────────
D = {
    "bg":      "#0f1421", "bg2":    "#1a2235", "bg3":  "#232f45",
    "text":    "#e2e8f0", "muted":  "#8899b0", "accent":"#00BCD4",
    "accent2": "#FF6B35", "success":"#6fcf97", "warning":"#f6cc52",
    "danger":  "#fc8181", "border": "rgba(255,255,255,0.09)",
}

TASK_STATUS_COLORS = {
    "planned":"#8899b0","ongoing":"#00BCD4",
    "completed":"#6fcf97","delayed":"#fc8181","cancelled":"#4a4a6a",
}
DELIVERABLE_STATUS_COLORS = {
    "planned":"#8899b0","in_progress":"#f6cc52","submitted":"#00BCD4",
    "accepted":"#6fcf97","delayed":"#fc8181","cancelled":"#4a4a6a",
}
MILESTONE_STATUS_COLORS = {
    "planned":"#8899b0","achieved":"#6fcf97",
    "partially_achieved":"#f6cc52","delayed":"#fc8181","not_achieved":"#e74c3c",
}


def _layout(fig, title="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(color=D["text"], size=13)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=height, margin=dict(l=10, r=10, t=100 if title else 20, b=50),
        font=dict(color=D["text"], size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=D["text"], size=10),
                    orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"],
                   zerolinecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"],
                   zerolinecolor="rgba(255,255,255,0.1)"),
    )
    return fig


def _month_to_date(project_start, month_num):
    if not project_start or not month_num:
        return None
    try:
        from dateutil.relativedelta import relativedelta
        return project_start + relativedelta(months=int(month_num) - 1)
    except Exception:
        return None


def _date_to_month(project_start, d):
    if not project_start or not d:
        return None
    try:
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(d, project_start)
        return max(1, delta.years * 12 + delta.months + 1)
    except Exception:
        return None


# ── 1. Task status donut ──────────────────────────────────────────────────────
def chart_task_status(tasks, title="Tasks by Status"):
    counts = {}
    for t in tasks:
        s = t.get("status", "planned")
        counts[s] = counts.get(s, 0) + 1
    if not counts:
        return go.Figure()
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [TASK_STATUS_COLORS.get(l, D["muted"]) for l in labels]
    fig = go.Figure(go.Pie(
        labels=[l.replace("_", " ").title() for l in labels],
        values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=D["bg"], width=2)),
        textfont=dict(color=D["text"]),
    ))
    return _layout(fig, title, 320)


# ── 2. Deliverable status donut ───────────────────────────────────────────────
def chart_deliverable_status(deliverables, title="Deliverables by Status"):
    counts = {}
    for d in deliverables:
        s = d.get("status", "planned")
        counts[s] = counts.get(s, 0) + 1
    if not counts:
        return go.Figure()
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [DELIVERABLE_STATUS_COLORS.get(l, D["muted"]) for l in labels]
    fig = go.Figure(go.Pie(
        labels=[l.replace("_", " ").title() for l in labels],
        values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=D["bg"], width=2)),
        textfont=dict(color=D["text"]),
    ))
    return _layout(fig, title, 320)


# ── 3. Milestone timeline ─────────────────────────────────────────────────────
def chart_milestone_timeline(milestones, project_start=None,
                              title="Milestone Timeline"):
    if not milestones:
        return go.Figure()

    use_dates = project_start is not None

    def _x(month_num):
        if not month_num:
            return None
        try:
            m = int(month_num)
        except Exception:
            return None
        if use_dates:
            return _month_to_date(project_start, m)
        return m

    def _label(month_num):
        if not month_num:
            return "—"
        try:
            m = int(month_num)
        except Exception:
            return "—"
        if use_dates and project_start:
            d = _month_to_date(project_start, m)
            return d.strftime("%B %Y") if d else f"M{m}"
        return f"Month {m}"

    sorted_ms     = sorted(milestones, key=lambda m: m.get("due_month", 0) or 0)
    names         = [f"{m['milestone_number']}: {m.get('milestone_title','')[:30]}"
                     for m in sorted_ms]
    status_colors = [MILESTONE_STATUS_COLORS.get(m.get("status","planned"), D["muted"])
                     for m in sorted_ms]
    planned_x     = [_x(m.get("planned_due_month") or m.get("due_month")) for m in sorted_ms]
    planned_lbl   = [_label(m.get("planned_due_month") or m.get("due_month")) for m in sorted_ms]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=planned_x, y=names, mode="markers",
        marker=dict(symbol="circle", size=14,
                    color=status_colors,  opacity=0.35,
                    line=dict(color=status_colors, width=2)),
        name="Planned", customdata=planned_lbl,
        hovertemplate="<b>%{y}</b><br>📅 Planned: %{customdata}<extra></extra>",
    ))

    ach_x, ach_y, ach_lbl = [], [], []
    for m, name in zip(sorted_ms, names):
        if m.get("status") == "achieved" and m.get("achieved_date"):
            try:
                ad = date.fromisoformat(str(m["achieved_date"])[:10])
                ach_x.append(ad if use_dates else
                             (_date_to_month(project_start, ad) if project_start else
                              int(m.get("due_month") or 0)))
                ach_y.append(name)
                ach_lbl.append(ad.strftime("%B %Y") if use_dates else
                               f"Month {m.get('due_month','?')}")
            except Exception:
                pass

    if ach_x:
        fig.add_trace(go.Scatter(
            x=ach_x, y=ach_y, mode="markers",
            marker=dict(symbol="diamond", size=14, color=D["success"],
                        line=dict(color="white", width=1)),
            name="Achieved", customdata=ach_lbl,
            hovertemplate="<b>%{y}</b><br>✅ Achieved: %{customdata}<extra></extra>",
        ))

    xaxis = dict(type="date", title="Calendar Date") if use_dates else dict(title="Project Month")
    fig.update_layout(xaxis=xaxis, yaxis=dict(autorange="reversed"))
    return _layout(fig, title, max(280, len(milestones) * 42 + 80))


# ── 4. Progress over time ─────────────────────────────────────────────────────
def chart_progress_over_time(snapshots, title="Overall Progress by Period"):
    if not snapshots:
        return go.Figure()
    periods  = [s["reporting_period"] for s in snapshots]
    progress = [float(s.get("overall_progress_pct", 0) or 0) for s in snapshots]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=periods, y=[100] * len(periods), mode="lines",
        line=dict(color="rgba(111,207,151,0.33)", dash="dash", width=2),
        name="Target (100%)",
    ))
    fig.add_trace(go.Scatter(
        x=periods, y=progress, mode="lines+markers",
        line=dict(color=D["accent"], width=3),
        marker=dict(size=8, color=D["accent"]),
        fill="tozeroy", fillcolor="rgba(0,188,212,0.13)",
        name="Actual Progress",
        hovertemplate="Period %{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Reporting Period", yaxis_title="Progress %",
                      yaxis=dict(range=[0, 110]))
    return _layout(fig, title, 320)


# ── 5. WP completion bar chart ────────────────────────────────────────────────
def chart_wp_completion(work_packages, tasks, deliverables,
                         title="Completion by Work Package"):
    if not work_packages:
        return go.Figure()
    wp_labels, task_done, task_total, del_done, del_total = [], [], [], [], []
    for wp in work_packages:
        wid = wp["wp_id"]
        wt  = [t for t in tasks        if t.get("wp_id") == wid]
        wd  = [d for d in deliverables if d.get("wp_id") == wid]
        wp_labels.append(wp.get("wp_number", ""))
        task_total.append(len(wt))
        task_done.append(sum(1 for t in wt if t.get("status") == "completed"))
        del_total.append(len(wd))
        del_done.append(sum(1 for d in wd if d.get("status") in ("accepted", "submitted")))
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Tasks — Total",       x=wp_labels, y=task_total,
                         marker_color="rgba(0,188,212,0.33)",
                         hovertemplate="%{x}: %{y} tasks total<extra></extra>"))
    fig.add_trace(go.Bar(name="Tasks — Done",         x=wp_labels, y=task_done,
                         marker_color=D["accent"],
                         hovertemplate="%{x}: %{y} completed<extra></extra>"))
    fig.add_trace(go.Bar(name="Deliverables — Total", x=wp_labels, y=del_total,
                         marker_color="rgba(111,207,151,0.33)",
                         hovertemplate="%{x}: %{y} deliverables total<extra></extra>"))
    fig.add_trace(go.Bar(name="Deliverables — Done",  x=wp_labels, y=del_done,
                         marker_color=D["success"],
                         hovertemplate="%{x}: %{y} accepted<extra></extra>"))
    fig.update_layout(barmode="group", xaxis_title="Work Package", yaxis_title="Count")
    return _layout(fig, title, 360)


# ── 6. Delay analysis ─────────────────────────────────────────────────────────
def chart_delay_analysis(items, number_col, title_col, planned_col, actual_col,
                          title="Delay Analysis (months)"):
    labels, delays = [], []
    for item in items:
        planned = item.get(planned_col) or item.get("due_month") or 0
        actual  = item.get(actual_col)
        if actual and planned:
            try:
                delay = int(actual) - int(planned)
                labels.append(f"{item.get(number_col,'')}: {item.get(title_col,'')[:25]}")
                delays.append(delay)
            except Exception:
                pass
    if not labels:
        return go.Figure()
    colors = [D["danger"] if d > 0 else (D["success"] if d < 0 else D["muted"]) for d in delays]
    fig = go.Figure(go.Bar(
        x=delays, y=labels, orientation="h",
        marker_color=colors, marker_line_width=0,
        hovertemplate="%{y}<br>Delay: %{x} month(s)<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(xaxis_title="Delay (months)", yaxis=dict(autorange="reversed"))
    return _layout(fig, title, max(300, len(labels) * 32 + 80))


# ── 7. KPI achievement ────────────────────────────────────────────────────────
def chart_kpi_achievement(kpis, title="KPI Achievement vs Target"):
    if not kpis:
        return go.Figure()
    labels, baselines, targets, achieved = [], [], [], []
    for k in kpis:
        labels.append(f"{k['kpi_number']}: {k.get('kpi_title','')[:30]}")
        try:    baselines.append(float(k.get("baseline_value","0") or 0))
        except: baselines.append(0)
        try:    targets.append(float(k.get("target_value","0") or 0))
        except: targets.append(0)
        try:    achieved.append(float(k.get("achieved_value","0") or 0))
        except: achieved.append(0)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Baseline", x=labels, y=baselines,
                         marker_color="rgba(136,153,176,0.33)"))
    fig.add_trace(go.Bar(name="Target",   x=labels, y=targets,
                         marker_color="rgba(0,188,212,0.33)"))
    fig.add_trace(go.Bar(name="Achieved", x=labels, y=achieved,
                         marker_color=D["success"]))
    fig.update_layout(barmode="group", xaxis_tickangle=-30)
    return _layout(fig, title, 380)


# ── 8. Budget gauge ───────────────────────────────────────────────────────────
def chart_budget_gauge(planned, spent, title="Budget Consumption"):
    pct   = round(spent / planned * 100, 1) if planned else 0
    color = D["success"] if pct < 75 else (D["warning"] if pct < 95 else D["danger"])
    fig   = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = pct,
        number = {"suffix": "%", "font": {"color": D["text"], "size": 36}},
        gauge  = {
            "axis":      {"range": [0, 100], "tickcolor": D["muted"],
                          "tickfont": {"color": D["muted"], "size": 10}},
            "bar":       {"color": color, "thickness": 0.7},
            "bgcolor":   "rgba(0,0,0,0)",
            "borderwidth": 0,
            "threshold": {"line": {"color": D["danger"], "width": 3},
                          "thickness": 0.8, "value": 90},
        },
        title = {"text": f"<b>{title}</b><br>€{spent:,.0f} of €{planned:,.0f}",
                 "font": {"color": D["muted"], "size": 12}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=280, margin=dict(l=20, r=20, t=60, b=20),
                      font=dict(color=D["text"]))
    return fig


# ── 9. Partner map ────────────────────────────────────────────────────────────
def chart_partner_map(partners, project_title="", scope="world"):
    try:
        from config import COUNTRY_ISO
    except ImportError:
        COUNTRY_ISO = {}

    if not partners:
        return go.Figure()

    country_data = {}
    for p in partners:
        country  = (p.get("country") or "").strip()
        iso      = COUNTRY_ISO.get(country, "")
        if not iso:
            continue
        is_coord = p.get("is_coordinator", False)
        if country not in country_data:
            country_data[country] = {"iso": iso, "is_coord": is_coord, "partners": []}
        if is_coord:
            country_data[country]["is_coord"] = True
        pname = p.get("full_name", "") or p.get("short_name", "")
        country_data[country]["partners"].append(pname)

    if not country_data:
        return go.Figure()

    coord_rows   = [(c, i) for c, i in country_data.items() if i["is_coord"]]
    partner_rows = [(c, i) for c, i in country_data.items() if not i["is_coord"]]

    fig = go.Figure()

    if partner_rows:
        fig.add_trace(go.Choropleth(
            locations=[i["iso"] for _, i in partner_rows],
            z=[1] * len(partner_rows),
            text=[c for c, _ in partner_rows],
            customdata=[[len(i["partners"]),
                         "<br>".join(f"• {p}" for p in i["partners"])]
                        for _, i in partner_rows],
            colorscale=[[0, D["success"]], [1, D["success"]]],
            showscale=False,
            marker_line_color="rgba(255,255,255,0.3)",
            marker_line_width=0.8,
            hovertemplate="<b>%{text}</b><br>Partners: %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            name="Partner",
        ))

    if coord_rows:
        fig.add_trace(go.Choropleth(
            locations=[i["iso"] for _, i in coord_rows],
            z=[2] * len(coord_rows),
            text=[c for c, _ in coord_rows],
            customdata=[[len(i["partners"]),
                         "<br>".join(f"• {p}" for p in i["partners"]) + "<br>⭐ Coordinator"]
                        for _, i in coord_rows],
            colorscale=[[0, D["accent"]], [1, D["accent"]]],
            showscale=False,
            marker_line_color="rgba(255,255,255,0.5)",
            marker_line_width=1.2,
            hovertemplate="<b>%{text}</b><br>%{customdata[1]}<extra></extra>",
            name="Coordinator",
        ))

    # For europe scope: use explicit lat/lon bounds so Turkey & Ukraine are visible
    if scope == "europe":
        geo_cfg = dict(
            showcoastlines=True, coastlinecolor="rgba(255,255,255,0.15)",
            showland=True, landcolor="#1a2235",
            showocean=True, oceancolor="#0f1421",
            showframe=False, showcountries=True,
            countrycolor="rgba(255,255,255,0.08)",
            bgcolor="rgba(0,0,0,0)",
            projection_type="mercator",
            lataxis_range=[30, 72],
            lonaxis_range=[-28, 50],
        )
    else:
        geo_cfg = dict(
            scope=scope,
            showcoastlines=True, coastlinecolor="rgba(255,255,255,0.15)",
            showland=True, landcolor="#1a2235",
            showocean=True, oceancolor="#0f1421",
            showframe=False, showcountries=True,
            countrycolor="rgba(255,255,255,0.08)",
            bgcolor="rgba(0,0,0,0)",
        )
    fig.update_layout(
        geo=geo_cfg,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=420, margin=dict(l=0, r=0, t=40, b=0),
        font_color=D["text"], showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=D["text"])),
        title=dict(
            text=f"🌍 Partner Countries — {project_title}" if project_title else "🌍 Partner Countries",
            font=dict(color=D["text"], size=13),
        ),
    )
    return fig


# ── Export helper ─────────────────────────────────────────────────────────────
def fig_to_html(fig, title=""):
    if title:
        fig.update_layout(title=dict(text=title))
    return fig.to_html(
        full_html=True, include_plotlyjs=True,
        config={"responsive": True, "scrollZoom": True, "displayModeBar": True},
    )
