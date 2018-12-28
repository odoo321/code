import json
import urllib2

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


def geo_find(addr):
    if not addr:
        return None
    url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
    url += urllib2.quote(addr.encode('utf8'))

    try:
        result = json.load(urllib2.urlopen(url))
    except Exception as e:
        raise UserError(_('Cannot contact geolocation servers. Please make sure that your Internet connection is up and running (%s).') % e)

    if result['status'] != 'OK':
        return None

    try:
        geo = result['results'][0]['geometry']['location']
        return float(geo['lat']), float(geo['lng'])
    except (KeyError, ValueError):
        return None


def geo_query_address(street=None, zip=None, city=None, state=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street,
                                              ("%s %s" % (zip or '', city or '')).strip(),
                                              state,
                                              country])))

class Branch(models.Model):
    _inherit = 'res.company'

    lat_comapny = fields.Float('Latitude', digits=(16, 5))
    lng_company = fields.Float('Longitude', digits=(16, 5))
    checkin_radius = fields.Float('Check In Radius')
    checkin_radius_selection = fields.Selection([('km', 'KM'),('meter', 'Meter')], 'Unit')
    checkout_radius = fields.Float('Check Out Radius')
    checkout_radius_selection = fields.Selection([('km', 'KM'), ('meter', 'Meter')], 'Unit')
    allow_boundary_check_in = fields.Boolean('Allow Out of Boundary Check In', help="If ticked, system allow user to check in if it is out of boundary.")
    allow_boundary_check_out = fields.Boolean('Allow Out of Boundary Check Out',  help="If ticked, system allow user to check out if it is out of boundary.")

    @api.multi
    def geo_localize_company(self):
        # We need country names in English below
        result = geo_find(geo_query_address(street=self.street,
                                            zip=self.zip,
                                            city=self.city,
                                            state=self.state_id.name,
                                            country=self.country_id.name))
        if result is None:
            raise UserError(_('Please check company address or try again!'))

        if result:
            self.lat_comapny = result[0]
            self.lng_company = result[1]
        return True