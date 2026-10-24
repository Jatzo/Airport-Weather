"""Turns the raw dictionary from the service into a small object."""

from dataclasses import dataclass


@dataclass
class Weather:
    icao: str
    name: str
    temperature_c: float
    dew_point_c: float
    wind_direction: int | str
    wind_speed_kt: int
    wind_gust_kt: int | None
    visibility_miles: float
    visibility_is_minimum: bool  # True when the service sent "10+", meaning "at least"
    clouds: list  # empty list when the sky is clear


def parse_metar(data):
    # Visibility is a number (4.35) or a string ("10+"), in statute miles.
    visibility = str(data["visib"])
    visibility_is_minimum = visibility.endswith("+")
    visibility_miles = float(visibility.replace("+", ""))

    return Weather(
        icao=data["icaoId"],
        name=data["name"],
        temperature_c=data["temp"],
        dew_point_c=data["dewp"],
        wind_direction=data["wdir"],
        wind_speed_kt=data["wspd"],
        wind_gust_kt=data.get("wgst"),
        visibility_miles=visibility_miles,
        visibility_is_minimum=visibility_is_minimum,
        clouds=data["clouds"],
    )
