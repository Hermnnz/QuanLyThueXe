from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDemoCatalog(TransactionCase):
    def test_real_catalog_counts(self):
        for key, expected in [('vinfast', 10), ('datbike', 8)]:
            brand = self.env.ref('motorbike_rental_demo.demo_w8_brand_' + key)
            self.assertEqual(self.env['fleet.vehicle.model'].search_count([('brand_id', '=', brand.id)]), expected)
            self.assertNotIn('Demo', brand.name)
        self.assertEqual(self.env.ref('motorbike_rental_demo.demo_w8_model_era').name, 'ERA')

    def test_catalog_hidden_independent_of_role(self):
        for xmlid in ['fleet.fleet_configuration', 'fleet.fleet_models_configuration',
                      'fleet.fleet_vehicle_model_brand_menu', 'fleet.fleet_vehicle_model_menu']:
            self.assertFalse(self.env.ref(xmlid).active)
        model = self.env.ref('motorbike_rental_demo.demo_w8_model_evo')
        vehicle = self.env.ref('motorbike_rental_demo.demo_w8_vehicle_1')
        self.assertEqual(vehicle.model_id, model)
        self.assertEqual(self.env.ref('motorbike_rental_demo.demo_w8_price_evo').model_id, model)
