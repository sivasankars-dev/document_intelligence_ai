from datetime import timedelta
from shared.models.obligation import Obligation

class RecurrenceEngine:
    @staticmethod
    def generate_next(obligation):
        if obligation.recurrence == "YEARLY":
            next_due = obligation.due_date + timedelta(days=365)

            return Obligation(
                document_id=obligation.document_id,
                user_id=obligation.user_id,
                title=obligation.title,
                due_date=next_due,
                recurrence="YEARLY"
            )

        return None
