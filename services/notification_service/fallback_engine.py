class FallbackEngine:
    def get_next_channel(self, channels, current_channel):
        try:
            idx = channels.index(current_channel)
            return channels[idx + 1]
        except:
            return None
