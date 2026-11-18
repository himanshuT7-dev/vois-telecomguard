#!/usr/bin/env python3
"""
TelecomGuard – Proactive Telco Risk & Retention Pipeline
Data Generation Script (Agent 1 - Data Engineering)

Generates synthetic enterprise telecom data for VOIS:
- data/dim_customers.csv (~2,000 customers across UK, DE, IN)
- data/dim_exchange_rates.csv (EUR FX rates: GBP=1.17, EUR=1.0, INR=0.011)
- data/raw_usage_logs.csv (50,000 daily telemetry logs over 30 days)

Risk & Anomaly Injections:
- ~3% Bill Shock / Balance Burn customers (roaming in last 7 days with spend > 1.35x normal monthly spend)
- ~3% Silent Network Frustration customers (latency > 180ms for 3+ consecutive days with 0 open support tickets)
- ~5% Dirty rows (NULL tower_id, negative latency_ms, duplicate record_ids)
"""

import os
import random
from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker

# Fixed random seeds for strict reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)

fake = Faker()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. FX Exchange Rates Definition
# ---------------------------------------------------------
FX_RATES = {
    "GBP": 1.1700,
    "EUR": 1.0000,
    "INR": 0.0110,
}

COUNTRY_CURRENCY = {
    "UK": "GBP",
    "DE": "EUR",
    "IN": "INR",
}

# ---------------------------------------------------------
# 2. Customer Dimension Generation (~2,000 Customers)
# ---------------------------------------------------------
def generate_customers(total_customers=2000):
    """
    Generates ~2,000 customers across UK, DE, IN with contract split:
    - UK: 700 customers (80% Postpaid / 20% Prepaid)
    - DE: 700 customers (80% Postpaid / 20% Prepaid)
    - IN: 600 customers (20% Postpaid / 80% Prepaid)
    """
    customers = []
    
    country_splits = [
        {"country": "UK", "total": 700, "postpaid_pct": 0.80},
        {"country": "DE", "total": 700, "postpaid_pct": 0.80},
        {"country": "IN", "total": 600, "postpaid_pct": 0.20},
    ]
    
    cust_idx = 1
    base_date = date(2026, 10, 20)

    for market in country_splits:
        c_code = market["country"]
        c_total = market["total"]
        n_postpaid = int(c_total * market["postpaid_pct"])
        n_prepaid = c_total - n_postpaid
        
        contract_types = ["Postpaid"] * n_postpaid + ["Prepaid"] * n_prepaid
        random.shuffle(contract_types)
        
        for ctype in contract_types:
            cust_id = f"CUST-{c_code}-{cust_idx:05d}"
            name = fake.name()
            email = f"{name.lower().replace(' ', '.')}.{cust_idx}@vodafone-telecomguard.test"
            
            # Generate country-appropriate phone prefixes
            if c_code == "UK":
                phone = f"+44 7{random.randint(100000000, 999999999)}"
                device = random.choices(["iOS", "Android"], weights=[0.52, 0.48])[0]
                if ctype == "Postpaid":
                    spend_eur = round(random.gauss(48.0, 10.0), 2)
                    spend_eur = max(28.0, min(85.0, spend_eur))
                else:
                    spend_eur = round(random.gauss(22.0, 5.0), 2)
                    spend_eur = max(12.0, min(38.0, spend_eur))
            elif c_code == "DE":
                phone = f"+49 15{random.randint(10000000, 99999999)}"
                device = random.choices(["iOS", "Android"], weights=[0.42, 0.58])[0]
                if ctype == "Postpaid":
                    spend_eur = round(random.gauss(42.0, 9.0), 2)
                    spend_eur = max(25.0, min(75.0, spend_eur))
                else:
                    spend_eur = round(random.gauss(19.0, 4.5), 2)
                    spend_eur = max(10.0, min(32.0, spend_eur))
            else:  # IN
                phone = f"+91 9{random.randint(100000000, 999999999)}"
                device = random.choices(["iOS", "Android"], weights=[0.18, 0.82])[0]
                if ctype == "Postpaid":
                    spend_eur = round(random.gauss(15.0, 3.5), 2)
                    spend_eur = max(8.0, min(28.0, spend_eur))
                else:
                    spend_eur = round(random.gauss(7.0, 1.8), 2)
                    spend_eur = max(3.5, min(14.0, spend_eur))
            
            signup_days_ago = random.randint(180, 1200)
            signup_date = base_date - timedelta(days=signup_days_ago)
            
            customers.append({
                "customer_id": cust_id,
                "name": name,
                "email": email,
                "phone_number": phone,
                "country": c_code,
                "contract_type": ctype,
                "signup_date": signup_date.isoformat(),
                "normal_monthly_spend_eur": spend_eur,
                "device_type": device,
            })
            cust_idx += 1

    df_customers = pd.DataFrame(customers)
    return df_customers

# ---------------------------------------------------------
# 3. Exchange Rates Dimension Generation
# ---------------------------------------------------------
def generate_exchange_rates():
    """
    Generates EUR exchange rates table:
    - GBP: 1.1700
    - EUR: 1.0000
    - INR: 0.0110
    """
    rates = [
        {"currency_code": "GBP", "fx_rate_to_eur": 1.1700, "effective_date": "2026-10-20"},
        {"currency_code": "EUR", "fx_rate_to_eur": 1.0000, "effective_date": "2026-10-20"},
        {"currency_code": "INR", "fx_rate_to_eur": 0.0110, "effective_date": "2026-10-20"},
    ]
    return pd.DataFrame(rates)

# ---------------------------------------------------------
# 4. Cell Towers Pool
# ---------------------------------------------------------
TOWERS = {
    "UK": [f"TWR-UK-LON-{i:03d}" for i in range(1, 35)] +
          [f"TWR-UK-MAN-{i:03d}" for i in range(1, 20)] +
          [f"TWR-UK-BIR-{i:03d}" for i in range(1, 15)],
    "DE": [f"TWR-DE-BER-{i:03d}" for i in range(1, 35)] +
          [f"TWR-DE-MUC-{i:03d}" for i in range(1, 20)] +
          [f"TWR-DE-FRA-{i:03d}" for i in range(1, 15)],
    "IN": [f"TWR-IN-MUM-{i:03d}" for i in range(1, 35)] +
          [f"TWR-IN-DEL-{i:03d}" for i in range(1, 20)] +
          [f"TWR-IN-BLR-{i:03d}" for i in range(1, 15)],
}

ROAMING_DESTINATIONS = {
    "UK": ["ES", "FR", "IT", "US", "GR", "PT", "IE"],
    "DE": ["AT", "CH", "IT", "ES", "TR", "FR", "NL"],
    "IN": ["AE", "UK", "SG", "TH", "US", "SA", "MY"],
}

# ---------------------------------------------------------
# 5. Usage Telemetry Generation (50,000 Records, 30 Days)
# ---------------------------------------------------------
def generate_usage_logs(df_customers, total_records=50000, num_days=30):
    """
    Generates 50,000 daily usage logs over 30 days across customers.
    Injects:
    1. ~3% Bill Shock / Balance Burn cohort (roaming in last 7 days, spend > 1.35x normal)
    2. ~3% Silent Network Frustration cohort (latency > 180ms for 3+ consecutive days, tickets = 0)
    3. ~5% Dirty rows (NULL tower_id, negative latency_ms, duplicate record_ids)
    """
    start_date = date(2026, 10, 20)
    end_date = start_date + timedelta(days=num_days - 1)  # 2026-11-18
    all_dates = [start_date + timedelta(days=d) for d in range(num_days)]
    last_7_days = all_dates[-7:]  # Last 7 calendar days

    n_cust = len(df_customers)
    
    # Select risk cohorts
    # Cohort 1: Bill Shock / Balance Burn (~3% = 60 customers)
    n_bill_shock = int(round(n_cust * 0.03))  # 60
    # Cohort 2: Silent Network Frustration (~3% = 60 customers)
    n_silent_frustration = int(round(n_cust * 0.03))  # 60

    all_cust_ids = df_customers["customer_id"].tolist()
    shuffled_cust_ids = all_cust_ids.copy()
    random.shuffle(shuffled_cust_ids)

    bill_shock_custs = set(shuffled_cust_ids[:n_bill_shock])
    silent_frust_custs = set(shuffled_cust_ids[n_bill_shock:n_bill_shock + n_silent_frustration])

    # Pre-map customer metadata for fast generation
    cust_meta = {}
    for _, row in df_customers.iterrows():
        cust_meta[row["customer_id"]] = {
            "country": row["country"],
            "contract_type": row["contract_type"],
            "normal_monthly_spend_eur": row["normal_monthly_spend_eur"],
            "currency": COUNTRY_CURRENCY[row["country"]],
            "fx_rate": FX_RATES[COUNTRY_CURRENCY[row["country"]]],
        }

    # Assign dates to customers to reach exactly total_records
    # Mandatory inclusions:
    # - Bill shock customers MUST be active on all last 7 days
    # - Silent frustration customers MUST be active on consecutive days (e.g. days 24, 25, 26, 27)
    records_plan = []
    scheduled_pairs = set()

    for cid in bill_shock_custs:
        for d in last_7_days:
            records_plan.append((cid, d))
            scheduled_pairs.add((cid, d))

    consecutive_frust_days = all_dates[23:28]  # 5 consecutive days near end
    for cid in silent_frust_custs:
        for d in consecutive_frust_days:
            if (cid, d) not in scheduled_pairs:
                records_plan.append((cid, d))
                scheduled_pairs.add((cid, d))

    # Fill the rest of the 50,000 schedule randomly across all customers & dates
    remaining_slots = total_records - len(records_plan)
    
    # Candidate pool of (customer, date) pairs not yet scheduled
    all_possible_pairs = [
        (cid, d) for cid in all_cust_ids for d in all_dates if (cid, d) not in scheduled_pairs
    ]
    random.shuffle(all_possible_pairs)
    records_plan.extend(all_possible_pairs[:remaining_slots])

    # Shuffle the schedule so logs are distributed naturally
    random.shuffle(records_plan)

    # Generate telemetry rows
    logs = []
    rec_counter = 1

    for cid, log_date in records_plan:
        meta = cust_meta[cid]
        c_code = meta["country"]
        currency = meta["currency"]
        fx = meta["fx_rate"]
        normal_monthly = meta["normal_monthly_spend_eur"]
        is_bill_shock = cid in bill_shock_custs
        is_silent_frust = cid in silent_frust_custs

        rec_id = f"REC-{rec_counter:08d}"
        rec_counter += 1

        is_roaming = False
        roaming_country = ""
        
        # --- Network latency and tickets ---
        if is_silent_frust:
            open_tickets = 0  # Crucial condition: Silent customer has 0 tickets
            if log_date in consecutive_frust_days:
                # Degraded network on consecutive days: latency > 180 ms
                latency_ms = round(random.uniform(188.0, 340.0), 1)
                packet_loss_pct = round(random.uniform(3.5, 9.5), 2)
            else:
                latency_ms = round(random.uniform(22.0, 75.0), 1)
                packet_loss_pct = round(random.uniform(0.1, 1.8), 2)
        else:
            # Normal network: latency typically 18 - 85ms
            latency_ms = round(random.gauss(38.0, 14.0), 1)
            latency_ms = max(15.0, min(140.0, latency_ms))
            packet_loss_pct = round(random.uniform(0.05, 1.95), 2)
            # Normal customers occasionally open tickets
            open_tickets = random.choices([0, 1, 2], weights=[0.92, 0.07, 0.01])[0]

        # --- Roaming and Spend ---
        if is_bill_shock:
            if log_date in last_7_days:
                is_roaming = True
                roaming_country = random.choice(ROAMING_DESTINATIONS[c_code])
                # High daily roaming spend projecting > 1.35x normal monthly spend
                # Spending ~14% to 22% of normal monthly spend per roaming day
                daily_spend_eur = round(normal_monthly * random.uniform(0.14, 0.23), 2)
                data_used_mb = round(random.uniform(2500.0, 7500.0), 1)
                voice_min = round(random.uniform(25.0, 95.0), 1)
                sms_cnt = random.randint(4, 18)
            else:
                # Normal spend in prior days (~1/30th of normal spend)
                daily_spend_eur = round((normal_monthly / 30.0) * random.uniform(0.85, 1.15), 2)
                data_used_mb = round(random.uniform(400.0, 2200.0), 1)
                voice_min = round(random.uniform(2.0, 30.0), 1)
                sms_cnt = random.randint(0, 5)
        else:
            # Occasional light roaming for non-shock users (does not cause >1.35x spend)
            if random.random() < 0.035:
                is_roaming = True
                roaming_country = random.choice(ROAMING_DESTINATIONS[c_code])
                daily_spend_eur = round((normal_monthly / 30.0) * random.uniform(1.05, 1.45), 2)
                data_used_mb = round(random.uniform(600.0, 2600.0), 1)
                voice_min = round(random.uniform(5.0, 35.0), 1)
                sms_cnt = random.randint(1, 8)
            else:
                daily_spend_eur = round((normal_monthly / 30.0) * random.uniform(0.70, 1.25), 2)
                data_used_mb = round(random.uniform(200.0, 2400.0), 1)
                voice_min = round(random.uniform(0.0, 28.0), 1)
                sms_cnt = random.randint(0, 6)

        daily_spend_eur = max(0.10, daily_spend_eur)
        # Convert spend to local currency
        daily_spend_local = round(daily_spend_eur / fx, 2)
        # Recalculate exact daily_spend_eur from local to maintain perfect consistency
        daily_spend_eur = round(daily_spend_local * fx, 2)

        tower_id = random.choice(TOWERS[c_code])

        logs.append({
            "record_id": rec_id,
            "customer_id": cid,
            "date": log_date.isoformat(),
            "country": c_code,
            "is_roaming": is_roaming,
            "roaming_country": roaming_country if is_roaming else "",
            "data_used_mb": data_used_mb,
            "voice_minutes": voice_min,
            "sms_count": sms_cnt,
            "daily_spend_local": daily_spend_local,
            "currency": currency,
            "daily_spend_eur": daily_spend_eur,
            "latency_ms": latency_ms,
            "packet_loss_pct": packet_loss_pct,
            "tower_id": tower_id,
            "open_support_tickets": open_tickets,
        })

    df_logs = pd.DataFrame(logs)

    # ---------------------------------------------------------
    # 6. Inject ~5% Dirty Rows (2,500 rows total)
    # ---------------------------------------------------------
    # Total dirty records: 2,500 rows (5.0%)
    # - 833 rows: NULL tower_id
    # - 833 rows: Negative latency_ms
    # - 834 rows: Duplicate record_id
    n_dirty_tower = 833
    n_dirty_latency = 833
    n_dirty_duplicates = 834
    total_dirty = n_dirty_tower + n_dirty_latency + n_dirty_duplicates  # 2500

    # Pick disjoint indices for dirty injections (avoiding corrupting critical risk rows)
    # Find candidate rows from normal customers
    candidate_indices = [
        i for i, row in df_logs.iterrows()
        if row["customer_id"] not in bill_shock_custs and row["customer_id"] not in silent_frust_custs
    ]
    random.shuffle(candidate_indices)

    tower_dirty_idx = candidate_indices[:n_dirty_tower]
    latency_dirty_idx = candidate_indices[n_dirty_tower:n_dirty_tower + n_dirty_latency]
    dup_dirty_idx = candidate_indices[n_dirty_tower + n_dirty_latency:total_dirty]

    # Inject NULL tower_id (empty string in CSV)
    for idx in tower_dirty_idx:
        df_logs.at[idx, "tower_id"] = ""

    # Inject negative latency_ms
    for idx in latency_dirty_idx:
        neg_val = round(random.uniform(-150.0, -5.0), 1)
        df_logs.at[idx, "latency_ms"] = neg_val

    # Inject duplicate record_id (take existing valid record_ids from elsewhere in df_logs)
    source_dup_ids = df_logs.loc[candidate_indices[total_dirty:total_dirty + n_dirty_duplicates], "record_id"].tolist()
    for i, idx in enumerate(dup_dirty_idx):
        df_logs.at[idx, "record_id"] = source_dup_ids[i]

    return df_logs, bill_shock_custs, silent_frust_custs, {
        "null_tower_count": n_dirty_tower,
        "negative_latency_count": n_dirty_latency,
        "duplicate_record_count": n_dirty_duplicates,
        "total_dirty_rows": total_dirty,
    }

# ---------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------
def main():
    print("=" * 70)
    print("TelecomGuard: Synthetic Data Generation Pipeline (VOIS)")
    print("=" * 70)

    # 1. Customers
    print("\n[1/3] Generating dim_customers.csv (~2,000 customers)...")
    df_customers = generate_customers(total_customers=2000)
    cust_path = os.path.join(OUTPUT_DIR, "dim_customers.csv")
    df_customers.to_csv(cust_path, index=False)
    print(f" -> Saved: {cust_path} ({len(df_customers):,} rows)")

    # 2. Exchange Rates
    print("\n[2/3] Generating dim_exchange_rates.csv...")
    df_rates = generate_exchange_rates()
    rates_path = os.path.join(OUTPUT_DIR, "dim_exchange_rates.csv")
    df_rates.to_csv(rates_path, index=False)
    print(f" -> Saved: {rates_path} ({len(df_rates):,} rows)")

    # 3. Usage Logs
    print("\n[3/3] Generating raw_usage_logs.csv (50,000 telemetry logs)...")
    df_logs, bill_shock_custs, silent_frust_custs, dirty_meta = generate_usage_logs(
        df_customers, total_records=50000, num_days=30
    )
    logs_path = os.path.join(OUTPUT_DIR, "raw_usage_logs.csv")
    df_logs.to_csv(logs_path, index=False)
    print(f" -> Saved: {logs_path} ({len(df_logs):,} rows)")

    # ---------------------------------------------------------
    # Verification & Summary Audit
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("EXECUTION SUMMARY & DATA INTEGRITY AUDIT")
    print("=" * 70)

    # Customers summary
    print("\n1. CUSTOMER BASE BREAKDOWN:")
    for country in ["UK", "DE", "IN"]:
        sub = df_customers[df_customers["country"] == country]
        postpaid_cnt = (sub["contract_type"] == "Postpaid").sum()
        prepaid_cnt = (sub["contract_type"] == "Prepaid").sum()
        print(f"   - {country}: {len(sub):,} customers | Postpaid: {postpaid_cnt} ({postpaid_cnt/len(sub)*100:.1f}%) | Prepaid: {prepaid_cnt} ({prepaid_cnt/len(sub)*100:.1f}%)")
    print(f"   Total Customers: {len(df_customers):,}")

    # Exchange rates summary
    print("\n2. EUR EXCHANGE RATES (dim_exchange_rates):")
    for _, r in df_rates.iterrows():
        print(f"   - {r['currency_code']}: {r['fx_rate_to_eur']:.4f} EUR (effective: {r['effective_date']})")

    # Injected risks summary
    print("\n3. INJECTED TELCO RETENTION RISKS:")
    print(f"   - Bill Shock / Balance Burn Users: {len(bill_shock_custs):,} users ({len(bill_shock_custs)/len(df_customers)*100:.1f}%)")
    print(f"     * Criteria: Roaming abroad in last 7 days + 30-day spend > 1.35x normal monthly spend.")
    
    # Check spend projection for bill shock users
    total_spends = df_logs.groupby("customer_id")["daily_spend_eur"].sum()
    shock_ratios = []
    for cid in bill_shock_custs:
        actual_spend = total_spends.get(cid, 0.0)
        norm_spend = df_customers.loc[df_customers["customer_id"] == cid, "normal_monthly_spend_eur"].values[0]
        shock_ratios.append(actual_spend / norm_spend)
    print(f"     * Verification: Min ratio = {min(shock_ratios):.2f}x | Mean ratio = {np.mean(shock_ratios):.2f}x | Max ratio = {max(shock_ratios):.2f}x")

    print(f"\n   - Silent Network Frustration Users: {len(silent_frust_custs):,} users ({len(silent_frust_custs)/len(df_customers)*100:.1f}%)")
    print(f"     * Criteria: latency_ms > 180 for 3+ consecutive days + open_support_tickets = 0.")
    # Verification of silent frustration users
    silent_verified = 0
    for cid in silent_frust_custs:
        c_logs = df_logs[df_logs["customer_id"] == cid].sort_values("date")
        tickets = c_logs["open_support_tickets"].sum()
        high_lat_runs = (c_logs["latency_ms"] > 180).astype(int)
        # Check max consecutive runs
        max_run = 0
        cur_run = 0
        for val in high_lat_runs:
            if val == 1:
                cur_run += 1
                if cur_run > max_run:
                    max_run = cur_run
            else:
                cur_run = 0
        if tickets == 0 and max_run >= 3:
            silent_verified += 1
    print(f"     * Verification: {silent_verified}/{len(silent_frust_custs)} users confirmed meeting exact 3+ consecutive high-latency days with 0 tickets.")

    # Dirty records summary
    print("\n4. INJECTED DIRTY / ANOMALOUS RECORDS (RAW TELEMETRY):")
    actual_null_towers = (df_logs["tower_id"] == "").sum() + df_logs["tower_id"].isna().sum()
    actual_neg_latency = (df_logs["latency_ms"] < 0).sum()
    actual_dup_ids = df_logs["record_id"].duplicated().sum()
    actual_total_dirty = actual_null_towers + actual_neg_latency + actual_dup_ids
    dirty_pct = (actual_total_dirty / len(df_logs)) * 100

    print(f"   - NULL tower_id rows:       {actual_null_towers:,} ({actual_null_towers/len(df_logs)*100:.2f}%)")
    print(f"   - Negative latency_ms rows: {actual_neg_latency:,} ({actual_neg_latency/len(df_logs)*100:.2f}%)")
    print(f"   - Duplicate record_id rows: {actual_dup_ids:,} ({actual_dup_ids/len(df_logs)*100:.2f}%)")
    print(f"   - TOTAL DIRTY RECORDS:      {actual_total_dirty:,} / {len(df_logs):,} rows ({dirty_pct:.2f}%)")
    print(f"   - Clean Valid Records:      {len(df_logs) - actual_total_dirty:,} rows ({(len(df_logs) - actual_total_dirty)/len(df_logs)*100:.2f}%)")

    print("\n" + "=" * 70)
    print("ALL DATA ASSETS GENERATED SUCCESSFULLY IN data/")
    print("=" * 70)

if __name__ == "__main__":
    main()
