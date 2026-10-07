-- =====================================================================
-- AgriPredict : Phase 5 - Market Prices, Profit Analytics, Admin & Audit
-- Run: mysql -u root -p agripredict < agripredict_phase5_market_admin.sql
-- =====================================================================

USE agripredict;

-- ---------------------------------------------------------------------
-- 1. Crops columns: avg_yield_q_per_acre and est_cost_per_acre
-- ---------------------------------------------------------------------
SET @col1_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'crops' AND column_name = 'avg_yield_q_per_acre'
);
SET @stmt1 = IF(@col1_exists = 0, 'ALTER TABLE crops ADD COLUMN avg_yield_q_per_acre DECIMAL(8,2) NULL', 'SELECT 1');
PREPARE s1 FROM @stmt1; EXECUTE s1; DEALLOCATE PREPARE s1;

SET @col2_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'crops' AND column_name = 'est_cost_per_acre'
);
SET @stmt2 = IF(@col2_exists = 0, 'ALTER TABLE crops ADD COLUMN est_cost_per_acre DECIMAL(10,2) NULL', 'SELECT 1');
PREPARE s2 FROM @stmt2; EXECUTE s2; DEALLOCATE PREPARE s2;

-- Update sample yields and costs if null
UPDATE crops SET avg_yield_q_per_acre = 20.00, est_cost_per_acre = 25000.00 WHERE crop_name = 'Rice' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 22.00, est_cost_per_acre = 20000.00 WHERE crop_name = 'Maize' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 16.00, est_cost_per_acre = 18000.00 WHERE crop_name = 'Wheat' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 8.00,  est_cost_per_acre = 15000.00 WHERE crop_name = 'Soybean' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 6.00,  est_cost_per_acre = 30000.00 WHERE crop_name = 'Cotton' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 350.00,est_cost_per_acre = 60000.00 WHERE crop_name = 'Sugarcane' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 7.00,  est_cost_per_acre = 14000.00 WHERE crop_name = 'Chickpea' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 6.00,  est_cost_per_acre = 13000.00 WHERE crop_name = 'Pigeon Pea' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 9.00,  est_cost_per_acre = 18000.00 WHERE crop_name = 'Groundnut' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 10.00, est_cost_per_acre = 12000.00 WHERE crop_name = 'Jowar' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 10.00, est_cost_per_acre = 11000.00 WHERE crop_name = 'Bajra' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 80.00, est_cost_per_acre = 35000.00 WHERE crop_name = 'Onion' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 120.00,est_cost_per_acre = 40000.00 WHERE crop_name = 'Tomato' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 4.00,  est_cost_per_acre = 10000.00 WHERE crop_name = 'Moong' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 4.00,  est_cost_per_acre = 10000.00 WHERE crop_name = 'Urad' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 5.00,  est_cost_per_acre = 11000.00 WHERE crop_name = 'Lentil' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 200.00,est_cost_per_acre = 70000.00 WHERE crop_name = 'Banana' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 90.00, est_cost_per_acre = 80000.00 WHERE crop_name = 'Grapes' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 100.00,est_cost_per_acre = 25000.00 WHERE crop_name = 'Watermelon' AND avg_yield_q_per_acre IS NULL;
UPDATE crops SET avg_yield_q_per_acre = 30.00, est_cost_per_acre = 30000.00 WHERE crop_name = 'Mango' AND avg_yield_q_per_acre IS NULL;

-- ---------------------------------------------------------------------
-- 2. Market Prices Unique Key
-- ---------------------------------------------------------------------
SET @uq_exists = (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'market_prices' AND index_name = 'uq_price_crop_district_date'
);
SET @stmt_uq = IF(@uq_exists = 0, 'ALTER TABLE market_prices ADD CONSTRAINT uq_price_crop_district_date UNIQUE (crop_id, district, price_date)', 'SELECT 1');
PREPARE s_uq FROM @stmt_uq; EXECUTE s_uq; DEALLOCATE PREPARE s_uq;

-- ---------------------------------------------------------------------
-- 3. Table: admin_audit_log
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_audit_log (
  log_id     INT AUTO_INCREMENT PRIMARY KEY,
  table_name VARCHAR(40) NOT NULL,
  record_id  INT NOT NULL,
  action     ENUM('UPDATE', 'DELETE') NOT NULL,
  old_data   JSON DEFAULT NULL,
  new_data   JSON DEFAULT NULL,
  changed_by VARCHAR(100) NOT NULL,
  changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_table (table_name, record_id, changed_at)
);

-- ---------------------------------------------------------------------
-- 4. Triggers on crops and market_prices for audit log & price alerts
-- ---------------------------------------------------------------------
DELIMITER $$

DROP TRIGGER IF EXISTS trg_crops_au$$
CREATE TRIGGER trg_crops_au AFTER UPDATE ON crops FOR EACH ROW BEGIN
  INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by)
  VALUES ('crops', NEW.crop_id, 'UPDATE',
    JSON_OBJECT('crop_name', OLD.crop_name, 'season', OLD.season, 'duration_days', OLD.duration_days,
                'min_ph', OLD.min_ph, 'max_ph', OLD.max_ph, 'min_temp', OLD.min_temp, 'max_temp', OLD.max_temp,
                'n', OLD.n_required, 'p', OLD.p_required, 'k', OLD.k_required,
                'yield_q_per_acre', OLD.avg_yield_q_per_acre, 'cost_per_acre', OLD.est_cost_per_acre),
    JSON_OBJECT('crop_name', NEW.crop_name, 'season', NEW.season, 'duration_days', NEW.duration_days,
                'min_ph', NEW.min_ph, 'max_ph', NEW.max_ph, 'min_temp', NEW.min_temp, 'max_temp', NEW.max_temp,
                'n', NEW.n_required, 'p', NEW.p_required, 'k', NEW.k_required,
                'yield_q_per_acre', NEW.avg_yield_q_per_acre, 'cost_per_acre', NEW.est_cost_per_acre),
    COALESCE(@app_user, CURRENT_USER()));
END$$

DROP TRIGGER IF EXISTS trg_crops_ad$$
CREATE TRIGGER trg_crops_ad AFTER DELETE ON crops FOR EACH ROW BEGIN
  INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by)
  VALUES ('crops', OLD.crop_id, 'DELETE',
    JSON_OBJECT('crop_name', OLD.crop_name, 'season', OLD.season, 'duration_days', OLD.duration_days,
                'yield_q_per_acre', OLD.avg_yield_q_per_acre, 'cost_per_acre', OLD.est_cost_per_acre),
    NULL, COALESCE(@app_user, CURRENT_USER()));
END$$

DROP TRIGGER IF EXISTS trg_price_ai$$
CREATE TRIGGER trg_price_ai AFTER INSERT ON market_prices FOR EACH ROW BEGIN
  DECLARE v_prev DECIMAL(10,2);

  SET v_prev = (SELECT m.price_per_quintal FROM market_prices m
                WHERE m.crop_id = NEW.crop_id AND m.district = NEW.district
                  AND m.price_date < NEW.price_date
                ORDER BY m.price_date DESC LIMIT 1);

  IF v_prev IS NOT NULL AND v_prev > 0 AND NEW.price_per_quintal >= v_prev * 1.10 THEN
    INSERT IGNORE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT cc.farm_id, 'Price',
           CONCAT(c.crop_name, ' price in ', NEW.district, ' rose to Rs ',
                  NEW.price_per_quintal, '/quintal (up ',
                  ROUND((NEW.price_per_quintal / v_prev - 1) * 100, 1),
                  '% from Rs ', v_prev, '). Consider timing your sale.'),
           CONCAT('price:', NEW.crop_id, ':', NEW.district, ':', NEW.price_date)
    FROM crop_cycles cc
    JOIN farms fm   ON fm.farm_id  = cc.farm_id
    JOIN farmers f  ON f.farmer_id = fm.farmer_id
    JOIN crops c    ON c.crop_id   = cc.crop_id
    WHERE cc.crop_id = NEW.crop_id
      AND cc.status IN ('Planned','Growing')
      AND f.district = NEW.district;
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_prices_au$$
CREATE TRIGGER trg_prices_au AFTER UPDATE ON market_prices FOR EACH ROW BEGIN
  INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by)
  VALUES ('market_prices', NEW.price_id, 'UPDATE',
    JSON_OBJECT('crop_id', OLD.crop_id, 'district', OLD.district,
                'price_per_quintal', OLD.price_per_quintal, 'price_date', OLD.price_date),
    JSON_OBJECT('crop_id', NEW.crop_id, 'district', NEW.district,
                'price_per_quintal', NEW.price_per_quintal, 'price_date', NEW.price_date),
    COALESCE(@app_user, CURRENT_USER()));
END$$

DROP TRIGGER IF EXISTS trg_prices_ad$$
CREATE TRIGGER trg_prices_ad AFTER DELETE ON market_prices FOR EACH ROW BEGIN
  INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by)
  VALUES ('market_prices', OLD.price_id, 'DELETE',
    JSON_OBJECT('crop_id', OLD.crop_id, 'district', OLD.district,
                'price_per_quintal', OLD.price_per_quintal, 'price_date', OLD.price_date),
    NULL, COALESCE(@app_user, CURRENT_USER()));
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 5. Views: latest_prices_view & cycle_expense_summary_view
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW latest_prices_view AS
SELECT
  c.crop_id,
  c.crop_name,
  mp.district,
  mp.price_per_quintal,
  mp.price_date
FROM market_prices mp
JOIN crops c ON c.crop_id = mp.crop_id
WHERE mp.price_date = (
  SELECT MAX(m.price_date)
  FROM market_prices m
  WHERE m.crop_id = mp.crop_id AND m.district = mp.district
);

CREATE OR REPLACE VIEW cycle_expense_summary_view AS
SELECT
  f.farmer_id,
  cc.farm_id,
  cc.cycle_id,
  c.crop_name,
  e.category,
  SUM(e.amount) AS category_total,
  ROUND(100.0 * SUM(e.amount) / SUM(SUM(e.amount)) OVER (PARTITION BY cc.cycle_id), 1) AS pct_of_cycle
FROM expenses e
JOIN crop_cycles cc ON cc.cycle_id = e.cycle_id
JOIN farms fm       ON fm.farm_id = cc.farm_id
JOIN farmers f      ON f.farmer_id = fm.farmer_id
JOIN crops c        ON c.crop_id = cc.crop_id
GROUP BY f.farmer_id, cc.farm_id, cc.cycle_id, c.crop_name, e.category;

-- ---------------------------------------------------------------------
-- 6. Stored Procedures: estimate_crop_profit & profit_for_recommendations
-- ---------------------------------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS estimate_crop_profit$$
CREATE PROCEDURE estimate_crop_profit(IN p_farm_id INT, IN p_crop_id INT)
BEGIN
  DECLARE v_district VARCHAR(60);
  DECLARE v_area     DECIMAL(6,2);
  DECLARE v_cnt      INT DEFAULT 0;

  SELECT COUNT(*) INTO v_cnt FROM farms WHERE farm_id = p_farm_id;
  IF v_cnt = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Farm not found';
  END IF;
  SELECT COUNT(*) INTO v_cnt FROM crops WHERE crop_id = p_crop_id;
  IF v_cnt = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Crop not found';
  END IF;

  SELECT fm.district, COALESCE(f.area_acres, 1) INTO v_district, v_area
  FROM farms f JOIN farmers fm ON fm.farmer_id = f.farmer_id
  WHERE f.farm_id = p_farm_id;

  SELECT
    c.crop_name,
    mp.district              AS price_district,
    mp.price_per_quintal,
    mp.price_date,
    c.avg_yield_q_per_acre,
    c.est_cost_per_acre,
    ROUND(c.avg_yield_q_per_acre * mp.price_per_quintal)                         AS revenue_per_acre,
    ROUND(c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre)   AS profit_per_acre,
    ROUND((c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre)
          / (c.duration_days / 30))                                              AS profit_per_acre_per_month,
    v_area                                                                       AS farm_area_acres,
    ROUND((c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre) * v_area) AS profit_for_farm
  FROM crops c
  LEFT JOIN market_prices mp ON mp.price_id = (
      SELECT m.price_id FROM market_prices m
      WHERE m.crop_id = c.crop_id
      ORDER BY (m.district = v_district) DESC, m.price_date DESC, m.price_id DESC
      LIMIT 1)
  WHERE c.crop_id = p_crop_id;
END$$

DROP PROCEDURE IF EXISTS profit_for_recommendations$$
CREATE PROCEDURE profit_for_recommendations(IN p_farm_id INT)
BEGIN
  DECLARE v_district VARCHAR(60);
  DECLARE v_area     DECIMAL(6,2);
  DECLARE v_cnt      INT DEFAULT 0;

  SELECT COUNT(*) INTO v_cnt FROM farms WHERE farm_id = p_farm_id;
  IF v_cnt = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Farm not found';
  END IF;

  SELECT fm.district, COALESCE(f.area_acres, 1) INTO v_district, v_area
  FROM farms f JOIN farmers fm ON fm.farmer_id = f.farmer_id
  WHERE f.farm_id = p_farm_id;

  SELECT
    x.prediction_id,
    x.rank_no,
    c.crop_id,
    c.crop_name,
    x.suitability_score,
    mp.price_per_quintal,
    mp.district AS price_district,
    mp.price_date,
    c.avg_yield_q_per_acre,
    c.est_cost_per_acre,
    ROUND(c.avg_yield_q_per_acre * mp.price_per_quintal)                       AS revenue_per_acre,
    ROUND(c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre) AS profit_per_acre,
    ROUND((c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre)
          / (c.duration_days / 30))                                            AS profit_per_acre_per_month,
    ROUND((c.avg_yield_q_per_acre * mp.price_per_quintal - c.est_cost_per_acre) * v_area) AS profit_for_farm
  FROM (
    SELECT p.prediction_id, p.crop_id, p.rank_no, p.suitability_score,
           (SELECT m.price_id FROM market_prices m
            WHERE m.crop_id = p.crop_id
            ORDER BY (m.district = v_district) DESC, m.price_date DESC, m.price_id DESC
            LIMIT 1) AS price_id
    FROM predictions p
    WHERE p.farm_id = p_farm_id
      AND p.predicted_on = (SELECT MAX(p2.predicted_on) FROM predictions p2
                            WHERE p2.farm_id = p_farm_id)
  ) x
  JOIN crops c ON c.crop_id = x.crop_id
  LEFT JOIN market_prices mp ON mp.price_id = x.price_id
  ORDER BY x.rank_no;
END$$

DELIMITER ;
