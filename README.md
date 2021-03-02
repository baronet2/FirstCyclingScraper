# FirstCyclingScraper

This repository provides a tool to scrape data from firstcycling.com.

## Usage
The relevant scripts are contained in `FirstCyclingScraper.py`. Import them by adding that file to your working directory and using:
```python
from SpotifyPlaylistScraper import *
```

To load data for a rider, you will need the rider id used by firstcycling.com in the url.
For example, for Primoz Roglic, the rider is 18655.
You can see this from the url of his profile page: https://firstcycling.com/rider.php?r=18655.

Riders are loaded into a `Rider` object. To load data for a rider, use:
```python
r = Rider(18655)
```

You can also load details for a rider in a particular year using an additional argument:
```python
r = Rider(18655, 2020)
```

## How it Works
The program uses `requests` and `bs4` to load data from firstcycling.com

## Contributing
If you would like to contribute to the code, please feel free to open a pull request. Feel free to open an issue to request features, identify bugs, or discuss the tool.
