-- =====================================================================
-- AgriPredict : Phase 2 - Stored Procedures and Functions
-- Run: mysql -u root -p agripredict < agripredict_phase2_recommend.sql
-- =====================================================================

USE agripredict;

DELIMITER $$

DROP FUNCTION IF EXISTS get_season$$
CREATE FUNCTION get_season(p_date DATE) RETURNS VARCHAR(10) CHARSET utf8mb4
    DETERMINISTIC
BEGIN
  RETURN CASE
    WHEN MONTH(p_date) BETWEEN 6 AND 10 THEN 'Kharif'
    WHEN MONTH(p_date) IN (11,12,1,2,3)  THEN 'Rabi'
    ELSE 'Zaid'
  END;
END$$

DROP PROCEDURE IF EXISTS recommend_crops$$
CREATE PROCEDURE recommend_crops(
  IN p_farm_id INT,
  IN p_test_id INT,
  IN p_season  VARCHAR(10)
)
BEGIN
  DECLARE v_n, v_p, v_k DECIMAL(6,2);
  DECLARE v_ph          DECIMAL(3,1);
  DECLARE v_temp, v_hum DECIMAL(6,2);
  DECLARE v_rain        DECIMAL(8,2);
  DECLARE v_weather_id  INT;
  DECLARE v_cnt         INT DEFAULT 0;
  DECLARE v_season      VARCHAR(10);

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  -- 1. Validate Soil Test
  SELECT COUNT(*) INTO v_cnt
  FROM soil_tests
  WHERE test_id = p_test_id AND farm_id = p_farm_id
    AND nitrogen IS NOT NULL AND phosphorus IS NOT NULL
    AND potassium IS NOT NULL AND ph IS NOT NULL;

  IF v_cnt = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Soil test not found for this farm, or N/P/K/pH is missing';
  END IF;

  SELECT nitrogen, phosphorus, potassium, ph
    INTO v_n, v_p, v_k, v_ph
  FROM soil_tests
  WHERE test_id = p_test_id AND farm_id = p_farm_id;

  -- 2. Validate Weather Data (last 30 days)
  SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm) * 30, MAX(weather_id)
    INTO v_temp, v_hum, v_rain, v_weather_id
  FROM weather_records
  WHERE farm_id = p_farm_id
    AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

  IF v_temp IS NULL OR v_hum IS NULL OR v_rain IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No recent weather data for this farm (need last 30 days)';
  END IF;

  -- 3. Determine Season
  SET v_season = COALESCE(p_season, get_season(CURDATE()));

  -- 4. Temporary table for scored crops
  DROP TEMPORARY TABLE IF EXISTS scored_crops;
  CREATE TEMPORARY TABLE scored_crops (
    crop_id        INT,
    crop_name      VARCHAR(60),
    season         VARCHAR(10),
    ph_score       DECIMAL(5,2),
    temp_score     DECIMAL(5,2),
    humidity_score DECIMAL(5,2),
    rain_score     DECIMAL(5,2),
    n_score        DECIMAL(5,2),
    p_score        DECIMAL(5,2),
    k_score        DECIMAL(5,2),
    total_score    DECIMAL(5,2)
  );

  INSERT INTO scored_crops
  SELECT
    s.crop_id, s.crop_name, s.season,
    s.ph_score, s.temp_score, s.humidity_score, s.rain_score,
    s.n_score, s.p_score, s.k_score,
    ROUND( s.ph_score       * 0.15
         + s.temp_score     * 0.20
         + s.humidity_score * 0.10
         + s.rain_score     * 0.20
         + s.n_score        * 0.12
         + s.p_score        * 0.12
         + s.k_score        * 0.11, 2) AS total_score
  FROM (
    SELECT
      c.crop_id, c.crop_name, c.season,
      CASE WHEN v_ph BETWEEN c.min_ph AND c.max_ph THEN 100
           ELSE GREATEST(0, 100 - 100 * LEAST(ABS(v_ph - c.min_ph), ABS(v_ph - c.max_ph))
                                   / GREATEST(c.max_ph - c.min_ph, 1)) END AS ph_score,
      CASE WHEN v_temp BETWEEN c.min_temp AND c.max_temp THEN 100
           ELSE GREATEST(0, 100 - 100 * LEAST(ABS(v_temp - c.min_temp), ABS(v_temp - c.max_temp))
                                   / GREATEST(c.max_temp - c.min_temp, 1)) END AS temp_score,
      CASE WHEN v_hum BETWEEN c.min_humidity AND c.max_humidity THEN 100
           ELSE GREATEST(0, 100 - 100 * LEAST(ABS(v_hum - c.min_humidity), ABS(v_hum - c.max_humidity))
                                   / GREATEST(c.max_humidity - c.min_humidity, 1)) END AS humidity_score,
      CASE WHEN v_rain BETWEEN c.min_rainfall AND c.max_rainfall THEN 100
           ELSE GREATEST(0, 100 - 100 * LEAST(ABS(v_rain - c.min_rainfall), ABS(v_rain - c.max_rainfall))
                                   / GREATEST(c.max_rainfall - c.min_rainfall, 1)) END AS rain_score,
      GREATEST(0, LEAST(100, CASE WHEN v_n >= c.n_required
            THEN 100 - 50 * (v_n - c.n_required) / c.n_required
            ELSE 100 * v_n / c.n_required END)) AS n_score,
      GREATEST(0, LEAST(100, CASE WHEN v_p >= c.p_required
            THEN 100 - 50 * (v_p - c.p_required) / c.p_required
            ELSE 100 * v_p / c.p_required END)) AS p_score,
      GREATEST(0, LEAST(100, CASE WHEN v_k >= c.k_required
            THEN 100 - 50 * (v_k - c.k_required) / c.k_required
            ELSE 100 * v_k / c.k_required END)) AS k_score
    FROM crops c
    WHERE v_season = 'ALL'
       OR c.season = v_season
       OR c.season = 'Annual'
  ) s;

  -- 5. Insert Top 3 into Predictions table
  START TRANSACTION;

  INSERT INTO predictions (farm_id, test_id, weather_id, crop_id, suitability_score, rank_no)
  SELECT p_farm_id, p_test_id, v_weather_id, t.crop_id, t.total_score, t.rn
  FROM (
    SELECT crop_id, total_score,
           ROW_NUMBER() OVER (ORDER BY total_score DESC, crop_name) AS rn
    FROM scored_crops
  ) t
  WHERE t.rn <= 3;

  COMMIT;

  -- 6. Return Top 3 Recommendations
  SELECT
    t.rn AS rank_no, t.crop_name, t.season, t.total_score AS suitability,
    t.ph_score, t.temp_score, t.humidity_score, t.rain_score,
    t.n_score, t.p_score, t.k_score
  FROM (
    SELECT sc.*, ROW_NUMBER() OVER (ORDER BY total_score DESC, crop_name) AS rn
    FROM scored_crops sc
  ) t
  WHERE t.rn <= 3
  ORDER BY t.rn;

  DROP TEMPORARY TABLE IF EXISTS scored_crops;
END$$

DELIMITER ;
