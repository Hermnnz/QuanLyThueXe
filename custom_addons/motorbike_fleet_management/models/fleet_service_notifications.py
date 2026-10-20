from markupsafe import Markup
from odoo import api, fields, models


ACTIVITY_XMLID = 'motorbike_fleet_management.activity_service_created'


class FleetServiceNotifications(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    def _new_service_recipients(self):
        self.ensure_one()
        users = self.env['res.users'].sudo()
        company = self.vehicle_id.company_id or self.company_id
        manager = self.vehicle_id.manager_id
        def eligible(user):
            return (user.active and not user.share and user.id != self.env.ref('base.user_root').id
                    and (not company or company in user.company_ids)
                    and self.with_user(user).has_access('read'))
        if manager and eligible(manager):
            return manager
        group = self.env.ref('fleet.fleet_group_manager')
        domain = [('active', '=', True), ('share', '=', False), ('groups_id', 'in', group.id)]
        if company:
            domain.append(('company_ids', 'in', company.id))
        return users.search(domain).filtered(eligible)

    def _notify_new_service(self):
        """One in-app activity per eligible responsible user, no email dispatch."""
        for service in self.filtered(lambda s: s.active and s.is_electric_motorbike
                                      and s.state in ('new',)):
            for user in service._new_service_recipients():
                existing = service.sudo().activity_ids.filtered(lambda a:
                    a.activity_type_id == self.env.ref(ACTIVITY_XMLID) and a.user_id == user)
                if existing:
                    continue
                note = Markup('<p>Phiếu #%s — xe %s.</p><p>Nội dung: %s</p>') % (
                    service.id, service.vehicle_id.vehicle_code or service.vehicle_id.display_name,
                    service.description or 'Chưa nhập nội dung')
                service.sudo().with_context(mail_activity_quick_update=True).activity_schedule(
                    ACTIVITY_XMLID, user_id=user.id, date_deadline=fields.Date.context_today(service.with_user(user)),
                    summary='Phiếu bảo dưỡng mới #%s — %s' % (service.id, service.vehicle_id.vehicle_code or ''),
                    note=note)

    @api.model_create_multi
    def create(self, vals_list):
        services = super().create(vals_list)
        if not self.env.context.get('install_mode'):
            services._notify_new_service()
        return services

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') in ('running', 'done', 'cancelled'):
            self.sudo().activity_feedback([ACTIVITY_XMLID], feedback='Phiếu đã bắt đầu xử lý hoặc đã kết thúc.')
        return result
