import frappe
from frappe.model.document import Document


class LiftOperator(Document):
    def validate(self):
        if not self.operator_name:
            frappe.throw("Operator Name is required")
        if not self.user:
            frappe.throw("User is required")