from datetime import timedelta
from odoo import models, fields, api

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"

    price = fields.Float()
    status = fields.Selection([("accepted", "Accepted"), ("refused", "Refused")], copy=False)
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True
    )

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
    
        for record in self:
            base_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = base_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        
        for record in self:
            if record.date_deadline:
                base_date = record.create_date.date() if record.create_date else fields.Date.today()
                record.validity = (record.date_deadline - base_date).days

    @api.onchange("validity")
    def _onchange_validity(self):
       
        if self.validity:
            base_date = self.create_date.date() if self.create_date else fields.Date.today()
            self.date_deadline = base_date + timedelta(days=self.validity)

    @api.onchange("date_deadline")
    def _onchange_date_deadline(self):
        
        if self.date_deadline:
            base_date = self.create_date.date() if self.create_date else fields.Date.today()
            self.validity = (self.date_deadline - base_date).days
