from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from meeting_utils import round_time_to_15_min


def test_round_time_to_15_min_exact():
    dt = datetime(2024, 1, 1, 10, 30, 5)
    result = round_time_to_15_min(dt)
    assert result.minute == 30
    assert result.second == 0


def test_round_time_to_15_min_down():
    dt = datetime(2024, 1, 1, 10, 37)
    result = round_time_to_15_min(dt)
    assert result.minute == 30
    assert result.second == 0
