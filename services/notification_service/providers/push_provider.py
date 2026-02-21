class PushProvider:
    def send(self, recipient: str, message: str):
        print(f"Sending PUSH to {recipient}: {message}")
