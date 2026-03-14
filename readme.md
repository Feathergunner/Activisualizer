# Activity Visualizer

Some scripts for downloading, parsing and visualizing activity-data from a garmin account.
To create plots that aggregate data of multiple activities, to visualize training progress.

## Examples
![Visualizing Pace vs. Heartrate](example_running.png "Pace vs. Heartrate")
![Visualizing elevation profile of multiple runs](example_totalele.png "Elevation Profile")
![Visualizing cumulative elevation gain of multiple runs](example_cumele.png "Elevation Gain")

## Usage
For downloading data, and for scatterplots of heartrate vs. pace (per split): `main.py`.
Run `python main.py --help` for information on arguments.


For elevation profiles and plots of cumulative elevation gains: run `python visualize_full.py` (see function `plot_elevation_profiles`).
These functionalities will be included into the main program in the future :)