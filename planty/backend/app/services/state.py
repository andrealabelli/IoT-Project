from dataclasses import dataclass

from app.models.entities import PlantState


@dataclass
class StateInput:
    soil_moisture: float
    air_temperature: float
    air_humidity: float
    soil_threshold: float
    temp_min: float
    temp_max: float
    humidity_min: float
    humidity_max: float


def calculate_state(data: StateInput) -> PlantState:
    if data.soil_moisture < 0 or data.air_temperature < -40:
        return PlantState.SENSOR_ERROR
    if data.soil_moisture < data.soil_threshold:
        return PlantState.NEEDS_WATER
    if not (data.temp_min <= data.air_temperature <= data.temp_max) or not (
        data.humidity_min <= data.air_humidity <= data.humidity_max
    ):
        return PlantState.MOVE_PLANT
    return PlantState.OK
