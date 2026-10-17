"""Tests for describe.py and the command line. No test here touches the network."""

import json
from pathlib import Path

from airport_weather import cli
from airport_weather.describe import (
    compass_name,
    describe_clouds,
    describe_report,
    describe_temperature,
    describe_visibility,
    describe_wind,
)
from airport_weather.fetch import WeatherError
from airport_weather.parse import parse_metar

FIXTURES = Path(__file__).parent / "fixtures"


def load_weather(name):
    with open(FIXTURES / f"{name}.json") as file:
        return parse_metar(json.load(file)[0])


# wind


def test_a_wind_is_described_with_a_compass_name_and_speed():
    assert describe_wind(load_weather("egll")) == "Wind from the north-northeast at 7 knots."


def test_a_gusting_wind_says_how_hard_it_gusts():
    assert describe_wind(load_weather("kbos")) == "Wind from the northwest at 13 knots, gusting 20."


def test_a_variable_wind_has_no_direction_in_the_sentence():
    assert describe_wind(load_weather("egph")) == "Wind variable at 2 knots."


def test_no_wind_is_called_calm():
    assert describe_wind(load_weather("edited_calm")) == "Wind calm."


def test_360_degrees_comes_back_round_to_north():
    assert compass_name(360) == "north"
    assert compass_name(247) == "west-southwest"


# temperature


def test_temperature_and_dew_point_are_shown_in_celsius():
    assert describe_temperature(load_weather("egll")) == "Temperature 11 C, dew point 9 C."


# visibility


def test_a_minimum_visibility_says_or_more():
    # 10 statute miles is 16.09 km.
    assert describe_visibility(load_weather("kjfk")) == "Visibility 16 km or more."


def test_a_low_visibility_keeps_a_decimal_place():
    # 2.49 statute miles is 4.0 km.
    assert describe_visibility(load_weather("bikf")) == "Visibility 4.0 km."


# cloud


def test_each_cloud_layer_gets_its_own_sentence():
    assert describe_clouds(load_weather("egll")) == [
        "Few clouds at 1,800 ft.",
        "Scattered cloud at 3,000 ft.",
        "Broken cloud at 3,900 ft.",
    ]


def test_clear_skies_and_cavok_are_both_described_as_clear():
    assert describe_clouds(load_weather("kden")) == ["Clear skies."]
    assert describe_clouds(load_weather("egph")) == ["Clear skies."]


# the whole report


def test_the_report_starts_with_the_airport_name_and_code():
    first_line = describe_report(load_weather("egll")).splitlines()[0]
    assert first_line == "London/Heathrow Intl, EN, GB (EGLL)"


# command line


def test_a_bad_code_is_refused_before_any_request(monkeypatch, capsys):
    def should_not_run(code):
        raise AssertionError("fetch_metar was called for a bad code")

    monkeypatch.setattr(cli, "fetch_metar", should_not_run)

    assert cli.main(["XXXX1"]) == 1
    assert "not an airport code" in capsys.readouterr().err


def test_a_lowercase_code_is_accepted(monkeypatch, capsys):
    with open(FIXTURES / "egll.json") as file:
        report = json.load(file)[0]
    monkeypatch.setattr(cli, "fetch_metar", lambda code: report)

    assert cli.main(["egll"]) == 0
    assert "Wind from the north-northeast" in capsys.readouterr().out


def test_a_fetch_problem_prints_one_line_and_exits_non_zero(monkeypatch, capsys):
    def no_report(code):
        raise WeatherError("No weather report found for EGLL.")

    monkeypatch.setattr(cli, "fetch_metar", no_report)

    assert cli.main(["EGLL"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "No weather report found for EGLL.\n"
