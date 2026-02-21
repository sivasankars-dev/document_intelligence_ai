from sqlalchemy.orm import Session
from shared.models.reminder import Reminder
from sqlalchemy import and_
from datetime import datetime


class ReminderRepository:
    @staticmethod
    def create(db: Session, reminder: Reminder):
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    @staticmethod
    def get_pending_reminders(db: Session, current_time):
        return (
            db.query(Reminder)
            .filter(Reminder.remind_at <= current_time)
            .filter(Reminder.status == "PENDING")
            .all()
        )

    @staticmethod
    def fetch_batch_for_processing(db, batch_size=50):
        now = datetime.utcnow()
        reminders = (
            db.query(Reminder)
            .filter(
                and_(
                    Reminder.remind_at <= now,
                    Reminder.status == "PENDING",
                    Reminder.locked_at.is_(None)
                )
            )
            .limit(batch_size)
            .with_for_update(skip_locked=True)
            .all()
        )
        for reminder in reminders:
            reminder.locked_at = now
        db.commit()
        return reminders
