from abc import ABC, abstractmethod

class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> dict:
        """
        Sends a notification and returns delivery metadata.
        Example return:
        {
            "provider": "email",
            "message_id": "...",
            "status": "sent"
        }
        """
