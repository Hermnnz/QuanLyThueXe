from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUpfrontPayments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Upfront customer"})
        brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Upfront brand"})
        model = cls.env["fleet.vehicle.model"].create({
            "name": "Upfront bike", "brand_id": brand.id, "vehicle_type": "bike",
        })
        cls.vehicle = cls.env["fleet.vehicle"].create({
            "model_id": model.id, "is_electric_motorbike": True,
            "operational_status": "available", "technical_ready": True,
        })
        cls.price = cls.env["rental.vehicle.type"].create({
            "name": "Upfront price", "model_id": model.id, "daily_rate": 300000,
        })

    def contract_values(self, **overrides):
        return {
            "customer_id": self.customer.id,
            "start_date": "2026-12-01 03:00:00",
            "end_date": "2026-12-03 03:00:00",
            "deposit_amount": 2000000,
            "line_ids": [(0, 0, {
                "vehicle_id": self.vehicle.id, "vehicle_type_id": self.price.id,
            })],
            **overrides,
        }

    def contract(self, **overrides):
        return self.env["rental.contract"].create(self.contract_values(**overrides))

    def receipt(self, contract, transaction_type="rental_payment", amount=600000, **overrides):
        return self.env["motorbike.rental.payment"].create({
            "contract_id": contract.id, "customer_id": contract.customer_id.id,
            "currency_id": contract.currency_id.id, "transaction_type": transaction_type,
            "amount": amount, "payment_method": "cash", "state": "confirmed",
            **overrides,
        })

    def assert_unpaid(self, contract, message):
        with self.assertRaisesRegex(UserError, message), self.cr.savepoint():
            contract.action_confirm()
        self.assertEqual(contract.state, "draft")

    def test_create_prepares_one_unpaid_deposit_receipt(self):
        contract = self.contract()
        deposit = contract.payment_ids
        self.assertEqual(len(deposit), 1)
        self.assertEqual(deposit.transaction_type, "deposit")
        self.assertEqual(deposit.amount, contract.deposit_amount)
        self.assertEqual(deposit.customer_id, contract.customer_id)
        self.assertEqual(deposit.currency_id, contract.currency_id)
        self.assertEqual(deposit.state, "draft")
        contract.notes = "Ghi chú mới"
        self.assertEqual(len(contract.payment_ids), 1)

    def test_batch_create_and_copy_have_independent_deposits(self):
        contracts = self.env["rental.contract"].create([
            self.contract_values(), self.contract_values(deposit_amount=1000000),
        ])
        for contract in contracts:
            self.assertEqual(len(contract.payment_ids), 1)
            self.assertEqual(contract.payment_ids.amount, contract.deposit_amount)
        contracts[0].payment_ids.action_confirm()
        copied = contracts[0].copy()
        self.assertEqual(len(copied.payment_ids), 1)
        self.assertEqual(copied.payment_ids.state, "draft")
        self.assertNotEqual(copied.payment_ids, contracts[0].payment_ids)

    def test_draft_receipts_do_not_allow_signing(self):
        contract = self.contract()
        self.receipt(contract, state="draft")
        self.assert_unpaid(contract, "tiền cọc")

    def test_deposit_alone_does_not_pay_rent(self):
        contract = self.contract()
        contract.payment_ids.action_confirm()
        self.assert_unpaid(contract, "tiền thuê")

    def test_rent_alone_does_not_pay_deposit(self):
        contract = self.contract()
        self.receipt(contract, amount=2600000)
        self.assert_unpaid(contract, "tiền cọc")

    def test_partial_receipts_allow_signing_only_when_both_are_fully_paid(self):
        contract = self.contract()
        contract.payment_ids.amount = 1500000
        contract.payment_ids.action_confirm()
        self.receipt(contract)
        self.assert_unpaid(contract, "tiền cọc")
        self.receipt(contract, transaction_type="deposit", amount=500000)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")

    def test_cancelled_receipts_do_not_allow_signing(self):
        contract = self.contract()
        contract.payment_ids.action_cancel()
        self.receipt(contract)
        self.assert_unpaid(contract, "tiền cọc")

    def test_partial_rent_and_other_transaction_types_do_not_cover_rent(self):
        contract = self.contract()
        contract.payment_ids.action_confirm()
        self.receipt(contract, amount=300000)
        self.receipt(contract, transaction_type="additional_payment", amount=300000)
        self.assert_unpaid(contract, "tiền thuê")
        self.receipt(contract, amount=300000)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")

    def test_other_contract_payments_cannot_be_used(self):
        contract, other = self.contract(), self.contract()
        other.payment_ids.action_confirm()
        self.receipt(other)
        self.assert_unpaid(contract, "tiền cọc")

    def test_wrong_customer_or_currency_cannot_be_used(self):
        contract = self.contract()
        contract.payment_ids.action_confirm()
        other_customer = self.env["res.partner"].create({"name": "Other upfront customer"})
        self.receipt(contract, customer_id=other_customer.id)
        other_currency = self.env["res.currency"].with_context(active_test=False).search([
            ("id", "!=", contract.currency_id.id),
        ], limit=1)
        other_currency.active = True
        self.receipt(contract, currency_id=other_currency.id)
        self.assert_unpaid(contract, "tiền thuê")

    def test_direct_state_write_cannot_bypass_payment_check(self):
        contract = self.contract()
        with self.assertRaisesRegex(UserError, "Chưa thể ký"), self.cr.savepoint():
            contract.write({"state": "confirmed"})
        self.assertEqual(contract.state, "draft")

    def test_updated_deposit_requirement_is_checked_at_signing(self):
        contract = self.contract()
        contract.payment_ids.action_confirm()
        self.receipt(contract)
        contract.deposit_amount = 2500000
        self.assert_unpaid(contract, "tiền cọc")

    def test_zero_deposit_needs_no_zero_amount_receipt(self):
        contract = self.contract(deposit_amount=0)
        self.assertFalse(contract.payment_ids)
        self.receipt(contract)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")

    def test_rental_user_can_create_and_sign_after_finance_receives_payment(self):
        group = self.env.ref("motorbike_rental_core.group_rental_user")
        user = self.env["res.users"].create({
            "name": "Upfront rental officer", "login": "upfront-rental-officer",
            "groups_id": [(6, 0, [group.id])],
        })
        contract = self.env["rental.contract"].with_user(user).create(self.contract_values())
        self.assert_unpaid(contract, "tiền cọc")
        with self.assertRaises(AccessError), self.cr.savepoint():
            contract.sudo().payment_ids.with_user(user).action_confirm()
        contract.sudo().payment_ids.action_confirm()
        self.receipt(contract)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")
