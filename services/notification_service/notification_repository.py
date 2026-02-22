from shared.models.notification_log import NotificationLog


class NotificationRepository:
    @staticmethod
    def save_log(
        db,
        reminder_id,
        channel,
        recipient,
        status,
        provider_message_id=None,
        error_message=None,
    ):
        log = NotificationLog(
            reminder_id=reminder_id,
            channel=channel,
            recipient=recipient,
            status=status,
            provider_message_id=provider_message_id,
            error_message=error_message,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
