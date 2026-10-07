

DROP DATABASE IF EXISTS agripredict;
CREATE DATABASE agripredict CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agripredict;

-- ---------------------------------------------------------------------
-- 1. USERS (farmers + admins)
-- ---------------------------------------------------------------------
CREATE TABLE farmers (
  farmer_id      INT AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(100) NOT NULL,
  phone          VARCHAR(15)  NOT NULL UNIQUE,
  email          VARCHAR(100) UNIQUE,
  password_hash  VARCHAR(255) NOT NULL,          -- bcrypt/argon2 hash, never plain text
  district       VARCHAR(60),
  village        VARCHAR(80),
  language       ENUM('en','mr','hi') NOT NULL DEFAULT 'en',
  role           ENUM('farmer','admin') NOT NULL DEFAULT 'farmer',
  is_active      TINYINT(1) NOT NULL DEFAULT 1,
  created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login     TIMESTAMP NULL
);

-- ---------------------------------------------------------------------
-- 2. FARMS
-- ---------------------------------------------------------------------
CREATE TABLE farms (
  farm_id      INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id    INT NOT NULL,
  farm_name    VARCHAR(100) NOT NULL,
  area_acres   DECIMAL(6,2) CHECK (area_acres > 0),
  latitude     DECIMAL(9,6),
  longitude    DECIMAL(9,6),
  soil_type    ENUM('Black','Red','Alluvial','Laterite','Sandy','Clay','Loamy') ,
  irrigation   ENUM('Rainfed','Canal','Well','Drip','Sprinkler') DEFAULT 'Rainfed',
  CONSTRAINT fk_farms_farmer FOREIGN KEY (farmer_id)
    REFERENCES farmers(farmer_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 3. SOIL TESTS
-- ---------------------------------------------------------------------
CREATE TABLE soil_tests (
  test_id      INT AUTO_INCREMENT PRIMARY KEY,
  farm_id      INT NOT NULL,
  test_date    DATE NOT NULL,
  nitrogen     DECIMAL(6,2) CHECK (nitrogen   >= 0),
  phosphorus   DECIMAL(6,2) CHECK (phosphorus >= 0),
  potassium    DECIMAL(6,2) CHECK (potassium  >= 0),
  ph           DECIMAL(3,1) CHECK (ph BETWEEN 0 AND 14),
  moisture     DECIMAL(5,2) CHECK (moisture BETWEEN 0 AND 100),
  organic_carbon DECIMAL(4,2),
  CONSTRAINT fk_soil_farm FOREIGN KEY (farm_id)
    REFERENCES farms(farm_id) ON DELETE CASCADE,
  INDEX idx_soil_farm_date (farm_id, test_date)
);

-- ---------------------------------------------------------------------
-- 4. WEATHER RECORDS (cached from API or entered manually)
-- ---------------------------------------------------------------------
CREATE TABLE weather_records (
  weather_id   INT AUTO_INCREMENT PRIMARY KEY,
  farm_id      INT NOT NULL,
  record_date  DATE NOT NULL,
  temperature  DECIMAL(4,1),            -- deg C
  humidity     DECIMAL(5,2),            -- %
  rainfall_mm  DECIMAL(6,2),
  source       ENUM('api','manual') NOT NULL DEFAULT 'api',
  CONSTRAINT fk_weather_farm FOREIGN KEY (farm_id)
    REFERENCES farms(farm_id) ON DELETE CASCADE,
  UNIQUE KEY uq_weather_farm_date (farm_id, record_date),
  INDEX idx_weather_date (record_date)
);

-- ---------------------------------------------------------------------
-- 5. CROPS (master data with ideal growing conditions)
--    rainfall = approx average monthly rainfall (mm) during the growing period
--    n/p/k_required = ideal soil level, same scale as soil_tests
-- ---------------------------------------------------------------------
CREATE TABLE crops (
  crop_id        INT AUTO_INCREMENT PRIMARY KEY,
  crop_name      VARCHAR(60) NOT NULL UNIQUE,
  season         ENUM('Kharif','Rabi','Zaid','Annual') NOT NULL,
  duration_days  INT NOT NULL,
  min_ph DECIMAL(3,1), max_ph DECIMAL(3,1),
  min_temp DECIMAL(4,1), max_temp DECIMAL(4,1),
  min_humidity DECIMAL(5,2), max_humidity DECIMAL(5,2),
  min_rainfall DECIMAL(6,2), max_rainfall DECIMAL(6,2),
  n_required INT, p_required INT, k_required INT
);

-- ---------------------------------------------------------------------
-- 6. PREDICTIONS (history of recommendations)
-- ---------------------------------------------------------------------
CREATE TABLE predictions (
  prediction_id     INT AUTO_INCREMENT PRIMARY KEY,
  farm_id           INT NOT NULL,
  test_id           INT NOT NULL,
  weather_id        INT NULL,
  crop_id           INT NOT NULL,
  suitability_score DECIMAL(5,2) NOT NULL,
  rank_no           TINYINT NOT NULL,
  predicted_on      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pred_farm    FOREIGN KEY (farm_id)    REFERENCES farms(farm_id)             ON DELETE CASCADE,
  CONSTRAINT fk_pred_test    FOREIGN KEY (test_id)    REFERENCES soil_tests(test_id)        ON DELETE CASCADE,
  CONSTRAINT fk_pred_weather FOREIGN KEY (weather_id) REFERENCES weather_records(weather_id) ON DELETE SET NULL,
  CONSTRAINT fk_pred_crop    FOREIGN KEY (crop_id)    REFERENCES crops(crop_id),
  INDEX idx_pred_farm_time (farm_id, predicted_on)
);

-- ---------------------------------------------------------------------
-- 7. CROP CYCLES  ("current status" lives here)
-- ---------------------------------------------------------------------
CREATE TABLE crop_cycles (
  cycle_id          INT AUTO_INCREMENT PRIMARY KEY,
  farm_id           INT NOT NULL,
  crop_id           INT NOT NULL,
  prediction_id     INT NULL,                   -- which recommendation led to this
  sowing_date       DATE,
  expected_harvest  DATE,
  actual_harvest    DATE NULL,
  status            ENUM('Planned','Growing','Harvested','Failed') NOT NULL DEFAULT 'Planned',
  yield_kg          DECIMAL(10,2) NULL,
  selling_price_per_quintal DECIMAL(10,2) NULL,
  CONSTRAINT fk_cycle_farm FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE,
  CONSTRAINT fk_cycle_crop FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
  CONSTRAINT fk_cycle_pred FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id) ON DELETE SET NULL,
  INDEX idx_cycle_farm_status (farm_id, status)
);

-- ---------------------------------------------------------------------
-- 8. EXPENSES
-- ---------------------------------------------------------------------
CREATE TABLE expenses (
  expense_id    INT AUTO_INCREMENT PRIMARY KEY,
  cycle_id      INT NOT NULL,
  category      ENUM('Seeds','Fertilizer','Pesticide','Labour','Irrigation','Machinery','Other') NOT NULL,
  amount        DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
  expense_date  DATE NOT NULL,
  notes         VARCHAR(200),
  CONSTRAINT fk_exp_cycle FOREIGN KEY (cycle_id) REFERENCES crop_cycles(cycle_id) ON DELETE CASCADE,
  INDEX idx_exp_cycle (cycle_id)
);

-- ---------------------------------------------------------------------
-- 9. MARKET PRICES (mandi rates)
-- ---------------------------------------------------------------------
CREATE TABLE market_prices (
  price_id          INT AUTO_INCREMENT PRIMARY KEY,
  crop_id           INT NOT NULL,
  district          VARCHAR(60) NOT NULL,
  price_per_quintal DECIMAL(10,2) NOT NULL,
  price_date        DATE NOT NULL,
  CONSTRAINT fk_price_crop FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
  INDEX idx_price_lookup (crop_id, district, price_date)
);

-- ---------------------------------------------------------------------
-- 10. FERTILIZERS
-- ---------------------------------------------------------------------
CREATE TABLE fertilizers (
  fert_id      INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(60) NOT NULL UNIQUE,
  n_pct        DECIMAL(5,2) NOT NULL DEFAULT 0,
  p_pct        DECIMAL(5,2) NOT NULL DEFAULT 0,   -- as P2O5 %
  k_pct        DECIMAL(5,2) NOT NULL DEFAULT 0,   -- as K2O %
  price_per_kg DECIMAL(8,2)
);

-- ---------------------------------------------------------------------
-- 11. CROP STAGES (calendar / reminders)
-- ---------------------------------------------------------------------
CREATE TABLE crop_stages (
  stage_id    INT AUTO_INCREMENT PRIMARY KEY,
  crop_id     INT NOT NULL,
  stage_name  VARCHAR(60) NOT NULL,
  start_day   INT NOT NULL,                 -- days after sowing
  end_day     INT NOT NULL,
  task        VARCHAR(200),
  CONSTRAINT fk_stage_crop FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
  CHECK (end_day >= start_day),
  INDEX idx_stage_crop (crop_id, start_day)
);

-- ---------------------------------------------------------------------
-- 12. CROP ROTATION RULES
-- ---------------------------------------------------------------------
CREATE TABLE crop_rotation_rules (
  rule_id             INT AUTO_INCREMENT PRIMARY KEY,
  previous_crop_id    INT NOT NULL,
  recommended_crop_id INT NOT NULL,
  reason              VARCHAR(200),
  CONSTRAINT fk_rot_prev FOREIGN KEY (previous_crop_id)    REFERENCES crops(crop_id) ON DELETE CASCADE,
  CONSTRAINT fk_rot_next FOREIGN KEY (recommended_crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
  UNIQUE KEY uq_rotation (previous_crop_id, recommended_crop_id)
);

-- ---------------------------------------------------------------------
-- 13. ALERTS
-- ---------------------------------------------------------------------
CREATE TABLE alerts (
  alert_id    INT AUTO_INCREMENT PRIMARY KEY,
  farm_id     INT NOT NULL,
  alert_type  ENUM('Rain','Heat','Frost','Drought','Pest','Task','Price') NOT NULL,
  message     VARCHAR(255) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_read     TINYINT(1) NOT NULL DEFAULT 0,
  CONSTRAINT fk_alert_farm FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE,
  INDEX idx_alert_farm_read (farm_id, is_read, created_at)
);

-- ---------------------------------------------------------------------
-- 14. TRANSLATIONS (multilingual UI)
-- ---------------------------------------------------------------------
CREATE TABLE translations (
  text_key  VARCHAR(80) NOT NULL,
  lang      ENUM('en','mr','hi') NOT NULL,
  text      VARCHAR(255) NOT NULL,
  PRIMARY KEY (text_key, lang)
);

-- =====================================================================
-- SEED DATA
-- =====================================================================

-- Crops: name, season, days, pH, temp, humidity, rainfall, N, P, K
INSERT INTO crops
(crop_name, season, duration_days, min_ph, max_ph, min_temp, max_temp, min_humidity, max_humidity, min_rainfall, max_rainfall, n_required, p_required, k_required)
VALUES
('Rice',        'Kharif', 120, 5.5, 7.0, 20, 30, 70, 90, 150, 300,  80, 48, 40),
('Maize',       'Kharif', 100, 5.5, 7.0, 18, 27, 55, 75,  60, 110,  78, 48, 20),
('Wheat',       'Rabi',   120, 6.0, 7.5, 12, 25, 40, 70,  30, 100, 100, 50, 40),
('Soybean',     'Kharif', 100, 6.0, 7.0, 20, 30, 60, 85,  60, 120,  25, 60, 40),
('Cotton',      'Kharif', 180, 5.8, 8.0, 21, 30, 60, 85,  60, 110, 118, 46, 20),
('Sugarcane',   'Annual', 365, 6.5, 7.5, 20, 32, 60, 85,  75, 150, 120, 60, 60),
('Chickpea',    'Rabi',   100, 6.0, 8.0, 15, 25, 15, 50,  60, 100,  40, 68, 80),
('Pigeon Pea',  'Kharif', 150, 5.0, 7.0, 20, 32, 40, 65, 100, 200,  21, 68, 20),
('Groundnut',   'Kharif', 110, 6.0, 7.0, 22, 30, 50, 75,  50, 100,  25, 50, 75),
('Jowar',       'Kharif', 110, 6.0, 8.0, 25, 33, 40, 70,  40,  90,  80, 40, 40),
('Bajra',       'Kharif',  85, 6.0, 8.0, 25, 35, 40, 65,  40,  80,  60, 30, 30),
('Onion',       'Rabi',   120, 6.0, 7.5, 13, 28, 50, 75,  30,  80, 100, 50, 60),
('Tomato',      'Rabi',   110, 6.0, 7.0, 18, 30, 55, 80,  40, 100, 100, 60, 80),
('Moong',       'Zaid',    65, 6.2, 7.2, 25, 32, 65, 90,  30,  80,  21, 47, 20),
('Urad',        'Kharif',  80, 6.5, 7.5, 25, 35, 55, 75,  50,  90,  40, 67, 19),
('Lentil',      'Rabi',   110, 6.0, 7.5, 18, 30, 50, 75,  30,  70,  19, 68, 19),
('Banana',      'Annual', 300, 5.5, 7.0, 24, 32, 70, 90,  80, 150, 100, 82, 50),
('Grapes',      'Annual', 150, 5.5, 6.5, 20, 28, 65, 85,  50,  90,  23,132,200),
('Watermelon',  'Zaid',    90, 6.0, 7.0, 22, 30, 70, 90,  40,  70, 100, 17, 50),
('Mango',       'Annual', 150, 5.5, 7.5, 24, 35, 40, 65,  70, 120,  20, 27, 30);

-- Fertilizers (prices are approximate, update via admin)
INSERT INTO fertilizers (name, n_pct, p_pct, k_pct, price_per_kg) VALUES
('Urea',           46,  0,  0,  6.00),
('DAP',            18, 46,  0, 27.00),
('MOP (Potash)',    0,  0, 60, 34.00),
('SSP',             0, 16,  0,  8.00),
('NPK 10:26:26',   10, 26, 26, 30.00),
('NPK 19:19:19',   19, 19, 19, 90.00);

-- Crop rotation rules (cereal -> legume restores nitrogen, etc.)
INSERT INTO crop_rotation_rules (previous_crop_id, recommended_crop_id, reason)
SELECT p.crop_id, r.crop_id, x.reason FROM (
  SELECT 'Rice'      AS prev, 'Chickpea'   AS nxt, 'Legume after cereal fixes nitrogen and breaks pest cycles' AS reason UNION ALL
  SELECT 'Rice',            'Wheat',               'Standard rice-wheat sequence for Rabi season' UNION ALL
  SELECT 'Wheat',           'Moong',               'Short-duration legume restores soil nitrogen' UNION ALL
  SELECT 'Wheat',           'Soybean',             'Legume after cereal reduces fertilizer need' UNION ALL
  SELECT 'Maize',           'Chickpea',            'Legume after cereal fixes nitrogen' UNION ALL
  SELECT 'Cotton',          'Wheat',               'Cereal after cotton breaks bollworm cycle' UNION ALL
  SELECT 'Cotton',          'Chickpea',            'Legume after a heavy feeder restores fertility' UNION ALL
  SELECT 'Soybean',         'Wheat',               'Cereal uses the nitrogen left by soybean' UNION ALL
  SELECT 'Soybean',         'Onion',               'Different family reduces disease build-up' UNION ALL
  SELECT 'Groundnut',       'Jowar',               'Cereal after legume uses fixed nitrogen' UNION ALL
  SELECT 'Onion',           'Maize',               'Different family; breaks onion disease cycle' UNION ALL
  SELECT 'Tomato',          'Maize',               'Avoids repeated soil-borne disease on solanaceous crops' UNION ALL
  SELECT 'Jowar',           'Chickpea',            'Legume after cereal fixes nitrogen' UNION ALL
  SELECT 'Bajra',           'Lentil',              'Legume after cereal fixes nitrogen'
) x
JOIN crops p ON p.crop_name = x.prev
JOIN crops r ON r.crop_name = x.nxt;

-- Sample crop stages (Rice and Wheat; add the rest later via admin panel)
INSERT INTO crop_stages (crop_id, stage_name, start_day, end_day, task)
SELECT c.crop_id, s.stage_name, s.start_day, s.end_day, s.task FROM (
  SELECT 'Rice' AS crop, 'Nursery / Transplanting' AS stage_name, 0 AS start_day, 25 AS end_day, 'Prepare nursery, transplant seedlings' AS task UNION ALL
  SELECT 'Rice', 'Tillering',            26,  55, 'First top-dressing of nitrogen, keep field flooded' UNION ALL
  SELECT 'Rice', 'Panicle initiation',   56,  80, 'Second nitrogen dose, watch for stem borer' UNION ALL
  SELECT 'Rice', 'Flowering',            81, 100, 'Maintain water level, avoid stress' UNION ALL
  SELECT 'Rice', 'Grain filling and harvest', 101, 120, 'Drain field, harvest at maturity' UNION ALL
  SELECT 'Wheat', 'Germination',          0,  20, 'Light irrigation after sowing' UNION ALL
  SELECT 'Wheat', 'Crown root initiation', 21,  40, 'First irrigation and nitrogen top-dressing' UNION ALL
  SELECT 'Wheat', 'Tillering',            41,  65, 'Weed control, second irrigation' UNION ALL
  SELECT 'Wheat', 'Flowering',            66,  90, 'Irrigate, monitor rust' UNION ALL
  SELECT 'Wheat', 'Grain filling and harvest', 91, 120, 'Final irrigation, harvest at maturity'
) s JOIN crops c ON c.crop_name = s.crop;

-- UI translations (starter set)
INSERT INTO translations (text_key, lang, text) VALUES
('login',            'en', 'Login'),
('login',            'mr', 'लॉगिन'),
('login',            'hi', 'लॉगिन'),
('register',         'en', 'Register'),
('register',         'mr', 'नोंदणी करा'),
('register',         'hi', 'पंजीकरण करें'),
('my_farms',         'en', 'My Farms'),
('my_farms',         'mr', 'माझी शेती'),
('my_farms',         'hi', 'मेरे खेत'),
('recommend_crop',   'en', 'Recommend Crop'),
('recommend_crop',   'mr', 'पिकाची शिफारस'),
('recommend_crop',   'hi', 'फसल सुझाव'),
('current_status',   'en', 'Current Status'),
('current_status',   'mr', 'सध्याची स्थिती'),
('current_status',   'hi', 'वर्तमान स्थिति'),
('history',          'en', 'History'),
('history',          'mr', 'इतिहास'),
('history',          'hi', 'इतिहास');
