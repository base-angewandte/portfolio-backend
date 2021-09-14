from datetime import datetime


class DateTimeComparator:

    max_seconds: int

    def __init__(self, max_seconds=30):
        """Compare date time objects with.

        :param max_seconds:
        """
        self.max_seconds = max_seconds

    def greater_then(self, first: datetime, second: datetime) -> bool:
        """Checks if the first is greater then the second with the given max
        seconds as fuzzyness.

        :param first:
        :param second:
        :return:
        """
        return (first - second).total_seconds() > self.max_seconds

    def smaller_then(self, first: datetime, second: datetime) -> bool:
        """Checks if the first is smaller then the second with the given max
        seconds as fuzzyness.

        :param first:
        :param second:
        :return:
        """
        return (first - second).total_seconds() > self.max_seconds

    def about_the_same(self, first: datetime, second: datetime) -> bool:
        # Checks if the difference is within the given fuzzyness
        return abs((first - second).total_seconds()) < self.max_seconds
