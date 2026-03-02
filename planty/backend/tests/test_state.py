from app.models.entities import PlantState
from app.services.state import StateInput, calculate_state


def test_needs_water():
    state = calculate_state(StateInput(20, 22, 50, 35, 15, 30, 30, 75))
    assert state == PlantState.NEEDS_WATER


def test_move_plant():
    state = calculate_state(StateInput(60, 40, 50, 35, 15, 30, 30, 75))
    assert state == PlantState.MOVE_PLANT
