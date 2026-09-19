"""Q3 -- generate 8 deterministic shards of user-signup records.

Same seeded-generation pattern as the spam dataset. Each shard gets a KNOWN,
seeded number of deliberately invalid rows, so the counts reported by the Job
pods can be checked against ground truth.

    python3 validator/generate_shards.py          -> validator/shards/shard_0..7.csv
"""
import csv
import os
import random

random.seed(2026)

N_SHARDS = 8
ROWS_PER_SHARD = 400
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shards")

FIRST = ["asha", "ravi", "meera", "karthik", "divya", "arjun", "neha", "vikram"]
LAST = ["iyer", "nair", "rao", "menon", "sharma", "gupta", "reddy", "bose"]
DOMAINS = ["example.com", "mail.co", "iitm.ac.in", "corp.io"]
COUNTRIES = ["IN", "US", "DE", "SG", "AU"]

CORRUPTIONS = [
    lambda e: e.replace("@", ""),
    lambda e: e.split("@")[0] + "@",
    lambda e: "@" + e.split("@")[1],
    lambda e: e.replace(".", ""),
]

os.makedirs(OUT_DIR, exist_ok=True)
ground_truth = {}

for shard in range(N_SHARDS):
    n_bad = 12 + (shard * 4)
    bad_idx = set(random.sample(range(ROWS_PER_SHARD), n_bad))
    rows = []
    for i in range(ROWS_PER_SHARD):
        name = f"{random.choice(FIRST)}.{random.choice(LAST)}"
        email = f"{name}{i}@{random.choice(DOMAINS)}"
        country = random.choice(COUNTRIES)
        date = f"2026-0{random.randint(1, 9)}-{random.randint(10, 28)}"
        if i in bad_idx:
            mode = random.randint(0, 4)
            if mode == 4:
                country = ""
            else:
                email = CORRUPTIONS[mode](email)
        rows.append((f"u{shard}_{i:04d}", email, date, country))

    path = os.path.join(OUT_DIR, f"shard_{shard}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "email", "signup_date", "country"])
        w.writerows(rows)
    ground_truth[shard] = n_bad
    print(f"wrote {path}  rows={ROWS_PER_SHARD}  invalid={n_bad}")

print("\nGROUND TRUTH (compare against the pod logs):")
print(ground_truth, " total =", sum(ground_truth.values()))
