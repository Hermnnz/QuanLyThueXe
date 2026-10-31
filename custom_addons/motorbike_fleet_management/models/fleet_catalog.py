# -*- coding: utf-8 -*-
import base64
import logging
import os

from odoo import fields, models
from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

_MODEL_IMAGE_MAPPING = {
    'model_vinfast_evo200': 'vinfast_evo200.jpg',
    'model_vinfast_evo200_lite': 'vinfast_evo200_lite.webp',
    'model_vinfast_feliz_s': 'vinfast_feliz_s.webp',
    'model_vinfast_klara_s': 'vinfast_klara_s.jpg',
    'model_vinfast_vento_s': 'vinfast_vento_s.jpg',
    'model_vinfast_theon_s': 'vinfast_theon_s.jpg',
    'model_vinfast_ludo': 'vinfast_ludo.jpg',
    'model_vinfast_impes': 'vinfast_impes.png',
    'model_vinfast_klara_a2': 'vinfast_klara_a2.jpg',
    'model_vinfast_feliz': 'vinfast_feliz.webp',
    'model_datbike_weaver': 'datbike_weaver.jpg',
    'model_datbike_weaver_200': 'datbike_weaver_200.jpg',
    'model_datbike_weaver_pp': 'datbike_weaver_pp.jpg',
    'model_datbike_quantum': 'datbike_quantum.jpg',
    'model_datbike_quantum_s1': 'datbike_quantum_s1.jpg',
    'model_datbike_quantum_s2': 'datbike_quantum_s2.jpg',
    'model_datbike_quantum_s3': 'datbike_quantum_s3.jpg',
    'model_datbike_era': 'datbike_era.webp',
}


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    image_128 = fields.Image(
        string='Ảnh dòng xe',
        max_width=512,
        max_height=512,
        help='Ảnh chụp thực tế của dòng xe máy điện.',
    )

    def _register_hook(self):
        super()._register_hook()
        # Đảm bảo môi trường khác khi kéo code về (kể cả database cũ đã tồn tại)
        # vẫn tự động nạp ảnh thực tế cho các dòng xe nếu chưa có ảnh.
        updated = False
        for xml_id, img_file in _MODEL_IMAGE_MAPPING.items():
            model = self.env.ref(f'motorbike_fleet_management.{xml_id}', raise_if_not_found=False)
            if model and not model.image_128:
                try:
                    p = file_path(f'motorbike_fleet_management/static/src/img/{img_file}')
                    if p and os.path.isfile(p):
                        with open(p, 'rb') as f:
                            data = base64.b64encode(f.read())
                        model.sudo().write({'image_128': data})
                        updated = True
                except Exception as e:
                    _logger.warning('Không thể nạp ảnh tự động cho %s: %s', xml_id, e)
        if updated:
            self.env.cr.commit()
