from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
import secrets
import json
import logging

_logger = logging.getLogger(__name__)

class RestAuthController(http.Controller):

    def api_response(self, data=None, message="", code=200):
        """Standard success response format"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "code": code
        }

    def api_error(self, message="Something went wrong", code=400):
        """Standard error response format"""
        return {
            "success": False,
            "error": {
                "message": message,
                "code": code
            }
        }

    @http.route('/api/login', type='json', auth='public', methods=['POST'], csrf=False)
    def login(self, **params):
        raw_data = request.httprequest.data
        _logger.info("Raw request data: %s", raw_data)

        try:
            data = json.loads(raw_data)
            db = data.get('db')
            email = data.get('email')
            password = data.get('password')
        except Exception as e:
            return {'error': f'Invalid JSON: {str(e)}'}

        if not all([db, email, password]):
            return {'error': 'Missing db, email or password'}

        # Use a credentials dict for neatness
        credentials = {
            'login': email,
            'password': password,
            'type': 'password'  # Explicitly specify the authentication type
        }

        # Authenticate using unpacked credentials
        try:
            uid = request.session.authenticate(db, credentials)
        except Exception as e:
            error_msg = str(e)
            status_code = 500

            # Handle specific error cases
            if 'database' in error_msg and 'does not exist' in error_msg:
                status_code = 400
                error_msg = f"Database '{db}' does not exist"
            elif 'password authentication failed' in error_msg:
                status_code = 401
                error_msg = "Database connection failed - invalid credentials"
            elif 'invalid credentials' in error_msg.lower():
                status_code = 401
                error_msg = "Invalid email or password"

            _logger.error("Authentication error: %s", error_msg)
            return self.api_error(error_msg, status_code)

        if not uid:
            return self.api_error("Invalid credentials", 401)

            # Process successful login
        actual_uid = uid.get('uid')
        user = request.env['res.users'].sudo().browse(actual_uid)

        # Token management
        token_rec = request.env['rest.api.key'].sudo().search([
            ('user_id', '=', actual_uid),
            ('active', '=', True),
            ('expires_at', '>', fields.Datetime.now())
        ], limit=1)

        if not token_rec:
            token = secrets.token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(days=7)
            token_rec = request.env['rest.api.key'].sudo().create({
                'user_id': actual_uid,
                'token': token,
                'expires_at': expires,
            })

        # Prepare success response data
        response_data = {
            'token': token_rec.token,
            'expires_at': token_rec.expires_at.isoformat(),
            'user': {'email': user.login},
            'session_id': request.session.sid,
        }

        return self.api_response(
            data=response_data,
            message="Login successful",
            code=200
        )