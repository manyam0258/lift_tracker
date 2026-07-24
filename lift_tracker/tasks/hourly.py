import frappe


def cleanup_old_sync_logs():
    """Clean up old synced cycles (older than 90 days)"""
    from frappe.utils import add_days, getdate
    
    cutoff = add_days(getdate(), -90)
    deleted = frappe.db.delete("Lift Cycle", {
        "synced_from_mobile": 1,
        "synced_at": ["<", cutoff]
    })
    
    if deleted:
        frappe.logger().info(f"Cleaned up {deleted} old synced lift cycles")