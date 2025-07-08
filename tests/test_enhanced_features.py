import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from meeting_utils import TokenManager


def test_token_manager_round_trip(tmp_path):
    token_file = tmp_path / "token.txt"
    tm = TokenManager(token_file=str(token_file))
    assert tm.get_token() is None
    assert tm.set_token("abc123") is True
    assert tm.get_token() == "abc123"
