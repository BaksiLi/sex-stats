#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime
from enum import Enum
from re import match
from typing import NamedTuple, Optional

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from pandas import DataFrame, read_csv, to_datetime

__version__ = '1.3 (i-miss-you)'


class Regex(str, Enum):
    Year = r'(?P<Year>(19|2\d)?\d{2})'
    Month = r'(?P<Month>1[0-2]|0\d)'
    Day = r'(?P<Day>[123]\d|0\d)'
    Hour = r'(?P<Hour>[01]?\d|2[0-3])'
    Minute = r'(?P<Minute>[0-5]\d)'
    Second = r'(?P<Second>[0-5]\d)'
    Time = fr'{Hour}:{Minute}(:{Second})?'
    Repeat = r'(?P<Repeat>\d) times?'
    Kind = r'(?P<Kind>\w+( \(\w+\))?)'


class TimeStamp(NamedTuple):
    """A Timestamp namedtuple, no accurate time required.
    """
    Year: int
    Month: int
    Day: int
    Hour: int = 0
    Minute: int = 0
    Second: int = 0

    @property
    def _datetime(self):
        return datetime(*(int(_) if _ else 0 for _ in self))


class LogLine(NamedTuple):
    """A Log Line nametuple.
    """
    TimeStamp: TimeStamp
    Repeat: int = 1
    Kind: Optional[str] = None


def parse_time_str(time_str: str) -> TimeStamp:
    """Parse time string and return a TimeStamp object.
    """
    acceptable_regex = {
        fr'^{Regex.Year}-{Regex.Month}-{Regex.Day}\*{Regex.Time}',
        fr'^{Regex.Day}/{Regex.Month}/{Regex.Year} {Regex.Time}'
    }

    for regex in acceptable_regex:
        if (matched := match(regex, time_str)):
            return TimeStamp(**matched.groupdict())


def parse_log_line(line: str) -> LogLine:
    """Parse log line and return a LogLine object.
    """
    acceptable_regex = fr'^.+ {Regex.Repeat} {Regex.Kind}'

    if (timestamp := parse_time_str(line)):
        matched = match(acceptable_regex, line)
        return LogLine(timestamp._datetime, int(matched['Repeat']),
                       matched['Kind'])


def read_activity_log(fp: str, header: int = 1) -> DataFrame:
    """Reads Sex Activity Log file.
    """
    with open(fp, 'r') as f:
        df = DataFrame(map(parse_log_line, f.readlines()[header:]))
        df['TimeStamp'] = to_datetime(df.TimeStamp)
        # df.set_index('TimeStamp')
        return df


def read_activity_whealth(fp: str):
    """Reads Sex Activity data from wHealth.
    """
    df = read_csv(fp, sep=';')

    # clean data
    df = df.drop(columns=['unit', 'name', 'source'], axis=1)\
           .rename(columns={'startdate': 'TimeStamp', 'value': 'Repeat'})

    df['TimeStamp'] = to_datetime(df.TimeStamp)
    df['Kind'] = 'Unknown'

    return df


def group_data(df, offset_alias: str = 'M'):
    """Group DataFrame data by an time period offset.
    """
    available_offset = ('W', 'SM', 'M', 'Q', 'A', 'H')
    if offset_alias in available_offset:
        return df.resample(offset_alias, on='TimeStamp')


def plot_freq_bar(df, offset_alias: str = 'M', ax=None, legend: bool = True):
    """Plot Frequency against Time Period.
    """
    if not ax:
        ax = plt.subplot()

    grouped = group_data(df, offset_alias)
    df_sum = grouped['Kind'].value_counts().unstack()

    df_sum.set_index(df_sum.index.map(lambda s: s.strftime('%y\n%m')))\
          .plot(rot=0, kind='bar', ax=ax, stacked=True, legend=legend)
    grouped['Repeat'].sum()\
                     .plot(style='--o',
                           ax=ax,
                           color='grey',
                           use_index=False,
                           label='Overall',
                           legend=legend)

    ax.set_title('Frequency vs Time Period')
    ax.set_ylabel('Frequency')
    ax.set_xlabel(f'Period ({offset_alias})')


def time_function(df: DataFrame):
    """Returns a function that calculates o’clock fractions.

    Should I keep narrowing the divisions as the size goes bigger?
        -> no, because < 1 min does not make sense. 6 mins already suffice.
    """
    data_size = df.shape[0]

    def fn(x):
        if data_size <= 50:  # use whole hour
            step = round(x.minute/60)
        elif data_size <= 100:  # use half division (every 30 mins)
            step = round(x.minute/60*2)/2
        elif data_size <= 200:  # use quatre division (every 15 mins)
            step = round(x.minute/60*4)/4
        else:  # use tenth division of hour (every 6 mins)
            step = round(x.minute/60, 1)
        return x.hour + step

    return fn


def plot_density(df, ax=None, legend: bool = True):
    """Plot KDE (Kernel Density Estimation).
    """
    if not ax:
        ax = plt.subplot()

    grouped = df.set_index('TimeStamp')\
                .groupby(time_function(df))['Kind'].value_counts().unstack()

    grouped.plot.kde(ax=ax, legend=legend)

    ax.set_title('Kernel Density Estimation')
    ax.set_ylabel('Density')
    ax.set_xlabel('Repeated Times')


def plot_day_hour(df, ax=None, legend: bool = True):
    """Plot activities in a day.
    """
    if not ax:
        ax = plt.subplot()

    grouped = df.set_index('TimeStamp')\
                .groupby(time_function(df))['Kind'].value_counts().unstack()

    # Plot mean
    grouped_mean = grouped.mean(axis=1)  # .fillna(0)
    ax.plot(grouped_mean.index, grouped_mean, color='grey', linestyle='-', label='Mean')

    # Plot scattered points
    for kind in grouped.columns:
        plt.scatter(grouped.index, grouped[kind], label=kind)

    ax.set_title('Activities in a Day')
    ax.set_ylabel('Frequency')
    ax.set_xlabel('O’Clock')
    ax.set_xlim(-.5, 24.5)
    ax.set_ylim(0, grouped.max().max() + 1)
    ax.set_yticks(list(range(int(grouped.max().max()) + 2)))
    ax.set_xticks(list(range(24)))

    if legend:
        ax.legend()


def plot_all(df):
    """Plot all three charts in one large diagram.
    """
    fig = plt.figure(constrained_layout=True)
    fig.suptitle(f'Sex Activity Statistics ({df.Repeat.size} entries)')

    gs = GridSpec(2, 2, figure=fig)

    ax = fig.add_subplot(gs[0, :])
    plot_day_hour(df, ax=ax, legend=False)

    ax2 = fig.add_subplot(gs[1, 0])
    plot_freq_bar(df, ax=ax2, legend=False)

    ax3 = fig.add_subplot(gs[1, 1])
    plot_density(df, ax=ax3, legend=False)

    handles, labels = ax3.get_legend_handles_labels()
    fig.legend(handles, labels, title='Kind', loc='upper right')


def cli_parsed():
    parser = ArgumentParser(
            description='Analyse sex activity data.',
            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('--file', '-f', required=True, help='Log file path.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chart',
                       choices=['freq', 'day', 'kde', 'all'],
                       help='Specify charts to plot \
                             (options: freq, day, kde, all).')
    group.add_argument('--all',
                       action='store_true',
                       help='Plot all charts in one large diagram.')

    return parser


if __name__ == '__main__':
    args = cli_parsed().parse_args()

    # Read dataset (csv and txt)
    if args.file.rsplit('.', 1)[-1] == 'csv':
        log_lines = read_activity_whealth(args.file)
    else:
        log_lines = read_activity_log(args.file)

    # Plot settings
    sns.set()
    plot_fns = {
        'freq': plot_freq_bar,
        'day': plot_day_hour,
        'kde': plot_density,
    }

    if args.all:
        plot_all(log_lines)
    elif args.chart == 'all':
        for fn in plot_fns.values():
            fn(log_lines)
            plt.show()
    elif args.chart in plot_fns:
        plot_fns[args.chart](log_lines)
    plt.show()
