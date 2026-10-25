from prometheus_client import Counter

LOGIN_OPERATIONS = Counter(
    "locals_login_operations_total",
    "Completed login operations by outcome",
    labelnames=["outcome"],
)

PLAYBACK_LINK_REQUESTS = Counter(
    "locals_playback_link_requests_total",
    "Completed playback link requests by outcome",
    labelnames=["outcome"],
)

AUDIO_UPLOADS = Counter(
    "locals_audio_uploads_total",
    "Complete audio upload operations by outcome",
    labelnames=["outcome"],
)

REVIEWS_SUBMITTED=Counter(
    "locals_review_submitted_total",
    "Complete review upload operations by outcome",
    labelnames=["outcome"],
)

for outcome in ("success", "rejected", "error"):
    LOGIN_OPERATIONS.labels(outcome=outcome)
    AUDIO_UPLOADS.labels(outcome=outcome)
    PLAYBACK_LINK_REQUESTS.labels(outcome=outcome)
    REVIEWS_SUBMITTED.labels(outcome=outcome)