from datetime import datetime, timedelta, date
from typing import Tuple

from app.schemas.metrics import PeriodType, PeriodFilter


def get_period_dates(period: PeriodFilter) -> Tuple[datetime, datetime]:
    """
    Calculate start and end dates based on period type.
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    current_year = now.year
    
    if period.period_type == PeriodType.THIS_YEAR:
        start = datetime(current_year, 1, 1)
        end = now
        
    elif period.period_type == PeriodType.LAST_YEAR:
        start = datetime(current_year - 1, 1, 1)
        end = datetime(current_year - 1, 12, 31, 23, 59, 59)
        
    elif period.period_type == PeriodType.THIS_MONTH:
        start = today.replace(day=1)
        end = now
        
    elif period.period_type == PeriodType.LAST_MONTH:
        first_of_this_month = today.replace(day=1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        start = last_of_last_month.replace(day=1)
        end = last_of_last_month.replace(hour=23, minute=59, second=59)
        
    elif period.period_type == PeriodType.THIS_WEEK:
        # Week starts on Monday
        start = today - timedelta(days=today.weekday())
        end = now
        
    elif period.period_type == PeriodType.LAST_WEEK:
        # Last week Monday to Sunday
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(days=1)
        start = last_monday
        end = last_sunday.replace(hour=23, minute=59, second=59)
        
    elif period.period_type == PeriodType.Q1:
        start = datetime(current_year, 1, 1)
        end = datetime(current_year, 3, 31, 23, 59, 59)
        
    elif period.period_type == PeriodType.Q2:
        start = datetime(current_year, 4, 1)
        end = datetime(current_year, 6, 30, 23, 59, 59)
        
    elif period.period_type == PeriodType.Q3:
        start = datetime(current_year, 7, 1)
        end = datetime(current_year, 9, 30, 23, 59, 59)
        
    elif period.period_type == PeriodType.Q4:
        start = datetime(current_year, 10, 1)
        end = datetime(current_year, 12, 31, 23, 59, 59)
        
    elif period.period_type == PeriodType.CUSTOM:
        if not period.start_date or not period.end_date:
            raise ValueError("Custom period requires start_date and end_date")
        start = datetime.combine(period.start_date, datetime.min.time())
        end = datetime.combine(period.end_date, datetime.max.time())
        
    else:
        # Default to this month
        start = today.replace(day=1)
        end = now
    
    return start, end


