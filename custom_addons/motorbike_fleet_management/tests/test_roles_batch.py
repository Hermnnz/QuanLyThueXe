from odoo import Command, fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError
from odoo.tools.safe_eval import safe_eval
from lxml import etree


@tagged('post_install', '-at_install')
class TestFleetRoleBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        def user(login, group):
            return cls.env['res.users'].create({'name': login, 'login': login,
                'company_id': cls.env.company.id, 'company_ids': [Command.set(cls.env.company.ids)],
                'groups_id': [Command.set(cls.env.ref(group).ids)]})
        cls.staff = user('batch.staff.test','motorbike_fleet_management.group_fleet_staff')
        cls.manager = user('batch.manager.test','motorbike_fleet_management.group_fleet_manager')
        brand = cls.env['fleet.vehicle.model.brand'].create({'name':'Batch test'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name':'EV','brand_id':brand.id,'vehicle_type':'bike'})

    def vehicle(self, **values):
        return self.env['fleet.vehicle'].create({'model_id':self.model.id,'is_electric_motorbike':True,
            'operational_status':'available','technical_ready':True,**values})

    def job(self, vehicle, **values):
        return self.env['fleet.vehicle.log.services'].create({'vehicle_id':vehicle.id,**values})

    def test_staff_can_create_but_not_edit_delete_or_fake_history(self):
        self.assertFalse(self.staff.has_group('fleet.fleet_group_manager'))
        vehicle = self.env['fleet.vehicle'].with_user(self.staff).create({
            'model_id':self.model.id,'is_electric_motorbike':True})
        service = self.env['fleet.vehicle.log.services'].with_user(self.staff).create({'vehicle_id':vehicle.id})
        for record, values in [(vehicle,{'license_plate':'DENIED'}),(vehicle,{'active':False}),
                               (service,{'description':'DENIED'}),(service,{'state':'done'})]:
            with self.assertRaises(AccessError),self.cr.savepoint():record.write(values)
        with self.assertRaises(AccessError),self.cr.savepoint():service.unlink()
        with self.assertRaises(AccessError),self.cr.savepoint():service.action_cancel()
        with self.assertRaises(AccessError),self.cr.savepoint():vehicle.action_confirm_technical_ready()
        with self.assertRaises(AccessError),self.cr.savepoint():
            self.env['fleet.vehicle.log.services'].with_user(self.staff).create({'vehicle_id':vehicle.id,'state':'running'})

    def test_staff_start_and_result_wizard_make_vehicle_ready(self):
        vehicle = self.vehicle(rental_blocked=True, block_reason='Giữ kiểm kê')
        service = self.job(vehicle).with_user(self.staff)
        service.action_start()
        self.assertEqual(vehicle.operational_status,'maintenance')
        action = service.action_done()
        self.assertEqual(action['res_model'],'motorbike.service.complete.wizard')
        self.assertEqual(service.state,'running')
        wizard = self.env['motorbike.service.complete.wizard'].with_user(self.staff).create({
            'service_id':service.id,'result':'Đã sửa và chạy thử đạt'})
        wizard.action_complete()
        self.assertEqual(service.state,'done')
        self.assertEqual(service.result,'Đã sửa và chạy thử đạt')
        self.assertEqual(vehicle.operational_status,'available')
        self.assertTrue(vehicle.technical_ready)
        self.assertTrue(vehicle.rental_blocked)
        with self.assertRaises(AccessError),self.cr.savepoint():service.write({'amount':1})

    def test_archive_lane_restore_and_rental_exclusion(self):
        vehicle = self.vehicle()
        vehicle.with_user(self.manager).active = False
        self.assertEqual(vehicle.operational_status,'inactive')
        self.assertFalse(vehicle.active)
        self.assertFalse(vehicle.technical_ready)
        self.assertFalse(vehicle.check_fleet_availability('2027-01-01','2027-01-02')[0]['fleet_ok'])
        self.assertFalse(self.env['fleet.vehicle'].search([('id','=',vehicle.id)]))
        action = self.env.ref('motorbike_fleet_management.action_electric_motorbikes')
        ctx = safe_eval(action.context)
        self.assertFalse(ctx['active_test'])
        self.assertIn(vehicle, self.env['fleet.vehicle'].with_context(**ctx).search([('id','=',vehicle.id)]))
        vehicle.with_user(self.manager).active = True
        self.assertEqual(vehicle.operational_status,'pending_inspection')
        self.assertFalse(vehicle.technical_ready)
        vehicle.with_user(self.manager).action_confirm_technical_ready()
        self.assertEqual(vehicle.operational_status,'available')
        with self.assertRaises(AccessError),self.cr.savepoint():
            vehicle.with_user(self.staff)._write_operational_state({'technical_ready':True})
        with self.assertRaises(UserError),self.cr.savepoint():vehicle.with_user(self.manager).unlink()

    def test_running_or_rented_vehicle_cannot_archive(self):
        vehicle = self.vehicle()
        service = self.job(vehicle)
        service.action_start()
        with self.assertRaises(UserError),self.cr.savepoint():vehicle.active=False
        service.action_cancel()
        self.assertEqual(vehicle.operational_status,'pending_inspection')
        vehicle.action_confirm_technical_ready()
        vehicle.write({'operational_status':'renting'})
        with self.assertRaises(UserError),self.cr.savepoint():vehicle.active=False

    def test_last_completed_job_releases_but_cancellation_does_not(self):
        vehicle = self.vehicle()
        first,second = self.job(vehicle,result='Xong'),self.job(vehicle,result='Xong')
        (first|second).action_start()
        first.action_done()
        self.assertEqual(vehicle.operational_status,'maintenance')
        second.action_done()
        self.assertEqual(vehicle.operational_status,'available')
        third=self.job(vehicle)
        third.action_start(); third.action_cancel()
        self.assertEqual(vehicle.operational_status,'pending_inspection')

    def test_staff_cannot_target_another_company_through_wizard(self):
        other=self.env['res.company'].create({'name':'Batch other'})
        vehicle=self.vehicle(company_id=other.id)
        job=self.job(vehicle)
        job.action_start()
        with self.assertRaises(AccessError),self.cr.savepoint():job.with_user(self.staff).action_start()
        with self.assertRaises(AccessError),self.cr.savepoint():
            self.env['fleet.vehicle.log.services'].with_user(self.staff).create({'vehicle_id':vehicle.id})
        wizard=self.env['motorbike.service.complete.wizard'].with_user(self.staff).create({
            'service_id':job.id,'result':'Không được phép'})
        with self.assertRaises(AccessError),self.cr.savepoint():wizard.action_complete()
        self.assertEqual(job.state,'running')

    def test_staff_forms_not_editable_and_corner_badges_exist(self):
        for model in ['fleet.vehicle','fleet.vehicle.log.services']:
            arch=self.env[model].with_user(self.staff).get_view(view_type='form')['arch']
            self.assertEqual(etree.fromstring(arch.encode()).get('edit'),'false')
        arch=self.env.ref('motorbike_fleet_management.vehicle_kanban_electric').arch_db
        self.assertIn('o_fleet_kanban_ribbon',arch)
        self.assertIn('o_fleet_secondary_badges',arch)

    def test_manager_header_buttons_are_not_duplicated(self):
        vehicle = self.env['fleet.vehicle'].with_user(self.manager).get_view(view_type='form')['arch']
        self.assertEqual(len(etree.fromstring(vehicle.encode()).xpath("//header/button[@name='action_confirm_technical_ready']")), 1)
        service = self.env['fleet.vehicle.log.services'].with_user(self.manager).get_view(view_type='form')['arch']
        self.assertEqual(len(etree.fromstring(service.encode()).xpath("//header/button[@name='action_cancel']")), 1)

    def test_default_context_cannot_bypass_staff_initial_state(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['fleet.vehicle'].with_user(self.staff).with_context(
                default_operational_status='available', default_technical_ready=True).create({
                    'model_id': self.model.id, 'is_electric_motorbike': True})
        vehicle = self.vehicle()
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['fleet.vehicle.log.services'].with_user(self.staff).with_context(default_active=False).create({'vehicle_id': vehicle.id})

    def test_restore_mixed_batch_cannot_change_rented_vehicle(self):
        inactive, rented = self.vehicle(), self.vehicle()
        inactive.active = False
        rented.write({'operational_status': 'renting'})
        with self.assertRaises(UserError), self.cr.savepoint():
            (inactive | rented).write({'active': True})
        self.assertEqual(rented.operational_status, 'renting')
        self.assertEqual(inactive.operational_status, 'inactive')
