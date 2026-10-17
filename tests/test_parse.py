"""Tests for fetch.py and parse.py. No test here touches the network."""

import json
from pathlib import Path

import pytest
import requests

from airport_weather import fetch
from airport_weather.fetch import WeatherError, fetch_metar
from airport_weather.parse import parse_metar

FIXTURES = Path(__file__).parent / "fixtures"


def load_report(name):
    with open(FIXTURES / f"{name}.json") as file:
        return json.load(file)[0]


class FakeResponse:
    """Stands in for the object requests.get returns."""

    def __init__(self, text):
        self.text = text

    def json(self):
        return json.loads(self.text)


# parse.py


def test_the_basic_values_are_read_from_a_real_report():
    weather = parse_metar(load_report("egll"))

    assert weather.icao == "EGLL"
    assert weather.temperature_c == 11
    assert weather.dew_point_c == 9
    assert weather.wind_direction == 30
    assert weather.wind_speed_kt == 7
    assert weather.wind_gust_kt is None


def test_a_variable_wind_keeps_the_word_vrb():
    weather = parse_metar(load_report("egph"))

    assert weather.wind_direction == "VRB"


def test_gusts_are_read_when_the_report_has_them():
    weather = parse_metar(load_report("kbos"))

    assert weather.wind_speed_kt == 13
    assert weather.wind_gust_kt == 20


def test_a_visibility_with_a_plus_is_a_minimum():
    weather = parse_metar(load_report("kjfk"))

    assert weather.visibility_miles == 10
    assert weather.visibility_is_minimum is True


def test_a_visibility_number_is_not_a_minimum():
    weather = parse_metar(load_report("bikf"))

    assert weather.visibility_miles == 2.49
    assert weather.visibility_is_minimum is False


def test_clear_skies_give_an_empty_cloud_list():
    weather = parse_metar(load_report("kden"))

    assert weather.clouds == []


def test_cloud_layers_keep_their_order_and_height():
    weather = parse_metar(load_report("egll"))

    assert weather.clouds == [
        {"cover": "FEW", "base": 1800},
        {"cover": "SCT", "base": 3000},
        {"cover": "BKN", "base": 3900},
    ]


# fetch.py


def test_a_report_is_returned_when_the_service_answers(monkeypatch):
    answer = FakeResponse(json.dumps([{"icaoId": "EGLL"}]))
    monkeypatch.setattr(fetch.requests, "get", lambda *args, **kwargs: answer)

    assert fetch_metar("EGLL") == {"icaoId": "EGLL"}


def test_an_empty_answer_means_no_report_is_available(monkeypatch):
    answer = FakeResponse("")
    monkeypatch.setattr(fetch.requests, "get", lambda *args, **kwargs: answer)

    with pytest.raises(WeatherError, match="No weather report found for XXXX"):
        fetch_metar("XXXX")


def test_no_network_gives_a_friendly_error(monkeypatch):
    def no_network(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr(fetch.requests, "get", no_network)

    with pytest.raises(WeatherError, match="internet connection"):
        fetch_metar("EGLL")


def test_a_timeout_is_not_mistaken_for_no_network(monkeypatch):
    # ConnectTimeout is both a Timeout and a ConnectionError, so it goes
    # wrong if the two except blocks are in the wrong order.
    def too_slow(*args, **kwargs):
        raise requests.ConnectTimeout()

    monkeypatch.setattr(fetch.requests, "get", too_slow)

    with pytest.raises(WeatherError, match="too long"):
        fetch_metar("EGLL")
