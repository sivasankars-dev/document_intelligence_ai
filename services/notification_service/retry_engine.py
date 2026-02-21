class RetryEngine:
    def should_retry(self, reminder):
        return reminder.retry_count < reminder.max_retries
    def increment_retry(self, reminder, error_message):
        reminder.retry_count += 1
        reminder.last_error = error_message