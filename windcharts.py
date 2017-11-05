from datetime import datetime, timedelta

from falconweather import session_manager
from falconweather.models import WindMeasurement

import pygal
from pygal.style import CleanStyle

from sqlalchemy import func


def query_1h(session):
    q = session.query(
        WindMeasurement.avg_mph.label('avg'),
        WindMeasurement.max_mph.label('max')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - 3600
    ).order_by(
        WindMeasurement.epoch.asc()
    )

    last_1h = [(float(row.avg), float(row.max)) for row in q.all()]
    return last_1h


def query_24h(session):
    q = session.query(
        WindMeasurement.avg_mph.label('avg'),
        WindMeasurement.max_mph.label('max')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - 86400
    ).order_by(
        WindMeasurement.epoch.asc()
    )

    last_24h = [(float(row.avg), float(row.max)) for row in q.all()]
    return last_24h


BASE_CHART = pygal.Config()
BASE_CHART.height = 400
BASE_CHART.width = 1024
BASE_CHART.y_title = 'mph'
# base_chart.interpolate = 'cubic'
BASE_CHART.x_label_rotation = 20
BASE_CHART.show_legend = False
BASE_CHART.style = CleanStyle


CHARTS = {
    # averages
    'avg_1h': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (1h)',
        'data_method': query_1h,
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed',

    },
    'avg_24h': {
        'chart_type': pygal.Line,
        'title': 'Average Wind Speed (24h)',
        'data_method': query_24h,
        'data_keys': {
            0: 'Average Speed'
        },
        'data_label': 'Wind Speed'
    },

    # maxes
    'max_1h': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (1h)',
        'data_method': query_1h,
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed',

    },
    'max_24h': {
        'chart_type': pygal.Line,
        'title': 'Maximum Wind Speed (24h)',
        'data_method': query_24h,
        'data_keys': {
            1: 'Max Speed'
        },
        'data_label': 'Wind Speed'
    }
}

if __name__ == '__main__':
    for chart, attrs in CHARTS.items():
        c = attrs['chart_type'](BASE_CHART)
        c.title = attrs['title']

        with session_manager.get_session() as session:
            # query_function = globals()['query_{}'.format(chart)]
            query_function = attrs['data_method']
            data = query_function(session)

        for i, label in attrs['data_keys'].items():
            c.add(label, [d[i] for d in data], show_dots=False)
        # c.add(attrs['data_label'], [d[0] for d in data], show_dots=False)

        c.render_to_file('/srv/www/net.8harvest.weather/public/wind_{}.svg'.format(chart))
        c.render_to_png('/srv/www/net.8harvest.weather/public/wind_{}.png'.format(chart))
