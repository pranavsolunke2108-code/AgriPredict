-- =====================================================================
-- AgriPredict : Phase 4 - Agronomic Advisory, Crop Calendar, and Alerts
-- Run: mysql -u root -p agripredict < agripredict_phase4_advisory.sql
-- =====================================================================

USE agripredict;

-- ---------------------------------------------------------------------
-- 1. Table update: alerts.dedupe_key
-- ---------------------------------------------------------------------
SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'alerts' AND column_name = 'dedupe_key'
);
SET @stmt = IF(@col_exists = 0, 'ALTER TABLE alerts ADD COLUMN dedupe_key VARCHAR(100) NULL UNIQUE', 'SELECT 1');
PREPARE stmt FROM @stmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 2. View: crop_calendar_view
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW crop_calendar_view AS
SELECT
  cc.cycle_id AS cycle_id,
  fm.farm_id AS farm_id,
  f.farmer_id AS farmer_id,
  c.crop_id AS crop_id,
  c.crop_name AS crop_name,
  cs.stage_id AS stage_id,
  cs.stage_name AS stage_name,
  cs.start_day AS start_day,
  cs.end_day AS end_day,
  IF(cc.sowing_date IS NOT NULL, DATE_ADD(cc.sowing_date, INTERVAL cs.start_day DAY), NULL) AS start_date,
  IF(cc.sowing_date IS NOT NULL, DATE_ADD(cc.sowing_date, INTERVAL cs.end_day DAY), NULL) AS end_date,
  CASE
    WHEN cc.sowing_date IS NULL THEN 'Upcoming'
    WHEN CURDATE() > DATE_ADD(cc.sowing_date, INTERVAL cs.end_day DAY) THEN 'Done'
    WHEN CURDATE() < DATE_ADD(cc.sowing_date, INTERVAL cs.start_day DAY) THEN 'Upcoming'
    ELSE 'Current'
  END AS stage_status,
  cs.task AS task
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
JOIN crop_stages cs ON cs.crop_id = cc.crop_id;

-- ---------------------------------------------------------------------
-- 3. Triggers for Automatic Weather Alerts (on weather_records)
-- ---------------------------------------------------------------------
DELIMITER $$

DROP TRIGGER IF EXISTS trg_weather_ai$$
CREATE TRIGGER trg_weather_ai AFTER INSERT ON weather_records FOR EACH ROW
BEGIN
  -- Rain Alert
  IF NEW.rainfall_mm IS NOT NULL AND NEW.rainfall_mm >= 50.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Rain',
      CONCAT('Heavy rainfall alert (', NEW.rainfall_mm, ' mm) recorded on ', NEW.record_date, '. Ensure adequate drainage in fields.'),
      CONCAT('rain_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Heat Alert
  IF NEW.temperature IS NOT NULL AND NEW.temperature >= 38.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Heat',
      CONCAT('High temperature alert (', NEW.temperature, '°C) on ', NEW.record_date, '. Ensure frequent light irrigation to prevent crop heat stress.'),
      CONCAT('heat_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Frost Alert
  IF NEW.temperature IS NOT NULL AND NEW.temperature <= 4.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Frost',
      CONCAT('Frost warning (', NEW.temperature, '°C) on ', NEW.record_date, '. Protect sensitive crops from cold injury.'),
      CONCAT('frost_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Drought Alert
  IF NEW.temperature >= 35.0 AND NEW.humidity IS NOT NULL AND NEW.humidity < 25.0
     AND (NEW.rainfall_mm IS NULL OR NEW.rainfall_mm = 0) THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Drought',
      CONCAT('Dry weather / drought alert on ', NEW.record_date, ' (Temp: ', NEW.temperature, '°C, Humidity: ', NEW.humidity, '%). Soil moisture conservation advised.'),
      CONCAT('drought_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_weather_au$$
CREATE TRIGGER trg_weather_au AFTER UPDATE ON weather_records FOR EACH ROW
BEGIN
  -- Rain Alert
  IF NEW.rainfall_mm IS NOT NULL AND NEW.rainfall_mm >= 50.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Rain',
      CONCAT('Heavy rainfall alert (', NEW.rainfall_mm, ' mm) recorded on ', NEW.record_date, '. Ensure adequate drainage in fields.'),
      CONCAT('rain_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Heat Alert
  IF NEW.temperature IS NOT NULL AND NEW.temperature >= 38.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Heat',
      CONCAT('High temperature alert (', NEW.temperature, '°C) on ', NEW.record_date, '. Ensure frequent light irrigation to prevent crop heat stress.'),
      CONCAT('heat_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Frost Alert
  IF NEW.temperature IS NOT NULL AND NEW.temperature <= 4.0 THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Frost',
      CONCAT('Frost warning (', NEW.temperature, '°C) on ', NEW.record_date, '. Protect sensitive crops from cold injury.'),
      CONCAT('frost_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;

  -- Drought Alert
  IF NEW.temperature >= 35.0 AND NEW.humidity IS NOT NULL AND NEW.humidity < 25.0
     AND (NEW.rainfall_mm IS NULL OR NEW.rainfall_mm = 0) THEN
    INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
    VALUES (
      NEW.farm_id,
      'Drought',
      CONCAT('Dry weather / drought alert on ', NEW.record_date, ' (Temp: ', NEW.temperature, '°C, Humidity: ', NEW.humidity, '%). Soil moisture conservation advised.'),
      CONCAT('drought_', NEW.farm_id, '_', NEW.record_date)
    )
    ON DUPLICATE KEY UPDATE message = VALUES(message);
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 4. Stored Procedure: recommend_fertilizer
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS recommend_fertilizer$$
CREATE PROCEDURE recommend_fertilizer(
  IN p_farm_id INT,
  IN p_test_id INT,
  IN p_crop_id INT
)
BEGIN
  DECLARE v_area DECIMAL(6,2);
  DECLARE v_n, v_p, v_k DECIMAL(6,2);
  DECLARE v_req_n, v_req_p, v_req_k INT;
  DECLARE v_def_n, v_def_p, v_def_k DECIMAL(6,2);
  DECLARE v_dap_acre, v_n_from_dap, v_rem_n, v_urea_acre, v_mop_acre DECIMAL(8,2);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  -- Validation
  IF NOT EXISTS (SELECT 1 FROM farms WHERE farm_id = p_farm_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Farm not found';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM crops WHERE crop_id = p_crop_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Crop not found';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM soil_tests WHERE test_id = p_test_id AND farm_id = p_farm_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Soil test not found for this farm';
  END IF;

  SELECT area_acres INTO v_area FROM farms WHERE farm_id = p_farm_id;
  SELECT nitrogen, phosphorus, potassium INTO v_n, v_p, v_k FROM soil_tests WHERE test_id = p_test_id;
  SELECT n_required, p_required, k_required INTO v_req_n, v_req_p, v_req_k FROM crops WHERE crop_id = p_crop_id;

  -- Deficit calculation
  SET v_def_n = GREATEST(0, v_req_n - IFNULL(v_n, 0));
  SET v_def_p = GREATEST(0, v_req_p - IFNULL(v_p, 0));
  SET v_def_k = GREATEST(0, v_req_k - IFNULL(v_k, 0));

  -- DAP provides 46% P2O5 and 18% N
  SET v_dap_acre = IF(v_def_p > 0, ROUND(v_def_p / 0.46, 2), 0);
  SET v_n_from_dap = v_dap_acre * 0.18;

  -- Urea provides 46% N (balance after DAP)
  SET v_rem_n = GREATEST(0, v_def_n - v_n_from_dap);
  SET v_urea_acre = IF(v_rem_n > 0, ROUND(v_rem_n / 0.46, 2), 0);

  -- MOP provides 60% K2O
  SET v_mop_acre = IF(v_def_k > 0, ROUND(v_def_k / 0.60, 2), 0);

  -- Return results (empty if all doses are 0)
  SELECT
    f.name AS fertilizer,
    r.kg_per_acre,
    ROUND(r.kg_per_acre * v_area, 2) AS kg_for_farm,
    ROUND(r.kg_per_acre * v_area * f.price_per_kg, 2) AS estimated_cost
  FROM (
    SELECT 'DAP' AS fert_name, v_dap_acre AS kg_per_acre WHERE v_dap_acre > 0
    UNION ALL
    SELECT 'Urea' AS fert_name, v_urea_acre AS kg_per_acre WHERE v_urea_acre > 0
    UNION ALL
    SELECT 'MOP (Potash)' AS fert_name, v_mop_acre AS kg_per_acre WHERE v_mop_acre > 0
  ) r
  JOIN fertilizers f ON f.name = r.fert_name;
END$$

-- ---------------------------------------------------------------------
-- 5. Stored Procedure: rotation_advice
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS rotation_advice$$
CREATE PROCEDURE rotation_advice(
  IN p_farm_id INT
)
BEGIN
  DECLARE v_prev_crop_id INT DEFAULT NULL;
  DECLARE v_current_season VARCHAR(10);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  IF NOT EXISTS (SELECT 1 FROM farms WHERE farm_id = p_farm_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Farm not found';
  END IF;

  -- Find previous crop from last harvested/failed cycle
  SELECT crop_id INTO v_prev_crop_id
  FROM crop_cycles
  WHERE farm_id = p_farm_id AND status IN ('Harvested', 'Failed')
  ORDER BY actual_harvest DESC, cycle_id DESC
  LIMIT 1;

  IF v_prev_crop_id IS NULL THEN
    -- Return empty result set
    SELECT
      NULL AS crop_id,
      NULL AS crop_name,
      NULL AS season,
      NULL AS is_in_season,
      NULL AS duration_days,
      NULL AS reason
    WHERE 1 = 0;
  ELSE
    SET v_current_season = get_season(CURDATE());

    SELECT
      c.crop_id,
      c.crop_name,
      c.season,
      IF(c.season = v_current_season OR c.season = 'Annual', 1, 0) AS is_in_season,
      c.duration_days,
      r.reason
    FROM crop_rotation_rules r
    JOIN crops c ON c.crop_id = r.recommended_crop_id
    WHERE r.previous_crop_id = v_prev_crop_id
    ORDER BY is_in_season DESC, c.crop_name ASC;
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 6. Stored Procedure: generate_task_alerts
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS generate_task_alerts$$
CREATE PROCEDURE generate_task_alerts(
  IN p_days_ahead INT
)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  IF p_days_ahead IS NULL THEN
    SET p_days_ahead = 2;
  END IF;

  INSERT INTO alerts (farm_id, alert_type, message, dedupe_key)
  SELECT
    cc.farm_id,
    'Task' AS alert_type,
    CONCAT(c.crop_name, ' (', cs.stage_name, '): ', cs.task) AS message,
    CONCAT('task_', cc.cycle_id, '_', cs.stage_id, '_', CURDATE()) AS dedupe_key
  FROM crop_cycles cc
  JOIN crops c ON c.crop_id = cc.crop_id
  JOIN crop_stages cs ON cs.crop_id = cc.crop_id
  WHERE cc.status = 'Growing'
    AND cc.sowing_date IS NOT NULL
    AND (
      DATEDIFF(CURDATE(), cc.sowing_date) BETWEEN cs.start_day AND cs.end_day
      OR cs.start_day BETWEEN DATEDIFF(CURDATE(), cc.sowing_date) AND DATEDIFF(CURDATE(), cc.sowing_date) + p_days_ahead
    )
  ON DUPLICATE KEY UPDATE message = VALUES(message);

  SELECT ROW_COUNT() AS alerts_generated;
END$$

DELIMITER ;
