import frappe
from frappe.model.document import Document


class DailyKPISummary(Document):
    def validate(self):
        if not self.kpi_id:
            frappe.throw("KPI ID is required")
        if not self.date:
            frappe.throw("Date is required")
        if not self.operator:
            frappe.throw("Operator is required")