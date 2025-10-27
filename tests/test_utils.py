from app.utils import add


def test_add_function() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


