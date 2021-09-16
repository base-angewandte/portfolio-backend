from datetime import datetime
from typing import Optional


class DateTimeComparator:

    max_seconds: int
    default_max_seconds: int = 30

    def __init__(self, max_seconds: Optional[int] = None):
        """Compare date time objects with.

        :param max_seconds:
        """
        self.max_seconds = max_seconds if max_seconds.__class__ is int else self.default_max_seconds

    def greater_then(self, first: Optional[datetime], second: Optional[datetime]) -> Optional[bool]:
        """Checks if the first is greater then the second with the given max
        seconds as fuzziness.

        :param first:
        :param second:
        :return:
        """
        if not self.comparable(first, second):
            return None
        return (first > second) and not self.about_the_same(first, second)

    def smaller_then(self, first: Optional[datetime], second: Optional[datetime]) -> Optional[bool]:
        """Checks if the first is smaller then the second with the given max
        seconds as fuzziness.

        :param first:
        :param second:
        :return:
        """
        if not self.comparable(first, second):
            return None
        return (first < second) and not self.about_the_same(first, second)

    def about_the_same(self, first: Optional[datetime], second: Optional[datetime]) -> Optional[bool]:
        # Checks if the difference is within the given fuzziness
        if not self.comparable(first, second):
            return None
        return abs((first - second).total_seconds()) < self.max_seconds

    def comparable(self, first: Optional[datetime], second: Optional[datetime]) -> bool:
        return all((first, second))
