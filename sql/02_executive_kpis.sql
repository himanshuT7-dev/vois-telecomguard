-- =====================================================================================
-- TelecomGuard Cloud Data Warehouse - Executive KPIs & Operational Mart Queries
-- Dataset: vois_telecomguard
-- Target Platform: Google BigQuery Sandbox ($0 No-Billing Free Tier)
--
-- CRITICAL ARCHITECTURAL CONSTRAINT:
-- BigQuery Sandbox strictly forbids DML (INSERT, UPDATE, DELETE, MERGE).
-- All queries below are 100% read-only analytical queries or CREATE OR REPLACE VIEW 
-- definitions optimized for cost-free execution in BigQuery Sandbox.
-- =====================================================================================

-- =====================================================================================
-- KPI 1: REVENUE AT RISK BY MARKET & PLAN TYPE
-- Purpose: Executive roll-up providing visibility into revenue exposure across operating
--          markets (DE, UK, IT, ES, etc.) and customer segments (Postpaid vs. Prepaid).
-- =====================================================================================

CREATE OR REPLACE VIEW `vois_telecomguard.v_kpi_revenue_at_risk_by_market` AS
SELECT
  a.market_code,
  a.plan_type,
  COUNT(DISTINCT a.customer_id) AS impacted_customers,
  COUNT(1) AS total_active_alerts,
  ROUND(SUM(a.revenue_at_risk_eur), 2) AS total_revenue_at_risk_eur,
  ROUND(
    SUM(IF(a.alert_type = 'BILL_SHOCK', a.revenue_at_risk_eur, 0.0)), 
    2
  ) AS bill_shock_revenue_at_risk_eur,
  ROUND(
    SUM(IF(a.alert_type = 'SILENT_NETWORK_FRUSTRATION', a.revenue_at_risk_eur, 0.0)), 
    2
  ) AS silent_frustration_revenue_at_risk_eur,
  COUNTIF(a.severity = 'CRITICAL') AS critical_severity_alerts,
  COUNTIF(a.severity = 'HIGH') AS high_severity_alerts,
  ROUND(
    SUM(a.revenue_at_risk_eur) / NULLIF(COUNT(DISTINCT a.customer_id), 0), 
    2
  ) AS avg_revenue_at_risk_per_customer_eur,
  ROUND(
    100.0 * SUM(a.revenue_at_risk_eur) / NULLIF(SUM(SUM(a.revenue_at_risk_eur)) OVER (), 0),
    2
  ) AS pct_of_global_revenue_at_risk
FROM `vois_telecomguard.mart_customer_alerts` a
WHERE a.is_suppressed = FALSE
GROUP BY a.market_code, a.plan_type
ORDER BY total_revenue_at_risk_eur DESC;

-- -------------------------------------------------------------------------------------
-- Ready-to-Run Analytical Query 1: Revenue at Risk by Market & Plan Type
-- -------------------------------------------------------------------------------------
SELECT
  market_code,
  plan_type,
  impacted_customers,
  total_active_alerts,
  total_revenue_at_risk_eur,
  bill_shock_revenue_at_risk_eur,
  silent_frustration_revenue_at_risk_eur,
  critical_severity_alerts,
  high_severity_alerts,
  avg_revenue_at_risk_per_customer_eur,
  pct_of_global_revenue_at_risk
FROM `vois_telecomguard.v_kpi_revenue_at_risk_by_market`;


-- =====================================================================================
-- KPI 2: DATA QUALITY PASS RATE % & ANOMALY QUARANTINE METRICS
-- Purpose: Monitors pipeline reliability, measuring clean records passing to fact_daily_usage
--          against quarantined records in audit_data_quality_errors, with failure taxonomy.
-- =====================================================================================

CREATE OR REPLACE VIEW `vois_telecomguard.v_kpi_data_quality_metrics` AS
WITH clean_counts AS (
  SELECT
    COUNT(1) AS clean_record_count
  FROM `vois_telecomguard.fact_daily_usage`
),
quarantine_counts AS (
  SELECT
    COUNT(1) AS quarantined_record_count,
    COUNTIF(STRPOS(dq_failure_reason, 'MISSING_TOWER_ID') > 0 OR STRPOS(dq_failure_reason, 'NULL_TOWER_ID') > 0) AS missing_tower_id_count,
    COUNTIF(STRPOS(dq_failure_reason, 'NEGATIVE_LATENCY') > 0) AS negative_latency_count,
    COUNTIF(STRPOS(dq_failure_reason, 'DUPLICATE_RECORD_ID') > 0) AS duplicate_record_count,
    COUNTIF(STRPOS(dq_failure_reason, ';') > 0) AS multiple_defects_count
  FROM `vois_telecomguard.audit_data_quality_errors`
),
pipeline_volume AS (
  SELECT
    c.clean_record_count,
    q.quarantined_record_count,
    (c.clean_record_count + q.quarantined_record_count) AS total_records_evaluated,
    q.missing_tower_id_count,
    q.negative_latency_count,
    q.duplicate_record_count,
    q.multiple_defects_count
  FROM clean_counts c
  CROSS JOIN quarantine_counts q
)
SELECT
  total_records_evaluated,
  clean_record_count AS clean_records_passed,
  quarantined_record_count AS quarantined_records_failed,
  ROUND(
    100.0 * clean_record_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS dq_pass_rate_pct,
  ROUND(
    100.0 * quarantined_record_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS dq_quarantine_rate_pct,
  missing_tower_id_count,
  ROUND(
    100.0 * missing_tower_id_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS missing_tower_id_pct,
  negative_latency_count,
  ROUND(
    100.0 * negative_latency_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS negative_latency_pct,
  duplicate_record_count,
  ROUND(
    100.0 * duplicate_record_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS duplicate_record_pct,
  multiple_defects_count,
  ROUND(
    100.0 * multiple_defects_count / NULLIF(total_records_evaluated, 0), 
    2
  ) AS multiple_defects_pct
FROM pipeline_volume;

-- -------------------------------------------------------------------------------------
-- Ready-to-Run Analytical Query 2A: Overall Data Quality Health
-- -------------------------------------------------------------------------------------
SELECT
  total_records_evaluated,
  clean_records_passed,
  quarantined_records_failed,
  dq_pass_rate_pct,
  dq_quarantine_rate_pct,
  missing_tower_id_count,
  missing_tower_id_pct,
  negative_latency_count,
  negative_latency_pct,
  duplicate_record_count,
  duplicate_record_pct
FROM `vois_telecomguard.v_kpi_data_quality_metrics`;

-- -------------------------------------------------------------------------------------
-- Ready-to-Run Analytical Query 2B: Daily Data Quality Pass Rate Trend
-- Slices pass rate by usage_date to detect telemetry sensor degradation over time.
-- -------------------------------------------------------------------------------------
WITH daily_clean AS (
  SELECT
    usage_date,
    COUNT(1) AS daily_clean_count
  FROM `vois_telecomguard.fact_daily_usage`
  GROUP BY usage_date
),
daily_quarantine AS (
  SELECT
    usage_date,
    COUNT(1) AS daily_quarantine_count,
    COUNTIF(STRPOS(dq_failure_reason, 'MISSING_TOWER_ID') > 0 OR STRPOS(dq_failure_reason, 'NULL_TOWER_ID') > 0) AS daily_missing_tower_id,
    COUNTIF(STRPOS(dq_failure_reason, 'NEGATIVE_LATENCY') > 0) AS daily_negative_latency,
    COUNTIF(STRPOS(dq_failure_reason, 'DUPLICATE_RECORD_ID') > 0) AS daily_duplicates
  FROM `vois_telecomguard.audit_data_quality_errors`
  GROUP BY usage_date
),
daily_combined AS (
  SELECT
    COALESCE(c.usage_date, q.usage_date) AS usage_date,
    COALESCE(c.daily_clean_count, 0) AS clean_count,
    COALESCE(q.daily_quarantine_count, 0) AS quarantine_count,
    (COALESCE(c.daily_clean_count, 0) + COALESCE(q.daily_quarantine_count, 0)) AS total_evaluated,
    COALESCE(q.daily_missing_tower_id, 0) AS missing_tower_id_count,
    COALESCE(q.daily_negative_latency, 0) AS negative_latency_count,
    COALESCE(q.daily_duplicates, 0) AS duplicate_record_count
  FROM daily_clean c
  FULL OUTER JOIN daily_quarantine q
    ON c.usage_date = q.usage_date
)
SELECT
  usage_date,
  total_evaluated,
  clean_count AS passed_records,
  quarantine_count AS quarantined_records,
  ROUND(100.0 * clean_count / NULLIF(total_evaluated, 0), 2) AS daily_pass_rate_pct,
  missing_tower_id_count,
  negative_latency_count,
  duplicate_record_count
FROM daily_combined
ORDER BY usage_date DESC;


-- =====================================================================================
-- KPI 3: TOP RETENTION ACTION QUEUE
-- Purpose: Real-time operational worklist for Retention Managers, Care Specialists, 
--          and CRM Automation. Prioritizes customers with highest revenue at risk,
--          providing prescriptive Postpaid vs. Prepaid mitigation actions.
-- =====================================================================================

CREATE OR REPLACE VIEW `vois_telecomguard.v_kpi_top_retention_action_queue` AS
SELECT
  DENSE_RANK() OVER (
    ORDER BY a.revenue_at_risk_eur DESC, a.alert_date DESC
  ) AS global_priority_rank,
  DENSE_RANK() OVER (
    PARTITION BY a.market_code 
    ORDER BY a.revenue_at_risk_eur DESC, a.alert_date DESC
  ) AS market_priority_rank,
  a.alert_id,
  a.alert_date,
  a.customer_id,
  a.customer_name,
  a.market_code,
  a.plan_type,
  a.alert_type,
  a.severity,
  a.revenue_at_risk_eur,
  a.trigger_metric_value,
  a.threshold_metric_value,
  a.normal_monthly_spend_eur,
  a.recommended_action,
  COALESCE(CAST(a.days_since_previous_alert AS STRING), 'FIRST_ALERT') AS days_since_last_alert,
  a.generated_at
FROM `vois_telecomguard.mart_customer_alerts` a
WHERE a.is_suppressed = FALSE
ORDER BY a.revenue_at_risk_eur DESC;

-- -------------------------------------------------------------------------------------
-- Ready-to-Run Analytical Query 3A: Top 50 Global Retention Action Queue
-- -------------------------------------------------------------------------------------
SELECT
  global_priority_rank,
  market_priority_rank,
  alert_date,
  customer_id,
  customer_name,
  market_code,
  plan_type,
  alert_type,
  severity,
  revenue_at_risk_eur,
  trigger_metric_value,
  threshold_metric_value,
  recommended_action
FROM `vois_telecomguard.v_kpi_top_retention_action_queue`
ORDER BY global_priority_rank ASC
LIMIT 50;

-- -------------------------------------------------------------------------------------
-- Ready-to-Run Analytical Query 3B: Retention Action Summary by Prescribed Intervention
-- Rolls up customer volume and financial exposure per specific retention action.
-- -------------------------------------------------------------------------------------
SELECT
  a.market_code,
  a.plan_type,
  a.alert_type,
  a.recommended_action,
  COUNT(DISTINCT a.customer_id) AS distinct_customers_targeted,
  COUNT(1) AS total_action_items,
  ROUND(SUM(a.revenue_at_risk_eur), 2) AS total_revenue_protected_eur,
  ROUND(AVG(a.revenue_at_risk_eur), 2) AS avg_revenue_per_customer_eur
FROM `vois_telecomguard.mart_customer_alerts` a
WHERE a.is_suppressed = FALSE
GROUP BY a.market_code, a.plan_type, a.alert_type, a.recommended_action
ORDER BY total_revenue_protected_eur DESC;
