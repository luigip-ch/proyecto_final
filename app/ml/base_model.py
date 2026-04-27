from abc import ABC, abstractmethod


class BaseModel(ABC):

    @abstractmethod
    def load_data(self) -> None: ...

    @abstractmethod
    def train(self) -> None: ...

    @abstractmethod
    def predict(self) -> list[int]: ...
