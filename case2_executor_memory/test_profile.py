"""Run locally without Spark: python3 case2_executor_memory/test_profile.py"""

from bad import profile_partition as buffered
from fixed import profile_partition as streamed


class Row(dict):
    """Only the Spark Row interface used by the profiler."""

    visited = False

    def asDict(self):
        return self

    def items(self):
        self.visited = True
        return super().items()


def checked_rows():
    for value in (None, 0, -1, 2):
        row = Row(fare=value, zone=1)
        yield row
        assert row.visited, "The profiler buffered input instead of processing it"


if __name__ == "__main__":
    rows = [Row(fare=value, zone=1) for value in (None, 0, -1, 2)]
    expected = [("fare", 4, 1), ("zone", 4, 0)]
    for profile in (buffered, streamed):
        assert sorted(profile(iter(rows))) == expected
        assert list(profile(iter([]))) == []
        # Partition-local profiles must add up to the same global report.
        halves = list(profile(iter(rows[:2]))) + list(profile(iter(rows[2:])))
        assert [(column, sum(n for c, n, _ in halves if c == column),
                 sum(m for c, _, m in halves if c == column))
                for column in ("fare", "zone")] == expected
    assert sorted(streamed(checked_rows())) == expected
    print("Profiles agree; empty partitions work; fixed input is streamed.")
