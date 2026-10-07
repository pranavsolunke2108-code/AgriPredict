-- =====================================================================
-- AgriPredict : Phase 6c - Role-based MySQL accounts (least privilege)
-- Run as a MySQL admin (root) after phases 1-5:
--   mysql -u root -p < agripredict_phase6_security.sql
--
-- Three accounts:
--   agripredict_app     the web backend: read/write data, run procedures,
--                       but cannot change the schema (no DROP/ALTER/CREATE)
--   agripredict_report  read-only, for reports/analysts: sees dashboard views
--                       and reference tables, NOT the farmers table (so no
--                       password hashes or phone numbers)
--   agripredict_migrate runs the .sql setup files (full rights on this DB only)
--
-- !! CHANGE THE PASSWORDS BELOW before running, and put the app password in
-- !! your .env (DB_USER=agripredict_app). Never commit real passwords.
-- If the backend runs on another machine, replace 'localhost' with its host.
-- =====================================================================

CREATE USER IF NOT EXISTS 'agripredict_app'@'localhost'     IDENTIFIED BY 'App_AgriPredict#2026';
ALTER USER 'agripredict_app'@'localhost'     IDENTIFIED BY 'App_AgriPredict#2026';
CREATE USER IF NOT EXISTS 'agripredict_report'@'localhost'  IDENTIFIED BY 'Report_AgriPredict#2026';
ALTER USER 'agripredict_report'@'localhost'  IDENTIFIED BY 'Report_AgriPredict#2026';
CREATE USER IF NOT EXISTS 'agripredict_migrate'@'localhost' IDENTIFIED BY 'Migrate_AgriPredict#2026';
ALTER USER 'agripredict_migrate'@'localhost' IDENTIFIED BY 'Migrate_AgriPredict#2026';

-- ---- App: data access + procedures --------------------------------------
-- CREATE TEMPORARY TABLES is needed because recommend_crops builds a temp table.
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE, CREATE TEMPORARY TABLES
  ON agripredict.* TO 'agripredict_app'@'localhost';

-- ---- Report: read-only views + non-sensitive reference tables -----------
GRANT SELECT ON agripredict.current_status_view       TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.farmer_history_view       TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.farmer_summary_view       TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.crop_calendar_view        TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.latest_prices_view        TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.cycle_expense_summary_view TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.crops                     TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.fertilizers               TO 'agripredict_report'@'localhost';
GRANT SELECT ON agripredict.market_prices             TO 'agripredict_report'@'localhost';

-- ---- Migrate: full control of this database only ------------------------
GRANT ALL PRIVILEGES ON agripredict.* TO 'agripredict_migrate'@'localhost';

FLUSH PRIVILEGES;

-- Check what each account can do (screenshot for the report)
SHOW GRANTS FOR 'agripredict_app'@'localhost';
SHOW GRANTS FOR 'agripredict_report'@'localhost';
SHOW GRANTS FOR 'agripredict_migrate'@'localhost';

-- ---------------------------------------------------------------------
-- Quick tests to run from a terminal (each should behave as noted):
--   mysql -u agripredict_app -p agripredict -e "SELECT COUNT(*) FROM crops;"        -> works
--   mysql -u agripredict_app -p agripredict -e "DROP TABLE crops;"                  -> ERROR 1142 denied
--   mysql -u agripredict_report -p agripredict -e "SELECT * FROM farmers;"          -> ERROR 1142 denied
--   mysql -u agripredict_report -p agripredict -e "DELETE FROM crops;"              -> ERROR 1142 denied
--
-- To remove the accounts later:
--   DROP USER 'agripredict_app'@'localhost';
--   DROP USER 'agripredict_report'@'localhost';
--   DROP USER 'agripredict_migrate'@'localhost';
-- ---------------------------------------------------------------------
