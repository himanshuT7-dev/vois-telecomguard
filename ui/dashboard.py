#!/usr/bin/env python3
"""
TelecomGuard — Operational & Financial Audit Terminal
Vodafone Europe & Regional Affiliates | BI Visualization Engine

Design Specification:
- Crisp European Telecom Operations & Financial Audit Terminal
- Swiss grid typography, Bloomberg/Linear clarity
- Vodafone #E60000 crimson accent on #F8F9FA off-white / #FFFFFF 1px #E2E8F0 bordered surfaces
- #0F172A slate ink typography, tabular-nums monospace alignment for metrics
- Zero emojis, zero neon/purple gradients, zero dark glassmorphism, zero SaaS fluff
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & ROOT STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TelecomGuard | Financial Audit & Operations Terminal",
    page_icon="none",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
/* Global Reset & Swiss Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #F8F9FA !important;
    color: #0F172A !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    font-feature-settings: "cv02", "cv03", "cv04", "cv11" !important;
}

/* Eliminate default Streamlit chrome fluff */
header[data-testid="stHeader"] {
    background: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0 !important;
    height: 3rem !important;
    z-index: 100 !important;
}
.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1600px !important;
}
footer {
    display: none !important;
}
#MainMenu {
    visibility: hidden !important;
}

/* Institutional Terminal Banner */
.terminal-header {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #E60000;
    padding: 16px 22px;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-sizing: border-box !important;
}
.terminal-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #0F172A;
    margin: 0;
    line-height: 1.35;
    padding-top: 2px;
}
.terminal-subtitle {
    font-size: 0.75rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
    font-weight: 500;
}
.terminal-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #334155;
    text-align: right;
    line-height: 1.5;
    font-variant-numeric: tabular-nums;
}
.status-pill {
    display: inline-block;
    padding: 2px 8px;
    font-size: 0.70rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid #CBD5E1;
    background: #F1F5F9;
    color: #0F172A;
    border-radius: 2px;
}
.status-pill-live {
    border-color: #FECACA;
    background: #FEF2F2;
    color: #991B1B;
}

/* -------------------------------------------------------------
   Full-Width Horizontal Navigation Bar (Centered Swiss-Grid)
   ------------------------------------------------------------- */
/* Remove vertical gap between terminal header and navbar */
div[data-testid="stVerticalBlock"] > div:has(.terminal-header) {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stRadio"]) {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
div[data-testid="element-container"]:has(div[data-testid="stRadio"]) {
    width: 100% !important;
    max-width: 100% !important;
    margin-top: 0px !important;
    margin-bottom: 20px !important;
    padding: 0 !important;
}

/* Outer navbar container: full-width white surface with 1px border */
div[data-testid="stRadio"] {
    width: 100% !important;
    max-width: 100% !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-top: none !important;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

/* Hide empty Streamlit widget label so it doesn't push down the radiogroup */
div[data-testid="stRadio"] > label[data-testid="stWidgetLabel"] {
    display: none !important;
    height: 0 !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Radiogroup flex container: CENTER the tabs horizontally across the full-width bar */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important; /* ZERO WRAPPING */
    justify-content: center !important; /* CENTER ALIGN TABS */
    align-items: center !important;
    width: 100% !important;
    height: 44px !important;
    gap: 28px !important;
    background: transparent !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 16px !important;
    box-sizing: border-box !important;
}

/* Each tab item: scope strictly to data-baseweb="radio" */
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    flex: 0 0 auto !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 44px !important;
    line-height: 44px !important;
    padding: 0 12px !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0px !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    transition: all 0.15s ease-in-out !important;
}

/* Hide the default radio circle indicator */
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Tab typography */
div[data-testid="stRadio"] label[data-baseweb="radio"] p,
div[data-testid="stRadio"] label[data-baseweb="radio"] span,
div[data-testid="stRadio"] label[data-baseweb="radio"] div[data-testid="stMarkdownContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #64748B !important;
    white-space: nowrap !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 44px !important;
    transition: color 0.15s ease-in-out !important;
}

/* Hover state */
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover p,
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover span {
    color: #0F172A !important;
}

/* Active tab state: sharp bold #0F172A text with 3px #E60000 crimson bottom border */
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"],
div[data-testid="stRadio"] label[data-baseweb="radio"][data-checked="true"] {
    background: transparent !important;
    border-bottom: 3px solid #E60000 !important;
}

div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p,
div[data-testid="stRadio"] label[data-baseweb="radio"][data-checked="true"] p,
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] span,
div[data-testid="stRadio"] label[data-baseweb="radio"][data-checked="true"] span {
    color: #0F172A !important;
    font-weight: 700 !important;
}

/* KPI Card Typography & Alignment */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 2px;
    padding: 16px 18px;
    height: 100%;
}
.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
}
.metric-caption {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
}
.metric-code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #94A3B8;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #0F172A;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    margin-bottom: 6px;
}
.metric-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-variant-numeric: tabular-nums;
    color: #475569;
    display: flex;
    align-items: center;
    gap: 6px;
}
.delta-tag {
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 2px;
    font-size: 0.68rem;
}
.delta-neutral {
    background: #F1F5F9;
    color: #334155;
    border: 1px solid #E2E8F0;
}
.delta-alert {
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FCA5A5;
}
.delta-positive {
    background: #F0FDF4;
    color: #166534;
    border: 1px solid #BBF7D0;
}

/* Section Header Panels */
.section-header {
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 8px;
    margin-top: 20px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.section-title {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #0F172A;
    margin: 0;
}
.section-annotation {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #64748B;
    text-transform: uppercase;
}

/* Operational Tables & Monospace Cells */
.table-container {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 2px;
    padding: 0;
    overflow-x: auto;
}
table.ops-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.76rem;
    text-align: left;
}
table.ops-table th {
    background: #F8F9FA;
    border-bottom: 1px solid #E2E8F0;
    padding: 9px 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
    font-size: 0.68rem;
    white-space: nowrap;
}
table.ops-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #F1F5F9;
    color: #1E293B;
    vertical-align: middle;
}
table.ops-table tr:hover td {
    background: #F8FAFC;
}
.num-cell {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    text-align: right;
}
.id-cell {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #0F172A;
}

/* Risk Badges */
.badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 2px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-family: 'Inter', sans-serif;
}
.badge-bill-shock {
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
}
.badge-frustration {
    background: #F8FAFC;
    color: #334155;
    border: 1px solid #CBD5E1;
}
.badge-market {
    font-family: 'JetBrains Mono', monospace;
    background: #F1F5F9;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    padding: 1px 5px;
}

/* Terminal Console Box */
.terminal-console {
    background: #0F172A;
    color: #F8FAFC;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    padding: 14px 18px;
    border: 1px solid #1E293B;
    border-radius: 2px;
    line-height: 1.5;
    white-space: pre-wrap;
    max-height: 380px;
    overflow-y: auto;
}

/* Streamlit Button & Widget Overrides */
div[data-testid="stDownloadButton"] > button,
div[data-testid="stButton"] > button {
    background-color: #0F172A !important;
    color: #FFFFFF !important;
    border: 1px solid #0F172A !important;
    border-radius: 2px !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 6px 14px !important;
}
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stButton"] > button:hover {
    background-color: #E60000 !important;
    border-color: #E60000 !important;
    color: #FFFFFF !important;
}

/* Data Editor Border & Header Alignment */
div[data-testid="stDataEditor"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 2px !important;
    background: #FFFFFF !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT FOR TICKET STATUSES
# -----------------------------------------------------------------------------
if "ticket_statuses" not in st.session_state:
    st.session_state["ticket_statuses"] = {}

if "etl_execution_log" not in st.session_state:
    st.session_state["etl_execution_log"] = None

if "last_etl_timestamp" not in st.session_state:
    st.session_state["last_etl_timestamp"] = "2026-11-18 21:04 UTC"


# -----------------------------------------------------------------------------
# 3. DATA LOAD & RE-EVALUATION LOGIC
# -----------------------------------------------------------------------------
def load_audit_data():
    """
    Attempts to read data from `data/` directory.
    Supports both production mart exports (`mart_customer_alerts.csv`, `audit_data_quality_errors.csv`,
    `fact_daily_usage.csv`) and ad-hoc exports (`flagged_customers.csv`, `quarantine_metrics.csv`).
    Falls back to a deterministic, high-fidelity dataset representing
    Vodafone UK, Germany (DE), and India (IN) operations.
    """
    alerts_path = os.path.join("data", "mart_customer_alerts.csv")
    flagged_path = os.path.join("data", "flagged_customers.csv")
    audit_err_path = os.path.join("data", "audit_data_quality_errors.csv")
    quarantine_path = os.path.join("data", "quarantine_metrics.csv")
    fact_usage_path = os.path.join("data", "fact_daily_usage.csv")

    flagged_df = None
    quarantine_df = None
    total_ingested_count = 50000

    # 1. Load Alert / Flagged Customer Records
    if os.path.exists(alerts_path):
        try:
            raw_alerts = pd.read_csv(alerts_path)
            df_mapped = raw_alerts.copy()
            if "market_code" in df_mapped.columns and "market" not in df_mapped.columns:
                df_mapped["market"] = df_mapped["market_code"]
            elif "country" in df_mapped.columns and "market" not in df_mapped.columns:
                df_mapped["market"] = df_mapped["country"]

            if "contract_type" in df_mapped.columns and "plan_type" not in df_mapped.columns:
                df_mapped["plan_type"] = df_mapped["contract_type"]
            if "plan_type" in df_mapped.columns:
                df_mapped["plan_type"] = df_mapped["plan_type"].astype(str).str.title()

            if "alert_type" in df_mapped.columns and "risk_type" not in df_mapped.columns:
                df_mapped["risk_type"] = df_mapped["alert_type"].replace({
                    "BILL_SHOCK": "Bill Shock",
                    "SILENT_NETWORK_FRUSTRATION": "Silent Frustration",
                    "Balance Burn": "Bill Shock",
                    "Silent Network Frustration": "Silent Frustration",
                })
            elif "risk_category" in df_mapped.columns and "risk_type" not in df_mapped.columns:
                df_mapped["risk_type"] = df_mapped["risk_category"].replace({
                    "BILL_SHOCK": "Bill Shock",
                    "SILENT_NETWORK_FRUSTRATION": "Silent Frustration",
                    "Balance Burn": "Bill Shock",
                    "Silent Network Frustration": "Silent Frustration",
                })

            if "revenue_at_risk_eur" not in df_mapped.columns:
                if "projected_spend_eur" in df_mapped.columns and "normal_monthly_spend_eur" in df_mapped.columns:
                    df_mapped["revenue_at_risk_eur"] = np.where(
                        df_mapped["risk_type"].isin(["Bill Shock", "Balance Burn"]),
                        np.maximum(df_mapped["projected_spend_eur"] - df_mapped["normal_monthly_spend_eur"], df_mapped["projected_spend_eur"]),
                        df_mapped["normal_monthly_spend_eur"]
                    ).round(2)
                else:
                    df_mapped["revenue_at_risk_eur"] = 120.0

            if "recommended_action" not in df_mapped.columns:
                df_mapped["recommended_action"] = "Proactive retention dispatch & tariff check"

            # Filter out suppressed or normal alerts if present
            if "is_suppressed" in df_mapped.columns:
                df_mapped = df_mapped[df_mapped["is_suppressed"] == False]
            if "risk_type" in df_mapped.columns:
                df_mapped = df_mapped[df_mapped["risk_type"].isin(["Bill Shock", "Silent Frustration"])]

            flagged_df = df_mapped
        except Exception:
            flagged_df = None

    elif os.path.exists(flagged_path):
        try:
            flagged_df = pd.read_csv(flagged_path)
            if "market_code" in flagged_df.columns and "market" not in flagged_df.columns:
                flagged_df["market"] = flagged_df["market_code"]
            if "plan_type" in flagged_df.columns:
                flagged_df["plan_type"] = flagged_df["plan_type"].astype(str).str.title()
        except Exception:
            flagged_df = None

    # 2. Load Quarantine / Error Records
    if os.path.exists(audit_err_path):
        try:
            raw_audit = pd.read_csv(audit_err_path)
            err_counts = None
            if "dq_failure_reason" in raw_audit.columns:
                reasons = raw_audit["dq_failure_reason"].dropna().str.split("; ").explode().str.strip()
                err_counts = reasons[reasons != ""].value_counts().reset_index()
                err_counts.columns = ["quarantine_reason", "records_quarantined"]
            elif "error_type" in raw_audit.columns:
                err_counts = raw_audit["error_type"].value_counts().reset_index()
                err_counts.columns = ["quarantine_reason", "records_quarantined"]

            if err_counts is not None and not err_counts.empty:
                severity_map = {
                    "NEGATIVE_LATENCY": "CRITICAL",
                    "MISSING_TOWER_ID": "HIGH",
                    "NULL_TOWER_ID": "HIGH",
                    "DUPLICATE_RECORD_ID": "LOW",
                    "INVALID_MSISDN_FORMAT": "HIGH",
                    "NEGATIVE_CDR_DURATION": "CRITICAL",
                    "TARIFF_CODE_UNMAPPED": "MEDIUM",
                }
                sla_map = {
                    "NEGATIVE_LATENCY": 2,
                    "MISSING_TOWER_ID": 4,
                    "NULL_TOWER_ID": 4,
                    "DUPLICATE_RECORD_ID": 24,
                    "INVALID_MSISDN_FORMAT": 4,
                    "NEGATIVE_CDR_DURATION": 2,
                    "TARIFF_CODE_UNMAPPED": 12,
                }
                err_counts["severity"] = err_counts["quarantine_reason"].map(lambda x: severity_map.get(x, "MEDIUM"))
                err_counts["sla_hours"] = err_counts["quarantine_reason"].map(lambda x: sla_map.get(x, 12))
                quarantine_df = err_counts
        except Exception:
            quarantine_df = None

    elif os.path.exists(quarantine_path):
        try:
            quarantine_df = pd.read_csv(quarantine_path)
        except Exception:
            quarantine_df = None

    # 3. Calculate dynamic total ingestion count if fact_daily_usage exists
    if os.path.exists(fact_usage_path):
        try:
            fact_df = pd.read_csv(fact_usage_path, usecols=["record_id"])
            if quarantine_df is not None:
                total_ingested_count = len(fact_df) + quarantine_df["records_quarantined"].sum()
            else:
                total_ingested_count = len(fact_df)
        except Exception:
            pass

    # Deterministic fallback generation if data files are missing or incomplete
    if flagged_df is None or flagged_df.empty:
        np.random.seed(42)
        n_samples = 320

        markets = ["UK", "DE", "IN"]
        market_weights = [0.42, 0.38, 0.20]
        assigned_markets = np.random.choice(markets, size=n_samples, p=market_weights)

        plan_types = ["Postpaid", "Prepaid"]
        assigned_plans = []
        for m in assigned_markets:
            if m in ["UK", "DE"]:
                assigned_plans.append(np.random.choice(plan_types, p=[0.82, 0.18]))
            else:
                assigned_plans.append(np.random.choice(plan_types, p=[0.35, 0.65]))

        risk_types = ["Bill Shock", "Silent Frustration"]
        assigned_risks = np.random.choice(risk_types, size=n_samples, p=[0.45, 0.55])

        records = []
        for i in range(n_samples):
            m = assigned_markets[i]
            p = assigned_plans[i]
            r = assigned_risks[i]
            cid = f"CUST-{m}-{100000 + i * 37 + np.random.randint(10, 99)}"

            if r == "Bill Shock":
                base_charge = 35.0 if p == "Postpaid" else 15.0
                spike_multiplier = np.random.uniform(2.8, 14.5)
                overage_eur = base_charge * spike_multiplier
                revenue_at_risk = round(overage_eur, 2)
                latency = round(np.random.uniform(18.0, 48.0), 1)
                packet_loss = round(np.random.uniform(0.1, 1.2), 2)
                bill_delta_pct = round((spike_multiplier - 1.0) * 100, 1)

                actions = [
                    "Proactive Billing Care: Issue spend threshold SMS notification; offer plan upgrade or recurring data bolt-on before month-end invoice",
                    "Dispute freeze & goodwill waiver (€50 threshold)",
                    "Prepaid Burn Care: Send high-consumption SMS alert with discounted 30-day recurring bundle offer to preserve customer balance",
                ]
                recommended_action = actions[i % len(actions)]
            else:
                revenue_at_risk = round(np.random.uniform(28.0, 310.0), 2)
                latency = round(np.random.uniform(75.0, 195.0), 1)
                packet_loss = round(np.random.uniform(3.8, 12.4), 2)
                bill_delta_pct = round(np.random.uniform(-35.0, 5.0), 1)

                actions = [
                    "VIP Network Care: Initiate proactive account outreach, open network engineering cell check, and credit 10 EUR goodwill loyalty voucher",
                    "Network Retention Care: Push automated network APN reconfiguration profile and grant complimentary 5GB 3-day network compensation booster",
                    "Network Retention Care: Dispatch cell diagnostic team and offer goodwill data pack",
                ]
                recommended_action = actions[i % len(actions)]

            records.append({
                "customer_id": cid,
                "market": m,
                "plan_type": p,
                "risk_type": r,
                "revenue_at_risk_eur": revenue_at_risk,
                "recommended_action": recommended_action,
                "latency_ms": latency,
                "packet_loss_pct": packet_loss,
                "bill_delta_pct": bill_delta_pct,
                "tenure_months": int(np.random.randint(4, 84)),
            })

        flagged_df = pd.DataFrame(records)

    if quarantine_df is None or quarantine_df.empty:
        quarantine_df = pd.DataFrame([
            {"quarantine_reason": "DUPLICATE_RECORD_ID", "records_quarantined": 834, "severity": "LOW", "sla_hours": 24},
            {"quarantine_reason": "NULL_TOWER_ID", "records_quarantined": 833, "severity": "HIGH", "sla_hours": 4},
            {"quarantine_reason": "NEGATIVE_LATENCY", "records_quarantined": 833, "severity": "CRITICAL", "sla_hours": 2},
        ])

    # Attach live action_status column from st.session_state if present
    if "action_status" not in flagged_df.columns:
        statuses = []
        for cid in flagged_df["customer_id"]:
            statuses.append(st.session_state["ticket_statuses"].get(cid, "Pending"))
        flagged_df["action_status"] = statuses

    return flagged_df, quarantine_df, total_ingested_count


flagged_data, quarantine_data, total_ingested_records = load_audit_data()

# -----------------------------------------------------------------------------
# 4. GLOBAL TERMINAL HEADER
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="terminal-header">
        <div>
            <div class="terminal-title">TELECOMGUARD &nbsp;|&nbsp; REVENUE ASSURANCE & RETENTION AUDIT TERMINAL</div>
            <div class="terminal-subtitle">Vodafone Operations Centre Europe & Affiliates &bull; Multi-Market Governance Engine</div>
        </div>
        <div class="terminal-meta">
            <div>AUDIT BATCH: <span style="font-weight:700;">2026-W47-02</span> &nbsp;|&nbsp; STATUS: <span class="status-pill status-pill-live">PIPELINE VERIFIED</span></div>
            <div style="margin-top:3px; color:#64748B;">SYSTEM TIMESTAMP: {st.session_state['last_etl_timestamp']} &nbsp;|&nbsp; INGESTION SLA: 99.98%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 5. HORIZONTAL TOP NAVIGATION BAR (NAVBAR)
# -----------------------------------------------------------------------------
NAV_OPTIONS = [
    "01 · EXECUTIVE OVERVIEW",
    "02 · RETENTION QUEUE",
    "03 · PIPELINE SIMULATOR",
]

page_selection = st.radio(
    label="TERMINAL_NAVBAR_SELECT",
    options=NAV_OPTIONS,
    index=0,
    horizontal=True,
    label_visibility="collapsed",
    key="top_nav_bar_radio",
)


# -----------------------------------------------------------------------------
# 6. PAGE 1: LEADERSHIP & DATA GOVERNANCE
# -----------------------------------------------------------------------------
if page_selection == "01 · EXECUTIVE OVERVIEW":
    total_rev_at_risk = flagged_data["revenue_at_risk_eur"].sum()
    bill_shock_count = len(flagged_data[flagged_data["risk_type"] == "Bill Shock"])
    frustration_count = len(flagged_data[flagged_data["risk_type"] == "Silent Frustration"])

    total_ingested = total_ingested_records
    total_quarantined = quarantine_data["records_quarantined"].sum()
    dq_pass_rate = ((total_ingested - total_quarantined) / total_ingested) * 100 if total_ingested > 0 else 95.0

    # 4 Sharp KPI Metric Blocks
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">TOTAL REVENUE AT RISK</span>
                    <span class="metric-code">METRIC-REV-01</span>
                </div>
                <div class="metric-value">&euro;{total_rev_at_risk:,.2f}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-alert">+3.4%</span>
                    <span>vs. previous audit cycle</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">BILL SHOCK CASES</span>
                    <span class="metric-code">FLAG-BSHOCK-02</span>
                </div>
                <div class="metric-value">{bill_shock_count:,}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-neutral">50.0% OF QUEUE</span>
                    <span>mean overage &euro;{(total_rev_at_risk / bill_shock_count if bill_shock_count else 0):,.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">SILENT FRUSTRATION CASES</span>
                    <span class="metric-code">FLAG-SLNT-03</span>
                </div>
                <div class="metric-value">{frustration_count:,}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-alert">+7.8% RISK</span>
                    <span>unreported QoE failure</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">PIPELINE DATA QUALITY PASS RATE</span>
                    <span class="metric-code">GOV-DQ-04</span>
                </div>
                <div class="metric-value">{dq_pass_rate:.2f}%</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-positive">SLA COMPLIANT</span>
                    <span>{total_quarantined:,} quarantined / {total_ingested:,}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # SECTION: SIDE-BY-SIDE MARKET COMPARISON (UK, DE, IN by Postpaid vs Prepaid)
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div class="section-header">
            <span class="section-title">REGIONAL MARKET RISK BENCHMARK &bull; UK &bull; DE &bull; IN</span>
            <span class="section-annotation">DIMENSION: PLAN_TYPE (POSTPAID VS. PREPAID) &bull; CURRENCY: EUR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    market_agg = flagged_data.groupby(["market", "plan_type"]).agg(
        revenue_at_risk=("revenue_at_risk_eur", "sum"),
        account_count=("customer_id", "count"),
        avg_rev_per_account=("revenue_at_risk_eur", "mean"),
    ).reset_index()

    col_chart_mkt, col_table_mkt = st.columns([6, 5])

    with col_chart_mkt:
        fig_market = go.Figure()

        markets_ordered = ["UK", "DE", "IN"]
        postpaid_vals = []
        prepaid_vals = []

        for m in markets_ordered:
            post_val = market_agg[(market_agg["market"] == m) & (market_agg["plan_type"] == "Postpaid")]["revenue_at_risk"].sum()
            prep_val = market_agg[(market_agg["market"] == m) & (market_agg["plan_type"] == "Prepaid")]["revenue_at_risk"].sum()
            postpaid_vals.append(post_val)
            prepaid_vals.append(prep_val)

        # Primary Series: Postpaid (Deep Slate #0F172A)
        fig_market.add_trace(go.Bar(
            name="Postpaid",
            x=markets_ordered,
            y=postpaid_vals,
            marker_color="#0F172A",
            marker_line_width=1,
            marker_line_color="#0F172A",
            text=[f"€{v:,.0f}" for v in postpaid_vals],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color="#0F172A"),
        ))

        # Secondary Series: Prepaid (Vodafone Crimson #E60000)
        fig_market.add_trace(go.Bar(
            name="Prepaid",
            x=markets_ordered,
            y=prepaid_vals,
            marker_color="#E60000",
            marker_line_width=1,
            marker_line_color="#E60000",
            text=[f"€{v:,.0f}" for v in prepaid_vals],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color="#E60000"),
        ))

        fig_market.update_layout(
            barmode="group",
            bargroupgap=0.15,
            bargap=0.35,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=40, r=20, t=25, b=40),
            height=320,
            font=dict(family="Inter", size=12, color="#0F172A"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, family="Inter"),
            ),
            xaxis=dict(
                showgrid=False,
                linecolor="#CBD5E1",
                linewidth=1,
                tickfont=dict(family="JetBrains Mono", size=12, color="#0F172A"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#F1F5F9",
                gridwidth=1,
                linecolor="#CBD5E1",
                linewidth=1,
                tickformat="€,.0f",
                tickfont=dict(family="JetBrains Mono", size=10, color="#64748B"),
            ),
        )
        st.plotly_chart(fig_market, use_container_width=True, config={"displayModeBar": False})

    with col_table_mkt:
        mkt_rows = []
        for _, row in market_agg.sort_values(by=["revenue_at_risk"], ascending=False).iterrows():
            mkt_rows.append(
                f"<tr><td><span class='badge badge-market'>{row['market']}</span></td>"
                f"<td style='font-weight: 500;'>{row['plan_type']}</td>"
                f"<td class='num-cell'>{row['account_count']:,}</td>"
                f"<td class='num-cell' style='font-weight:600;'>&euro;{row['revenue_at_risk']:,.2f}</td>"
                f"<td class='num-cell'>&euro;{row['avg_rev_per_account']:,.2f}</td></tr>"
            )
        table_html = (
            "<div class='table-container' style='border: 1px solid #E2E8F0;'>"
            "<table class='ops-table'>"
            "<thead><tr><th>Market</th><th>Plan Type</th>"
            "<th class='num-cell'>Flagged Accounts</th>"
            "<th class='num-cell'>Revenue at Risk</th>"
            "<th class='num-cell'>Mean Exposure</th></tr></thead>"
            f"<tbody>{''.join(mkt_rows)}</tbody>"
            "</table></div>"
        )
        st.markdown(table_html, unsafe_allow_html=True)

        # Dynamic Audit Note computation
        market_plan_ranked = market_agg.sort_values(by="revenue_at_risk", ascending=False)
        top_segment = market_plan_ranked.iloc[0]
        top_mkt = top_segment["market"]
        top_plan = top_segment["plan_type"]
        top_rev = top_segment["revenue_at_risk"]
        top_accounts = top_segment["account_count"]
        top_pct = (top_rev / total_rev_at_risk * 100.0) if total_rev_at_risk > 0 else 0.0

        # Dynamic check of highest volume market
        sec_vol_segment = market_agg.sort_values(by="account_count", ascending=False).iloc[0]
        sec_mkt = sec_vol_segment["market"]
        sec_plan = sec_vol_segment["plan_type"]
        sec_count = sec_vol_segment["account_count"]

        audit_note_html = (
            "<div style='margin-top: 10px; padding: 12px 16px; background: #FFFFFF; border: 1px solid #E2E8F0; font-size: 0.73rem; color: #475569; line-height: 1.5;'>"
            "<span style='font-weight: 700; color: #0F172A;'>DYNAMIC AUDIT NOTE:</span> "
            f"{top_mkt} {top_plan} represents the single largest financial exposure at "
            f"<span style=\"font-family:'JetBrains Mono', monospace; font-weight:700; color:#0F172A;\">&euro;{top_rev:,.2f}</span> "
            f"({top_pct:.1f}% of global queue exposure across {top_accounts} accounts). "
            f"Highest case concentration occurs in {sec_mkt} {sec_plan} with {sec_count} flagged accounts undergoing active retention triage."
            "</div>"
        )
        st.markdown(audit_note_html, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION: DATA QUARANTINE BREAKDOWN & GOVERNANCE AUDIT
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div class="section-header">
            <span class="section-title">DATA GOVERNANCE & QUARANTINE DEAD-LETTER AUDIT</span>
            <span class="section-annotation">INGESTION QUALITY GATE &bull; 3GPP CDR & BILLING VALIDATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_qchart, col_qdetails = st.columns([7, 5])

    with col_qchart:
        quarantine_sorted = quarantine_data.sort_values(by="records_quarantined", ascending=True)

        fig_quarantine = go.Figure(go.Bar(
            x=quarantine_sorted["records_quarantined"],
            y=quarantine_sorted["quarantine_reason"],
            orientation="h",
            marker=dict(
                color=["#CBD5E1", "#475569", "#E60000", "#991B1B"][:len(quarantine_sorted)],
                line=dict(color="#0F172A", width=0.5),
            ),
            text=[f"{v:,} records" for v in quarantine_sorted["records_quarantined"]],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(family="JetBrains Mono", size=11, color="#FFFFFF"),
        ))

        fig_quarantine.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=10, r=20, t=10, b=30),
            height=280,
            font=dict(family="Inter", size=11, color="#0F172A"),
            xaxis=dict(
                showgrid=True,
                gridcolor="#F1F5F9",
                linecolor="#CBD5E1",
                tickfont=dict(family="JetBrains Mono", size=10, color="#64748B"),
                title=dict(text="QUARANTINED EVENT COUNT", font=dict(size=10, family="Inter", color="#64748B")),
            ),
            yaxis=dict(
                showgrid=False,
                linecolor="#CBD5E1",
                tickfont=dict(family="JetBrains Mono", size=10, color="#0F172A"),
            ),
        )
        st.plotly_chart(fig_quarantine, use_container_width=True, config={"displayModeBar": False})

    with col_qdetails:
        q_rows = []
        for _, r in quarantine_data.iterrows():
            sev_class = "delta-alert" if r["severity"] in ["CRITICAL", "HIGH"] else "delta-neutral"
            q_rows.append(
                f"<tr><td style=\"font-family:'JetBrains Mono'; font-size:0.70rem;\">{r['quarantine_reason']}</td>"
                f"<td><span class='delta-tag {sev_class}'>{r['severity']}</span></td>"
                f"<td class='num-cell'>{r['records_quarantined']:,}</td>"
                f"<td class='num-cell'>{r['sla_hours']}h</td></tr>"
            )
        q_table = (
            "<div class='table-container' style='border: 1px solid #E2E8F0;'>"
            "<table class='ops-table'>"
            "<thead><tr><th>Validation Check</th><th>Severity</th>"
            "<th class='num-cell'>Count</th><th class='num-cell'>SLA</th></tr></thead>"
            f"<tbody>{''.join(q_rows)}</tbody>"
            "</table></div>"
        )
        st.markdown(q_table, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. PAGE 2: RETENTION OPERATIONS QUEUE (INTERACTIVE & LIVE-UPDATABLE)
# -----------------------------------------------------------------------------
elif page_selection == "02 · RETENTION QUEUE":
    st.markdown(
        """
        <div class="section-header" style="margin-top: 4px;">
            <span class="section-title">ACTIVE RETENTION INTERVENTION QUEUE</span>
            <span class="section-annotation">PRIORITY: HIGH EXPOSURE REVENUE &bull; REAL-TIME TICKET DISPATCH</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # High-Density Filter Toolbar
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2, 2, 2, 3, 3])

    with f_col1:
        selected_market = st.selectbox(
            "MARKET",
            options=["ALL MARKETS", "UK", "DE", "IN"],
            index=0,
            key="queue_mkt_filter",
        )

    with f_col2:
        selected_plan = st.selectbox(
            "PLAN TYPE",
            options=["ALL PLANS", "Postpaid", "Prepaid"],
            index=0,
            key="queue_plan_filter",
        )

    with f_col3:
        selected_risk = st.selectbox(
            "RISK TYPE",
            options=["ALL RISKS", "Bill Shock", "Silent Frustration"],
            index=0,
            key="queue_risk_filter",
        )

    with f_col4:
        search_query = st.text_input(
            "SEARCH CUSTOMER ID",
            placeholder="e.g. CUST-UK-00120",
            key="queue_search_input",
        )

    with f_col5:
        max_eur_val = float(flagged_data["revenue_at_risk_eur"].max())
        min_rev_threshold = st.slider(
            "MIN REVENUE AT RISK (€)",
            min_value=0.0,
            max_value=round(max_eur_val, -1) if max_eur_val > 10 else 100.0,
            value=0.0,
            step=10.0,
            key="queue_rev_slider",
        )

    # Filter base dataset
    filtered_df = flagged_data.copy()

    if selected_market != "ALL MARKETS":
        filtered_df = filtered_df[filtered_df["market"] == selected_market]

    if selected_plan != "ALL PLANS":
        filtered_df = filtered_df[filtered_df["plan_type"] == selected_plan]

    if selected_risk != "ALL RISKS":
        filtered_df = filtered_df[filtered_df["risk_type"] == selected_risk]

    if search_query.strip():
        filtered_df = filtered_df[filtered_df["customer_id"].str.contains(search_query.strip(), case=False, na=False)]

    if min_rev_threshold > 0:
        filtered_df = filtered_df[filtered_df["revenue_at_risk_eur"] >= min_rev_threshold]

    # Ensure action_status reflects current session state
    filtered_df["action_status"] = [
        st.session_state["ticket_statuses"].get(cid, "Pending") for cid in filtered_df["customer_id"]
    ]

    filtered_df = filtered_df.sort_values(by="revenue_at_risk_eur", ascending=False).reset_index(drop=True)

    # Operational Live Metrics Calculation
    q_count = len(filtered_df)
    q_total_rev = filtered_df["revenue_at_risk_eur"].sum()
    resolved_mask = filtered_df["action_status"] == "Resolved"
    resolved_count = resolved_mask.sum()
    resolved_revenue = filtered_df.loc[resolved_mask, "revenue_at_risk_eur"].sum()
    in_progress_count = filtered_df["action_status"].isin(["Offer Sent", "Escalated to RAN"]).sum()
    pending_count = (filtered_df["action_status"] == "Pending").sum()

    # Sharp Operational KPI Banner
    rkpi1, rkpi2, rkpi3, rkpi4 = st.columns(4)

    with rkpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">RESOLVED REVENUE PROTECTED</span>
                    <span class="metric-code">LIVE-SAVE-01</span>
                </div>
                <div class="metric-value" style="color: #166534;">&euro;{resolved_revenue:,.2f}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-positive">{resolved_count} PROTECTED</span>
                    <span>of {q_count} filtered</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rkpi2:
        outstanding_exposure = q_total_rev - resolved_revenue
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">OUTSTANDING EXPOSURE</span>
                    <span class="metric-code">EXPOSURE-02</span>
                </div>
                <div class="metric-value">&euro;{outstanding_exposure:,.2f}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-alert">{pending_count + in_progress_count} REMAINING</span>
                    <span>active risk pool</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rkpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">IN PROGRESS (OFFER / RAN)</span>
                    <span class="metric-code">WORKFLOW-03</span>
                </div>
                <div class="metric-value">{in_progress_count}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-neutral">ACTIVE OUTREACH</span>
                    <span>tickets under handling</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rkpi4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-caption">PENDING ACTION</span>
                    <span class="metric-code">PENDING-04</span>
                </div>
                <div class="metric-value">{pending_count}</div>
                <div class="metric-delta">
                    <span class="delta-tag delta-alert">UNTOUCHED</span>
                    <span>immediate dispatch req.</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # High-Density Interactive Data Editor
    editor_cols = [
        "action_status",
        "customer_id",
        "market",
        "plan_type",
        "risk_type",
        "revenue_at_risk_eur",
        "recommended_action",
    ]

    edited_view = st.data_editor(
        filtered_df[editor_cols],
        column_config={
            "action_status": st.column_config.SelectboxColumn(
                "ACTION STATUS",
                help="Update ticket resolution status live in the operations terminal.",
                options=["Pending", "Offer Sent", "Escalated to RAN", "Resolved"],
                required=True,
                width="medium",
            ),
            "customer_id": st.column_config.TextColumn("CUSTOMER ID", disabled=True),
            "market": st.column_config.TextColumn("MARKET", disabled=True, width="small"),
            "plan_type": st.column_config.TextColumn("PLAN TYPE", disabled=True, width="small"),
            "risk_type": st.column_config.TextColumn("RISK CLASSIFICATION", disabled=True),
            "revenue_at_risk_eur": st.column_config.NumberColumn(
                "REVENUE AT RISK (€)",
                format="€%.2f",
                disabled=True,
            ),
            "recommended_action": st.column_config.TextColumn(
                "RECOMMENDED OPERATIONAL ACTION",
                disabled=True,
                width="large",
            ),
        },
        disabled=["customer_id", "market", "plan_type", "risk_type", "revenue_at_risk_eur", "recommended_action"],
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="retention_data_editor",
    )

    # Sync back any edited action statuses into st.session_state
    for _, r in edited_view.iterrows():
        cid = r["customer_id"]
        stat = r["action_status"]
        if st.session_state["ticket_statuses"].get(cid) != stat:
            st.session_state["ticket_statuses"][cid] = stat

    # CSV Export Button for Support Teams (reflecting live statuses)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    export_filename = f"telecomguard_retention_queue_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    csv_payload = edited_view.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=f"EXPORT FILTERED RETENTION QUEUE ({len(edited_view)} RECORDS .CSV)",
        data=csv_payload,
        file_name=export_filename,
        mime="text/csv",
        help="Export flagged accounts with updated live action statuses for CRM campaigns and outbound retention dialers.",
    )


# -----------------------------------------------------------------------------
# 8. PAGE 3: PIPELINE RUNNER & SIMULATOR
# -----------------------------------------------------------------------------
elif page_selection == "03 · PIPELINE SIMULATOR":
    st.markdown(
        """
        <div class="section-header" style="margin-top: 4px;">
            <span class="section-title">SYSTEM BATCH CONTROL & TELEMETRY SIMULATOR</span>
            <span class="section-annotation">ORCHESTRATION GATEWAY &bull; BIGQUERY ETL RUNNER &bull; MONTE CARLO STRESS TEST</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sim_col1, sim_col2 = st.columns([6, 6])

    with sim_col1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 18px 20px; border-radius: 2px;">
                <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #0F172A; margin-bottom: 8px;">
                    TELEMETRY SCENARIO SIMULATION PARAMETERS
                </div>
                <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 16px; line-height: 1.4;">
                    Inject synthetic operational stress factors into raw telemetry before triggering the daily warehouse ETL procedure.
                </div>
            """,
            unsafe_allow_html=True,
        )

        roaming_surge = st.slider(
            "ROAMING TARIFF SURGE MULTIPLIER",
            min_value=1.0,
            max_value=3.5,
            value=1.0,
            step=0.1,
            format="%.1fx",
            help="Simulates travel season / cross-border holiday surge by escalating out-of-bundle tariffs on roaming subscriber logs.",
        )

        latency_offset = st.slider(
            "RAN NETWORK LATENCY DEGRADATION OFFSET",
            min_value=0.0,
            max_value=120.0,
            value=0.0,
            step=10.0,
            format="+%.0f ms",
            help="Simulates radio access network (RAN) sector congestion or backhaul latency degradation across cell towers.",
        )

        st.markdown(
            f"""
            <div style="margin-top: 14px; padding: 10px 14px; background: #F8FAFC; border: 1px solid #E2E8F0; font-size: 0.72rem; color: #475569;">
                <span style="font-weight: 700; color: #0F172A;">SCENARIO IMPACT:</span>
                Roaming Surcharges at <span style="font-family:'JetBrains Mono'; font-weight:700;">{roaming_surge:.1f}x</span> nominal rate.
                Cell tower ping latencies elevated by <span style="font-family:'JetBrains Mono'; font-weight:700;">+{latency_offset:.0f} ms</span>.
                Expected to trigger elevated Bill Shock and Silent Frustration alerts across sensitive cohorts.
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        btn_c1, btn_c2 = st.columns([6, 6])
        with btn_c1:
            run_btn = st.button("RUN DAILY ETL BATCH", use_container_width=True)
        with btn_c2:
            reset_btn = st.button("RESET TO BASELINE TELEMETRY", use_container_width=True)

    with sim_col2:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 18px 20px; border-radius: 2px; height: 100%;">
                <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #0F172A; margin-bottom: 8px;">
                    ORCHESTRATION PIPELINE SPECIFICATIONS
                </div>
                <div style="font-size: 0.72rem; color: #475569; line-height: 1.6;">
                    <strong>TARGET ENGINE:</strong> Google BigQuery Sandbox ($0 Tier Free Warehouse)<br/>
                    <strong>EXECUTION ENTRYPOINT:</strong> <code>src/run_local_etl.py</code><br/>
                    <strong>TRANSFORMATION PHASES:</strong>
                    <ol style="margin-top: 4px; padding-left: 20px;">
                        <li><strong>Step 1:</strong> Data Quality Audit & Quarantine Filter (2,500 errors isolated)</li>
                        <li><strong>Step 2:</strong> Clean Fact Table Generation with Multi-Currency EUR Pegs</li>
                        <li><strong>Step 3:</strong> Rolling 7-Day Windowing & 7-Day Suppression Alert Mart</li>
                    </ol>
                    <strong>IDEMPOTENCY:</strong> 100% CTAS / Zero DML updates. Fully compatible with enterprise cron orchestrators.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Execution Handler
    if run_btn or reset_btn:
        logs_path = os.path.join("data", "raw_usage_logs.csv")
        backup_path = os.path.join("data", "raw_usage_logs_baseline.csv")

        # Create pristine baseline backup if it doesn't already exist
        if os.path.exists(logs_path) and not os.path.exists(backup_path):
            try:
                shutil.copyfile(logs_path, backup_path)
            except Exception:
                pass

        if reset_btn and os.path.exists(backup_path):
            shutil.copyfile(backup_path, logs_path)
            st.info("Raw telemetry restored to pristine baseline.")

        elif run_btn and (roaming_surge > 1.0 or latency_offset > 0.0) and os.path.exists(backup_path):
            # Apply simulation parameters from pristine baseline
            df_sim = pd.read_csv(backup_path)
            if roaming_surge > 1.0:
                roaming_mask = df_sim["is_roaming"] == True
                df_sim.loc[roaming_mask, "charge_amount"] = (
                    df_sim.loc[roaming_mask, "charge_amount"] * roaming_surge
                ).round(2)
                df_sim.loc[roaming_mask, "daily_spend_local"] = df_sim.loc[roaming_mask, "charge_amount"]

            if latency_offset > 0.0:
                valid_lat_mask = df_sim["latency_ms"] >= 0
                df_sim.loc[valid_lat_mask, "latency_ms"] = (
                    df_sim.loc[valid_lat_mask, "latency_ms"] + latency_offset
                ).round(1)

            df_sim.to_csv(logs_path, index=False)

        # Trigger run_local_etl.py
        with st.spinner("Executing TelecomGuard Daily ETL Batch (src/run_local_etl.py)..."):
            try:
                res = subprocess.run(
                    [sys.executable, "src/run_local_etl.py"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                stdout_log = res.stdout
                st.session_state["etl_execution_log"] = stdout_log
                st.session_state["last_etl_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                st.success("ETL Pipeline completed successfully! Data refreshed across all terminal views.")
                st.rerun()
            except Exception as e:
                st.error(f"ETL execution encountered an error: {e}")
                if hasattr(e, "stdout") and e.stdout:
                    st.session_state["etl_execution_log"] = e.stdout

    # Render terminal output log if available
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-header">
            <span class="section-title">ETL EXECUTION TERMINAL STDOUT LOG</span>
            <span class="section-annotation">STREAMS: AUDIT QUARANTINE &bull; FACT TABLE &bull; ACTION MART</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    log_display = st.session_state.get("etl_execution_log")
    if not log_display:
        log_display = """[TELECOMGUARD ORCHESTRATION READY]
Click 'RUN DAILY ETL BATCH' above to trigger src/run_local_etl.py in real-time.
Logs will stream directly to this audit console upon pipeline execution."""

    st.markdown(f'<div class="terminal-console">{log_display}</div>', unsafe_allow_html=True)
