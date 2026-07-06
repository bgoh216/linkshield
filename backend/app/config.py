"""
This is the single place you edit to change what's "plugged in".

To add a new compliance check: write the class (see checks/ssrf_check.py for
the shape), add it to SECURITY_CHECK_REGISTRY, add its name to ACTIVE_CHECKS
(or an env var). Nothing in main.py or dependencies.py needs to change.
"""

import os

from .checks import SSRFCheck, ReputationCheck
from .tracking import DBClickTracker, ExternalAnalyticsTracker

SECURITY_CHECK_REGISTRY = {
    "ssrf": SSRFCheck,
    "reputation": ReputationCheck,
}

# Factories rather than bare classes, since trackers have different constructor
# needs (DBClickTracker needs a db session, ExternalAnalyticsTracker doesn't).
TRACKER_FACTORIES = {
    "db": lambda db: DBClickTracker(db),
    "external": lambda db: ExternalAnalyticsTracker(api_key=os.getenv("ANALYTICS_API_KEY")),
}

# Comma-separated env vars let you toggle checks/trackers per environment
# without a code change or redeploy of application logic.
ACTIVE_CHECKS = os.getenv("ACTIVE_SECURITY_CHECKS", "ssrf,reputation").split(",")
ACTIVE_TRACKERS = os.getenv("ACTIVE_TRACKERS", "db").split(",")

# CORS origins allowed to make requests to this API. This is a security measure to prevent
FRONTEND_CORS_ORIGINS = os.getenv("FRONTEND_CORS_ORIGINS", "http://localhost:3000").split(",")
