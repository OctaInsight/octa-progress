"""Octa Project Progress Tracker — Supabase database layer."""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timezone, date
from config import FUNDED_STATUSES
import json


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["supabase"]["url"],
                         st.secrets["supabase"]["key"])

def db() -> Client:
    return _client()

def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Funded Projects ───────────────────────────────────────────────────────────

def get_funded_projects(organisation: str = "", is_admin: bool = False) -> tuple:
    """
    Returns (projects_list, error_string|None).
    Matches proposals where status = 'Funded' (proposal app)
    OR lifecycle_status = 'funded_project' (project phase).
    No organisation filtering — all funded projects are visible.
    """
    try:
        resp = db().table("proposals").select("*") \
                   .order("proposal_id", desc=True).execute()
        all_props = resp.data or []
    except Exception as e:
        return [], str(e)

    FUNDED = {
        "Funded", "funded",
        "funded_project", "ongoing_project", "ended_project",
        "Ongoing", "ongoing", "Ended", "ended",
    }

    projects = [
        p for p in all_props
        if (p.get("status") or "")           in FUNDED
        or (p.get("lifecycle_status") or "")  in FUNDED
    ]

    return projects, None

def get_project(proposal_id: str) -> dict | None:
    try:
        r = db().table("proposals").select("*") \
                .eq("proposal_id", proposal_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_project_status(proposal_id: str, data: dict) -> bool:
    """Update lifecycle_status and project dates."""
    try:
        db().table("proposals").update(data) \
            .eq("proposal_id", proposal_id).execute()
        return True
    except Exception:
        return False


# ── Month → date conversion ───────────────────────────────────────────────────

def month_to_date(project_start: date | None, month_num: int | None) -> date | None:
    """Convert relative project month (1-based) to calendar date."""
    if not project_start or not month_num:
        return None
    from dateutil.relativedelta import relativedelta
    try:
        return project_start + relativedelta(months=int(month_num) - 1)
    except Exception:
        return None


def date_to_month(project_start: date | None, d: date | None) -> int | None:
    """Convert calendar date to relative project month."""
    if not project_start or not d:
        return None
    try:
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(d, project_start)
        return max(1, delta.years * 12 + delta.months + 1)
    except Exception:
        return None


# ── Work Packages ─────────────────────────────────────────────────────────────

def get_work_packages(proposal_id: str) -> list:
    try:
        return db().table("work_packages").select("*") \
                   .eq("proposal_id", proposal_id) \
                   .order("sort_order").order("wp_number").execute().data or []
    except Exception:
        return []


# ── Tasks ─────────────────────────────────────────────────────────────────────

def get_tasks(proposal_id: str, wp_id: int = None) -> list:
    try:
        q = db().table("tasks_project").select("*") \
                .eq("proposal_id", proposal_id)
        if wp_id:
            q = q.eq("wp_id", wp_id)
        return q.order("task_number").execute().data or []
    except Exception:
        return []


def update_task_progress(task_id: int, status: str, progress: float,
                          actual_start: date = None, actual_end: date = None,
                          notes: str = "", updated_by: int = None) -> bool:
    try:
        patch = {
            "status":               status,
            "progress_percentage":  progress,
            "implementation_notes": notes,
            "updated_at":           _now(),
        }
        if actual_start: patch["actual_start_date"] = actual_start.isoformat()
        if actual_end:   patch["actual_end_date"]   = actual_end.isoformat()
        if updated_by:   patch["last_updated_by"]   = updated_by
        db().table("tasks_project").update(patch).eq("task_id", task_id).execute()
        return True
    except Exception:
        return False


def get_task_stats(tasks: list, project_start: date = None) -> dict:
    """Compute task statistics and deviations."""
    today   = date.today()
    total   = len(tasks)
    stats   = {"total":total,"completed":0,"ongoing":0,"planned":0,
               "delayed":0,"cancelled":0,"avg_progress":0.0,"overdue":[]}
    prog_sum= 0.0

    for t in tasks:
        s = t.get("status","planned")
        stats[s] = stats.get(s,0) + 1
        prog_sum += float(t.get("progress_percentage",0) or 0)

        # Detect overdue: planned end month passed but not completed
        end_m = t.get("planned_end_month") or t.get("end_month")
        if end_m and project_start and s not in ("completed","cancelled"):
            planned_end = month_to_date(project_start, int(end_m))
            if planned_end and planned_end < today:
                actual_end = t.get("actual_end_date")
                if not actual_end:
                    delay_days = (today - planned_end).days
                    stats["delayed"] = stats.get("delayed",0) + 1
                    stats["overdue"].append({**t, "delay_days": delay_days,
                                             "planned_end": planned_end})

    stats["avg_progress"] = round(prog_sum / total, 1) if total else 0.0
    return stats


# ── Deliverables ──────────────────────────────────────────────────────────────

def get_deliverables(proposal_id: str, wp_id: int = None) -> list:
    try:
        q = db().table("deliverables").select("*") \
                .eq("proposal_id", proposal_id)
        if wp_id:
            q = q.eq("wp_id", wp_id)
        return q.order("delivery_month").order("deliverable_number").execute().data or []
    except Exception:
        return []


def update_deliverable_progress(deliverable_id: int, status: str,
                                 progress: float,
                                 submission_date: date = None,
                                 acceptance_date: date = None,
                                 link: str = "", notes: str = "") -> bool:
    try:
        patch = {
            "status":             status,
            "progress_percentage": progress,
            "updated_at":         _now(),
        }
        if submission_date: patch["actual_submission_date"] = submission_date.isoformat()
        if acceptance_date: patch["acceptance_date"]        = acceptance_date.isoformat()
        if link:            patch["submission_link"]        = link
        if notes:           patch["reviewer_comment"]       = notes
        db().table("deliverables").update(patch) \
            .eq("deliverable_id", deliverable_id).execute()
        return True
    except Exception:
        return False


def get_deliverable_stats(deliverables: list, project_start: date = None) -> dict:
    today  = date.today()
    total  = len(deliverables)
    stats  = {"total":total,"accepted":0,"submitted":0,"in_progress":0,
              "planned":0,"delayed":0,"cancelled":0,"overdue":[]}
    for d in deliverables:
        s = d.get("status","planned")
        stats[s] = stats.get(s,0) + 1
        dm = d.get("planned_delivery_month") or d.get("delivery_month")
        if dm and project_start and s not in ("accepted","cancelled"):
            planned_dt = month_to_date(project_start, int(dm))
            if planned_dt and planned_dt < today:
                if not d.get("actual_submission_date"):
                    delay_days = (today - planned_dt).days
                    stats["overdue"].append({**d,"delay_days":delay_days,
                                             "planned_date":planned_dt})
    return stats


# ── Milestones ────────────────────────────────────────────────────────────────

def get_milestones(proposal_id: str) -> list:
    try:
        return db().table("milestones").select("*") \
                   .eq("proposal_id", proposal_id) \
                   .order("due_month").execute().data or []
    except Exception:
        return []


def update_milestone(milestone_id: int, status: str,
                      achieved_date: date = None, notes: str = "") -> bool:
    try:
        patch = {"status": status, "updated_at": _now()}
        if achieved_date: patch["achieved_date"]     = achieved_date.isoformat()
        if notes:         patch["achievement_notes"] = notes
        db().table("milestones").update(patch) \
            .eq("milestone_id", milestone_id).execute()
        return True
    except Exception:
        return False


def get_milestone_stats(milestones: list, project_start: date = None) -> dict:
    today  = date.today()
    total  = len(milestones)
    stats  = {"total":total,"achieved":0,"planned":0,"delayed":0,
              "partially_achieved":0,"not_achieved":0,"overdue":[]}
    for m in milestones:
        s = m.get("status","planned")
        stats[s] = stats.get(s,0) + 1
        dm = m.get("planned_due_month") or m.get("due_month")
        if dm and project_start and s not in ("achieved","not_achieved"):
            planned_dt = month_to_date(project_start, int(dm))
            if planned_dt and planned_dt < today:
                delay_days = (today - planned_dt).days
                stats["delayed"] = stats.get("delayed",0) + 1
                stats["overdue"].append({**m,"delay_days":delay_days,
                                         "planned_date":planned_dt})
    return stats


# ── KPIs ──────────────────────────────────────────────────────────────────────

def get_kpis(proposal_id: str, kpi_type: str = None) -> list:
    try:
        q = db().table("kpis").select("*").eq("proposal_id", proposal_id)
        if kpi_type: q = q.eq("kpi_type", kpi_type)
        return q.order("kpi_number").execute().data or []
    except Exception:
        return []


# ── Partners (for map) ────────────────────────────────────────────────────────

def get_project_partners(proposal_id: str) -> list:
    """
    Return full partner records for all partners in this project
    (coordinator + partners_list), with country data.
    """
    try:
        prop = get_project(proposal_id)
        if not prop:
            return []
        names = []
        coord = (prop.get("coordinator") or "").strip()
        if coord: names.append(coord)
        plist = prop.get("partners_list") or []
        if isinstance(plist, str):
            try:    plist = json.loads(plist)
            except: plist = [plist]
        names.extend([str(n).strip() for n in plist if n])

        if not names:
            return []

        all_p = db().table("partners").select(
            "id,full_name,short_name,country,partner_type,website,logo_url"
        ).order("full_name").execute().data or []

        result = []; seen = set()
        for name in names:
            nl = name.lower()
            for p in all_p:
                if p["id"] in seen: continue
                fn = (p.get("full_name")  or "").lower()
                sn = (p.get("short_name") or "").lower()
                if nl in fn or fn in nl or (sn and (nl in sn or sn in nl)):
                    is_coord = (name == coord)
                    result.append({**p, "is_coordinator": is_coord})
                    seen.add(p["id"])
                    break
        return result
    except Exception:
        return []


# ── Project snapshots ─────────────────────────────────────────────────────────

def save_snapshot(proposal_id: str, period: int,
                  tasks: list, deliverables: list,
                  milestones: list, budget_planned: float,
                  budget_spent: float, notes: str = "") -> bool:
    try:
        t_total = len(tasks)
        t_done  = sum(1 for t in tasks if t.get("status")=="completed")
        t_delay = sum(1 for t in tasks if t.get("status")=="delayed")
        d_total = len(deliverables)
        d_done  = sum(1 for d in deliverables if d.get("status")=="accepted")
        d_delay = sum(1 for d in deliverables if d.get("status")=="delayed")
        m_total = len(milestones)
        m_done  = sum(1 for m in milestones if m.get("status")=="achieved")
        overall = round(
            (t_done/t_total*100) if t_total else 0, 1
        )
        db().table("project_snapshots").upsert({
            "proposal_id":        proposal_id,
            "reporting_period":   period,
            "snapshot_date":      date.today().isoformat(),
            "tasks_total":        t_total, "tasks_completed":t_done, "tasks_delayed":t_delay,
            "deliverables_total": d_total, "deliverables_accepted":d_done, "deliverables_delayed":d_delay,
            "milestones_total":   m_total, "milestones_achieved":m_done,
            "budget_planned":     budget_planned,
            "budget_spent":       budget_spent,
            "overall_progress_pct": overall,
            "notes":              notes,
        }, on_conflict="proposal_id,reporting_period").execute()
        return True
    except Exception:
        return False


def get_snapshots(proposal_id: str) -> list:
    try:
        return db().table("project_snapshots").select("*") \
                   .eq("proposal_id", proposal_id) \
                   .order("reporting_period").execute().data or []
    except Exception:
        return []


# ── Budget summary ────────────────────────────────────────────────────────────

def get_budget_summary(proposal_id: str) -> dict:
    try:
        entries = db().table("budget_entries").select("*") \
                      .eq("proposal_id", proposal_id).execute().data or []
        total_planned = sum(float(e.get("planned_amount",0) or 0) for e in entries)
        total_spent   = sum(float(e.get("actual_spent_amount",0) or 0) for e in entries)
        return {
            "planned":   total_planned,
            "spent":     total_spent,
            "remaining": total_planned - total_spent,
            "pct_spent": round(total_spent/total_planned*100,1) if total_planned else 0,
        }
    except Exception:
        return {"planned":0,"spent":0,"remaining":0,"pct_spent":0}
