import frappe
from frappe import _


def lift_cycle_permission_query(user):
    if not user:
        user = frappe.session.user
    
    roles = frappe.get_roles(user)
    # Site Manager, Project Manager, System Manager, Administrator see all
    if any(r in roles for r in ["Site Manager", "Project Manager", "System Manager", "Administrator"]):
        return ""
    
    # Lift Operator sees only their own
    operator = frappe.db.get_value("Lift Operator", {"user": user}, "name")
    if operator:
        return f"`tabLift Cycle`.`operator` = '{operator}'"
    
    return "1=0"  # No access


def lift_cycle_has_permission(doc, user, ptype="read"):
    roles = frappe.get_roles(user)
    if any(r in roles for r in ["Site Manager", "Project Manager", "System Manager", "Administrator"]):
        return True
    
    if "Lift Operator" in roles:
        if ptype in ("create", "write"):
            return True
        operator = frappe.db.get_value("Lift Operator", {"user": user}, "name")
        return bool(operator and (not doc.operator or doc.operator == operator))
    
    return False