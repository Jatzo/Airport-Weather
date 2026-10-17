"""The only file that talks to the internet."""

import requests

METAR_URL = "https://aviationweather.gov/api/data/metar"


class WeatherError(Exception):
    pass


def fetch_metar(icao):
    """Return the latest METAR for one airport as a dictionary."""
    try:
        response = requests.get(
            METAR_URL,
            params={"ids": icao, "format": "json"},
            timeout=10,
        )
    # Timeout goes first: a connect timeout counts as a ConnectionError too.
    except requests.Timeout:
        raise WeatherError("The weather service took too long to answer. Try again in a minute.")
    except requests.ConnectionError:
        raise WeatherError("Could not reach the weather service. Check your internet connection.")

    # The service sends an empty answer when it has no report for that code.
    if response.text == "":
        raise WeatherError(f"No weather report found for {icao}. Check the code, or try a larger airport.")

    return response.json()[0]
