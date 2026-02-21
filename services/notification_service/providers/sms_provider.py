class SMSProvider:
    def send(self, recipient: str, message: str):
        print(f"Sending SMS to {recipient}: {message}")
