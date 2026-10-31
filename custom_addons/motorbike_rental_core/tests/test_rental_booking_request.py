import uuid

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRentalBookingRequestCustomerResolution(TransactionCase):

    def test_changed_identity_does_not_keep_stale_customer(self):
        suffix = uuid.uuid4().hex[:8]
        customer_a = self.env['res.partner'].create({
            'name': 'Customer A %s' % suffix,
            'phone': '0901%s' % suffix[:6],
            'is_rental_customer': True,
        })
        customer_b = self.env['res.partner'].create({
            'name': 'Customer B %s' % suffix,
            'phone': '0902%s' % suffix[:6],
            'is_rental_customer': True,
        })
        booking_request = self.env['rental.booking.request'].new({
            'customer_id': customer_a.id,
            'customer_name': customer_b.name,
            'phone': customer_b.phone,
            'email': '',
        })

        booking_request._onchange_customer_identity()

        self.assertFalse(booking_request.customer_id)
        self.assertEqual(booking_request._resolve_customer(), customer_b)

    def test_changed_identity_creates_customer_when_no_match_exists(self):
        suffix = uuid.uuid4().hex[:8]
        customer_a = self.env['res.partner'].create({
            'name': 'Customer A %s' % suffix,
            'phone': '0903%s' % suffix[:6],
            'is_rental_customer': True,
        })
        booking_request = self.env['rental.booking.request'].new({
            'customer_id': customer_a.id,
            'customer_name': 'New Customer %s' % suffix,
            'phone': '0904%s' % suffix[:6],
            'email': 'new-%s@example.com' % suffix,
        })

        customer = booking_request._resolve_customer()

        self.assertNotEqual(customer, customer_a)
        self.assertEqual(customer.name, booking_request.customer_name)
        self.assertEqual(customer.phone, booking_request.phone)
        self.assertEqual(customer.email, booking_request.email)
        self.assertTrue(customer.is_rental_customer)
