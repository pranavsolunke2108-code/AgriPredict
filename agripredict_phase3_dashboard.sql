-- =====================================================================
-- AgriPredict : Phase 3 - Crop Cycles, Dashboard Views, Triggers, and Procedures
-- Run: mysql -u root -p agripredict < agripredict_phase3_dashboard.sql
-- =====================================================================

USE agripredict;

-- ---------------------------------------------------------------------
-- 1. Table: crop_cycle_log (Audit Trail)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_cycle_log (
  log_id INT NOT NULL AUTO_INCREMENT,
  cycle_id INT NOT NULL,
  old_status ENUM('Planned','Growing','Harvested','Failed') DEFAULT NULL,
  new_status ENUM('Planned','Growing','Harvested','Failed') NOT NULL,
  changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (log_id),
  KEY idx_log_cycle (cycle_id, changed_at),
  CONSTRAINT fk_log_cycle FOREIGN KEY (cycle_id) REFERENCES crop_cycles (cycle_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. Views
-- ---------------------------------------------------------------------

-- View: current_status_view
CREATE OR REPLACE VIEW current_status_view AS
SELECT
  f.farmer_id AS farmer_id,
  fm.farm_id AS farm_id,
  fm.farm_name AS farm_name,
  cc.cycle_id AS cycle_id,
  c.crop_name AS crop_name,
  cc.status AS status,
  cc.sowing_date AS sowing_date,
  cc.expected_harvest AS expected_harvest,
  CASE
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > CURDATE() THEN NULL
    ELSE (TO_DAYS(CURDATE()) - TO_DAYS(cc.sowing_date))
  END AS days_since_sowing,
  CASE
    WHEN cc.sowing_date > CURDATE() THEN (TO_DAYS(cc.sowing_date) - TO_DAYS(CURDATE()))
    ELSE NULL
  END AS days_until_sowing,
  CASE
    WHEN cc.expected_harvest IS NULL THEN NULL
    ELSE (TO_DAYS(cc.expected_harvest) - TO_DAYS(CURDATE()))
  END AS days_to_harvest,
  CASE
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > CURDATE() THEN 0
    ELSE ROUND(LEAST(100, ((100 * (TO_DAYS(CURDATE()) - TO_DAYS(cc.sowing_date))) / c.duration_days)), 1)
  END AS progress_pct,
  CASE
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > CURDATE() THEN 'Not sown yet'
    ELSE COALESCE(
      (SELECT cs.stage_name
       FROM crop_stages cs
       WHERE cs.crop_id = cc.crop_id
         AND (TO_DAYS(CURDATE()) - TO_DAYS(cc.sowing_date)) BETWEEN cs.start_day AND cs.end_day
       LIMIT 1),
      'No stage data'
    )
  END AS current_stage,
  (SELECT cs.task
   FROM crop_stages cs
   WHERE cs.crop_id = cc.crop_id
     AND cc.sowing_date IS NOT NULL
     AND (TO_DAYS(CURDATE()) - TO_DAYS(cc.sowing_date)) BETWEEN cs.start_day AND cs.end_day
   LIMIT 1) AS current_task,
  COALESCE(
    (SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id),
    0
  ) AS expenses_so_far
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
WHERE cc.status IN ('Planned', 'Growing');

-- View: farmer_history_view
CREATE OR REPLACE VIEW farmer_history_view AS
SELECT
  f.farmer_id AS farmer_id,
  fm.farm_id AS farm_id,
  fm.farm_name AS farm_name,
  cc.cycle_id AS cycle_id,
  c.crop_name AS crop_name,
  cc.status AS status,
  cc.sowing_date AS sowing_date,
  cc.actual_harvest AS actual_harvest,
  cc.yield_kg AS yield_kg,
  cc.selling_price_per_quintal AS selling_price_per_quintal,
  ROUND(COALESCE(((cc.yield_kg / 100) * cc.selling_price_per_quintal), 0), 2) AS revenue,
  COALESCE(
    (SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id),
    0
  ) AS total_expenses,
  ROUND(
    COALESCE(((cc.yield_kg / 100) * cc.selling_price_per_quintal), 0) -
    COALESCE((SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id), 0),
    2
  ) AS profit
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
WHERE cc.status IN ('Harvested', 'Failed');

-- View: farmer_summary_view
CREATE OR REPLACE VIEW farmer_summary_view AS
SELECT
  f.farmer_id AS farmer_id,
  f.name AS name,
  (SELECT COUNT(0) FROM farms x WHERE x.farmer_id = f.farmer_id) AS total_farms,
  (SELECT COUNT(0) FROM current_status_view v WHERE v.farmer_id = f.farmer_id) AS active_cycles,
  (SELECT COUNT(0) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id) AS completed_cycles,
  COALESCE((SELECT SUM(h.revenue) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0) AS total_revenue,
  COALESCE((SELECT SUM(h.total_expenses) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0) AS total_expenses,
  COALESCE((SELECT SUM(h.profit) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0) AS net_profit
FROM farmers f
WHERE f.role = 'farmer';

-- ---------------------------------------------------------------------
-- 3. Triggers
-- ---------------------------------------------------------------------

DELIMITER $$

DROP TRIGGER IF EXISTS trg_cycle_bi$$
CREATE TRIGGER trg_cycle_bi BEFORE INSERT ON crop_cycles FOR EACH ROW
BEGIN
  DECLARE v_days INT;

  IF NEW.status IN ('Planned','Growing') AND EXISTS (
       SELECT 1 FROM crop_cycles
       WHERE farm_id = NEW.farm_id AND status IN ('Planned','Growing')) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'This farm already has an active crop cycle. Close it first.';
  END IF;

  IF NEW.expected_harvest IS NULL AND NEW.sowing_date IS NOT NULL THEN
    SELECT duration_days INTO v_days FROM crops WHERE crop_id = NEW.crop_id;
    SET NEW.expected_harvest = DATE_ADD(NEW.sowing_date, INTERVAL v_days DAY);
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_cycle_ai$$
CREATE TRIGGER trg_cycle_ai AFTER INSERT ON crop_cycles FOR EACH ROW
BEGIN
  INSERT INTO crop_cycle_log (cycle_id, old_status, new_status)
  VALUES (NEW.cycle_id, NULL, NEW.status);
END$$

DROP TRIGGER IF EXISTS trg_cycle_bu$$
CREATE TRIGGER trg_cycle_bu BEFORE UPDATE ON crop_cycles FOR EACH ROW
BEGIN
  DECLARE v_days INT;

  IF OLD.status IN ('Harvested','Failed') AND NEW.status IN ('Planned','Growing') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'A closed crop cycle cannot be reopened.';
  END IF;

  IF NEW.yield_kg IS NOT NULL AND OLD.yield_kg IS NULL
     AND NEW.status IN ('Planned','Growing') THEN
    SET NEW.status = 'Harvested';
  END IF;

  IF NEW.status = 'Growing' AND NEW.sowing_date IS NULL THEN
    SET NEW.sowing_date = CURDATE();
  END IF;

  IF NEW.expected_harvest IS NULL AND NEW.sowing_date IS NOT NULL THEN
    SELECT duration_days INTO v_days FROM crops WHERE crop_id = NEW.crop_id;
    SET NEW.expected_harvest = DATE_ADD(NEW.sowing_date, INTERVAL v_days DAY);
  END IF;

  IF NEW.status = 'Harvested' AND NEW.actual_harvest IS NULL THEN
    SET NEW.actual_harvest = CURDATE();
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_cycle_au$$
CREATE TRIGGER trg_cycle_au AFTER UPDATE ON crop_cycles FOR EACH ROW
BEGIN
  IF OLD.status <> NEW.status THEN
    INSERT INTO crop_cycle_log (cycle_id, old_status, new_status)
    VALUES (NEW.cycle_id, OLD.status, NEW.status);
  END IF;
END$$

-- ---------------------------------------------------------------------
-- 4. Stored Procedures
-- ---------------------------------------------------------------------

DROP PROCEDURE IF EXISTS start_crop_cycle$$
CREATE PROCEDURE start_crop_cycle(
  IN p_farm_id       INT,
  IN p_crop_id       INT,
  IN p_prediction_id INT,
  IN p_sowing_date   DATE
)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  IF NOT EXISTS (SELECT 1 FROM farms WHERE farm_id = p_farm_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Farm not found';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM crops WHERE crop_id = p_crop_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Crop not found';
  END IF;

  START TRANSACTION;

  INSERT INTO crop_cycles (farm_id, crop_id, prediction_id, sowing_date, status)
  VALUES (p_farm_id, p_crop_id, p_prediction_id, p_sowing_date,
          IF(p_sowing_date IS NOT NULL AND p_sowing_date <= CURDATE(), 'Growing', 'Planned'));

  COMMIT;

  SELECT LAST_INSERT_ID() AS cycle_id;
END$$

DROP PROCEDURE IF EXISTS close_crop_cycle$$
CREATE PROCEDURE close_crop_cycle(
  IN p_cycle_id          INT,
  IN p_status            VARCHAR(10),
  IN p_yield_kg          DECIMAL(10,2),
  IN p_price_per_quintal DECIMAL(10,2)
)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  IF p_status NOT IN ('Harvested','Failed') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Status must be Harvested or Failed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM crop_cycles WHERE cycle_id = p_cycle_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Crop cycle not found';
  END IF;
  IF p_status = 'Harvested' AND (p_yield_kg IS NULL OR p_yield_kg < 0) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A valid yield is required for a harvested cycle';
  END IF;

  START TRANSACTION;

  UPDATE crop_cycles
  SET status = p_status,
      yield_kg = IF(p_status = 'Harvested', p_yield_kg, yield_kg),
      selling_price_per_quintal = IF(p_status = 'Harvested', p_price_per_quintal, selling_price_per_quintal)
  WHERE cycle_id = p_cycle_id;

  COMMIT;

  SELECT * FROM crop_cycles WHERE cycle_id = p_cycle_id;
END$$

DELIMITER ;
