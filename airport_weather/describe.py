"""Turns a Weather object into plain English. Units: knots, km, Celsius, feet."""

COMPASS_POINTS = [
    "north", "north-northeast", "northeast", "east-northeast",
    "east", "east-southeast", "southeast", "south-southeast",
    "south", "south-southwest", "southwest", "west-southwest",
    "west", "west-northwest", "northwest", "north-northwest",
]

CLOUD_NAMES = {
    "FEW": "Few clouds",
    "SCT": "Scattered cloud",
    "BKN": "Broken cloud",
    "OVC": "Overcast",
}

KM_PER_MILE = 1.609344


def compass_name(degrees):
    # Each point covers 22.5 degrees. The % 16 makes 360 come back round to north.
    number = round(degrees / 22.5) % 16
    return COMPASS_POINTS[number]


def describe_wind(weather):
    speed = weather.wind_speed_kt

    if speed == 0:
        return "Wind calm."

    if weather.wind_direction == "VRB":
        text = f"Wind variable at {speed} knots"
    else:
        direction = compass_name(weather.wind_direction)
        text = f"Wind from the {direction} at {speed} knots"

    if weather.wind_gust_kt:
        text = text + f", gusting {weather.wind_gust_kt}"
    return text + "."


def describe_temperature(weather):
    temperature = round(weather.temperature_c)
    dew_point = round(weather.dew_point_c)
    return f"Temperature {temperature} C, dew point {dew_point} C."


def describe_visibility(weather):
    km = weather.visibility_miles * KM_PER_MILE

    # Below 5 km the tenths matter, so keep one decimal place there.
    if km >= 5:
        km = round(km)
    else:
        km = round(km, 1)

    text = f"Visibility {km} km"
    if weather.visibility_is_minimum:
        text = text + " or more"
    return text + "."


def describe_clouds(weather):
    # The service sends an empty list when the sky is clear.
    if len(weather.clouds) == 0:
        return ["Clear skies."]

    sentences = []
    for layer in weather.clouds:
        name = CLOUD_NAMES[layer["cover"]]
        sentences.append(f"{name} at {layer['base']:,} ft.")
    return sentences


def describe_report(weather):
    lines = [f"{weather.name} ({weather.icao})"]
    lines.append(describe_wind(weather))
    lines.append(describe_temperature(weather))
    lines.append(describe_visibility(weather))
    lines = lines + describe_clouds(weather)
    return "\n".join(lines)
