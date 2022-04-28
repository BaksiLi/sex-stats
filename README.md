# Sex Activity Statistics
> Analyze and visualize sex activity data from Apple HealthKit and more.

## Data Source
### Shortcuts (Log WooHoo)
[Log WooHoo](https://www.icloud.com/shortcuts/4409b2271c2b4ce7837ec0867c2e81e2) is a Shortcut for logging the sex activity data, and store them in Note.app .

<details>
<summary>Screenshot</summary>
<img src="./assets/log-woohoo.jpeg">
</details>

It works on both iOS (iPhone) and WatchOS (Apple Watch). It is also proudly produced by myself.

### wHealth
[wHealth Dashboard](https://apps.apple.com/us/app/whealth-dashboard/id1109404544) is an iOS app that visualize HealthKit data based on a fixed template. Data export is supported, the exported data is a semicolon-seperated .csv file.

It does not include activity kinds as the previous Shortcuts does.

## Script
The script is run by:

```
python sex_stats.py [-h] --file FILE (--chart {freq,day,kde,all} | --all)
```

N.B. Python >= 3.8 required, other dependencies are pandas, matplotlib, and seaborn.

## Showcase
Disclaimer: Data are fake.

- All-in-one
![Example: All in one](./assets/example-stats.png)
by `python sex_stats.py -f FILE --all`.

- Individual charts
can be generated at once by `python sex_stats.py -f FILE --chart all`.

![Example: Frequency](./assets/example-freq.png)
![Example: Day](./assets/example-day.png)
![Example: KDE](./assets/example-kde.png)
