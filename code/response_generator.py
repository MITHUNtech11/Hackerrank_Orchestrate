def grounded_response(issue: str, status: str, reason: str, docs: list[dict]) -> str:
    if status == "Escalated":
        return "Escalate to a human"

    if not docs:
        return "Escalate to a human"

    snippet = best_snippet(issue, docs[0]["text"])
    return (
        "Hi,\n\n"
        "Based on the support documentation, here is the relevant guidance:\n\n"
        f"{snippet}\n\n"
        "If this does not resolve the issue, please contact the appropriate support team through the documented support channel."
    )


def best_snippet(query: str, text: str, limit: int = 900) -> str:
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if len(s.strip()) > 20]
    qterms = {w.strip(".,:;!?()[]{}\"'").lower() for w in query.split() if len(w) > 2}
    scored = []
    for s in sentences:
        sterms = {w.strip(".,:;!?()[]{}\"'").lower() for w in s.split()}
        score = len(qterms & sterms)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [s for score, s in scored[:5] if score > 0]
    if not selected:
        selected = sentences[:4]
    out = ". ".join(selected)
    return out[:limit].strip()
