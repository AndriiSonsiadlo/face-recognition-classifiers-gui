from datetime import datetime


class TimeUtils:
    @staticmethod
    def get_hour() -> int:
        return datetime.now().hour

    @staticmethod
    def get_day() -> int:
        return datetime.now().day

    @staticmethod
    def get_month() -> int:
        return datetime.now().month
