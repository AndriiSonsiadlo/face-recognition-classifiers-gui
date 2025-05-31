from abc import ABC, abstractmethod


class DataListManager(ABC):
    def __init__(self):
        self.data_list = []
        self.search_query = ""

    @abstractmethod
    def load_data(self) -> None:
        pass

    def search(self, query: str) -> list:
        self.search_query = query.lower()
        return self._filter_data()

    @abstractmethod
    def _filter_data(self) -> list:
        pass

    def clear_search(self) -> list:
        self.search_query = ""
        return self.data_list
