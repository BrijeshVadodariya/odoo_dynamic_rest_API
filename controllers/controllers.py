from odoo import http, fields, models
from odoo.http import request, Response
import json
import datetime
import logging

_logger = logging.getLogger(__name__)

# -------------------------------------------
# Helper function to validate the token
# It grabs the Bearer token from headers,
# checks if it exists in the 'rest.api.key' model,
# and returns the related user if valid.
# -------------------------------------------
def authenticate_request():
    token = request.httprequest.headers.get('Authorization') or request.httprequest.headers.get('X-API-Key')
    if not token:
        return None
    token = token.replace('Bearer ', '')
    api_key = request.env['rest.api.key'].sudo().search([
        ('token', '=', token),
        ('active', '=', True),
        ('expires_at', '>', fields.Datetime.now())
    ], limit=1)
    return api_key.user_id if api_key else None

def api_response(data=None, message="", code=200):
    return {
        "success": True,
        "data": data,
        "message": message,
        "code": code
    }

def api_error(message="Something went wrong", code=400):
    return {
        "success": False,
        "error": {
            "message": message,
            "code": code
        }
    }



class RestAPIController(http.Controller):

    # -------------------------------------------
    # GET a single record from a model by ID
    # Endpoint: /api/<model>/<id>
    # Method: GET
    # Needs: Bearer token in header
    # Response: Dictionary of record data
    # -------------------------------------------
    @http.route('/api/<string:model>/<int:rec_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_record(self, model, rec_id, **kwargs):
        user = authenticate_request()
        if not user:
            return request.make_response(
                json.dumps(api_error("Unauthorized", 401)),
                headers=[('Content-Type', 'application/json')],
                status=401
            )

        try:
            record = request.env[model].sudo().browse(rec_id)
            if not record.exists():
                return request.make_response(
                    json.dumps(api_error(f"Record with ID {rec_id} not found", 404)),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )

            # Read the record data
            data = record.read()[0]

            # Iterate and convert problematic data types
            for key, value in data.items():
                if isinstance(value, datetime.datetime):
                    data[key] = fields.Datetime.to_string(value)
                elif isinstance(value, datetime.date):
                    data[key] = fields.Date.to_string(value)
                elif isinstance(value, bytes):
                    # Decode bytes to a UTF-8 string. Handle potential decoding errors.
                    try:
                        data[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        _logger.warning(
                            f"Could not decode bytes for field {key} in model {model} record {rec_id}. Falling back to base64 encoding.")
                        # If decoding to string fails (e.g., it's binary data like an image),
                        # you might want to encode it in base64.
                        import base64
                        data[key] = base64.b64encode(value).decode(
                            'ascii')  # Encode to base64 and then decode base64 to string
                elif isinstance(value, (int, float, str, bool, type(None), list, dict)):
                    # These are already JSON serializable
                    pass
                else:
                    # Handle other non-serializable types.
                    # For many2one, many2many, one2many fields, .read() returns (id, name) tuples/lists.
                    # json.dumps can handle these tuples/lists directly, so no special handling needed here for them.
                    # If you have custom Odoo field types that aren't handled, you might need specific conversion.
                    _logger.warning(
                        f"Field '{key}' has an unexpected type '{type(value).__name__}' for JSON serialization in model {model} record {rec_id}.")
                    # You might choose to convert to string, or exclude it, or handle it specifically.
                    data[key] = str(value)  # Fallback to string representation

            return request.make_response(
                json.dumps(api_response(data, "Record fetched successfully", 200)),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            _logger.exception("Error in get_record API route for model %s, record %s", model, rec_id)
            return request.make_response(
                json.dumps(api_error(f"Internal server error: {str(e)}", 500)),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # Search records from a model using domain
    # Endpoint: /api/<model>/search
    # Method: POST (jsonrpc)
    # Request Body:
    # {
    #     "jsonrpc": "2.0",
    #     "method": "call",
    #     "params": {
    #         "domain": [["is_published", "=", true]],
    #         "limit": 5,
    #         "order_by": "create_date desc",
    #         "fields": ["id", "name", "create_date"]
    #     }
    # }
    # Response: List of records
    # -------------------------------------------
    @http.route('/api/<string:model>/search', type='json', auth='public', methods=['POST'], csrf=False)
    def search_records(self, model, **params):
        user = authenticate_request()
        if not user:
            return api_error("Unauthorized", 401)

        try:
            domain = params.get('domain', [])
            limit = params.get('limit', 10)
            order_by = params.get('order_by', False)
            fields_list = params.get('fields', [])

            env_model = request.env[model].sudo()
            records = env_model.search(domain, limit=limit, order=order_by)
            results = records.read(fields_list or None)

            return api_response(results, "Records fetched successfully", 200)

        except Exception as e:
            return api_error(f"Internal server error: {str(e)}", 500)


    # -------------------------------------------
    # Get the schema (fields info) of a model
    # Endpoint: /api/<model>/schema
    # Method: GET
    # Needs: Bearer token in header
    # Response: Dictionary of field definitions
    # -------------------------------------------
    @http.route('/api/<string:model>/schema', type='http', auth='public', methods=['GET'], csrf=False)
    def get_model_schema(self, model, **kwargs):
        user = authenticate_request()
        if not user:
            return request.make_response(
                json.dumps(api_error("Unauthorized", 401)),
                headers=[('Content-Type', 'application/json')]
            )

        try:
            fields_info = request.env[model].sudo().fields_get()
            return request.make_response(
                json.dumps(api_response(fields_info, f"Schema for model '{model}' fetched successfully", 200)),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return request.make_response(
                json.dumps(api_error(f"Error fetching schema: {str(e)}", 500)),
                headers=[('Content-Type', 'application/json')]
            )


    # -------------------------------------------
    # Create a new record in the given model
    # Endpoint: /api/<model>/create
    # Method: POST
    # Payload: {
    #     "data": {
    #         "field1": "value1",
    #         ...
    #     }
    # }
    # Needs: Bearer token in header
    # Response: ID of newly created record
    # -------------------------------------------
    @http.route('/api/<string:model>/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_record(self, model, **kwargs):
        user = authenticate_request()
        if not user:
            return api_error("Unauthorized", 401)

        data = kwargs.get('data')
        if not data:
            return api_error("Missing 'data' in request body", 400)

        try:
            record = request.env[model].sudo().create(data)
            if isinstance(record, models.Model):
                # Single record
                return api_response({"id": record.id}, "Record created successfully", 201)
            else:
                # Multiple records
                return api_response({"ids": [rec.id for rec in record]}, f"{len(record)} records created", 201)

        except Exception as e:
            return api_error(f"Error creating record(s): {str(e)}", 500)


    # -------------------------------------------
    # Call any method of a model using execute_kw
    # Endpoint: /api/<model>/execute_kw
    # Method: POST
    # Payload: {
    #     "method": "search_read",
    #     "args": [ [("field", "=", "value")] ],
    #     "kwargs": {"fields": ["name", "email"]}
    # }
    # Needs: Bearer token in header
    # Response: Whatever the method returns
    # -------------------------------------------
    @http.route('/api/<string:model>/execute_kw', type='json', auth='public', methods=['POST'], csrf=False)
    def execute_kw(self, model, **kwargs):
        user = authenticate_request()
        if not user:
            return api_error("Unauthorized", 401)

        method = kwargs.get('method')
        args = kwargs.get('args', [])
        kwargs_method = kwargs.get('kwargs', {})

        if not method:
            return api_error("Missing 'method' in request body", 400)

        try:
            env_model = request.env[model].sudo()
            if not hasattr(env_model, method):
                return api_error(f"Method '{method}' does not exist on model '{model}'", 404)

            result = getattr(env_model, method)(*args, **kwargs_method)
            return api_response({"result": result}, f"Method '{method}' executed successfully")

        except Exception as e:
            return api_error(f"Failed to execute '{method}' on '{model}': {str(e)}", 500)


    # -------------------------------------------
    # Update an existing record by ID
    # Endpoint: /api/<model>/<id>/update
    # Method: PUT
    # Payload: {
    #     "data": {
    #         "field1": "new_value1",
    #         ...
    #     }
    # }
    # Needs: Bearer token in header
    # Response: Success or error message
    # -------------------------------------------
    @http.route('/api/<string:model>/<int:rec_id>/update', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_record(self, model, rec_id, **kwargs):
        user = authenticate_request()
        if not user:
            return api_error("Unauthorized", 401)

        try:
            record = request.env[model].sudo().browse(rec_id)
            if not record.exists():
                return api_error(f"Record with ID {rec_id} not found in '{model}'", 404)

            data = kwargs.get('data')
            if not data:
                return api_error("Missing 'data' in request body", 400)

            record.write(data)
            return api_response(
                {"id": rec_id, "updated_fields": list(data.keys())},
                f"Record {rec_id} updated successfully"
            )

        except Exception as e:
            return api_error(f"Failed to update record: {str(e)}", 500)


    # -------------------------------------------
    # Delete a record by ID
    # Endpoint: /api/<model>/<id>/delete
    # Method: DELETE
    # Needs: Bearer token in header
    # Response: Success or error message
    # -------------------------------------------
    @http.route('/api/<string:model>/<int:rec_id>/delete', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_record(self, model, rec_id, **kwargs):
        user = authenticate_request()
        if not user:
            # Return an unauthorized response as JSON
            response_data = {'error': 'Unauthorized'}
            return Response(json.dumps(response_data), headers=[('Content-Type', 'application/json')], status=401)

        record = request.env[model].sudo().browse(rec_id)
        if not record.exists():
            # Return a not found response as JSON
            response_data = {'error': 'Record not found'}
            return Response(json.dumps(response_data), headers=[('Content-Type', 'application/json')], status=404)

        try:
            record.unlink()
            response_data = {'success': True, 'message': f'Record {rec_id} deleted'}
            return Response(json.dumps(response_data), headers=[('Content-Type', 'application/json')], status=200)
        except Exception as e:
            # Handle potential deletion errors and return a 500 response as JSON
            response_data = {'error': str(e)}
            return Response(json.dumps(response_data), headers=[('Content-Type', 'application/json')], status=500)