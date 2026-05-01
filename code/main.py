import argparse
import pandas as pd

from retriever import CorpusRetriever
from classifier import normalize_company, domain_key, classify_request_type, classify_product_area
from safety import decide_status
from response_generator import grounded_response


def main():
    parser = argparse.ArgumentParser(description="Multi-domain support triage agent")
    parser.add_argument("--corpus", default="data", help="Support corpus folder")
    parser.add_argument("--input", default="support_tickets.csv", help="Input tickets CSV")
    parser.add_argument("--output", default="output.csv", help="Output CSV")
    parser.add_argument("--log", default="log.txt", help="Transcript log")
    args = parser.parse_args()

    retriever = CorpusRetriever(args.corpus)
    retriever.load()

    # Read CSV with robust handling for quoted fields with newlines
    df = None
    try:
        df = pd.read_csv(args.input, low_memory=False)
    except:
        try:
            df = pd.read_csv(args.input, engine='python', on_bad_lines='skip', low_memory=False)
        except:
            df = pd.read_csv(args.input, on_bad_lines='skip')
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    rows = []

    with open(args.log, "w", encoding="utf-8") as log:
        for _, r in df.iterrows():
            issue = str(r.get("Issue", "") if pd.notna(r.get("Issue", "")) else "")
            subject = str(r.get("Subject", "") if pd.notna(r.get("Subject", "")) else "")
            company = normalize_company(r.get("Company", ""), issue + " " + subject)
            dom = domain_key(company)

            query = (subject + " " + issue).strip()
            request_type = classify_request_type(query)
            product_area = classify_product_area(query, dom)

            docs = retriever.search(query, domain=dom if dom != "unknown" else None, top_k=5)
            top_score = docs[0]["score"] if docs else 0.0

            status, justification = decide_status(query, request_type, top_score)
            response = grounded_response(query, status, justification, docs)
            relevant = " | ".join([f'{d["title"]} ({d["score"]:.3f})' for d in docs[:3]])

            rows.append({
                "issue": issue,
                "subject": subject,
                "company": company,
                "response": response,
                "product_area": product_area,
                "status": status,
                "request_type": request_type,
                "justification": justification,
            })

            log.write("ISSUE:\n" + issue + "\n")
            log.write("SUBJECT: " + subject + "\n")
            log.write("COMPANY: " + company + "\n")
            log.write("PRODUCT_AREA: " + product_area + "\n")
            log.write("REQUEST_TYPE: " + request_type + "\n")
            log.write("STATUS: " + status + "\n")
            log.write("JUSTIFICATION: " + justification + "\n")
            log.write("RETRIEVED_DOCS: " + relevant + "\n")
            log.write("RESPONSE:\n" + response + "\n")
            log.write("=" * 80 + "\n")

    pd.DataFrame(rows, columns=[
        "issue", "subject", "company", "response", "product_area", "status", "request_type", "justification"
    ]).to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
