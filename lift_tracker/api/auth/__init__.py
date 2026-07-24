import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def operator_login(employee_id, pin):
    """Operator login with employee ID and PIN"""
    # Find operator by employee_id
    operator = frappe.db.get_value(
        "Lift Operator",
        {"employee_id": employee_id, "is_active": 1},
        ["name", "operator_name", "user", "shift"],
        as_dict=True
    )
    
    if not operator:
        frappe.throw(_("Invalid Employee ID"))
    
    # For demo, accept PIN 1234 for all operators
    # In production, implement proper PIN verification
    if pin != "1234":
        frappe.throw(_("Invalid PIN"))
    
    # Get user details
    user = frappe.get_doc("User", operator.user)
    
    # Generate API key if not exists (bypass permissions for guest login)
    if not user.api_key:
        user.api_key = frappe.generate_hash(length=15)
    if not user.api_secret:
        user.api_secret = frappe.generate_hash(length=15)
    user.save(ignore_permissions=True)
    
    return {
        "success": True,
        "operator": {
            "employee_id": employee_id,
            "name": operator.operator_name,
            "shift": operator.shift,
        },
        "api_key": user.api_key,
        "api_secret": user.api_secret,
        "message": "Login successful"
    }


@frappe.whitelist()
def get_operator_info():
    """Get current operator info"""
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(_("Not authenticated"))
    
    # Get operator linked to current user
    operator = frappe.db.get_value(
        "Lift Operator",
        {"user": frappe.session.user, "is_active": 1},
        ["name", "employee_id", "operator_name", "shift", "phone"],
        as_dict=True
    )
    
    if not operator:
        frappe.throw(_("No operator found for this user"))
    
    return {
        "employee_id": operator.employee_id,
        "name": operator.operator_name,
        "shift": operator.shift,
        "phone": operator.phone
    }


@frappe.whitelist(allow_guest=True)
def test_auth():
    """Test authentication endpoint"""
    return {"message": "Auth API working", "user": frappe.session.user}