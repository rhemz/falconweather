import os
import time

import falcon
from webargs.falconparser import parser as falcon_parser
from marshmallow import fields

from falconweather.db import SessionManager
from falconweather.models import WindMeasurement

import jinja2

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


class FalconWeatherResource(object):

    def __init__(self, session_manager):
        self.db = session_manager

    def load_template(self, name):
        path = os.path.join('templates', name)
        with open(os.path.abspath(path), 'r') as fp:
            return jinja2.Template(fp.read())


class WeatherResource(FalconWeatherResource):

    def on_get(self, req, resp):

        # get counts of measurements.  just wind for now.  others soon?
        with self.db.get_session() as session:
            q = session.query(func.count(WindMeasurement.epoch).label('count'))
            wind_count = q.one().count

        resp.media = {
            'status': 'ok',
            'wind_measurements': wind_count
        }


class WindResource(FalconWeatherResource):

    def on_get(self, req, resp):
        with self.db.get_session() as session:
            q = session.query(
                func.avg(WindMeasurement.avg_mph).label('avg'),
                func.max(WindMeasurement.max_mph).label('max')
            ).filter(
                WindMeasurement.epoch >= func.unix_timestamp(func.now()) - 3600
            )
            r = q.one()
            hour_avg = r.avg
            hour_max = r.max

            q = session.query(
                func.avg(WindMeasurement.avg_mph).label('avg'),
                func.max(WindMeasurement.max_mph).label('max')
            ).filter(
                WindMeasurement.epoch >= func.unix_timestamp(func.now()) - 86400
            )
            r = q.one()
            day_avg = r.avg
            day_max = r.max

        # load and render template
        template = self.load_template('wind.j2')
        resp.content_type = 'text/html'
        resp.body = template.render(
            hour_max=hour_max,
            hour_avg=hour_avg,
            day_max=day_max,
            day_avg=day_avg
        )

    def on_post(self, req, resp):
        args = falcon_parser.parse(
            argmap={'mph': fields.String(required=True)},
            req=req,
            force_all=True
        )

        avg, max = self._parse_payload(args['mph'])

        with self.db.get_session() as session:
            try:
                session.add(
                    WindMeasurement(
                        epoch=int(time.time()),
                        avg_mph=avg,
                        max_mph=max
                    )
                )
                session.commit()
            except IntegrityError:
                # duplicate timestamp.  usually the particle cloud fucking up
                print('duplicate particle request...')
                pass

        resp.media = {
            'status': 'ok',
            'avg_mph': avg,
            'max_mph': max
        }

    def _parse_payload(self, value):
        avg, max = value.split('|')

        return float(avg), float(max)


# start
session_manager = SessionManager(
    db_config={
        'host':     os.environ.get('FALCONWEATHER_DB_HOST', 'localhost'),
        'port':     os.environ.get('FALCONWEATHER_DB_PORT', 3306),
        'user':     os.environ.get('FALCONWEATHER_DB_USER', 'falconweather'),
        'password': os.environ.get('FALCONWEATHER_DB_PASSWORD', ''),
        'db':       os.environ.get('FALCONWEATHER_DB_NAME', 'falconweather'),
    },
    pool_args={
        'pool_size':    1,
        'pool_recycle': 600,
        'max_overflow': 4,
        'echo':         False,
        'echo_pool':    False
    }
)


api = falcon.API()
api.add_route('/', WeatherResource(session_manager))
api.add_route('/wind', WindResource(session_manager))
