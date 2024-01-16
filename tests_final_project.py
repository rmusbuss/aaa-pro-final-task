import pytest
from final_project import (
    check_winner,
    get_default_state,
    CONTINUE_GAME,
    FINISH_GAME,
    DEFAULT_STATE,
    won,
)


@pytest.fixture
def default_state():
    return get_default_state()


def test_check_winner_continue_game(default_state):
    status, result = check_winner(default_state)
    assert status == CONTINUE_GAME
    assert result == ""


def test_check_winner_cross_wins():
    field = [["X", "O", "X"], ["O", "X", "O"], ["X", "X", "O"]]
    status, result = check_winner(field)
    assert status == FINISH_GAME
    assert result == "WOW! X is winner!"


def test_check_winner_zero_wins():
    field = [["X", "O", "X"], ["O", "O", "X"], ["X", "O", "O"]]
    status, result = check_winner(field)
    assert status == FINISH_GAME
    assert result == "WOW! O is winner!"


def test_check_winner_tie():
    field = [["X", "O", "O"], ["O", "X", "X"], ["X", "X", "O"]]
    status, result = check_winner(field)
    assert status == FINISH_GAME
    assert result == "It is a TIE :( No one wins"


def test_won_no_winner():
    field = [["X", "O", "X"], [".", ".", "O"], ["X", "X", "."]]
    assert won(field) is None


def test_get_default_state_stays_same():
    new_default_state = get_default_state()
    new_default_state[0][1] = "X"
    new_default_state[2][2] = "O"
    new_default_state[1][0] = "X"
    assert get_default_state() == DEFAULT_STATE
