-- =====================================================================
-- AgriPredict : Phase 6a - Database Index Optimizations
-- Run as MySQL admin:
--   mysql -u root -p agripredict < agripredict_phase6_indexes.sql
-- =====================================================================

USE agripredict;

-- Helper procedure to safely drop an index if it exists
DROP PROCEDURE IF EXISTS drop_index_if_exists;

DELIMITER $$
CREATE PROCEDURE drop_index_if_exists(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64)
)
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
          AND index_name = p_index_name
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table_name, '` DROP INDEX `', p_index_name, '`');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

-- Drop redundant duplicate index on market_prices:
-- uq_price_crop_district_date (or uq_market_prices) already indexes (crop_id, district, price_date).
CALL drop_index_if_exists('market_prices', 'idx_price_lookup');

-- Clean up helper procedure
DROP PROCEDURE IF EXISTS drop_index_if_exists;
