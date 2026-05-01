HIGH_RISK_TERMS = [
    "restore my access", "not the workspace owner", "not the workspace admin",
    "increase my score", "move me to the next round", "graded me unfairly",
    "refund me today", "ban the seller", "order id", "payment", "refund asap",
    "site is down", "none of the submissions", "all requests are failing",
    "identity has been stolen", "security vulnerability", "bug bounty",
    "internal rules", "documents retrieved", "logic exact", "delete all files",
    "blocked during my trip", "carte", "fraud", "stolen", "dispute", "chargeback",
]

UNSUPPORTED_ACTION_TERMS = [
    "make visa refund", "ban the seller", "tell the company", "increase my score",
    "restore my access", "update it", "pause our subscription", "fill in the forms",
]


def decide_status(issue: str, request_type: str, top_score: float) -> tuple[str, str]:
    text = issue.lower()

    if any(term in text for term in HIGH_RISK_TERMS):
        return "Escalated", "Sensitive, high-risk, or action-request issue that should be handled by a human support agent."

    if any(term in text for term in UNSUPPORTED_ACTION_TERMS):
        return "Escalated", "The user requests an account, billing, scoring, legal, or third-party action that cannot be safely completed by the triage agent."

    if top_score < 0.12:
        return "Escalated", "The retrieved support documentation confidence is too low to provide a grounded answer."

    if request_type in {"security", "dispute"}:
        return "Escalated", "Security, fraud, or dispute-related issues require human support review."

    return "Replied", "The request appears answerable using the retrieved support documentation."
