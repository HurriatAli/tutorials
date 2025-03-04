from odoo import models, fields, api

class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Type"
    _order = "sequence, name"

    name = fields.Char(required=True)
    
    property_ids = fields.One2many("estate.property", "property_type_id", string="Properties")
    offer_ids = fields.One2many("estate.property.offer", "property_type_id", string="Offers")
    
    sequence = fields.Integer(default=1)
    offer_count = fields.Integer(compute="_compute_offer_count", string="Number of Offers", store=True)

    _sql_constraints = [
        ('unique_property_type_name', 'UNIQUE(name)', 'The property type name must be unique!')
    ]

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        """Computes the total number of offers per property type."""
        for record in self:
            record.offer_count = len(record.offer_ids)
