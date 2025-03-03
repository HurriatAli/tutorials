from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
from datetime import timedelta, date

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=lambda self: date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True)
    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)', 'The expected price must be strictly positive!'),
        ('check_selling_price', 'CHECK(selling_price >= 0)', 'The selling price must be positive!')
    ]
    @api.constrains("selling_price", "expected_price")
    def _check_selling_price(self):
        """Ensures selling price is at least 90% of the expected price."""
        for record in self:
            if not float_is_zero(record.selling_price, precision_rounding=0.01):  # Ignore 0 price
                min_acceptable_price = record.expected_price * 0.90
                if float_compare(record.selling_price, min_acceptable_price, precision_rounding=0.01) < 0:
                    raise ValidationError("The selling price cannot be lower than 90% of the expected price!")
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    total_area = fields.Integer(string="Total Area", compute="_compute_total_area", store=True)

    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        [('north', 'North'),
         ('south', 'South'),
         ('east', 'East'),
         ('west', 'West')]
    )

    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    salesperson_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user)

    state = fields.Selection(
        [('new', 'New'),
         ('offer_received', 'Offer Received'),
         ('offer_accepted', 'Offer Accepted'),
         ('sold', 'Sold'),
         ('cancelled', 'Cancelled')],
        required=True, copy=False, default='new'
    )

    best_price = fields.Float(string="Best Offer", compute="_compute_best_price", store=True)

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        """Compute the highest offer price for the property."""
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default=0)

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        """Compute total area as sum of living and garden area."""
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.onchange("garden")
    def _onchange_garden(self):
        """Set garden area and orientation when garden is enabled/disabled."""
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False

    def action_sold_property(self):
        """Marks property as sold, prevents selling if already cancelled."""
        for record in self:
            if record.state == "cancelled":
                raise UserError("A cancelled property cannot be sold!")
            record.state = "sold"

    def action_cancel_property(self):
        """Cancels the property, prevents cancelling if already sold."""
        for record in self:
            if record.state == "sold":
                raise UserError("A sold property cannot be cancelled!")
            record.state = "cancelled"
