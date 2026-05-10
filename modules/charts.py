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

    wp_labels, task_done, task_total, del_done, del_total = [], [], [], [], []

    for wp in work_packages:
        wid = wp["wp_id"]
        wt  = [t for t in tasks        if t.get("wp_id") == wid]
        wd  = [d for d in deliverables if d.get("wp_id") == wid]
        wp_labels.append(wp.get("wp_number",""))
        task_total.append(len(wt))
        task_done.append(sum(1 for t in wt if t.get("status") == "completed"))
        del_total.append(len(wd))
        del_done.append(sum(1 for d in wd if d.get("status") in ("accepted","submitted")))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Tasks — Total",   x=wp_labels, y=task_total,
                         marker_color=D["accent"]+"55",
                         hovertemplate="%{x}: %{y} tasks total<extra></extra>"))
    fig.add_trace(go.Bar(name="Tasks — Done",    x=wp_labels, y=task_done,
                         marker_color=D["accent"],
                         hovertemplate="%{x}: %{y} tasks completed<extra></extra>"))
    fig.add_trace(go.Bar(name="Deliverables — Total", x=wp_labels, y=del_total,
                         marker_color=D["success"]+"55",
                         hovertemplate="%{x}: %{y} deliverables total<extra></extra>"))
    fig.add_trace(go.Bar(name="Deliverables — Done",  x=wp_labels, y=del_done,
                         marker_color=D["success"],
                         hovertemplate="%{x}: %{y} deliverables accepted<extra></extra>"))

    fig.update_layout(barmode="group", xaxis_title="Work Package", yaxis_title="Count")
    return _layout(fig, title, 360)
