from abc import ABC, abstractmethod


class AbstractLLM(ABC):
    @abstractmethod
    def query(self, query: str) -> str:
        """
        Perform a query to the LLM

        :return: Output text as a string
        """
        pass
