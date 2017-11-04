import falcon
from webargs.falconparser import parser as falcon_parser
from marshmallow import fields


class WindResource(object):

    def on_post(self, req, resp):
        args = falcon_parser.parse(
            {
                'mph': fields.Float(required=True)
            },
            req=req,
            force_all=True
        )
        print(args)
        resp.media = args
        pass


api = falcon.API()
api.add_route('/wind', WindResource())
