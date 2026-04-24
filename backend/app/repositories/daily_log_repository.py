from app import db
from app.models import DailyLog

class DailyLogRepository:
    @staticmethod
    def get_by_user_and_date(user_id, log_date):
        return DailyLog.query.filter_by(user_id=user_id, log_date=log_date).first()

    @staticmethod
    def get_recent_logs(user_id, start_date):
        return DailyLog.query.filter(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start_date
        ).order_by(DailyLog.log_date).all()

    @staticmethod
    def create(daily_log):
        db.session.add(daily_log)
        db.session.commit()
        return daily_log

    @staticmethod
    def commit():
        db.session.commit()
