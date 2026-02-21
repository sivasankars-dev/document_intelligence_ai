from datetime import timedelta

from shared.models.reminder import Reminder
from services.obligation_service.reminder_repository import ReminderRepository


class ReminderGenerator:

    DEFAULT_OFFSETS = [30, 7, 1]

    @staticmethod
    def generate(db, obligation):

        if not obligation.due_date:
            return

        for days_before in ReminderGenerator.DEFAULT_OFFSETS:
            remind_time = obligation.due_date - timedelta(days=days_before)
            reminder = Reminder(
                obligation_id=obligation.id,
                remind_at=remind_time
            )
            ReminderRepository.create(db, reminder)
