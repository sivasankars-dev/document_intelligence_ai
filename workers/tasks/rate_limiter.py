class RateLimiter:
    def can_send(self, reminder_history):
        # Example: limit 5 reminders per day
        return len(reminder_history) < 5
