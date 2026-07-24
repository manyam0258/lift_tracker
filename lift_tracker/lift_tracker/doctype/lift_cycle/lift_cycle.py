import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, time_diff_in_seconds
import json


class LiftCycle(Document):
    def before_insert(self):
        self.set_cycle_id()

    def validate(self):
        self.validate_floors()
        self.set_cycle_id()
        self.calculate_duration()

    def validate_floors(self):
        if self.start_floor < 0 or self.start_floor > 17:
            frappe.throw(_("Start floor must be between 0-17"))
        if self.end_floor < 0 or self.end_floor > 17:
            frappe.throw(_("End floor must be between 0-17"))
        if self.start_floor == self.end_floor:
            frappe.throw(_("Start and end floor cannot be the same"))

    def set_cycle_id(self):
        if not self.cycle_id:
            self.cycle_id = f"LC-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}-{frappe.generate_hash(length=4)}"

    def calculate_duration(self):
        if self.duration_seconds is None and self.time:
            # Estimate based on floors (avg 5 sec/floor + 10 sec door ops)
            floor_diff = abs(self.end_floor - self.start_floor)
            self.duration_seconds = (floor_diff * 5) + 10


@frappe.whitelist()
def bulk_sync(cycles_json):
    """
    Bulk sync endpoint for mobile app offline sync.
    Accepts array of cycle objects, creates/updates in batch.
    """
    if isinstance(cycles_json, str):
        cycles = json.loads(cycles_json)
    else:
        cycles = cycles_json

    results = {"created": [], "updated": [], "errors": [], "synced_ids": []}

    for cycle_data in cycles:
        try:
            mobile_sync_id = cycle_data.get("mobile_sync_id")

            # Check if already synced
            existing = frappe.db.get_value("Lift Cycle", {"mobile_sync_id": mobile_sync_id}, "name")

            if existing:
                doc = frappe.get_doc("Lift Cycle", existing)
                doc.update(cycle_data)
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
            results["errors"].append({"mobile_sync_id": mobile_sync_id, "error": str(e)})

    return results


@frappe.whitelist()
def get_operator_dashboard(operator_id, from_date=None, to_date=None):
    """Dashboard API for mobile app"""
    if not from_date:
        from_date = getdate().replace(day=1)  # First of month
    if not to_date:
        to_date = getdate()

    # Get cycles
    cycles = frappe.get_all("Lift Cycle",
        filters={"operator": operator_id, "date": ["between", [from_date, to_date]]},
        fields=["*"],
        order_by="date desc, time desc"
    )

    # Calculate KPIs
    total = len(cycles)
    up = sum(1 for c in cycles if c.direction == "UP")
    down = sum(1 for c in cycles if c.direction == "DOWN")
    passengers = sum(c.passenger_count or 0 for c in cycles)
    material = sum(c.material_weight_kg or 0 for c in cycles)
    floors = set()
    for c in cycles:
        floors.add(c.start_floor)
        floors.add(c.end_floor)

    # Peak hour analysis
    hour_counts = {}
    for c in cycles:
        if c.time:
            hour = str(c.time)[:2]
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
    peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

    avg_duration = sum(c.duration_seconds or 0 for c in cycles) / total if total else 0

    return {
        "cycles": cycles,
        "kpis": {
            "total_cycles": total,
            "up_cycles": up,
            "down_cycles": down,
            "unique_floors_served": len(floors),
            "total_passengers": passengers,
            "total_material_kg": material,
            "avg_cycle_duration_sec": round(avg_duration, 1),
            "peak_hour": peak_hour,
            "utilization_pct": round((total * avg_duration) / (12 * 3600) * 100, 1) if total else 0
        }
    }


@frappe.whitelist()
def get_site_kpis(from_date, to_date):
    """Site-level KPIs for management dashboard"""
    cycles = frappe.get_all("Lift Cycle",
        filters={"date": ["between", [from_date, to_date]]},
        fields=["operator", "direction", "passenger_count", "material_weight_kg", "duration_seconds", "date", "time"]
    )

    # Aggregate by operator
    operator_stats = {}
    for c in cycles:
        op = c.operator
        if op not in operator_stats:
            operator_stats[op] = {"cycles": 0, "up": 0, "down": 0, "passengers": 0, "material": 0, "duration": 0}
        s = operator_stats[op]
        s["cycles"] += 1
        if c.direction == "UP": s["up"] += 1
        else: s["down"] += 1
        s["passengers"] += c.passenger_count or 0
        s["material"] += c.material_weight_kg or 0
        s["duration"] += c.duration_seconds or 0

    # Daily trends
    daily = {}
    for c in cycles:
        d = str(c.date)
        if d not in daily:
            daily[d] = {"total": 0, "up": 0, "down": 0, "passengers": 0}
        daily[d]["total"] += 1
        if c.direction == "UP": daily[d]["up"] += 1
        else: daily[d]["down"] += 1
        daily[d]["passengers"] += c.passenger_count or 0

    return {
        "operator_stats": operator_stats,
        "daily_trends": daily,
        "summary": {
            "total_cycles": len(cycles),
            "total_operators": len(operator_stats),
            "date_range": f"{from_date} to {to_date}"
        }
    }

