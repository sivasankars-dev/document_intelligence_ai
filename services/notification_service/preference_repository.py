from shared.models.notification_preference import NotificationPreference

def get_user_preferences(db, user_id):
    return (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
