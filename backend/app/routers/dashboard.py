from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()

    by_status: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    by_product: dict[str, int] = defaultdict(int)
    by_type: dict[str, int] = defaultdict(int)
    trend_buckets: dict[str, int] = defaultdict(int)

    for c in complaints:
        by_status[c.status.value if c.status else "Unknown"] += 1
        if c.severity:
            by_severity[c.severity.value] += 1
        if c.product_name:
            by_product[c.product_name] += 1
        if c.complaint_type:
            by_type[c.complaint_type.value] += 1
        if c.created_at:
            week = c.created_at.strftime("%Y-W%W")
            trend_buckets[week] += 1

    recent_trend = [{"period": k, "count": v} for k, v in sorted(trend_buckets.items())][-12:]

    return DashboardSummary(
        total=len(complaints),
        by_status=dict(by_status),
        by_severity=dict(by_severity),
        by_product=dict(by_product),
        by_type=dict(by_type),
        recent_trend=recent_trend,
    )
