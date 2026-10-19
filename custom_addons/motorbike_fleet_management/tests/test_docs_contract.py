"""Guard the Fleet field list from the team Word, including supplementary ODO."""
from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestFleetDocsContract(TransactionCase):
    def _visible_fields(self, xmlid, values):
        values = {'service_schedule_state': 'ok', 'service_odometer_recorded': False,
                  'service_interval_km': 0, 'service_interval_months': 0,
                  'service_last_date': False, **values}
        arch = self.env.ref(xmlid)._get_combined_arch()
        visible = set()
        for node in arch.xpath('.//field'):
            if not any(safe_eval(parent.get('invisible', 'False'), values)
                       for parent in [*reversed(list(node.iterancestors())), node]
                       if parent.get('invisible')):
                visible.add(node.get('name'))
        return visible

    def test_vehicle_doc_fields_visible(self):
        fields = self._visible_fields('fleet.fleet_vehicle_view_form', {
            'is_electric_motorbike': True, 'active': True, 'rental_blocked': True,
            'block_reason': 'Kiểm kê', 'operational_status': 'pending_inspection',
            'future_driver_id': False, 'vehicle_type': 'bike', 'service_activity': 'none',
            'power_unit': 'power'})
        expected = {'model_id', 'license_plate', 'acquisition_date', 'vehicle_code',
                    'operational_status', 'next_service_date', 'block_reason',
                    'is_electric_motorbike', 'technical_ready', 'rental_blocked', 'odometer'}
        self.assertFalse(expected - fields, str(expected - fields))
        self.assertFalse({'state_id', 'driver_id', 'category_id', 'car_value'} & fields)

    def test_classification_visible_even_when_unchecked(self):
        fields = self._visible_fields('fleet.fleet_vehicle_view_form', {
            'is_electric_motorbike': False, 'active': True, 'rental_blocked': False,
            'block_reason': False, 'operational_status': 'pending_inspection',
            'future_driver_id': False, 'vehicle_type': 'bike', 'service_activity': 'none',
            'power_unit': 'power'})
        self.assertIn('is_electric_motorbike', fields)

    def test_model_and_service_doc_fields_visible(self):
        model = self._visible_fields('fleet.fleet_vehicle_model_view_form', {'active': True})
        self.assertTrue({'name', 'brand_id', 'vehicle_type'} <= model)
        self.assertNotIn('category_id', model)
        service = self._visible_fields('fleet.fleet_vehicle_log_services_view_form', {
            'is_electric_motorbike': True, 'active': True, 'state': 'new'})
        expected = {'vehicle_id', 'description', 'state', 'date', 'notes', 'amount',
                    'maintenance_type', 'next_service_date', 'result', 'blocks_rental',
                    'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end'}
        self.assertFalse(expected - service, str(expected - service))
        self.assertFalse({'purchaser_id', 'technician_id', 'vendor_id', 'service_type_id'} & service)

    def test_scope_menus_and_stored_odometer(self):
        for xmlid in ['fleet.fleet_vehicle_model_category_menu', 'fleet.fleet_vehicles',
                      'fleet.menu_fleet_reporting', 'fleet.fleet_configuration',
                      'fleet.fleet_models_configuration',
                      'fleet.fleet_vehicle_model_brand_menu', 'fleet.fleet_vehicle_model_menu']:
            self.assertFalse(self.env.ref(xmlid).active)
        field = self.env['fleet.vehicle']._fields['odometer']
        self.assertTrue(field.store)
        self.assertFalse(field.compute)

    def test_native_button_box_hidden_but_inheritance_anchors_remain(self):
        arch = self.env.ref('fleet.fleet_vehicle_view_form')._get_combined_arch()
        native = arch.xpath("//div[@name='button_box']")[0]
        self.assertEqual(native.get('invisible'), '1')
        self.assertTrue(native.xpath(".//button[@name='open_assignation_logs']"))
        self.assertTrue(arch.xpath("//div[@name='rental_button_box']/button[@name='action_open_rental_services']"))
