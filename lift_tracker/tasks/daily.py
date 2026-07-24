import frappe
from frappe import _


def create_daily_kpis():
    """Run daily at midnight to compute KPIs for previous day"""
    yesterday = frappe.utils.add_days(frappe.utils.getdate(), -1)
    calculate_kpis_for_date(yesterday)


calculate_daily_kpis = create_daily_kpis


def calculate_kpis_for_date(target_date):
    cycles = frappe.get_all("Lift Cycle",
        filters={"date": target_date},
        fields=["operator", "direction", "passenger_count", "material_weight_kg", 
                "duration_seconds", "start_floor", "end_floor", "time"]
    )
    
    # Group by operator
    from collections import defaultdict
    operator_data = defaultdict(lambda: {
        "cycles": [], "up": 0, "down": 0, "passengers": 0, 
        "material": 0, "duration": 0, "floors": set(), "hours": defaultdict(int)
    })
    
    for c in cycles:
        op = c.operator
        d = operator_data[op]
        d["cycles"].append(c)
        if c.direction == "UP": d["up"] += 1
        else: d["down"] += 1
        d["passengers"] += c.passenger_count or 0
        d["material"] += c.material_weight_kg or 0
        d["duration"] += c.duration_seconds or 0
        d["floors"].add(c.start_floor)
        d["floors"].add(c.end_floor)
        if c.time:
            hour = str(c.time)[:2]
            d["hours"][hour] += 1
    
    # Create/update KPI records
    for operator, data in operator_data.items():
        total = len(data["cycles"])
        if total == 0:
            continue
        
        peak_hour = max(data["hours"], key=data["hours"].get) if data["hours"] else None
        avg_duration = data["duration"] / total
        utilization = (data["duration"] / (12 * 3600)) * 100  # 12hr shift
        
        kpi_id = f"KPI-{target_date}-{operator}"
        
        existing = frappe.db.exists("Daily KPI Summary", {"kpi_id": kpi_id})
        if existing:
            doc = frappe.get_doc("Daily KPI Summary", existing)
        else:
            doc = frappe.new_doc("Daily KPI Summary")
            doc.kpi_id = kpi_id
            doc.date = target_date
            doc.operator = operator
        
        doc.total_cycles = total
        doc.up_cycles = data["up"]
        doc.down_cycles = data["down"]
        doc.unique_floors_served = len(data["floors"])
        doc.total_passengers = data["passengers"]
        doc.total_material_kg = data["material"]
        doc.avg_cycle_duration_sec = round(avg_duration, 1)
        doc.peak_hour = peak_hour
        doc.utilization_pct = round(utilization, 1)
        
        if existing:
            doc.save()
        else:
            doc.insert()
    
    frappe.db.commit()
    frappe.logger().info(f"Calculated KPIs for {target_date}: {len(operator_data)} operators")