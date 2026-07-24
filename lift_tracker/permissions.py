import frappe
from frappe import _


def lift_cycle_permission_query(user):
    if not user:
        user = frappe.session.user
    
    # Site Manager and Project Manager see all
    if "Site Manager" in frappe.get_roles(user) or "Project Manager" in frappe.get_roles(user):
        return ""
    
    # Lift Operator sees only their own
    operator = frappe.db.get_value("Lift Operator", {"user": user}, "name")
    if operator:
        return f"`tabLift Cycle`.`operator` = '{operator}'"
    
    return "1=0"  # No access


def lift_cycle_has_permission(doc, user, ptype="read"):
    if "Site Manager" in frappe.get_roles(user) or "Project Manager" in frappe.get_roles(user):
        return True
    
    operator = frappe.db.get_value("Lift Operator", {"user": user}, "name")
    return operator and doc.operator == operator