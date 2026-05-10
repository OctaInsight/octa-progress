"""
Octa Project Progress Tracker — Reusable Plotly Charts
Every function returns a Plotly Figure.
Use fig.to_html(full_html=True, include_plotlyjs=True) to export as HTML.
Baseline/target shown in pale colours; actual in solid colours.
"""
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
# All colours defined inline — no config dependency at module level
try:
    from config import DARK as D
except ImportError:
    D = {"bg":"#0f1421","bg2":"#1a2235","bg3":"#232f45",
         "text":"#e2e8f0","muted":"#8899b0","accent":"#00BCD4",
         "accent2":"#FF6B35","success":"#6fcf97","warning":"#f6cc52",
         "danger":"#fc8181","border":"rgba(255,255,255,0.09)"}

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
# ── Local helper (avoids circular import with database.py) ────────────────────
def __date_to_month(project_start, d):
    """Convert a calendar date to a relative project month number (1-based)."""
    if not project_start or not d:
        return None
    try:
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(d, project_start)
        return max(1, delta.years * 12 + delta.months + 1)
    except Exception:
        return None




def _layout(fig, title: str = "", height: int = 380) -> go.Figure:
    """Apply dark theme layout to any figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(color=D["text"], size=13)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=0, r=0, t=40 if title else 10, b=40),
        font=dict(color=D["text"], size=11),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=D["text"], size=11),
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0
        ),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"],
                   zerolinecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"],
                   zerolinecolor="rgba(255,255,255,0.1)"),
    )
    return fig


# ── 1. Task status donut ──────────────────────────────────────────────────────

def chart_task_status(tasks: list, title: str = "Tasks by Status") -> go.Figure:
    counts = {}
    for t in tasks:
        s = t.get("status","planned")
        counts[s] = counts.get(s,0) + 1
    if not counts:
        return go.Figure()

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [TASK_STATUS_COLORS.get(l, D["muted"]) for l in labels]
    labels_nice = [l.replace("_"," ").title() for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels_nice, values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=D["bg"], width=2)),
        textfont=dict(color=D["text"]),
    ))
    return _layout(fig, title, 320)


# ── 2. Deliverable status donut ───────────────────────────────────────────────

def chart_deliverable_status(deliverables: list,
                              title: str = "Deliverables by Status") -> go.Figure:
    counts = {}
    for d in deliverables:
        s = d.get("status","planned")
        counts[s] = counts.get(s,0) + 1
    if not counts:
        return go.Figure()

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [DELIVERABLE_STATUS_COLORS.get(l, D["muted"]) for l in labels]

    fig = go.Figure(go.Pie(
        labels=[l.replace("_"," ").title() for l in labels],
        values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=D["bg"], width=2)),
        textfont=dict(color=D["text"]),
    ))
    return _layout(fig, title, 320)


# ── 3. Milestone timeline (planned vs achieved) ───────────────────────────────

def chart_milestone_timeline(milestones: list,
                              project_start: date = None,
                              title: str = "Milestone Timeline") -> go.Figure:
    """
    Horizontal timeline — x-axis shows actual calendar dates when
    project_start is known, otherwise relative month numbers.
    Planned = pale circles; Achieved = solid diamonds.
    """
    if not milestones:
        return go.Figure()

    try:
        from dateutil.relativedelta import relativedelta as _rdelta
        use_dates = project_start is not None
    except ImportError:
        use_dates = False

    def _m_to_x(month_num):
        """Convert month number to x-axis value (date or int)."""
        if not month_num:
            return None
        try:
            m = int(month_num)
        except Exception:
            return None
        if use_dates and project_start:
            return project_start + _rdelta(months=m - 1)
        return m

    def _m_label(month_num):
        """Human-readable label for hover."""
        if not month_num:
            return "—"
        try:
            m = int(month_num)
        except Exception:
            return "—"
        if use_dates and project_start:
            d = project_start + _rdelta(months=m - 1)
            return d.strftime("%B %Y")
        return f"Month {m}"

    sorted_ms = sorted(milestones, key=lambda m: m.get("due_month",0) or 0)
    names  = [f"{m['milestone_number']}: {m.get('milestone_title','')[:30]}"
              for m in sorted_ms]
    status_colors = [MILESTONE_STATUS_COLORS.get(m.get("status","planned"), D["muted"])
                     for m in sorted_ms]

    planned_x = [_m_to_x(m.get("planned_due_month") or m.get("due_month")) for m in sorted_ms]
    planned_labels = [_m_label(m.get("planned_due_month") or m.get("due_month")) for m in sorted_ms]

    fig = go.Figure()

    # Planned (pale circles)
    fig.add_trace(go.Scatter(
        x=planned_x, y=names, mode="markers",
        marker=dict(symbol="circle", size=14,
                    color=[c + "55" for c in status_colors],
                    line=dict(color=status_colors, width=2)),
        name="Planned",
        customdata=planned_labels,
        hovertemplate="<b>%{y}</b><br>📅 Planned: %{customdata}<extra></extra>",
    ))

    # Achieved (solid diamonds)
    ach_x, ach_y, ach_labels = [], [], []
    for m, name in zip(sorted_ms, names):
        if m.get("status") == "achieved" and m.get("achieved_date"):
            try:
                ad = date.fromisoformat(str(m["achieved_date"])[:10])
                ach_x.append(ad if use_dates else
                             (_date_to_month(project_start, ad) if project_start else
                              int(m.get("due_month") or 0)))
                ach_y.append(name)
                ach_labels.append(ad.strftime("%B %Y") if use_dates else
                                  f"Month {m.get('due_month','?')}")
            except Exception:
                pass

    if ach_x:
        fig.add_trace(go.Scatter(
            x=ach_x, y=ach_y, mode="markers",
            marker=dict(symbol="diamond", size=14, color=D["success"],
                        line=dict(color="white", width=1)),
            name="Achieved",
            customdata=ach_labels,
            hovertemplate="<b>%{y}</b><br>✅ Achieved: %{customdata}<extra></extra>",
        ))

    xaxis_cfg = dict(autorange=True)
    if use_dates:
        xaxis_cfg["type"] = "date"
        xaxis_cfg["title"] = "Calendar Date"
    else:
        xaxis_cfg["title"] = "Project Month"

    fig.update_layout(xaxis=xaxis_cfg, yaxis=dict(autorange="reversed"))
    return _layout(fig, title, max(280, len(milestones)*42+80))


# ── 4. Progress over time (snapshots) ────────────────────────────────────────

def chart_progress_over_time(snapshots: list,
                              title: str = "Overall Progress by Period") -> go.Figure:
    if not snapshots:
        return go.Figure()

    periods  = [s["reporting_period"] for s in snapshots]
    progress = [float(s.get("overall_progress_pct",0) or 0) for s in snapshots]
    target   = [100] * len(periods)

    fig = go.Figure()
    # Target line (pale)
    fig.add_trace(go.Scatter(
        x=periods, y=target, mode="lines",
        line=dict(color=D["success"]+"55", dash="dash", width=2),
        name="Target (100%)",
        hovertemplate="Period %{x}: Target %{y}%<extra></extra>",
    ))
    # Actual progress
    fig.add_trace(go.Scatter(
        x=periods, y=progress, mode="lines+markers",
        line=dict(color=D["accent"], width=3),
        marker=dict(size=8, color=D["accent"]),
        fill="tozeroy",
        fillcolor=D["accent"]+"22",
        name="Actual Progress",
        hovertemplate="Period %{x}: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(xaxis_title="Reporting Period", yaxis_title="Progress %",
                      yaxis=dict(range=[0,110]))
    return _layout(fig, title, 320)


# ── 5. Tasks vs deliverables per WP (stacked bar) ────────────────────────────

def chart_wp_completion(work_packages: list, tasks: list,
                         deliverables: list,
                         title: str = "Completion by Work Package") -> go.Figure:
    if not work_packages:
        return go.Figure()

    wp_labels  = [w.get("wp_number","") for w in work_packages]
    task_done  = []
    task_total = []
    del_done   = []
    del_total  = []

    for wp in work_packages:
        wid    = wp["wp_id"]
        wt     = [t for t in tasks if t.get("wp_id") == wid]
        wd     = [d for d in deliverables if d.get("wp_id") == wid]
        task_total.append(len(wt))
        task_done.append(sum(1 for t in wt if t.get("status")=="completed"))
        del_total.append(len(wd))
        del_done.append(sum(1 for d in wd if d.get("status") in ("accepted","submitted")))

    fig = go.Figure()

    # Task total (pale background bar)
    fig.add_trace(go.Bar(
        name="Tasks — Target", x=wp_labels, y=task_total,
        marker_color=D["accent"]+"33", marker_line_width=0, width=0.35,
        offset=-0.2,
        hovertemplate="%{x}: %{y} tasks total<extra></extra>",
    ))
    # Task completed (solid bar)
    fig.add_trace(go.Bar(
        name="Tasks — Completed", x=wp_labels, y=task_done,
        marker_color=D["accent"], marker_line_width=0, width=0.35,
        offset=-0.2,
        hovertemplate="%{x}: %{y} tasks completed<extra></extra>",
    ))
    # Deliverable total (pale)
    fig.add_trace(go.Bar(
        name="Deliverables — Target", x=wp_labels, y=del_total,
        marker_color=D["success"]+"33", marker_line_width=0, width=0.35,
        offset=0.2,
        hovertemplate="%{x}: %{y} deliverables total<extra></extra>",
    ))
    # Deliverables done (solid)
    fig.add_trace(go.Bar(
        name="Deliverables — Done", x=wp_labels, y=del_done,
        marker_color=D["success"], marker_line_width=0, width=0.35,
        offset=0.2,
        hovertemplate="%{x}: %{y} deliverables accepted<extra></extra>",
    ))

    fig.update_layout(barmode="overlay", xaxis_title="Work Package",
                      yaxis_title="Count")
    return _layout(fig, title, 360)


# ── 6. Delay analysis (planned vs actual months, bar chart) ──────────────────

def chart_delay_analysis(items: list, number_col: str, title_col: str,
                          planned_col: str, actual_col: str,
                          title: str = "Delay Analysis (months)") -> go.Figure:
    """
    Compares planned month vs actual month for tasks/deliverables.
    Positive = delayed, Negative = ahead of schedule.
    """
    labels, delays = [], []
    for item in items:
        planned = item.get(planned_col) or item.get("due_month") or 0
        actual  = item.get(actual_col)
        if actual and planned:
            delay = int(actual) - int(planned)
            labels.append(f"{item.get(number_col,'')}: {item.get(title_col,'')[:25]}")
            delays.append(delay)

    if not labels:
        return go.Figure()

    colors = [D["danger"] if d > 0 else (D["success"] if d < 0 else D["muted"])
              for d in delays]

    fig = go.Figure(go.Bar(
        x=delays, y=labels, orientation="h",
        marker_color=colors, marker_line_width=0,
        hovertemplate="%{y}<br>Delay: %{x} month(s)<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(
        xaxis_title="Delay (months) — positive = late, negative = ahead",
        yaxis=dict(autorange="reversed")
    )
    return _layout(fig, title, max(300, len(labels)*32+80))


# ── 7. KPI achievement (target vs achieved) ──────────────────────────────────

def chart_kpi_achievement(kpis: list,
                           title: str = "KPI Achievement vs Target") -> go.Figure:
    """Bar chart: baseline (pale) → target (mid) → achieved (solid)."""
    if not kpis:
        return go.Figure()

    labels    = [f"{k['kpi_number']}: {k.get('kpi_title','')[:30]}" for k in kpis]
    baselines = []
    targets   = []
    achieved  = []

    for k in kpis:
        try:    baselines.append(float(k.get("baseline_value","0") or 0))
        except: baselines.append(0)
        try:    targets.append(float(k.get("target_value","0") or 0))
        except: targets.append(0)
        try:    achieved.append(float(k.get("achieved_value","0") or 0))
        except: achieved.append(0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Baseline", x=labels, y=baselines,
                         marker_color=D["muted"]+"55", marker_line_width=0,
                         hovertemplate="%{x}<br>Baseline: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(name="Target", x=labels, y=targets,
                         marker_color=D["accent"]+"55", marker_line_width=0,
                         hovertemplate="%{x}<br>Target: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(name="Achieved", x=labels, y=achieved,
                         marker_color=D["success"], marker_line_width=0,
                         hovertemplate="%{x}<br>Achieved: %{y}<extra></extra>"))

    fig.update_layout(barmode="group", xaxis_tickangle=-30)
    return _layout(fig, title, 380)


# ── 8. Budget consumption gauge ──────────────────────────────────────────────

def chart_budget_gauge(planned: float, spent: float,
                        title: str = "Budget Consumption") -> go.Figure:
    pct   = round(spent / planned * 100, 1) if planned else 0
    color = D["success"] if pct < 75 else (D["warning"] if pct < 95 else D["danger"])

    fig = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = pct,
        number = {"suffix": "%", "font": {"color": D["text"], "size": 36}},
        gauge  = {
            "axis": {
                "range":    [0, 100],
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0%","25%","50%","75%","100%"],
                "tickcolor": D["muted"],
                "tickfont":  {"color": D["muted"], "size": 10},
            },
            "bar":         {"color": color, "thickness": 0.7},
            "bgcolor":     "rgba(0,0,0,0)",
            "borderwidth": 0,
            "threshold": {
                "line":      {"color": D["danger"], "width": 3},
                "thickness": 0.8,
                "value":     90,
            },
        },
        title = {
            "text": f"<b>{title}</b><br><span style='font-size:0.85em'>"
                    f"€{spent:,.0f} spent of €{planned:,.0f} planned</span>",
            "font": {"color": D["muted"], "size": 12},
        },
    ))
    fig.update_layout(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        height = 280,
        margin = dict(l=20, r=20, t=60, b=20),
        font   = dict(color=D["text"]),
    )
    return fig


# ── Export helpers ────────────────────────────────────────────────────────────

def fig_to_html(fig: go.Figure, title: str = "") -> str:
    """Export a Plotly figure as a self-contained HTML string."""
    if title:
        fig.update_layout(title=dict(text=title))
    return fig.to_html(
        full_html=True,
        include_plotlyjs=True,
        config={"responsive": True, "scrollZoom": True,
                "displayModeBar": True},
    )
