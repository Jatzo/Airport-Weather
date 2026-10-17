# Airport Weather

A small Python command line tool. Give it an airport code and it prints the current weather in plain English.

```
python -m airport_weather EGLL
```

```
London/Heathrow Intl, EN, GB (EGLL)
Wind from the north-northeast at 7 knots.
Temperature 11 C, dew point 9 C.
Visibility 10 km or more.
Few clouds at 1,800 ft.
Scattered cloud at 3,000 ft.
Broken cloud at 3,900 ft.
```
## What the numbers mean

The tool reads a METAR. That is the short coded weather report airports publish, usually every 30 minutes or every hour. Raw, it looks like this:

```
METAR EGLL 171550Z AUTO 03007KT 340V070 9999 -RA FEW018 SCT030 BKN039 11/09 Q1033 RERA
```

The tool turns that into sentences. The units are:

| Reading | Unit |
|---|---|
| Wind speed and gusts | knots |
| Visibility | kilometres |
| Temperature and dew point | degrees Celsius (C) |
| Cloud height | feet (ft) |

## Before you start

You need Python 3.11 or newer and an internet connection. The weather comes from the free [Aviation Weather Center data API](https://aviationweather.gov/data/api/). It needs no account and no key.

## Step 1: Set up

**Goal:** a clean Python environment with the two things this project uses: `requests` and `pytest`.

**Run** (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

**You should see:** `(.venv)` at the start of your prompt after the second command. After the last command, pytest runs. If your `tests` folder is empty, it says `no tests ran`. In this finished repo it says `25 passed`.

**Why:** a virtual environment keeps this project's packages separate from everything else on your computer, so nothing you install here can break another project. Running pytest before there is anything to test proves the tools are installed.

## Step 2: Fetch a METAR and print the raw text

**Goal:** get real data from the internet, before worrying about what it means.

**Run:**

```powershell
python -c "from airport_weather.fetch import fetch_metar; print(fetch_metar('EGLL')['rawOb'])"
```

**You should see** one line of coded text, like the raw METAR above. The numbers will differ, because the weather has moved on.

**Why:** the code that talks to the internet lives in one file, `airport_weather/fetch.py`, and does nothing else. The call is short:

```python
response = requests.get(
    METAR_URL,
    params={"ids": icao, "format": "json"},
    timeout=10,
)
```

`format=json` asks for the report as structured data, so we do not have to pick the coded text apart ourselves. The `timeout` is in seconds. Without it, a stalled connection leaves the tool hanging with no message.

Before writing any more code, I made a real request and read what came back. A few things were not obvious, and they shaped the rest of the code:

- Visibility is in **statute miles**, not kilometres. It is a number such as `4.35`, or a string such as `"10+"`, where the plus means "at least".
- Wind direction is a number of degrees, or the word `"VRB"` when the wind keeps changing direction.
- Gusts are in a field called `wgst`, and it is `null` when there are none.
- When the sky is clear, the cloud list is empty and a separate `cover` field says `CLR` or `CAVOK`.
- An airport the service does not know gets an empty answer with status 204, not an error message.

## Step 3: Parse the response into a dataclass

**Goal:** turn the loose dictionary into a small, predictable object.

**Run:**

```powershell
python -c "from airport_weather.fetch import fetch_metar; from airport_weather.parse import parse_metar; print(parse_metar(fetch_metar('EGLL')))"
```

**You should see** one long line starting `Weather(icao='EGLL', ...` with each value named.

**Why:** a dictionary can hold anything, and a misspelt key fails quietly. A dataclass has named, fixed fields, so the rest of the code can rely on them. In `airport_weather/parse.py`:

```python
@dataclass
class Weather:
    icao: str
    name: str
    temperature_c: float
    ...
```

Parsing is also the place to deal with the odd shapes from step 2. For example, `parse_metar` turns the visibility `"10+"` into the number `10` plus a flag saying it is a minimum. A variable wind keeps the word `"VRB"` as its direction, and the wind code checks for it later.

This version assumes the service sends every reading. Automatic stations sometimes leave one out, and then the tool would stop with an error. Handling that is a good next exercise.

## Step 4: Turn the values into plain English

**Goal:** wording a person can read at a glance.

**Run:**

```powershell
python -c "from airport_weather.fetch import fetch_metar; from airport_weather.parse import parse_metar; from airport_weather.describe import describe_report; print(describe_report(parse_metar(fetch_metar('EGLL'))))"
```

**You should see** the report from the top of this page, with current numbers.

**Why:** this code is kept apart from fetching and parsing so it can be tested with no internet at all. The rules it follows:

- **Wind:** the direction in degrees becomes a compass name. Each of the 16 names covers 22.5 degrees, and the `% 16` makes 360 degrees come back round to north. A speed of 0 is "Wind calm." whatever the direction says. `"VRB"` becomes "Wind variable at 2 knots."
- **Visibility:** miles are multiplied by 1.609 to get kilometres. At 5 km or more the answer is a whole number. Below that, one decimal place is kept, because that is where visibility starts to matter. A value that came with a plus gets "or more", so `"10+"` becomes "Visibility 16 km or more." An American `10SM` report gives 16 km and a European `9999` report gives 10 km, because the service sends different figures for each.
- **Cloud:** one sentence per layer, lowest first. FEW, SCT, BKN and OVC become "Few clouds", "Scattered cloud", "Broken cloud" and "Overcast". An empty list means the sky is clear, so it becomes "Clear skies."

## Step 5: Take the airport code from the command line

**Goal:** type any airport, instead of having EGLL written into the code.

**Run:**

```powershell
python -m airport_weather EGLL
python -m airport_weather kbos
```

**You should see** a report for each. The second shows gusts, for example "Wind from the northwest at 13 knots, gusting 20."

**Why:** `argparse` is Python's built-in way to read what you type after the command. It also gives you `-h` for free:

```powershell
python -m airport_weather -h
```

The code is changed to upper case, so `kbos` and `KBOS` are the same. `airport_weather/__main__.py` is what makes `python -m airport_weather` work: Python runs that file when you ask for a package by name.

## Step 6: Handle errors

**Goal:** when something goes wrong, print one friendly line and stop. Never show a traceback.

**Run** each of these:

```powershell
python -m airport_weather XXXX1
python -m airport_weather XXXX
```

**You should see:**

```
'XXXX1' is not an airport code. Use four letters, for example EGLL.
```

```
No weather report found for XXXX. Check the code, or try a larger airport.
```

Then check the exit code. Zero means success. Anything else means something went wrong:

```powershell
echo $LASTEXITCODE
```

It prints `1`.

**Why:** there are four things that can go wrong, and each has its own message:

| Problem | What you see |
|---|---|
| The code is not four letters | `'XXXX1' is not an airport code. Use four letters, for example EGLL.` |
| The service has no report | `No weather report found for XXXX. Check the code, or try a larger airport.` |
| No internet | `Could not reach the weather service. Check your internet connection.` |
| The service is too slow | `The weather service took too long to answer. Try again in a minute.` |

The code is checked first, before any request, so a typo never costs a network call. The other three come from `fetch.py`, which raises one error type, `WeatherError`, with the message already written. `cli.py` catches it, prints the message and returns 1.

In `fetch.py` the timeout is caught before the connection error. A connection timeout counts as both, so in the wrong order it would be reported as "no internet".

To see the no-internet message yourself, turn your wifi off and run the tool again.

## Step 7: Tests

**Goal:** prove each part works, without the internet.

**Run:**

```powershell
pytest
```

**You should see** `25 passed`.

**Why:** a test that needs the internet fails when your wifi does, and the weather changes every hour, so it could never check for an exact answer. Instead the tests use **fixtures**: saved copies of real responses in `tests/fixtures/`.

- `test_parse.py` checks that the right values come out of a response, and that each fetch problem gives the right message. It replaces `requests.get` with a stand-in, so no request is sent.
- `test_describe.py` checks the wording for wind, temperature, visibility and cloud, and the command line.

The fixtures are real responses, one per case:

| File | Why it is there |
|---|---|
| `egll.json` | Heathrow: three cloud layers |
| `kjfk.json` | New York: visibility sent as `"10+"` |
| `kden.json` | Denver: clear sky, empty cloud list |
| `egph.json` | Edinburgh: variable wind and `CAVOK` |
| `kbos.json` | Boston: gusts |
| `bikf.json` | Keflavik: visibility sent as a plain number |
| `edited_calm.json` | Heathrow with the wind set to 0 by hand |

`edited_calm.json` starts as a real response and is changed on purpose, because it is hard to catch a calm day on demand.

**To add a fixture:**

1. Save a real response. In PowerShell, replace `KSFO` with the airport you want, and `ksfo` with the file name:

   ```powershell
   curl.exe -s "https://aviationweather.gov/api/data/metar?ids=KSFO&format=json" -o tests/fixtures/ksfo.json
   ```

2. Write a test that loads it:

   ```python
   def test_my_new_case():
       weather = load_weather("ksfo")
       assert describe_wind(weather) == "Wind from the ..."
   ```

3. Run `pytest` and read the failure. It shows what the code actually said. Check that against the raw METAR in the fixture before you fix the test, because the test might be right and the code wrong.

Test names are sentences about behaviour, so a failure reads like a description of what broke.



<sub>This is an old project I managed to recover.</sub>
