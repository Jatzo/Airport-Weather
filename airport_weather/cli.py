"""The command line: read the code, fetch, parse, print."""

import argparse
import sys

from airport_weather.describe import describe_report
from airport_weather.fetch import WeatherError, fetch_metar
from airport_weather.parse import parse_metar


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m airport_weather",
        description="Print the current weather at an airport in plain English.",
    )
    parser.add_argument("icao", help="four-letter airport code, for example EGLL")
    args = parser.parse_args(argv)

    code = args.icao.upper()

    # Check before any request, so a typo never costs a network call.
    if len(code) != 4 or not code.isalpha():
        print(f"'{args.icao}' is not an airport code. Use four letters, for example EGLL.", file=sys.stderr)
        return 1

    try:
        data = fetch_metar(code)
    except WeatherError as error:
        print(error, file=sys.stderr)
        return 1

    weather = parse_metar(data)
    print(describe_report(weather))
    return 0
