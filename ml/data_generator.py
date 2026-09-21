from pathlib import Path
import random
import re
import pandas as pd
import numpy as np

CATEGORIES = ["Billing", "Technical", "Account", "Subscription", "Payment", "Other"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Open", "In Progress", "Resolved", "Escalated"]

ISSUES = {
    "Billing": [
        "an invoice line item I do not understand", "a duplicate monthly charge",
        "a tax amount that looks incorrect", "a billing address update",
        "an invoice that is missing from my account", "a charge after a plan change"
    ],
    "Technical": [
        "the mobile app closing during document upload", "a dashboard timeout",
        "a page returning an error after I click submit", "a sync that stopped overnight",
        "a feature that became unavailable after an update", "a file upload that never completes"
    ],
    "Account": [
        "being unable to sign in after a password change", "an account locked message",
        "updating the email address on my profile", "a verification step that keeps failing",
        "a profile detail that will not save", "restoring access to an existing account"
    ],
    "Subscription": [
        "changing from my current plan to another plan", "a renewal date that looks wrong",
        "understanding what is included in my plan", "cancelling before the next renewal",
        "a plan change that did not take effect", "a subscription showing the wrong tier"
    ],
    "Payment": [
        "a card payment being declined", "a payment remaining pending",
        "a checkout failure", "a payment I do not recognize",
        "a bank transfer not appearing in the account", "a payment showing twice"
    ],
    "Other": [
        "a general product question", "help understanding a feature",
        "a request that does not fit another support category",
        "clarification about the next step", "help finding information in the service",
        "a question about how the support process works"
    ],
}

OPENERS = [
    "Hi support, I need help with", "Could you please check", "I noticed",
    "I am trying to resolve", "Please investigate", "I wanted to report",
    "I have been unable to resolve", "Can you help me with"
]

CONTEXT = [
    "It started today.", "This has happened twice this week.",
    "I am using the web application.", "I am using the mobile application.",
    "I have already tried signing out and back in.", "I need this resolved before my next work session.",
    "There is no immediate deadline.", "The issue is affecting one transaction."
]

def _messy(text, rng):
    text = re.sub(r"\s+", " ", text).strip()
    if rng.random() < 0.08:
        text = text.replace("support", "Support")
    if rng.random() < 0.05:
        text += "  "
    if rng.random() < 0.04:
        text = text.replace("the ", "the  ")
    return text

def generate_dataset(n=3000, seed=42):
    rng = random.Random(seed)
    rows = []
    start = pd.Timestamp("2025-01-01")
    for i in range(1, n + 1):
        category = rng.choice(CATEGORIES)
        priority = rng.choices(PRIORITIES, weights=[25, 42, 24, 9], k=1)[0]
        issue = rng.choice(ISSUES[category])
        message = f"{rng.choice(OPENERS)} {issue}. {rng.choice(CONTEXT)}"
        if priority == "Critical":
            message = f"URGENT: {message}"
        if category == "Payment" and rng.random() < 0.15:
            message += " I am concerned the transaction may be unauthorized."
        message = _messy(message, rng)

        # Small, explicit label-noise component to prevent a falsely clean benchmark.
        if rng.random() < 0.025:
            noisy_category = rng.choice([c for c in CATEGORIES if c != category])
            category = noisy_category
        if rng.random() < 0.02:
            noisy_priority = rng.choice([p for p in PRIORITIES if p != priority])
            priority = noisy_priority

        created = start + pd.Timedelta(minutes=rng.randint(0, 525600))
        status = rng.choices(STATUSES, weights=[30, 25, 35, 10], k=1)[0]
        resolution = np.nan if status != "Resolved" else round(float(rng.lognormvariate(2.2, 0.8)), 2)
        rows.append({
            "ticket_id": i,
            "customer_id": f"CUST-{rng.randint(10000, 99999)}",
            "message": message,
            "category": category,
            "priority": priority,
            "status": status,
            "resolution_time": resolution,
            "created_at": created.isoformat(),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data" / "raw" / "support_tickets.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset()
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")
