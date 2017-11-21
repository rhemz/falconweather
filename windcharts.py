from datetime import datetime, timedelta
import os
import sys
import time

from falconweather import session_manager
from falconweather.models import WindMeasurement

import pygal
from pygal.style import CleanStyle

from sqlalchemy import func


def query_wind_speeds(session, cutoff):
    q = session.query(
        WindMeasurement.avg_mph.label('avg'),
        WindMeasurement.max_mph.label('max')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - cutoff
    ).order_by(
        WindMeasurement.epoch.asc()
    )

    last_24h = [(float(row.avg), float(row.max)) for row in q.all()]
    return last_24h


def query_groups(session, cutoff):
    q = session.query(
        func.round(WindMeasurement.avg_mph).label('avg'),
        func.count(WindMeasurement.avg_mph).label('count')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - cutoff
    ).group_by(
        func.round(WindMeasurement.avg_mph)
    )

    averages = [(int(row.avg), int(row.count)) for row in q.all()]
    return averages


def query_current_vs_max(session, cutoff):
    q = session.query(
        WindMeasurement.max_mph.label('current')
    ).order_by(
        WindMeasurement.epoch.desc()
    ).limit(1)
    current = q.one().current

    q = session.query(
        func.coalesce(func.max(WindMeasurement.max_mph), 1).label('max')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - cutoff
    )
    max = q.one().max

    return float(current), float(max)


def query_by_grouped_time(session, cutoff, column, group_func=func.date, sql_func=func.avg):
    q = session.query(
        sql_func(column).label('value'),
        group_func(func.from_unixtime(WindMeasurement.epoch)).label('date')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - cutoff,
        column >= 1
    ).group_by(
        'date'
    ).order_by(
        'date'
    )

    grouped_values = [(float(row.value), row.date) for row in q.all()]
    return grouped_values


def days_epoch(num_days):
    return 86400 * (int(time.time() / 86400) + num_days)


CHARTS = {
    # averages
    'avg_10m': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (10m)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 600},
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed',

    },
    'avg_1h': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (1h)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 3600},
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed',

    },
    'avg_24h': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (24h)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 86400},
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed'
    },
    'avg_7d': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (week)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 86400 * 7},
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed'
    },
    'avg_30d': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (mont)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 86400 * 30},
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed'
    },

    # maxes
    'max_10m': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (10m)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 600},
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed',

    },
    'max_1h': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (1h)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 3600},
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed',

    },
    'max_24h': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (24h)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 86400},
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed'
    },
    'max_7d': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (week)',
        'data_method': query_wind_speeds,
        'data_args': {'cutoff': 86400 * 7},
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed'
    },

    # other
    # 'grouped_1h': {
    #     'chart_type': pygal.Pie,
    #     'title': 'Wind Speed Frequency (1h)',
    #     'data_method': query_groups,
    #     'data_args': {'cutoff': 3600},
    #     'data_keys': {
    #         0: 'Wind Speeds'
    #     },
    #     'data_label': 'Wind Speed'
    # },
    # 'grouped_24h': {
    #     'chart_type': pygal.Pie,
    #     'title': 'Wind Speed Frequency (24h)',
    #     'data_method': query_groups,
    #     'data_args': {'cutoff': 86400},
    #     'data_keys': {
    #         0: 'Wind Speeds'
    #     },
    #     'data_label': 'Wind Speed'
    # },
    'daily_avg_7d': {
        'chart_type': pygal.HorizontalBar,
        'title': 'Daily Average (week)',
        'data_method': query_by_grouped_time,
        'data_args': {
            'cutoff': 7 * 86400,
            'column': WindMeasurement.avg_mph,
            'group_func': func.day,
            'sql_func': func.avg
        },
        'data_label': 'Wind Speed'
    },
    'daily_max_7d': {
        'chart_type': pygal.HorizontalBar,
        'title': 'Daily Max (week)',
        'data_method': query_by_grouped_time,
        'data_args': {
            'cutoff': 7 * 86400,
            'column': WindMeasurement.max_mph,
            'group_func': func.day,
            'sql_func': func.max
        },
        'data_label': 'Wind Speed'
    },
    'current_vs_24h': {
        'chart_type': pygal.SolidGauge,
        'title': 'Current Speed vs. 24h High',
        'data_method': query_current_vs_max,
        'data_args': {'cutoff': 86400},
        'data_keys': {
            0: 'Wind Speeds'
        },
        'data_label': 'Wind Speed'
    },
}

BASE_CHART = pygal.Config()
BASE_CHART.height = 400
BASE_CHART.width = 1200
BASE_CHART.y_title = 'mph'
# BASE_CHART.interpolate = 'cubic'
BASE_CHART.x_label_rotation = 20
BASE_CHART.legend_at_bottom = True
BASE_CHART.show_legend = False
BASE_CHART.style = CleanStyle
BASE_CHART.fill = False


if __name__ == '__main__':
    write_path = os.environ.get('FALCONWEATHER_CHART_PATH', None)
    if write_path is None:
        sys.exit('FALCONWEATHER_CHART_PATH not set')

    for chart, attrs in CHARTS.items():
        c = attrs['chart_type'](BASE_CHART)
        c.title = attrs['title']

        # call data function
        with session_manager.get_session() as session:

            query_function = attrs['data_method']
            data = query_function(session, **attrs['data_args'])

        # pie charts
        if isinstance(c, pygal.Pie):
            for speed, count in data:
                c.add('{} {}'.format(str(speed), BASE_CHART.y_title), count)

            c.width = int(BASE_CHART.height * 1.25)
            c.show_legend = True
            c.y_title = None

        # line charts
        elif isinstance(c, pygal.Line) or isinstance(c, pygal.StackedLine):
            for i, label in attrs['data_keys'].items():
                c.add(label, [d[i] for d in data], show_dots=False)

        # gauges
        elif isinstance(c, pygal.SolidGauge):
            c.inner_radius = 0.55
            c.width = BASE_CHART.height
            c.y_title = None
            c.x_title = None
            # c.half_pie = True
            c.value_formatter = lambda x: '{:.10g} mph'.format(x)

            c.add('current vs max', [{'value': data[0], 'max_value': data[1]}])

        elif isinstance(c, pygal.HorizontalBar) or isinstance(c, pygal.Bar):
            c.y_title = None
            c.x_title = 'mph'
            c.x_label_rotation = 0

            for value, time_label in data:
                c.add(time_label, value)

        c.render_to_file(os.path.join(write_path, 'wind_{}.svg'.format(chart)))
        c.render_to_png(os.path.join(write_path, 'wind_{}.png'.format(chart)))
