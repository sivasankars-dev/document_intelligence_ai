class EmailProvider:
    def send(self, recipient: str, message: str):
        print(f"Sending EMAIL to {recipient}: {message}")
