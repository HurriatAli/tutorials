from datetime import timedelta, date
from odoo import models, fields, api
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"

    price = fields.Float(required=True, string="Offer Price")
    _sql_constraints = [
        ('check_offer_price', 'CHECK(price > 0)', 'The offer price must be strictly positive!')
    ]
    status = fields.Selection([
        ("accepted", "Accepted"),
        ("refused", "Refused")
    ], copy=False, string="Status")

    partner_id = fields.Many2one("res.partner", required=True, string="Buyer")
    property_id = fields.Many2one("estate.property", required=True, string="Property")

    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True
    )

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        """Computes the offer deadline based on creation date and validity period."""
        for record in self:
            base_date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = base_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        """Sets validity period when the deadline is manually changed."""
        for record in self:
            if record.date_deadline:
                base_date = record.create_date.date() if record.create_date else fields.Date.today()
                record.validity = (record.date_deadline - base_date).days

    @api.onchange("validity")
    def _onchange_validity(self):
        """Updates date_deadline dynamically when validity changes."""
        if self.validity:
            base_date = self.create_date.date() if self.create_date else fields.Date.today()
            self.date_deadline = base_date + timedelta(days=self.validity)

    @api.onchange("date_deadline")
    def _onchange_date_deadline(self):
        """Updates validity dynamically when date_deadline changes."""
        if self.date_deadline:
            base_date = self.create_date.date() if self.create_date else fields.Date.today()
            self.validity = (self.date_deadline - base_date).days

    def action_accept_offer(self):
        """Accepts an offer, sets property as sold, and updates selling price."""
        for record in self:
            if record.property_id.state == "sold":
                raise UserError("This property is already sold!")

            # Ensure only one offer is accepted
            accepted_offers = record.property_id.offer_ids.filtered(lambda o: o.status == "accepted")
            if accepted_offers:
                raise UserError("Only one offer can be accepted for a property!")

            record.status = "accepted"
            record.property_id.write({
                "buyer_id": record.partner_id.id,
                "selling_price": record.price,
                "state": "offer_accepted"
            })

    def action_refuse_offer(self):
        """Refuses an offer."""
        for record in self:
            record.status = "refused"
