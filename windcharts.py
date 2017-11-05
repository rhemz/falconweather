from datetime import datetime, timedelta

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


CHARTS = {
    # averages
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

    # maxes
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

    # other
    'grouped_1h': {
        'chart_type': pygal.Pie,
        'title': 'Wind Speed Frequency (24h)',
        'data_method': query_groups,
        'data_args': {'cutoff': 3600},
        'data_keys': {
            0: 'Wind Speeds'
        },
        'data_label': 'Wind Speed'
    },
    'grouped_24h': {
        'chart_type': pygal.Pie,
        'title': 'Wind Speed Frequency (24h)',
        'data_method': query_groups,
        'data_args': {'cutoff': 86400},
        'data_keys': {
            0: 'Wind Speeds'
        },
        'data_label': 'Wind Speed'
    },
}

BASE_CHART = pygal.Config()
BASE_CHART.height = 400
BASE_CHART.width = 1024
BASE_CHART.y_title = 'mph'
# base_chart.interpolate = 'cubic'
BASE_CHART.x_label_rotation = 20
BASE_CHART.legend_at_bottom = True
BASE_CHART.show_legend = False
BASE_CHART.style = CleanStyle
BASE_CHART.fill = False


if __name__ == '__main__':
    for chart, attrs in CHARTS.items():
        c = attrs['chart_type'](BASE_CHART)
        c.title = attrs['title']

        with session_manager.get_session() as session:
            # query_function = globals()['query_{}'.format(chart)]
            query_function = attrs['data_method']
            data = query_function(session, **attrs['data_args'])

        # pie charts
        if isinstance(c, pygal.Pie):
            for speed, count in data:
                c.add('{} {}'.format(str(speed), BASE_CHART.y_title), count)

            c.width = int(BASE_CHART.height * 1.25)
            c.show_legend = True
            c.y_title = None
            # c.inner_radius = 0.4

        # line charts
        elif isinstance(c, pygal.Line) or isinstance(c, pygal.StackedLine):
            for i, label in attrs['data_keys'].items():
                c.add(label, [d[i] for d in data], show_dots=False)

        c.render_to_file('/srv/www/net.8harvest.weather/public/wind_{}.svg'.format(chart))
        c.render_to_png('/srv/www/net.8harvest.weather/public/wind_{}.png'.format(chart))
