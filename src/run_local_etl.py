#!/usr/bin/env python3
"""
TelecomGuard – Proactive Telco Risk & Retention Pipeline
Local ETL Execution Script (src/run_local_etl.py)

Mirrors the BigQuery Sandbox SQL procedures in:
- sql/01_telecomguard_etl_procedure.sql
- sql/02_executive_kpis.sql

Transformations:
1. Audit Data Quality Errors -> data/audit_data_quality_errors.csv (2,500 rows)
   - Flags NULL/empty tower_id, negative latency_ms, duplicate record_ids
2. Fact Daily Usage -> data/fact_daily_usage.csv (47,500 clean rows)
   - Currency normalization to EUR using dim_exchange_rates
3. Mart Customer Alerts -> data/mart_customer_alerts.csv (120 rows)
   - 60 Bill Shock / Balance Burn customers
   - 60 Silent Network Frustration customers
   - 7-day duplicate-alert suppression window
"""

import os
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd


def run_etl():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    cust_path = os.path.join(data_dir, "dim_customers.csv")
    rates_path = os.path.join(data_dir, "dim_exchange_rates.csv")
    logs_path = os.path.join(data_dir, "raw_usage_logs.csv")

    out_audit_path = os.path.join(data_dir, "audit_data_quality_errors.csv")
    out_fact_path = os.path.join(data_dir, "fact_daily_usage.csv")
    out_mart_path = os.path.join(data_dir, "mart_customer_alerts.csv")

    print("=" * 75)
    print("TELECOMGUARD: LOCAL ETL PIPELINE EXECUTION")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # 0. Load Raw Data
    # -------------------------------------------------------------------------
    print(f"\n[0/3] Reading source tables from {data_dir}...")
    df_customers = pd.read_csv(cust_path)
    df_rates = pd.read_csv(rates_path)
    df_logs = pd.read_csv(logs_path)

    print(f"  - dim_customers:    {len(df_customers):,} rows")
    print(f"  - dim_exchange_rates:{len(df_rates):,} rows")
    print(f"  - raw_usage_logs:   {len(df_logs):,} rows")

    now_iso = datetime.now(timezone.utc).isoformat()

    # -------------------------------------------------------------------------
    # 1. Step 1: Audit Data Quality Errors (Quarantine Table)
    # -------------------------------------------------------------------------
    print("\n[1/3] Executing STEP 1: Data Quality Audit & Quarantine Filter...")
    df_logs["date_dt"] = pd.to_datetime(df_logs["date"])

    # Rank duplicate records: ROW_NUMBER() OVER (PARTITION BY record_id ORDER BY date DESC)
    df_sorted = df_logs.sort_values(by=["record_id", "date_dt"], ascending=[True, False]).copy()
    df_sorted["record_rank"] = df_sorted.groupby("record_id").cumcount() + 1

    is_dup = df_sorted["record_rank"] > 1
    is_null_tower = df_sorted["tower_id"].isna() | (df_sorted["tower_id"].astype(str).str.strip() == "")
    is_neg_lat = df_sorted["latency_ms"] < 0

    dirty_mask = is_dup | is_null_tower | is_neg_lat
    df_dirty = df_sorted[dirty_mask].copy()

    # Build dq_failure_reason and error_type matching SQL ARRAY_TO_STRING
    dq_reasons = []
    error_types = []
    for _, row in df_dirty.iterrows():
        reasons = []
        if row["record_rank"] > 1:
            reasons.append("DUPLICATE_RECORD_ID")
        if pd.isna(row["tower_id"]) or str(row["tower_id"]).strip() == "":
            reasons.append("NULL_TOWER_ID")
        if row["latency_ms"] < 0:
            reasons.append("NEGATIVE_LATENCY")

        reason_str = "; ".join(reasons)
        dq_reasons.append(reason_str)

        if len(reasons) > 1:
            error_types.append("MULTIPLE_ERRORS")
        elif len(reasons) == 1:
            error_types.append(reasons[0])
        else:
            error_types.append("VALID")

    df_dirty["dq_failure_reason"] = dq_reasons
    df_dirty["error_type"] = error_types
    df_dirty["error_details"] = "Data Quality Quarantine: " + df_dirty["dq_failure_reason"]
    df_dirty["usage_date"] = df_dirty["date"]
    df_dirty["market_code"] = df_dirty["country"]
    df_dirty["quarantined_at"] = now_iso
    df_dirty["detected_at"] = now_iso

    audit_columns = [
        "record_id",
        "customer_id",
        "date",
        "usage_date",
        "country",
        "market_code",
        "tower_id",
        "latency_ms",
        "is_roaming",
        "roaming_country",
        "data_used_mb",
        "voice_minutes",
        "sms_count",
        "daily_spend_local",
        "currency",
        "packet_loss_pct",
        "open_support_tickets",
        "record_rank",
        "dq_failure_reason",
        "error_type",
        "error_details",
        "quarantined_at",
        "detected_at",
    ]

    df_audit = df_dirty[audit_columns].sort_values(by=["date", "record_id"])
    df_audit.to_csv(out_audit_path, index=False)
    print(f"  -> Exported audit_data_quality_errors.csv: {len(df_audit):,} rows (expected 2,500)")

    # -------------------------------------------------------------------------
    # 2. Step 2: Fact Daily Usage (Clean Warehouse Table)
    # -------------------------------------------------------------------------
    print("\n[2/3] Executing STEP 2: Building Clean fact_daily_usage...")
    clean_mask = ~dirty_mask
    df_clean = df_sorted[clean_mask].copy()

    # Join dim_customers for country validation and dim_exchange_rates for EUR normalization
    fx_map = dict(zip(df_rates["currency_code"], df_rates["fx_rate_to_eur"]))
    df_clean["exchange_rate_to_eur"] = df_clean["currency"].map(fx_map).fillna(1.0)
    df_clean["charge_eur"] = (df_clean["daily_spend_local"] * df_clean["exchange_rate_to_eur"]).round(4)
    df_clean["daily_spend_eur"] = df_clean["charge_eur"]
    df_clean["usage_date"] = df_clean["date"]
    df_clean["market_code"] = df_clean["country"]
    df_clean["charge_amount"] = df_clean["daily_spend_local"]
    df_clean["local_currency"] = df_clean["currency"]
    df_clean["etl_loaded_at"] = now_iso

    fact_columns = [
        "record_id",
        "customer_id",
        "date",
        "usage_date",
        "country",
        "market_code",
        "tower_id",
        "latency_ms",
        "is_roaming",
        "roaming_country",
        "data_used_mb",
        "voice_minutes",
        "sms_count",
        "daily_spend_local",
        "charge_amount",
        "currency",
        "local_currency",
        "exchange_rate_to_eur",
        "charge_eur",
        "daily_spend_eur",
        "packet_loss_pct",
        "open_support_tickets",
        "etl_loaded_at",
    ]

    df_fact = df_clean[fact_columns].sort_values(by=["date", "record_id"])
    df_fact.to_csv(out_fact_path, index=False)
    print(f"  -> Exported fact_daily_usage.csv: {len(df_fact):,} rows (expected 47,500)")

    # -------------------------------------------------------------------------
    # 3. Step 3: Mart Customer Alerts (Actionable Retention & Risk Mart)
    # -------------------------------------------------------------------------
    print("\n[3/3] Executing STEP 3: Evaluating Risk Triggers & Mart Alerts...")

    # Aggregate clean daily logs to ensure calendar-day customer grain
    df_fact["date_dt"] = pd.to_datetime(df_fact["date"])
    customer_daily = df_fact.groupby(["customer_id", "country", "market_code", "date_dt"]).agg(
        daily_spend_eur=("daily_spend_eur", "sum"),
        daily_avg_latency_ms=("latency_ms", "mean"),
        has_roaming=("is_roaming", lambda s: bool(s.any())),
        open_support_tickets=("open_support_tickets", "max"),
    ).reset_index().sort_values(by=["customer_id", "date_dt"])

    # Rolling 7-day sum of daily_spend_eur
    rolling_groups = []
    for cid, grp in customer_daily.groupby("customer_id"):
        grp_indexed = grp.set_index("date_dt")
        grp["last_7d_spend_eur"] = grp_indexed["daily_spend_eur"].rolling("7D", closed="both").sum().values
        rolling_groups.append(grp)
    df_rolling = pd.concat(rolling_groups).reset_index(drop=True)

    # LAG latencies and dates for Silent Network Frustration
    df_rolling["prev_day_1_latency_ms"] = df_rolling.groupby("customer_id")["daily_avg_latency_ms"].shift(1)
    df_rolling["prev_day_2_latency_ms"] = df_rolling.groupby("customer_id")["daily_avg_latency_ms"].shift(2)
    df_rolling["prev_day_1_date"] = df_rolling.groupby("customer_id")["date_dt"].shift(1)
    df_rolling["prev_day_2_date"] = df_rolling.groupby("customer_id")["date_dt"].shift(2)

    # Merge customer dimensions
    df_enriched = df_rolling.merge(df_customers, on="customer_id", suffixes=("", "_cust"))
    df_enriched["plan_type"] = df_enriched["contract_type"].astype(str).str.title()
    df_enriched["customer_name"] = df_enriched["name"]

    # 3A. Bill Shock / Balance Burn candidates
    # ((last_7d_spend / 7) * 30) > 1.35 * normal_monthly_spend_eur
    bs_mask = (df_enriched["normal_monthly_spend_eur"] > 0) & (
        ((df_enriched["last_7d_spend_eur"] / 7.0) * 30.0) > (1.35 * df_enriched["normal_monthly_spend_eur"])
    )
    df_bs_candidates = df_enriched[bs_mask].copy()

    df_bs_candidates["alert_type"] = "BILL_SHOCK"
    df_bs_candidates["risk_category"] = np.where(
        df_bs_candidates["contract_type"] == "Prepaid", "Balance Burn", "Bill Shock"
    )
    projected_spend = ((df_bs_candidates["last_7d_spend_eur"] / 7.0) * 30.0).round(2)
    df_bs_candidates["projected_spend_eur"] = projected_spend
    df_bs_candidates["trigger_metric_value"] = projected_spend
    df_bs_candidates["threshold_metric_value"] = (1.35 * df_bs_candidates["normal_monthly_spend_eur"]).round(2)
    df_bs_candidates["spend_ratio"] = (projected_spend / df_bs_candidates["normal_monthly_spend_eur"]).round(2)
    df_bs_candidates["avg_latency_ms"] = df_bs_candidates["daily_avg_latency_ms"].round(2)
    df_bs_candidates["consecutive_bad_network_days"] = 0
    df_bs_candidates["revenue_at_risk_eur"] = projected_spend

    is_critical_bs = projected_spend > (2.0 * df_bs_candidates["normal_monthly_spend_eur"])
    df_bs_candidates["severity"] = np.where(is_critical_bs, "CRITICAL", "HIGH")
    df_bs_candidates["alert_severity"] = df_bs_candidates["severity"]

    df_bs_candidates["trigger_reason"] = [
        f"Projected 30-day spend of €{proj:.2f} exceeds 135% of baseline (€{norm:.2f})"
        for proj, norm in zip(projected_spend, df_bs_candidates["normal_monthly_spend_eur"])
    ]

    actions_bs = []
    for ctype in df_bs_candidates["contract_type"]:
        if ctype == "Postpaid":
            actions_bs.append(
                "Proactive Billing Care: Issue spend threshold SMS notification; offer plan upgrade or recurring data bolt-on before month-end invoice"
            )
        else:
            actions_bs.append(
                "Prepaid Burn Care: Send high-consumption SMS alert with discounted 30-day recurring bundle offer to preserve customer balance"
            )
    df_bs_candidates["recommended_action"] = actions_bs

    # 3B. Silent Network Frustration candidates
    # >180ms latency for 3 consecutive days with open_support_tickets = 0
    sf_mask = (
        (df_enriched["daily_avg_latency_ms"] > 180.0)
        & (df_enriched["prev_day_1_latency_ms"] > 180.0)
        & (df_enriched["prev_day_2_latency_ms"] > 180.0)
        & ((df_enriched["date_dt"] - df_enriched["prev_day_1_date"]).dt.days == 1)
        & ((df_enriched["prev_day_1_date"] - df_enriched["prev_day_2_date"]).dt.days == 1)
        & (df_enriched["open_support_tickets"] == 0)
    )
    df_sf_candidates = df_enriched[sf_mask].copy()

    df_sf_candidates["alert_type"] = "SILENT_NETWORK_FRUSTRATION"
    df_sf_candidates["risk_category"] = "Silent Network Frustration"
    is_critical_sf = df_sf_candidates["daily_avg_latency_ms"] > 250.0
    df_sf_candidates["severity"] = np.where(is_critical_sf, "CRITICAL", "HIGH")
    df_sf_candidates["alert_severity"] = df_sf_candidates["severity"]

    df_sf_candidates["trigger_metric_value"] = df_sf_candidates["daily_avg_latency_ms"].round(2)
    df_sf_candidates["projected_spend_eur"] = df_sf_candidates["normal_monthly_spend_eur"].round(2)
    df_sf_candidates["threshold_metric_value"] = 180.0
    df_sf_candidates["spend_ratio"] = 1.00
    df_sf_candidates["avg_latency_ms"] = df_sf_candidates["daily_avg_latency_ms"].round(2)
    df_sf_candidates["consecutive_bad_network_days"] = 3
    df_sf_candidates["revenue_at_risk_eur"] = df_sf_candidates["normal_monthly_spend_eur"].round(2)

    df_sf_candidates["trigger_reason"] = [
        f"Severe network latency ({lat:.1f}ms) sustained for 3 consecutive days with 0 open support tickets"
        for lat in df_sf_candidates["daily_avg_latency_ms"]
    ]

    actions_sf = []
    for ctype in df_sf_candidates["contract_type"]:
        if ctype == "Postpaid":
            actions_sf.append(
                "VIP Network Care: Initiate proactive account outreach, open network engineering cell check, and credit 10 EUR goodwill loyalty voucher"
            )
        else:
            actions_sf.append(
                "Network Retention Care: Push automated network APN reconfiguration profile and grant complimentary 5GB 3-day network compensation booster"
            )
    df_sf_candidates["recommended_action"] = actions_sf

    # Combine candidates
    df_raw_alerts = pd.concat([df_bs_candidates, df_sf_candidates], ignore_index=True)

    # 3C. Cooldown & Suppression: 7-day rolling duplicate suppression
    df_raw_alerts["alert_date"] = df_raw_alerts["date_dt"].dt.date
    df_raw_alerts["initial_detection_date"] = df_raw_alerts.groupby(["customer_id", "alert_type"])["date_dt"].transform("min")
    df_raw_alerts["suppression_window_id"] = (df_raw_alerts["date_dt"] - df_raw_alerts["initial_detection_date"]).dt.days // 7
    df_raw_alerts["window_occurrence_rank"] = df_raw_alerts.groupby(["customer_id", "alert_type", "suppression_window_id"])["date_dt"].rank(method="first")

    # Filter unsuppressed alerts
    df_unsuppressed = df_raw_alerts[df_raw_alerts["window_occurrence_rank"] == 1].copy()
    df_unsuppressed = df_unsuppressed.sort_values(by=["revenue_at_risk_eur", "alert_date"], ascending=[False, True]).reset_index(drop=True)

    # Generate sequential unique alert IDs
    alert_ids = [f"ALT-{row['alert_date'].strftime('%Y%m%d')}-{idx + 1:04d}" for idx, row in df_unsuppressed.iterrows()]
    df_unsuppressed["alert_id"] = alert_ids
    df_unsuppressed["is_suppressed"] = False
    df_unsuppressed["days_since_previous_alert"] = np.nan
    df_unsuppressed["generated_at"] = now_iso

    mart_columns = [
        "alert_id",
        "alert_date",
        "customer_id",
        "customer_name",
        "market_code",
        "country",
        "plan_type",
        "contract_type",
        "alert_type",
        "risk_category",
        "severity",
        "alert_severity",
        "trigger_metric_value",
        "threshold_metric_value",
        "projected_spend_eur",
        "normal_monthly_spend_eur",
        "spend_ratio",
        "avg_latency_ms",
        "consecutive_bad_network_days",
        "open_support_tickets",
        "revenue_at_risk_eur",
        "trigger_reason",
        "recommended_action",
        "suppression_window_id",
        "days_since_previous_alert",
        "is_suppressed",
        "generated_at",
    ]

    df_mart = df_unsuppressed[mart_columns]
    df_mart.to_csv(out_mart_path, index=False)

    bs_total = (df_mart["alert_type"] == "BILL_SHOCK").sum()
    sf_total = (df_mart["alert_type"] == "SILENT_NETWORK_FRUSTRATION").sum()
    print(f"  -> Exported mart_customer_alerts.csv: {len(df_mart):,} rows ({bs_total} Bill Shock, {sf_total} Silent Frustration)")

    # -------------------------------------------------------------------------
    # 4. Final Verification Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("ETL PIPELINE VALIDATION & INTEGRITY METRICS")
    print("=" * 75)
    total_evaluated = len(df_fact) + len(df_audit)
    pass_rate = (len(df_fact) / total_evaluated) * 100.0
    print(f"Total Telemetry Logs Evaluated:  {total_evaluated:,}")
    print(f"Clean Records (Fact Table):      {len(df_fact):,} (Pass Rate: {pass_rate:.1f}%)")
    print(f"Quarantined Records (DQ Errors): {len(df_audit):,} (Fail Rate: {100.0 - pass_rate:.1f}%)")
    print(f"Total Actionable Retention Mart: {len(df_mart):,} accounts")
    print(f"  - Bill Shock / Balance Burn:   {bs_total:,} accounts")
    print(f"  - Silent Network Frustration:  {sf_total:,} accounts")
    print(f"Total Revenue At Risk:           €{df_mart['revenue_at_risk_eur'].sum():,.2f}")
    print("=" * 75)
    print("ETL Execution Complete. Data assets ready for Streamlit dashboard.\n")


if __name__ == "__main__":
    run_etl()
