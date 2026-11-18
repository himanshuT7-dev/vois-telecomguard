-- =====================================================================================
-- TelecomGuard Cloud Data Warehouse - Daily ETL Stored Procedure
-- Dataset: vois_telecomguard
-- Target Platform: Google BigQuery Sandbox ($0 No-Billing Free Tier)
-- 
-- CRITICAL ARCHITECTURAL CONSTRAINT:
-- BigQuery Sandbox strictly forbids DML statements (INSERT, UPDATE, DELETE, MERGE).
-- Every transformation in this procedure strictly adheres to CTAS 
-- (`CREATE OR REPLACE TABLE ... AS SELECT`) and `CREATE OR REPLACE VIEW`.
-- =====================================================================================

CREATE OR REPLACE PROCEDURE `vois_telecomguard.sp_run_daily_etl`()
BEGIN
  -- -----------------------------------------------------------------------------------
  -- STEP 1: AUDIT DATA QUALITY ERRORS (Quarantine Table)
  -- Quarantines malformed rows:
  --   1. tower_id IS NULL OR TRIM(tower_id) = '' (Network telemetry loss)
  --   2. latency_ms < 0 (Clock drift / sensor corruption)
  --   3. duplicate record_id (via ROW_NUMBER() OVER (PARTITION BY record_id ORDER BY date DESC) > 1)
  -- Generates explicit, semicolon-delimited `dq_failure_reason` tags for operational triage.
  -- -----------------------------------------------------------------------------------
  CREATE OR REPLACE TABLE `vois_telecomguard.audit_data_quality_errors` AS
  WITH raw_standardized AS (
    SELECT
      r.record_id,
      r.customer_id,
      CAST(r.date AS DATE) AS usage_date,
      CAST(r.date AS DATE) AS `date`,
      r.country AS market_code,
      r.country AS country,
      r.tower_id,
      r.latency_ms,
      COALESCE(r.is_roaming, FALSE) AS is_roaming,
      r.roaming_country,
      COALESCE(r.data_used_mb, 0.0) AS data_used_mb,
      COALESCE(r.voice_minutes, 0.0) AS voice_minutes,
      COALESCE(r.sms_count, 0) AS sms_count,
      COALESCE(r.daily_spend_local, 0.0) AS daily_spend_local,
      COALESCE(r.currency, 'EUR') AS currency,
      COALESCE(r.packet_loss_pct, 0.0) AS packet_loss_pct,
      COALESCE(r.open_support_tickets, 0) AS open_support_tickets,
      ROW_NUMBER() OVER (
        PARTITION BY r.record_id 
        ORDER BY CAST(r.date AS DATE) DESC
      ) AS record_rank
    FROM `vois_telecomguard.raw_usage_logs` r
  ),
  quarantine_evaluated AS (
    SELECT
      r.*,
      ARRAY_TO_STRING([
        IF(r.record_rank > 1, 'DUPLICATE_RECORD_ID', NULL),
        IF(r.tower_id IS NULL OR TRIM(r.tower_id) = '', 'NULL_TOWER_ID', NULL),
        IF(r.latency_ms < 0, 'NEGATIVE_LATENCY', NULL)
      ], '; ') AS dq_failure_reason,
      CASE
        WHEN r.record_rank > 1 AND (r.tower_id IS NULL OR TRIM(r.tower_id) = '') AND r.latency_ms < 0 THEN 'MULTIPLE_ERRORS'
        WHEN r.record_rank > 1 THEN 'DUPLICATE_RECORD_ID'
        WHEN r.tower_id IS NULL OR TRIM(r.tower_id) = '' THEN 'NULL_TOWER_ID'
        WHEN r.latency_ms < 0 THEN 'NEGATIVE_LATENCY'
        ELSE 'VALID'
      END AS error_type,
      CURRENT_TIMESTAMP() AS quarantined_at,
      CURRENT_TIMESTAMP() AS detected_at
    FROM raw_standardized r
  )
  SELECT
    record_id,
    customer_id,
    `date`,
    usage_date,
    country,
    market_code,
    tower_id,
    latency_ms,
    is_roaming,
    roaming_country,
    data_used_mb,
    voice_minutes,
    sms_count,
    daily_spend_local,
    currency,
    packet_loss_pct,
    open_support_tickets,
    record_rank,
    dq_failure_reason,
    error_type,
    CONCAT('Data Quality Quarantine: ', dq_failure_reason) AS error_details,
    quarantined_at,
    detected_at
  FROM quarantine_evaluated
  WHERE dq_failure_reason != '';

  -- -----------------------------------------------------------------------------------
  -- STEP 2: FACT DAILY USAGE (Clean Warehouse Table)
  -- Specifications:
  --   - Partitioned by: date
  --   - Clustered by: customer_id
  --   - Only clean records: record_rank = 1, tower_id IS NOT NULL, latency_ms >= 0
  --   - Currency conversion: charge_eur / daily_spend_eur converted via dim_exchange_rates
  -- -----------------------------------------------------------------------------------
  CREATE OR REPLACE TABLE `vois_telecomguard.fact_daily_usage`
  PARTITION BY date
  CLUSTER BY customer_id
  AS
  WITH raw_standardized AS (
    SELECT
      r.record_id,
      r.customer_id,
      CAST(r.date AS DATE) AS `date`,
      CAST(r.date AS DATE) AS usage_date,
      r.country,
      r.country AS market_code,
      r.tower_id,
      r.latency_ms,
      COALESCE(r.is_roaming, FALSE) AS is_roaming,
      r.roaming_country,
      COALESCE(r.data_used_mb, 0.0) AS data_used_mb,
      COALESCE(r.voice_minutes, 0.0) AS voice_minutes,
      COALESCE(r.sms_count, 0) AS sms_count,
      COALESCE(r.daily_spend_local, 0.0) AS daily_spend_local,
      COALESCE(r.currency, 'EUR') AS currency,
      COALESCE(r.packet_loss_pct, 0.0) AS packet_loss_pct,
      COALESCE(r.open_support_tickets, 0) AS open_support_tickets,
      ROW_NUMBER() OVER (
        PARTITION BY r.record_id 
        ORDER BY CAST(r.date AS DATE) DESC
      ) AS record_rank
    FROM `vois_telecomguard.raw_usage_logs` r
  ),
  clean_logs AS (
    SELECT
      r.*
    FROM raw_standardized r
    WHERE r.record_rank = 1
      AND r.tower_id IS NOT NULL 
      AND TRIM(r.tower_id) != ''
      AND r.latency_ms >= 0
  )
  SELECT
    c.record_id,
    c.customer_id,
    c.date,
    c.usage_date,
    COALESCE(cust.country, c.country) AS country,
    COALESCE(cust.country, c.country) AS market_code,
    c.tower_id,
    c.latency_ms,
    c.is_roaming,
    c.roaming_country,
    c.data_used_mb,
    c.voice_minutes,
    c.sms_count,
    c.daily_spend_local,
    c.daily_spend_local AS charge_amount,
    c.currency,
    c.currency AS local_currency,
    COALESCE(xr.fx_rate_to_eur, 1.0) AS exchange_rate_to_eur,
    ROUND(
      CAST(c.daily_spend_local * COALESCE(xr.fx_rate_to_eur, 1.0) AS NUMERIC), 
      4
    ) AS charge_eur,
    ROUND(
      CAST(c.daily_spend_local * COALESCE(xr.fx_rate_to_eur, 1.0) AS NUMERIC), 
      4
    ) AS daily_spend_eur,
    c.packet_loss_pct,
    c.open_support_tickets,
    CURRENT_TIMESTAMP() AS etl_loaded_at
  FROM clean_logs c
  LEFT JOIN `vois_telecomguard.dim_customers` cust
    ON c.customer_id = cust.customer_id
  LEFT JOIN `vois_telecomguard.dim_exchange_rates` xr
    ON c.currency = xr.currency_code;

  -- -----------------------------------------------------------------------------------
  -- STEP 3: MART CUSTOMER ALERTS (Actionable Retention & Risk Mart)
  -- Specifications:
  --   - Partitioned by: alert_date
  --   - Clustered by: risk_category, country
  --   - Bill Shock Detection:
  --       Rolling 7-day spend extrapolated to 30 days > 1.35 * normal_monthly_spend_eur
  --       ((last_7d_spend / 7) * 30) > 1.35 * normal_monthly_spend_eur
  --   - Silent Network Frustration Detection:
  --       3 consecutive days with latency_ms > 180ms AND open_support_tickets = 0
  --       via LAG(latency_ms, 1) and LAG(latency_ms, 2)
  --   - Includes:
  --       * revenue_at_risk_eur: Estimated monthly billing/spend at risk of churn
  --       * Tailored Postpaid vs. Prepaid recommended_action
  --       * 7-day duplicate-alert suppression filter (cooldown per customer & alert type)
  -- -----------------------------------------------------------------------------------
  CREATE OR REPLACE TABLE `vois_telecomguard.mart_customer_alerts`
  PARTITION BY alert_date
  CLUSTER BY risk_category, country
  AS
  WITH customer_daily_usage AS (
    -- Aggregate daily usage per customer to ensure strict calendar-day grain
    SELECT
      f.customer_id,
      f.country,
      f.market_code,
      f.date,
      f.usage_date,
      SUM(f.daily_spend_eur) AS daily_spend_eur,
      AVG(f.latency_ms) AS daily_avg_latency_ms,
      MAX(IF(f.is_roaming, 1, 0)) AS has_roaming,
      MAX(f.open_support_tickets) AS open_support_tickets
    FROM `vois_telecomguard.fact_daily_usage` f
    GROUP BY f.customer_id, f.country, f.market_code, f.date, f.usage_date
  ),
  customer_rolling_metrics AS (
    SELECT
      s.customer_id,
      s.country,
      s.market_code,
      s.date,
      s.usage_date,
      s.daily_spend_eur,
      s.daily_avg_latency_ms,
      s.has_roaming,
      s.open_support_tickets,
      -- BigQuery-compatible rolling 7-day sum using integer day offset
      SUM(s.daily_spend_eur) OVER (
        PARTITION BY s.customer_id
        ORDER BY UNIX_DATE(s.date)
        RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
      ) AS last_7d_spend_eur,
      -- Lagged latencies and dates for Silent Network Frustration detection
      LAG(s.daily_avg_latency_ms, 1) OVER (
        PARTITION BY s.customer_id
        ORDER BY s.date
      ) AS prev_day_1_latency_ms,
      LAG(s.daily_avg_latency_ms, 2) OVER (
        PARTITION BY s.customer_id
        ORDER BY s.date
      ) AS prev_day_2_latency_ms,
      LAG(s.date, 1) OVER (
        PARTITION BY s.customer_id
        ORDER BY s.date
      ) AS prev_day_1_date,
      LAG(s.date, 2) OVER (
        PARTITION BY s.customer_id
        ORDER BY s.date
      ) AS prev_day_2_date
    FROM customer_daily_usage s
  ),
  enriched_customer_windows AS (
    SELECT
      m.customer_id,
      COALESCE(cust.name, 'Valued Customer') AS customer_name,
      m.country,
      m.market_code,
      UPPER(COALESCE(cust.contract_type, 'POSTPAID')) AS plan_type,
      COALESCE(cust.contract_type, 'Postpaid') AS contract_type,
      m.date,
      m.usage_date,
      m.daily_spend_eur,
      m.daily_avg_latency_ms,
      m.has_roaming,
      m.last_7d_spend_eur,
      m.prev_day_1_latency_ms,
      m.prev_day_2_latency_ms,
      m.prev_day_1_date,
      m.prev_day_2_date,
      cust.normal_monthly_spend_eur,
      COALESCE(m.open_support_tickets, 0) AS open_support_tickets
    FROM customer_rolling_metrics m
    JOIN `vois_telecomguard.dim_customers` cust
      ON m.customer_id = cust.customer_id
  ),
  raw_alert_candidates AS (
    -- ---------------------------------------------------------------------------------
    -- Trigger 1: Bill Shock / Balance Burn
    -- ((last_7d_spend / 7) * 30) > 1.35 * normal_monthly_spend_eur
    -- ---------------------------------------------------------------------------------
    SELECT
      GENERATE_UUID() AS alert_id,
      w.date AS alert_date,
      w.customer_id,
      w.customer_name,
      w.market_code,
      w.country,
      w.plan_type,
      w.contract_type,
      'BILL_SHOCK' AS alert_type,
      IF(w.contract_type = 'Prepaid', 'Balance Burn', 'Bill Shock') AS risk_category,
      IF(((w.last_7d_spend_eur / 7.0) * 30.0) > (2.0 * w.normal_monthly_spend_eur), 'CRITICAL', 'HIGH') AS severity,
      IF(((w.last_7d_spend_eur / 7.0) * 30.0) > (2.0 * w.normal_monthly_spend_eur), 'CRITICAL', 'HIGH') AS alert_severity,
      ROUND((w.last_7d_spend_eur / 7.0) * 30.0, 2) AS trigger_metric_value,
      ROUND((w.last_7d_spend_eur / 7.0) * 30.0, 2) AS projected_spend_eur,
      ROUND(1.35 * w.normal_monthly_spend_eur, 2) AS threshold_metric_value,
      ROUND(w.normal_monthly_spend_eur, 2) AS normal_monthly_spend_eur,
      ROUND(((w.last_7d_spend_eur / 7.0) * 30.0) / NULLIF(w.normal_monthly_spend_eur, 0), 2) AS spend_ratio,
      ROUND(w.daily_avg_latency_ms, 2) AS avg_latency_ms,
      0 AS consecutive_bad_network_days,
      w.open_support_tickets,
      ROUND((w.last_7d_spend_eur / 7.0) * 30.0, 2) AS revenue_at_risk_eur,
      CONCAT(
        'Projected 30-day spend of €', 
        CAST(ROUND((w.last_7d_spend_eur / 7.0) * 30.0, 2) AS STRING), 
        ' exceeds 135% of baseline (€', 
        CAST(ROUND(w.normal_monthly_spend_eur, 2) AS STRING), 
        ')'
      ) AS trigger_reason,
      CASE
        WHEN w.contract_type = 'Postpaid' THEN
          'Proactive Billing Care: Issue spend threshold SMS notification; offer plan upgrade or recurring data bolt-on before month-end invoice'
        WHEN w.contract_type = 'Prepaid' THEN
          'Prepaid Burn Care: Send high-consumption SMS alert with discounted 30-day recurring bundle offer to preserve customer balance'
        ELSE
          'Proactive Billing Care: Engage customer regarding elevated consumption rate'
      END AS recommended_action
    FROM enriched_customer_windows w
    WHERE w.normal_monthly_spend_eur > 0
      AND ((w.last_7d_spend_eur / 7.0) * 30.0) > (1.35 * w.normal_monthly_spend_eur)

    UNION ALL

    -- ---------------------------------------------------------------------------------
    -- Trigger 2: Silent Network Frustration
    -- >180ms latency for 3 consecutive days with open_support_tickets = 0
    -- ---------------------------------------------------------------------------------
    SELECT
      GENERATE_UUID() AS alert_id,
      w.date AS alert_date,
      w.customer_id,
      w.customer_name,
      w.market_code,
      w.country,
      w.plan_type,
      w.contract_type,
      'SILENT_NETWORK_FRUSTRATION' AS alert_type,
      'Silent Network Frustration' AS risk_category,
      IF(w.daily_avg_latency_ms > 250.0, 'CRITICAL', 'HIGH') AS severity,
      IF(w.daily_avg_latency_ms > 250.0, 'CRITICAL', 'HIGH') AS alert_severity,
      ROUND(w.daily_avg_latency_ms, 2) AS trigger_metric_value,
      ROUND(w.normal_monthly_spend_eur, 2) AS projected_spend_eur,
      180.0 AS threshold_metric_value,
      ROUND(w.normal_monthly_spend_eur, 2) AS normal_monthly_spend_eur,
      1.00 AS spend_ratio,
      ROUND(w.daily_avg_latency_ms, 2) AS avg_latency_ms,
      3 AS consecutive_bad_network_days,
      w.open_support_tickets,
      ROUND(w.normal_monthly_spend_eur, 2) AS revenue_at_risk_eur,
      CONCAT(
        'Severe network latency (', 
        CAST(ROUND(w.daily_avg_latency_ms, 1) AS STRING), 
        'ms) sustained for 3 consecutive days with 0 open support tickets'
      ) AS trigger_reason,
      CASE
        WHEN w.contract_type = 'Postpaid' THEN
          'VIP Network Care: Initiate proactive account outreach, open network engineering cell check, and credit 10 EUR goodwill loyalty voucher'
        WHEN w.contract_type = 'Prepaid' THEN
          'Network Retention Care: Push automated network APN reconfiguration profile and grant complimentary 5GB 3-day network compensation booster'
        ELSE
          'Network Retention Care: Dispatch cell diagnostic team and offer goodwill data pack'
      END AS recommended_action
    FROM enriched_customer_windows w
    WHERE w.daily_avg_latency_ms > 180.0
      AND w.prev_day_1_latency_ms > 180.0
      AND w.prev_day_2_latency_ms > 180.0
      AND DATE_DIFF(w.date, w.prev_day_1_date, DAY) = 1
      AND DATE_DIFF(w.prev_day_1_date, w.prev_day_2_date, DAY) = 1
      AND w.open_support_tickets = 0
  ),
  alert_first_dates AS (
    SELECT
      a.*,
      MIN(a.alert_date) OVER (
        PARTITION BY a.customer_id, a.alert_type
      ) AS initial_detection_date
    FROM raw_alert_candidates a
  ),
  alert_cooldown_ranked AS (
    SELECT
      f.*,
      -- Partition alerts into 7-day rolling cooldown buckets from initial detection
      DIV(DATE_DIFF(f.alert_date, f.initial_detection_date, DAY), 7) AS suppression_window_id,
      ROW_NUMBER() OVER (
        PARTITION BY f.customer_id, f.alert_type, DIV(DATE_DIFF(f.alert_date, f.initial_detection_date, DAY), 7)
        ORDER BY f.alert_date ASC
      ) AS window_occurrence_rank
    FROM alert_first_dates f
  ),
  unsuppressed_alerts AS (
    SELECT
      r.alert_id,
      r.alert_date,
      r.customer_id,
      r.customer_name,
      r.market_code,
      r.country,
      r.plan_type,
      r.contract_type,
      r.alert_type,
      r.risk_category,
      r.severity,
      r.alert_severity,
      r.trigger_metric_value,
      r.threshold_metric_value,
      r.projected_spend_eur,
      r.normal_monthly_spend_eur,
      r.spend_ratio,
      r.avg_latency_ms,
      r.consecutive_bad_network_days,
      r.open_support_tickets,
      r.revenue_at_risk_eur,
      r.trigger_reason,
      r.recommended_action,
      r.suppression_window_id,
      DATE_DIFF(
        r.alert_date,
        LAG(r.alert_date) OVER (PARTITION BY r.customer_id, r.alert_type ORDER BY r.alert_date),
        DAY
      ) AS days_since_previous_alert,
      FALSE AS is_suppressed,
      CURRENT_TIMESTAMP() AS generated_at
    FROM alert_cooldown_ranked r
    WHERE r.window_occurrence_rank = 1 -- 7-day duplicate-alert suppression filter
  )
  SELECT
    alert_id,
    alert_date,
    customer_id,
    customer_name,
    market_code,
    country,
    plan_type,
    contract_type,
    alert_type,
    risk_category,
    severity,
    alert_severity,
    trigger_metric_value,
    threshold_metric_value,
    projected_spend_eur,
    normal_monthly_spend_eur,
    spend_ratio,
    avg_latency_ms,
    consecutive_bad_network_days,
    open_support_tickets,
    revenue_at_risk_eur,
    trigger_reason,
    recommended_action,
    suppression_window_id,
    days_since_previous_alert,
    is_suppressed,
    generated_at
  FROM unsuppressed_alerts;

END;
