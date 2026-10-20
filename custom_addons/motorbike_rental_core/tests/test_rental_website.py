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
            'is_electric_motorbike': True,
            'operational_status': 'available',
            'technical_ready': True,
        })
        self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': '29-WEB02',
            'is_electric_motorbike': True,
            'operational_status': 'available',
            'technical_ready': True,
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

    def test_availability_only_counts_fleet_ready_vehicles(self):
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Fleet Readiness Website Test Brand',
        })
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Fleet Readiness Website Test Model',
            'brand_id': brand.id,
            'vehicle_type': 'bike',
        })
        rental_type = self.env['rental.vehicle.type'].create({
            'name': 'Fleet Readiness Website Test Price',
            'model_id': model.id,
            'currency_id': self.env.company.currency_id.id,
            'daily_rate': 250000,
        })
        self.env['fleet.vehicle'].create([
            {
                'model_id': model.id,
                'license_plate': '29-READY01',
                'is_electric_motorbike': True,
                'operational_status': 'available',
                'technical_ready': True,
            },
            {
                'model_id': model.id,
                'license_plate': '29-READY02',
                'is_electric_motorbike': True,
                'operational_status': 'pending_inspection',
                'technical_ready': False,
            },
            {
                'model_id': model.id,
                'license_plate': '29-READY03',
                'is_electric_motorbike': True,
                'operational_status': 'maintenance',
                'technical_ready': False,
            },
            {
                'model_id': model.id,
                'license_plate': '29-READY04',
                'is_electric_motorbike': True,
                'operational_status': 'available',
                'technical_ready': True,
                'rental_blocked': True,
                'block_reason': 'Website availability test',
            },
        ])

        response = self.url_open('/thue-xe')

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.text,
            (
                rf'<input(?=[^>]*id="quantity_{rental_type.id}")'
                rf'(?=[^>]*max="1")[^>]*>'
            ),
        )

    def test_all_rental_prices_are_listed_across_pages(self):
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Paged Website Test Brand',
        })
        rental_types = self.env['rental.vehicle.type']
        for index in range(13):
            model = self.env['fleet.vehicle.model'].create({
                'name': f'Paged Website Test Model {index}',
                'brand_id': brand.id,
                'vehicle_type': 'bike',
            })
            rental_types |= self.env['rental.vehicle.type'].create({
                'name': f'Paged Website Test Price {index}',
                'model_id': model.id,
                'currency_id': self.env.company.currency_id.id,
                'daily_rate': 250000 + index,
            })

        response = self.url_open('/thue-xe')

        self.assertEqual(response.status_code, 200)
        for rental_type in rental_types:
            self.assertIn(rental_type.name, response.text)
        self.assertIn('data-rental-page="2"', response.text)
        self.assertIn('data-rental-page="1"', response.text)
        self.assertIn('name="quantity_%s"' % rental_types[-1].id, response.text)

    def test_public_booking_creates_one_line_per_selected_vehicle(self):
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
            {
                'model_id': model.id,
                'license_plate': '29-MULTI01',
                'is_electric_motorbike': True,
                'operational_status': 'available',
                'technical_ready': True,
            },
            {
                'model_id': model.id,
                'license_plate': '29-MULTI02',
                'is_electric_motorbike': True,
                'operational_status': 'available',
                'technical_ready': True,
            },
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
