from abc import ABC, abstractmethod


class DataListManager(ABC):
    """Base class for list management"""

    def __init__(self):
        self.data_list = []
        self.search_query = ""

    @abstractmethod
    def load_data(self) -> None:
        """Load data from source"""
        pass

    def search(self, query: str) -> list:
        """Filter data by search query"""
        self.search_query = query.lower()
        return self._filter_data()

    @abstractmethod
    def _filter_data(self) -> list:
        """Implementation-specific filtering"""
        pass

    def clear_search(self) -> list:
        """Reset search and return all data"""
        self.search_query = ""
        return self.data_list
