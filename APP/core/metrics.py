from prometheus_client import Counter

LOGIN_OPERATIONS = Counter(
    "locals_login_operations_total",
    "Completed login operations by outcome",
    labelnames=["outcome"],
)

for outcome in ("success", "rejected", "error"):
    LOGIN_OPERATIONS.labels(outcome=outcome)