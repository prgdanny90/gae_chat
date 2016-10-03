import webapp2
class ParseHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("ok")

app = webapp2.WSGIApplication([
    ('/init', ParseHandler)
], debug=True)