from abc import ABC, abstractmethod

class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str):
        pass
