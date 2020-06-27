import os
import sys
import time

import falcon
from webargs.falconparser import parser as falcon_parser
from marshmallow import fields

from falconweather.db import SessionManager
from falconweather.models import WindMeasurement

import jinja2

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


DOCKERIZED = bool(os.environ.get('FALCONWEATHER_DOCKERIZED', False))
SITE_ADDR = os.environ.get('FALCONWEATHER_SITE', '')
MYSQL_ADDR = os.environ.get('DOCKER_HOST_IP', '127.0.0.1') if DOCKERIZED else '127.0.0.1'

ERROR_THRESHOLD = 90


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
            'wind_measurements': wind_count * 2,  # avg, max for each interval
            'wind_href': '{}/wind'.format(SITE_ADDR)
        }


class WindResource(FalconWeatherResource):

    def on_get(self, req, resp):
        with self.db.get_session() as session:
            one_min_avg, one_min_max = self._get_avg_max(session, cutoff=60)
            ten_min_avg, ten_min_max = self._get_avg_max(session, cutoff=600)
            hour_avg, hour_max = self._get_avg_max(session, cutoff=3600)
            twelve_hour_avg, twelve_hour_max = self._get_avg_max(session, cutoff=3600 * 12)
            day_avg, day_max = self._get_avg_max(session, cutoff=86400)
            week_avg, week_max = self._get_avg_max(session, cutoff=86400 * 7)
            month_avg, month_max = self._get_avg_max(session, cutoff=86400 * 30)
            alltime_avg, alltime_max = self._get_avg_max(session, cutoff=sys.maxsize)

            q = session.query(
                ((WindMeasurement.max_mph + WindMeasurement.max_mph) / 2).label('current')
            ).order_by(
                WindMeasurement.epoch.desc()
            ).limit(1)
            current = q.one().current

        # load and render template
        template = self.load_template('wind.j2')
        resp.content_type = 'text/html'

        try:
            resp.body = template.render(
                current=current,
                one_min=(one_min_avg, one_min_max),
                ten_min=(ten_min_avg, ten_min_max),
                hour=(hour_avg, hour_max),
                twelve_hour=(twelve_hour_avg, twelve_hour_max),
                day=(day_avg, day_max),
                week=(week_avg, week_max),
                month=(month_avg, month_max),
                alltime=(alltime_avg, alltime_max)
            )
        except Exception as e:
            print(e)
            print(locals())
            raise falcon.HTTPInternalServerError(description='Error generating stats')

    def on_post(self, req, resp):
        args = falcon_parser.parse(
            argmap={'mph': fields.String(required=True)},
            req=req,
            force_all=True
        )

        avg, max = self._parse_payload(args['mph'])

        if max >= ERROR_THRESHOLD:
            print('Likely erroneous measurement, discarding... {}'.format(args))
            resp.media = {
                'status': 'error',
                'message': 'Likely erroneous measurement, discarding... {}'.format(args)
            }
            return

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
                status = 'ok'
            except IntegrityError:
                # duplicate timestamp.  usually the particle cloud fucking up
                print('{} - duplicate particle request: {}...'.format(int(time.time()), args))
                status = 'duplicate'
                pass

        resp.media = {
            'status': status,
            'avg_mph': avg,
            'max_mph': max
        }

    def _get_avg_max(self, session, cutoff):
        q = session.query(
            func.coalesce(func.avg(WindMeasurement.avg_mph), 0).label('avg'),
            func.coalesce(func.max(WindMeasurement.max_mph), 0).label('max')
        ).filter(
            WindMeasurement.epoch >= func.unix_timestamp(func.now()) - cutoff
        )
        r = q.one()
        return r.avg, r.max

    def _parse_payload(self, value):
        avg, max = value.split('|')

        return float(avg), float(max)


# start
session_manager = SessionManager(
    db_config={
        'host':     MYSQL_ADDR,
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
