import falcon
from webargs.falconparser import parser as falcon_parser
from marshmallow import fields


class WindResource(object):

    def on_post(self, req, resp):
        print('posted')
        args = falcon_parser.parse(
            params={
                'mph': fields.Float(missing=True, required=True)
            },
            req=req,
            force_all=True
        )
        print(args)
        pass


api = falcon.API()
api.add_route('/wind', WindResource())
