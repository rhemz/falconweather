import os
import time

import falcon
from webargs.falconparser import parser as falcon_parser
from marshmallow import fields

from falconweather.db import SessionManager
from falconweather.models import WindMeasurement

from sqlalchemy import func


class FalconWeatherResource(object):

    def __init__(self, session_manager):
        self.db = session_manager


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

    def on_post(self, req, resp):
        args = falcon_parser.parse(
            argmap={
                'mph': fields.Float(required=True)
            },
            req=req,
            force_all=True
        )

        with self.db.get_session(autocommit=True) as session:
            session.add(
                WindMeasurement(
                    epoch=int(time.time()),
                    mph=args['mph'],
                )
            )
            session.flush()

        resp.media = {
            'status': 'ok',
            'args': args,
        }


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
