# First Cycling API

An unofficial Python API client to obtain data from https://firstcycling.com/.

## Usage

There are two main ways to interact with the API: using objects or using endpoints.

### Using Objects
The API provides classes to store data on riders and races using the `Rider` and `Race` class respectively. Objects of these classes have various methods to access associated endpoints and store the results. Some endpoints are already parsed automatically by the API.

For example, a rider's results for a certain year can be loaded into a `pandas.DataFrame` as follows:

```python
from first_cycling_api import Rider
r = Rider(65025) # Use the FirstCycling ID for the rider (found in the rider's profile page URL)
r.get_year(2020)
print(r.results[2020].results_df)
```

The results for a certain edition of a race can be obtained as a `pandas.DataFrame` as follows:

```python
from first_cycling_api import Race
r = Race(9)  # Use the FirstCycling ID for the race (found in the race page URL)
r.get_edition_results(2019)
print(r.editions[2019].results.results_table)
```

Objects can be exported in JSON format by using the `r.get_json()` method.

The following endpoint pages are currently parsed by the API:

- Rider results page for a year (e.g. https://firstcycling.com/rider.php?r=18258&y=2020)
- Results for a race edition (e.g. https://firstcycling.com/race.php?r=15&y=2019&e=04)
- Ranking pages (e.g. https://firstcycling.com/ranking.php?k=fc&rank=wel&y=2020&U23=1)
- Victory table statistics for races (e.g. https://firstcycling.com/race.php?r=9&k=W)

### Using Endpoints
Endpoints can be initialized with various parameters and return the HTML from the appropriate page in the `.response` attribute. The HTML can then be parsed using a package such as `bs4`. For some endpoints, the API also automatically parses the information and stores it in a convenient format.

For example, rankings pages can be loaded using the `Ranking` endpoint. The rankings table from the page is stores as a `pandas.DataFrame` in the `.table` attribute.

```python
from first_cycling_api import Ranking
r = Ranking(rank=1, y=2020)
print(r.table)
```

The following endpoint pages are currently mapped by the API:

- Rider pages (starting with https://firstcycling.com/rider.php?r=)
- Race pages (starting with https://firstcycling.com/race.php?r=)
- Ranking pages (starting with https://firstcycling.com/ranking.php?)

### ReadTheDocs

See the full documentation at https://firstcyclingapi.readthedocs.io/en/latest/.

## Contributing
Contributions are welcome! Please feel free to open issues, pull requests, and/or discussions.

Especially, there is room to help with:
- Mapping additional endpoints (e.g. pages starting with https://firstcycling.com/team.php?, or https://firstcycling.com/race.php?y=)
- Parsing results from additional pages (e.g. race startlists, race statistics)

## License
See the file called LICENSE. This project is not affiliated in any way with firstcycling.com.
