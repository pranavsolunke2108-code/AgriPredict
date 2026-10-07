-- =====================================================================
-- AgriPredict : Phase 6b - Index performance demo with EXPLAIN
-- Builds a SCRATCH table (perf_weather, 500,000 rows) so your real data is
-- untouched, then shows the same query with no index, a composite index and
-- a covering index. Everything is dropped at the end.
--
--   mysql -u root -p agripredict < agripredict_phase6_explain_demo.sql
--
-- Take screenshots of each EXPLAIN + timing for your report.
-- Absolute times depend on your machine; the relative drop is what matters.
-- =====================================================================

USE agripredict;

DROP TABLE IF EXISTS perf_weather;
DROP TABLE IF EXISTS perf_digits;

CREATE TABLE perf_digits (d INT PRIMARY KEY);
INSERT INTO perf_digits VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9);

-- Same shape as weather_records, but with NO secondary indexes
CREATE TABLE perf_weather (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  farm_id     INT NOT NULL,
  record_date DATE NOT NULL,
  temperature DECIMAL(4,1),
  humidity    DECIMAL(5,2),
  rainfall_mm DECIMAL(6,2)
);

-- 1000 farms x 500 days = 500,000 rows
INSERT INTO perf_weather (farm_id, record_date, temperature, humidity, rainfall_mm)
SELECT n DIV 500 + 1,
       DATE_SUB(CURDATE(), INTERVAL (n MOD 500) DAY),
       20 + (n MOD 15),
       50 + (n MOD 40),
       (n MOD 9) * 1.5
FROM (
  SELECT a.d + b.d * 10 + c.d * 100 + e.d * 1000 + f.d * 10000 + g.d * 100000 AS n
  FROM perf_digits a, perf_digits b, perf_digits c, perf_digits e, perf_digits f, perf_digits g
) t
WHERE n < 500000;

SELECT COUNT(*) AS total_rows FROM perf_weather;

-- The query recommend_crops runs: last 30 days of weather for one farm
-- ---------------------------------------------------------------------
-- STAGE 1: no index  (expect type=ALL, rows ~ 500000 = full table scan)
-- ---------------------------------------------------------------------
EXPLAIN SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

SET @t = NOW(6);
SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
SELECT 'stage 1: no index' AS stage, ROUND(TIMESTAMPDIFF(MICROSECOND, @t, NOW(6)) / 1000, 2) AS ms;

-- ---------------------------------------------------------------------
-- STAGE 2: composite index (farm_id, record_date)
--   equality column first, range column second
--   (expect type=range, rows ~ 30)
-- ---------------------------------------------------------------------
ALTER TABLE perf_weather ADD INDEX idx_farm_date (farm_id, record_date);

EXPLAIN SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

SET @t = NOW(6);
SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
SELECT 'stage 2: composite index' AS stage, ROUND(TIMESTAMPDIFF(MICROSECOND, @t, NOW(6)) / 1000, 2) AS ms;

-- ---------------------------------------------------------------------
-- STAGE 3: covering index - every column the query needs is inside the
-- index, so the table itself is never read (expect "Using index")
-- Trade-off: a bigger index to maintain on every insert
-- ---------------------------------------------------------------------
ALTER TABLE perf_weather
  ADD INDEX idx_farm_date_cover (farm_id, record_date, temperature, humidity, rainfall_mm);

EXPLAIN SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

SET @t = NOW(6);
SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm)
FROM perf_weather
WHERE farm_id = 777 AND record_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
SELECT 'stage 3: covering index' AS stage, ROUND(TIMESTAMPDIFF(MICROSECOND, @t, NOW(6)) / 1000, 2) AS ms;

-- ---------------------------------------------------------------------
-- BONUS: a function on the indexed column defeats the date part of the index
--   WHERE YEAR(record_date) = ...   -> type=ref: only farm_id narrows the search,
--                                      so all ~500 rows of that farm are checked
--   WHERE record_date >= ... AND < ... -> type=range: only the matching dates
--                                      are read (fewer rows; the gap grows with
--                                      more history per farm)
-- ---------------------------------------------------------------------
EXPLAIN SELECT COUNT(*) FROM perf_weather
WHERE farm_id = 777 AND YEAR(record_date) = YEAR(CURDATE());

EXPLAIN SELECT COUNT(*) FROM perf_weather
WHERE farm_id = 777
  AND record_date >= MAKEDATE(YEAR(CURDATE()), 1)
  AND record_date <  MAKEDATE(YEAR(CURDATE()) + 1, 1);

-- cleanup
DROP TABLE perf_weather;
DROP TABLE perf_digits;
