from datetime import datetime, timedelta

from falconweather import session_manager
from falconweather.models import WindMeasurement

import pygal
from pygal.style import LightStyle

from sqlalchemy import func

'''
data = [1.2, 2.5, 0.3, 0, 0, 0, 0, 0.9, 3.4, 2.1, 2.1, 2.5, 2.5, 3.4, 3.4, 3.4, 4, 3.7, 2.5, 3.7, 4.3, 3.7, 4.3, 5.5,
        4.6, 2.8, 2.5, 2.8, 1.8, 4, 1.8, 1.2, 0.9, 1.8, 2.5, 2.1, 0, 0.6, 0, 0, 0, 0, 0, 0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0.6, 0, 1.8, 1.2, 2.4, 0, 0, 0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 3.4, 0, 0.3, 2.5, 2.5, 4.3, 3.4, 1.8, 1.2, 2.1, 3.7, 3.7, 2.1, 2.1, 1.5, 1.5, 0.3, 0, 0, 0, 0,
        0.6, 0.9, 0.6, 0, 0, 0, 1.5, 1.2, 2.1, 0.6, 0, 0, 0, 0, 0, 0, 0, 0.9, 1.2, 0.6, 0, 0, 0, 0.3, 0, 0.3, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.3, 2.5, 3.4, 1.8, 0.6, 0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 2.5, 1.8, 3.4, 2.8, 1.5, 1.2, 0.9, 0, 0, 1.2, 2.1, 2.8, 4.9, 3.7, 1.8, 1.2, 1.8, 3.1,
        2.5, 1.5, 1.5, 0.9, 2.1, 2.1, 0.6, 2.5, 1.5, 3.1, 1.5, 1.2, 0.6, 0.9, 1.8, 1.8, 0.9, 1.2, 1.2, 0.3, 1.5, 2.5,
        1.2, 0.3, 1.5, 1.8, 0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.3, 1.8, 1.2, 2.5, 2.5, 3.7, 2.1, 1.2, 1.8, 1.5, 1.8,
        1.5, 1.8, 0.9, 0, 1.8, 1.8, 1.8, 1.5, 1.8, 2.5, 2.1, 1.8, 0.3, 0, 1.5, 2.1, 1.8, 0.6, 0, 0, 1.2, 2.8, 2.5]
'''

last_hour = None
last_day = None
last_week = None
last_month = None

with session_manager.get_session() as session:
    q = session.query(
        WindMeasurement.avg_mph.label('avg'),
        WindMeasurement.max_mph.label('max')
    ).filter(
        WindMeasurement.epoch >= func.unix_timestamp(func.now()) - 3600
    )

    last_hour = [(float(row.avg), float(row.max)) for row in q.all()]

line_chart = pygal.Line(
    x_label_rotation=20,
    style=LightStyle,
    # interpolate='cubic'
)
line_chart.title = 'Average Wind Speed (1h)'
line_chart.y_title = 'mph'
line_chart.height = 250

line_chart.x_labels = map(lambda d: d.strftime('%Y-%m-%d'), [
 datetime(2013, 1, 2),
 datetime(2013, 1, 12),
 datetime(2013, 2, 2),
 datetime(2013, 2, 22)])

line_chart.add('Wind Speed', [x[0] for x in last_hour], show_dots=False)

line_chart.render_to_file('wind_avg_1h.svg', show_legend=False)
