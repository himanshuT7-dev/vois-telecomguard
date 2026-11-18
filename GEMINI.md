# TelecomGuard – Proactive Telco Risk & Retention Pipeline
**VOIS (Vodafone Intelligent Solutions)**

## 1. Project Overview & Architecture
TelecomGuard is an enterprise risk, retention, and customer experience pipeline designed for VOIS operating across multinational markets: **United Kingdom (UK)**, **Germany (DE)**, and **India (IN)**.

The pipeline processes daily telecom network, billing, and roaming telemetry to proactively identify:
1. **Bill Shock / Balance Burn**: Customers traveling abroad incurring excessive roaming tariffs projected to exceed 135% of their typical baseline monthly spend.
2. **Silent Network Frustration**: Customers experiencing severe degraded network performance (latency > 180ms for 3+ consecutive days) who have zero open customer support tickets (high churn risk).
3. **Data Quality Governance**: Automated isolation and auditing of corrupted or malformed telemetry (duplicate records, negative latency, missing cell towers).

---

## 2. Multi-Country FX Normalization Standard
Financial metrics across all operating companies are normalized to **EUR (€)** to ensure unified enterprise reporting and risk evaluation.

| Currency | Market | Pegged / Normalized FX Rate to EUR | Calculation |
| :--- | :--- | :--- | :--- |
| **GBP** | United Kingdom (UK) | **1.1700** | `daily_spend_eur = daily_spend_local * 1.17` |
| **EUR** | Germany (DE) | **1.0000** | `daily_spend_eur = daily_spend_local * 1.00` |
| **INR** | India (IN) | **0.0110** | `daily_spend_eur = daily_spend_local * 0.011` |

---

## 3. Five-Table Star Schema Specification (Google BigQuery)

```
                            +--------------------+
                            | dim_exchange_rates |
                            +--------------------+
                                      |
+---------------+            +------------------+            +----------------------------+
| dim_customers | ---------> | fact_daily_usage | ---------> | audit_data_quality_errors  |
+---------------+            +------------------+            +----------------------------+
       |                              |
       +------------------------------+
                      |
                      v
            +---------------------+
            | mart_customer_alerts|
            +---------------------+
```

### Table 1: `dim_customers`
Dimension table storing customer demographics, subscription details, and baseline historical monthly spend.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | `STRING` | NO | Unique primary key (e.g. `CUST-UK-0001`) |
| `name` | `STRING` | NO | Full customer name |
| `email` | `STRING` | NO | Customer contact email |
| `phone_number` | `STRING` | NO | MSISDN phone number with country code |
| `country` | `STRING` | NO | Country code (`UK`, `DE`, `IN`) |
| `contract_type` | `STRING` | NO | Subscription tier (`Postpaid`, `Prepaid`) |
| `signup_date` | `DATE` | NO | Customer acquisition date |
| `normal_monthly_spend_eur` | `FLOAT64` | NO | Baseline expected monthly expenditure in EUR |
| `device_type` | `STRING` | YES | Primary handset OS / category (`iOS`, `Android`) |

### Table 2: `dim_exchange_rates`
Dimension table maintaining FX currency conversion multipliers into EUR.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `currency_code` | `STRING` | NO | 3-letter currency code (`GBP`, `EUR`, `INR`) |
| `fx_rate_to_eur` | `FLOAT64` | NO | Conversion multiplier into EUR |
| `effective_date` | `DATE` | NO | Effective currency conversion date |

### Table 3: `fact_daily_usage`
Curated fact table containing validated, clean daily telecommunication and network telemetry per customer.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | `STRING` | NO | Unique event log identifier |
| `customer_id` | `STRING` | NO | Reference to `dim_customers.customer_id` |
| `date` | `DATE` | NO | Log timestamp date |
| `country` | `STRING` | NO | Home market code (`UK`, `DE`, `IN`) |
| `is_roaming` | `BOOL` | NO | `TRUE` if subscriber operated outside home market |
| `roaming_country` | `STRING` | YES | Country code visited if roaming; otherwise `NULL` |
| `data_used_mb` | `FLOAT64` | NO | Cellular data volume consumed in megabytes |
| `voice_minutes` | `FLOAT64` | NO | Voice call duration in minutes |
| `sms_count` | `INT64` | NO | Number of SMS messages sent |
| `daily_spend_local` | `FLOAT64` | NO | Total daily billed charges in local currency |
| `currency` | `STRING` | NO | Local currency code (`GBP`, `EUR`, `INR`) |
| `daily_spend_eur` | `FLOAT64` | NO | Normalized daily expenditure in EUR |
| `latency_ms` | `FLOAT64` | NO | Network ping latency in milliseconds |
| `packet_loss_pct` | `FLOAT64` | NO | Cellular packet loss percentage |
| `tower_id` | `STRING` | NO | Cellular cell tower identifier |
| `open_support_tickets` | `INT64` | NO | Active unresolved customer support cases |

### Table 4: `audit_data_quality_errors`
Quarantine table capturing failed or anomalous raw records filtered during the ingestion cleansing step.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | `STRING` | YES | Raw log record ID (may contain duplicates or nulls) |
| `customer_id` | `STRING` | YES | Customer ID from raw log |
| `date` | `DATE` | YES | Event date from raw log |
| `error_type` | `STRING` | NO | Categorical error flag (`NULL_TOWER_ID`, `NEGATIVE_LATENCY`, `DUPLICATE_RECORD_ID`) |
| `error_details` | `STRING` | NO | Diagnostic summary and raw payload details |
| `detected_at` | `TIMESTAMP` | NO | Audit timestamp when error was flagged |

### Table 5: `mart_customer_alerts`
Action-oriented aggregate data mart feeding retention workflows, customer care, and executive dashboards.

| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `alert_id` | `STRING` | NO | Unique alert identifier (e.g. `ALT-202611-0001`) |
| `customer_id` | `STRING` | NO | Reference to `dim_customers.customer_id` |
| `country` | `STRING` | NO | Home country code (`UK`, `DE`, `IN`) |
| `contract_type` | `STRING` | NO | `Postpaid` or `Prepaid` |
| `risk_category` | `STRING` | NO | `Bill Shock`, `Silent Network Frustration`, or `Normal` |
| `alert_severity` | `STRING` | NO | `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` |
| `trigger_reason` | `STRING` | NO | Human-readable explanation of risk trigger |
| `projected_spend_eur` | `FLOAT64` | YES | 30-day projected expenditure in EUR |
| `normal_monthly_spend_eur` | `FLOAT64` | NO | Baseline customer monthly spend in EUR |
| `spend_ratio` | `FLOAT64` | YES | Projected spend divided by normal spend (`projected / normal`) |
| `avg_latency_ms` | `FLOAT64` | YES | Average network latency over degradation window |
| `consecutive_bad_network_days` | `INT64` | YES | Count of consecutive days where `latency_ms > 180` |
| `open_support_tickets` | `INT64` | NO | Open support ticket count (0 indicates silent frustration) |
| `recommended_action` | `STRING` | NO | Proactive intervention recommendation |
| `alert_date` | `DATE` | NO | Date alert was computed |

---

## 4. Google BigQuery Sandbox ($0 Tier) SQL Directives

To strictly adhere to **Google BigQuery Sandbox ($0 tier)** constraints:
1. **Strict DDL Only**: All data transformations, staging layers, audits, and marts MUST use idempotent `CREATE OR REPLACE TABLE \`<project>.<dataset>.<table>\` AS SELECT ...` statements.
2. **Zero DML Updates**: Do **NOT** use `UPDATE`, `DELETE`, or `MERGE` statements which require active billing/quotas and transaction locks.
3. **Partitioning & Clustering**:
   - `fact_daily_usage` should be partitioned by `date` (`PARTITION BY date`) and clustered by `customer_id` (`CLUSTER BY customer_id`).
   - `mart_customer_alerts` should be partitioned by `alert_date` (`PARTITION BY alert_date`) and clustered by `risk_category`, `country`.
4. **Deterministic Windowing**: Risk classification must use standard ANSI SQL window functions (`ROW_NUMBER()`, `LAG()`, `LEAD()`, `AVG() OVER (...)`) compatible with BigQuery Standard SQL.

---

## 5. Risk Detection Logic & Business Rules

### Rule A: Bill Shock & Balance Burn
- **Target Population**: Roaming abroad in the last 7 days of the observation window (`is_roaming = TRUE`).
- **Trigger**: Projected 30-day total spend in EUR exceeds `1.35x` (`135%`) of `dim_customers.normal_monthly_spend_eur`.
  - For **Postpaid**: Flagged as **"Bill Shock Risk"** (unexpected high invoice risk). Recommended action: Send SMS tariff alert & offer temporary roaming data pass.
  - For **Prepaid**: Flagged as **"Balance Burn Risk"** (rapid balance depletion). Recommended action: Proactive low-balance push notification & personalized recharge bonus.

### Rule B: Silent Network Frustration
- **Target Population**: Customers experiencing consecutive network degradation without seeking support.
- **Trigger**:
  - `latency_ms > 180` for **3 or more consecutive days**.
  - `open_support_tickets = 0` (unreported suffering).
- **Flag**: **"Silent Network Frustration"** (churn risk).
- **Recommended Action**: Proactive apology perk (free data pack / VIP retention voucher) & automated diagnostic probe dispatched to local cell tower.

### Rule C: Data Quality Auditing
- **Corrupted Records**:
  - `tower_id IS NULL` OR `tower_id = ''`
  - `latency_ms < 0`
  - Duplicate `record_id` (detected via `ROW_NUMBER() OVER(PARTITION BY record_id ORDER BY date) > 1`)
- **Handling**: Diverted to `audit_data_quality_errors`. Filtered out from `fact_daily_usage`.
