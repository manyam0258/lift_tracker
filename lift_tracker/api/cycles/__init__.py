import frappe
import json
from frappe import _


@frappe.whitelist()
def bulk_sync(cycles):
    """
    Bulk sync endpoint for mobile app offline sync.
    Accepts array of cycle objects, creates/updates in batch.
    """
    if isinstance(cycles, str):
        cycles = json.loads(cycles)
    
    results = {
        "created": [],
        "updated": [],
        "errors": [],
        "synced_ids": []
    }
    
    for cycle_data in cycles:
        try:
            mobile_sync_id = cycle_data.get("mobile_sync_id")
            
            if not cycle_data.get("operator") and frappe.session.user:
                op = frappe.db.get_value("Lift Operator", {"user": frappe.session.user}, "name")
                if op:
                    cycle_data["operator"] = op
            
            # Set doctype if not present
            if "doctype" not in cycle_data:
                cycle_data["doctype"] = "Lift Cycle"
            
            # Check if already synced
            existing = frappe.db.get_value("Lift Cycle", {"mobile_sync_id": mobile_sync_id}, "name")
            
            if existing:
                doc = frappe.get_doc("Lift Cycle", existing)
                allowed_fields = ["date", "time", "start_floor", "end_floor", "direction", 
                                "intermediate_stops", "stop_count", "load_type", 
                                "passenger_count", "material_weight_kg", 
                                "notes", "operator", "cycle_id"]
                for field in allowed_fields:
                    if field in cycle_data:
                        setattr(doc, field, cycle_data[field])
                doc.synced_from_mobile = 1
                doc.save()
                results["updated"].append(existing)
            else:
                cycle_data["synced_from_mobile"] = 1
                doc = frappe.get_doc(cycle_data)
                doc.insert()
                results["created"].append(doc.name)
            
            results["synced_ids"].append(mobile_sync_id)
            frappe.db.commit()
            
        except Exception as e:
            frappe.db.rollback()
            results["errors"].append({
                "mobile_sync_id": cycle_data.get("mobile_sync_id", "unknown"),
                "error": str(e)
            })
    
    return results