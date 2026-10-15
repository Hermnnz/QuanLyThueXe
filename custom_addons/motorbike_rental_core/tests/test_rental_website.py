import re
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestRentalWebsite(HttpCase):

    def test_rental_booking_page_is_available(self):
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Website Test Brand',
        })
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Evo',
            'brand_id': brand.id,
            'vehicle_type': 'bike',
        })
        rental_type = self.env['rental.vehicle.type'].create({
            'name': 'Website Test Price',
            'model_id': model.id,
            'currency_id': self.env.company.currency_id.id,
            'daily_rate': 250000,
        })
        vehicle = self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': '29-WEB01',
        })
        self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': '29-WEB02',
        })

        response = self.url_open('/thue-xe')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Chọn xe cho chuyến đi của bạn', response.text)
        self.assertIn('vehicle-card', response.text)
        self.assertIn(vehicle.model_id.display_name, response.text)
        self.assertIn(f'name="quantity_{rental_type.id}"', response.text)
        self.assertIn('max="2"', response.text)
        self.assertIn('Tổng xe tồn:', response.text)
        self.assertIn('evo.jpg', response.text)

    def test_public_booking_creates_one_line_per_selected_vehicle(self):
        rental_user_group = self.env.ref(
            'motorbike_rental_core.group_rental_user'
        )
        self.env['res.users'].create({
            'name': 'Rental Website Test User',
            'login': 'rental-website-test-user',
            'groups_id': [(6, 0, [rental_user_group.id])],
        })
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Multi Rental Test Brand',
        })
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Multi Rental Test Motorbike',
            'brand_id': brand.id,
            'vehicle_type': 'bike',
        })
        rental_type = self.env['rental.vehicle.type'].create({
            'name': 'Multi Rental Test Price',
            'model_id': model.id,
            'currency_id': self.env.company.currency_id.id,
            'daily_rate': 250000,
        })
        self.env['fleet.vehicle'].create([
            {'model_id': model.id, 'license_plate': '29-MULTI01'},
            {'model_id': model.id, 'license_plate': '29-MULTI02'},
        ])
        page = self.url_open('/thue-xe')
        csrf_token = re.search(
            r'name="csrf_token" value="([^"]+)"',
            page.text,
        ).group(1)
        start_date = fields.Datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        response = self.url_open(
            '/thue-xe',
            data={
                'csrf_token': csrf_token,
                'customer_name': 'Multiple Vehicle Test',
                'phone': '0900000000',
                'start_utc': fields.Datetime.to_string(start_date),
                'end_utc': fields.Datetime.to_string(end_date),
                f'quantity_{rental_type.id}': '2',
            },
            allow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        contract = self.env['rental.contract'].search(
            [('customer_id.phone', '=', '0900000000')],
            limit=1,
        )
        self.assertEqual(len(contract.line_ids), 2)
        self.assertEqual(
            set(contract.line_ids.mapped('vehicle_id.model_id').ids),
            {model.id},
        )
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', contract.customer_id.id),
            ('summary', '=', 'Yêu cầu thuê xe mới'),
        ])
        self.assertTrue(activities)
        self.assertEqual(
            set(activities.mapped('user_id').ids),
            set(
                self.env.ref(
                    'motorbike_rental_core.group_rental_user'
                ).users.filtered('active').ids
            ),
        )
