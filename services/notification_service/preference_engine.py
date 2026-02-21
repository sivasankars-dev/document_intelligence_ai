from datetime import datetime

class PreferenceEngine:
    def is_within_quiet_hours(self, preference):
        if not preference.quiet_hours_start:
            return False
        now = datetime.utcnow().time()
        start = datetime.strptime(preference.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(preference.quiet_hours_end, "%H:%M").time()
        return start <= now <= end

    def get_enabled_channels(self, preference):
        channels = []
        for ch in preference.channel_priority:
            if ch == "email" and preference.email_enabled:
                channels.append("email")
            if ch == "sms" and preference.sms_enabled:
                channels.append("sms")
            if ch == "push" and preference.push_enabled:
                channels.append("push")

        return channels
