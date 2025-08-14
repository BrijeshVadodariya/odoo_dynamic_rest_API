{
    'name': 'Odoo dynamic rest API',
    'summary': 'A RESTful API for seamless Odoo integration with external systems',
    'description': """
        This module provides a RESTful API for Odoo, enabling seamless integration with external systems.
        It supports secure authentication, CRUD operations on any Odoo model, custom method execution,
        and interactive API documentation via Swagger UI. Ideal for automating business processes
        and connecting Odoo with third-party applications.
    """,
    'author': 'Micra digital',
    'website': 'https://www.micra.digital',
    'support': "hello@micra.digital",
    'license': "LGPL-3",
    'category': 'Tools',
    'version': '18.0.1.0.0',
    'depends': ['base'],
    'data': [
        'data/cron.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/rest_api/static/swagger/swagger-ui.css',
            '/rest_api/static/swagger/swagger-ui-bundle.js',
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'images': [
        'static/description/icon.png',
        'static/description/swagger_screenshot.png',
    ],
    'maintainer': 'Micra digital',
    'price': 29.99,
    'currency': 'USD',
}