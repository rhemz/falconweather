import falcon


class WindResource(object):

    def on_post(self, req, resp):
        pass


api = falcon.API()
api.add_route('/wind', WindResource())
