def process_dead_letters(db):
    dead_reminders = db.query(Reminder).filter(
        Reminder.status == "DEAD_LETTER"
    ).all()

    for reminder in dead_reminders:
        print("Dead letter detected:", reminder.id)
