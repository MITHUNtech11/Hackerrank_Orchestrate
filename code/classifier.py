DOMAIN_KEYWORDS = {
    "hackerrank": ["hackerrank", "assessment", "test", "candidate", "interview", "proctor", "plagiarism", "score", "certificate", "submissions", "challenge"],
    "claude": ["claude", "anthropic", "team workspace", "bedrock", "lti", "api", "console", "subscription", "model", "crawler", "crawling"],
    "visa": ["visa", "card", "merchant", "transaction", "charge", "issuer", "fraud", "stolen", "blocked", "cash", "dispute"],
}

REQUEST_TYPES = {
    "bug": ["down", "not working", "stopped", "failing", "failed", "error", "bug", "blocker", "unable", "connectivity", "not responding"],
    "billing": ["refund", "money", "payment", "billing", "invoice", "subscription", "charge", "pause"],
    "account_access": ["access", "login", "seat", "workspace", "removed", "account", "admin", "owner"],
    "security": ["security", "vulnerability", "bug bounty", "identity", "stolen", "fraud", "otp", "password"],
    "dispute": ["dispute", "merchant", "wrong product", "chargeback", "refund me", "ban the seller"],
    "product_issue": ["how", "where", "can you", "i need", "i want", "what", "why", "please"],
    "invalid": ["delete all files from the system", "internal rules", "logic exact", "documents retrieved"],
}

PRODUCT_AREAS = {
    "hackerrank": {
        "assessment": ["assessment", "test", "candidate", "score", "reschedule", "certificate", "compatible check"],
        "interview": ["interview", "mock interview", "inactivity", "lobby", "screen share"],
        "billing": ["refund", "payment", "money", "subscription", "pause"],
        "users_roles": ["remove", "employee", "interviewer", "admin", "user"],
        "community": ["practice", "submissions", "challenge", "apply tab", "resume builder"],
        "security_compliance": ["infosec", "security forms", "hiring"],
    },
    "claude": {
        "account_access": ["workspace", "seat", "access", "admin", "owner"],
        "service_status": ["stopped", "not responding", "all requests", "failing", "down"],
        "privacy": ["data", "crawling", "website", "use my data", "models"],
        "security": ["security vulnerability", "bug bounty"],
        "api_integrations": ["bedrock", "api", "aws", "lti", "key"],
    },
    "visa": {
        "fraud_security": ["identity", "stolen", "fraud", "blocked"],
        "disputes": ["dispute", "merchant", "wrong product", "charge"],
        "emergency_cash": ["cash", "urgent"],
        "card_acceptance": ["minimum", "spend", "merchant"],
        "general_support": ["visa", "card"],
    },
}


def normalize_company(company: str, issue: str = "") -> str:
    c = str(company or "").strip()
    if c and c.lower() != "nan":
        return c
    text = issue.lower()
    scores = {d: sum(kw in text for kw in kws) for d, kws in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return {"hackerrank": "HackerRank", "claude": "Claude", "visa": "Visa"}.get(best, "None") if scores[best] else "None"


def domain_key(company: str) -> str:
    c = str(company).lower()
    if "hackerrank" in c:
        return "hackerrank"
    if "claude" in c or "anthropic" in c:
        return "claude"
    if "visa" in c:
        return "visa"
    return "unknown"


def classify_request_type(text: str) -> str:
    t = text.lower()
    scores = {label: sum(kw in t for kw in kws) for label, kws in REQUEST_TYPES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "product_issue"


def classify_product_area(text: str, domain: str) -> str:
    if domain not in PRODUCT_AREAS:
        return "conversation_management"
    t = text.lower()
    scores = {area: sum(kw in t for kw in kws) for area, kws in PRODUCT_AREAS[domain].items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general_support"
