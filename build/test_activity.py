"""Run: python3 build/test_activity.py"""
from activity import level, streaks


def test_level():
    assert level(0, 10) == 0
    assert level(1, 10) == 1
    assert level(5, 10) == 2
    assert level(10, 10) == 4
    assert level(3, 0) == 0  # empty year: no division by zero


def test_streaks():
    assert streaks([1, 1, 0, 1, 1, 1]) == (3, 3)
    assert streaks([1, 1, 1, 0]) == (3, 3)  # today not committed yet keeps the streak alive
    assert streaks([0, 0]) == (0, 0)
    assert streaks([1, 0, 0, 1]) == (1, 1)
    assert streaks([2, 3, 0, 0, 1, 0]) == (1, 2)
    assert streaks([]) == (0, 0)


if __name__ == "__main__":
    test_level()
    test_streaks()
    print("ok")
