app_name = "lift_tracker"
app_title = "Lift Tracker"
app_publisher = "Tridasa Realty"
app_description = "Lift operator cycle tracking with offline mobile sync"
app_email = "surendhranath@trusync.in"
app_license = "mit"

# Fixtures
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Lift Operator", "Site Manager"]]]},
    {"dt": "DocType", "filters": [["module", "=", "Lift Tracker"]]}
]

# Scheduled Jobs
scheduler_events = {
    "daily": [
        "lift_tracker.tasks.daily.calculate_daily_kpis"
    ],
    "hourly": [
        "lift_tracker.tasks.hourly.cleanup_old_sync_logs"
    ]
}

# Permissions
permission_query_conditions = {
    "Lift Cycle": "lift_tracker.permissions.lift_cycle_permission_query"
}

has_permission = {
    "Lift Cycle": "lift_tracker.permissions.lift_cycle_has_permission"
}

# Document Events
# doc_events = {
#     "Lift Cycle": {
#         "validate": "lift_tracker.lift_tracker.doctype.lift_cycle.lift_cycle.validate"
#     }
# }

# Override Whitelisted Methods
# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "lift_tracker.event.get_events"
# }

# Website
# website_generators = []

# Jinja
# jinja = {
#     "methods": "lift_tracker.utils.jinja_methods",
#     "filters": "lift_tracker.utils.jinja_filters"
# }

# Installation
# before_install = "lift_tracker.install.before_install"
# after_install = "lift_tracker.install.after_install"

# Testing
# before_tests = "lift_tracker.install.before_tests"

# Extend DocType Class
# extend_doctype_class = {
#     "Task": "lift_tracker.custom.task.CustomTaskMixin"
# }