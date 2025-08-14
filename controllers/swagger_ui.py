from odoo import http
from odoo.http import request

class SwaggerDocs(http.Controller):

    @http.route('/api/docs', auth='public', type='http', csrf=False)
    def swagger_ui(self, **kwargs):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Swagger UI</title>
          <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
          <script>
            const ui = SwaggerUIBundle({
              url: '/rest_api/static/swagger/swagger.yml',
              dom_id: '#swagger-ui',
              presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
              ],
              layout: "BaseLayout"
            })
          </script>
        </body>
        </html>
        """
        return request.make_response(html, headers=[('Content-Type', 'text/html')])
