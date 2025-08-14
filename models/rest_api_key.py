from odoo import models, fields, api
import secrets
from datetime import timedelta, datetime

class RestApiKey(models.Model):
    _name = 'rest.api.key'
    _description = 'REST API Access Token'
    _order = 'create_date desc'

    token = fields.Char(string='Access Token', readonly=True, copy=False)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    expires_at = fields.Datetime(string='Expiry Time', required=True)

    @api.model
    def create(self, vals):
        # Generate token if not passed
        if not vals.get('token'):
            vals['token'] = secrets.token_urlsafe(32)
        # Default expiry: 7 days
        if not vals.get('expires_at'):
            vals['expires_at'] = (datetime.utcnow() + timedelta(days=7)).isoformat()
        return super().create(vals)

    @api.model
    def deactivate_expired_tokens(self):
        expired_tokens = self.search([
            ('active', '=', True),
            ('expires_at', '<', fields.Datetime.now())
        ])
        expired_tokens.write({'active': False})