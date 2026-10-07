# AgriPredict - Report Notes

Material for the DBMS report and viva. Counts below match the final database:
**16 tables, 7 views, 10 stored procedures/functions, 11 triggers, 1 scheduled event.**
The ER diagram is in `agripredict_er_diagram.png` / `.svg`.

---

## 1. DBMS concepts used and where

| Concept | Where it appears in AgriPredict |
|---|---|
| Primary / foreign keys, `ON DELETE CASCADE` / `SET NULL` | All 16 tables. Deleting a farmer removes their farms, soil tests, weather, cycles and expenses automatically; deleting a prediction only clears the link in `crop_cycles` |
| `UNIQUE`, `NOT NULL`, `CHECK`, `ENUM` constraints | Unique phone/email; pH between 0 and 14; non-negative amounts; ENUMs for status, season, category, role |
| Normalization (1NF to 3NF) | Section 2 below |
| Indexes: composite, covering, unique | `agripredict_phase6_indexes.sql`; measured with EXPLAIN (section 4) |
| Views (7) | `current_status_view`, `farmer_history_view`, `farmer_summary_view`, `crop_calendar_view`, `latest_prices_view`, `cycle_expense_summary_view`, `crop_localized_view` |
| Stored procedures (9) and a function | `recommend_crops`, `start_crop_cycle`, `close_crop_cycle`, `recommend_fertilizer`, `rotation_advice`, `check_weather_alerts`, `generate_task_alerts`, `estimate_crop_profit`, `profit_for_recommendations`; function `get_season` |
| Triggers (11) | Crop cycle rules (4), weather alerts (2), price-jump alert (1), admin audit on crops and market prices (4) |
| Scheduled event | `ev_daily_task_alerts` runs `generate_task_alerts` every day at 6 AM |
| Transactions and error handling | `START TRANSACTION` / `COMMIT` with `EXIT HANDLER ... ROLLBACK; RESIGNAL` in the procedures; `SIGNAL SQLSTATE '45000'` for business-rule errors |
| Window functions | `ROW_NUMBER()` ranking in `recommend_crops`; `SUM() OVER (PARTITION BY ...)` for expense percentages |
| Joins, aggregates, correlated subqueries | Dashboard views, price lookup with district fallback, current growth stage |
| Temporary tables | `scored_crops` inside `recommend_crops` |
| Upserts and idempotent writes | `ON DUPLICATE KEY UPDATE` (weather, prices, translations), `INSERT IGNORE` with `dedupe_key` (alerts) |
| JSON column | `admin_audit_log.old_data` / `new_data` |
| Audit logging | `crop_cycle_log` (status history) and `admin_audit_log` (who changed what) |
| Security | bcrypt password hashes, JWT sessions, parameterized queries, ownership checks on every query, least-privilege MySQL accounts (`agripredict_phase6_security.sql`) |
| Backup and recovery | `backup_agripredict.sh` / `.ps1` (dump includes procedures, triggers and events) with a tested restore |
| Internationalization | `translations` table (97 keys x English/Marathi/Hindi) and `crop_localized_view` |

---

## 2. Normalization

**1NF - atomic values, no repeating groups.**
Each soil nutrient has its own column (`nitrogen`, `phosphorus`, `potassium`) instead of one text field like "N=90,P=45". A farm's many soil tests are rows in `soil_tests`, not columns such as `test1`, `test2`. Each ENUM column holds one value.

**2NF - no partial dependency on part of a composite key.**
The only composite primary key is `translations (text_key, lang)`; `text` depends on both parts. Every other table uses a single-column key, so partial dependency cannot occur. Crop properties (duration, pH range, nutrient needs) live only in `crops`, keyed by `crop_id`; `crop_cycles` stores just `crop_id`.

**3NF - no transitive dependency on non-key columns.**
- A farm's owner details are not copied into `farms`; it stores `farmer_id` and the district is read from `farmers`.
- Crop names, durations and ideal ranges are not repeated in `predictions` or `crop_cycles`.
- Totals (expenses per cycle, profit, progress %) are not stored; they are computed in views so they can never disagree with the underlying rows.

**BCNF.** In each table the determinants are candidate keys. Examples: `weather_records` has candidate keys `weather_id` and `(farm_id, record_date)`; `market_prices` has `price_id` and `(crop_id, district, price_date)`.

**Deliberate, controlled redundancy (say this in the viva - it shows you understand the trade-off):**
- `crop_cycles.expected_harvest` is derivable (sowing date + crop duration) but stored, and a trigger keeps it filled in, so the dashboard and reminder job read a plain column.
- `predictions.suitability_score` is a snapshot, so history stays unchanged even if crop ranges are edited later.
- `crop_cycles.selling_price_per_quintal` is the price the farmer actually got, which differs from the market price table.
- `alerts.message` stores the text as it was shown when the alert was raised.

---

## 3. Final table list (16)

`farmers`, `farms`, `soil_tests`, `weather_records`, `crops`, `crop_stages`, `crop_rotation_rules`, `fertilizers`, `market_prices`, `translations`, `predictions`, `crop_cycles`, `expenses`, `crop_cycle_log`, `alerts`, `admin_audit_log`

---

## 4. Index performance experiment (for the report)

Query: the average temperature, humidity and rainfall of one farm over the last 30 days (what `recommend_crops` does), on a scratch table of 500,000 rows (1,000 farms x 500 days).

| Stage | EXPLAIN access type | Rows examined | Time on my test run |
|---|---|---|---|
| No index | `ALL` (full table scan) | 500,000 | about 190 ms |
| Composite `(farm_id, record_date)` | `range` | 31 | about 0.4 ms |
| Covering `(farm_id, record_date, temperature, humidity, rainfall_mm)` | `range`, "Using index" | 31 | about 0.2 ms |

Times came from a MariaDB test server and will differ on your machine; **run `agripredict_phase6_explain_demo.sql` yourself and use your own numbers and screenshots**. The pattern (full scan to index range scan, hundreds of times fewer rows) is what to explain.

Points to make:
- Put the equality column (`farm_id`) first and the range column (`record_date`) second.
- A covering index avoids reading the table but makes inserts slightly slower and uses more space, which is why it was only demonstrated on the scratch table.
- Wrapping an indexed column in a function (`YEAR(record_date) = ...`) stops the index from narrowing by date; the range form (`record_date >= ... AND record_date < ...`) is better.
- Redundant indexes were removed (`expenses(cycle_id)` and the duplicate on `market_prices`) because every extra index slows writes.

---

## 5. Known limitations (state these honestly in the report)

1. **Seed data is approximate.** Crop ideal ranges, yields, costs, fertilizer prices and mandi prices are starter values, not verified agronomic or market data. Profit and fertilizer outputs are estimates, only as good as that data.
2. **The recommender is rule-based.** It scores how close conditions are to each crop's range with fixed weights. It is not a trained model and has not been validated against real outcomes. Long-duration annual crops (banana, sugarcane) can dominate the top 3, so profit per month is shown for fair comparison.
3. **Fertilizer advice is indicative.** The nutrient gap is treated as kg/ha to apply, which is a simplification. Local agriculture department dose recommendations should take priority.
4. **Weather input** is the average of the last 30 days, not a forecast, and rainfall thresholds are per 30 days.
5. **Season logic** is by sowing time (Kharif Jun-Sep, Rabi Oct-Feb, Zaid Mar-May); regional calendars vary.
6. **One active crop per farm** is enforced by a trigger. Intercropping and multi-plot farms must be modelled as separate farms.
7. **CHECK constraints** are enforced only by MySQL 8.0.16+ (and MariaDB 10.2+); older MySQL accepts but ignores them.
8. **The daily reminder event** needs `event_scheduler = ON`; the app also has a fallback job.
9. **Translations** should be reviewed by native speakers; agricultural terms differ by region.
10. **Not covered:** HTTPS/TLS deployment, phone or email verification, rate limiting, and database replication.

---

## 6. Likely viva questions - short answers

**Why MySQL with InnoDB?** InnoDB supports transactions, foreign keys, row-level locking and crash recovery, which this app needs (a cycle start, price update or harvest must be all-or-nothing).

**Procedure vs function?** A procedure is called with `CALL`, can return result sets and run transactions. A function returns one value and is used inside queries (`get_season(CURDATE())`).

**Trigger vs procedure?** A trigger runs automatically on INSERT/UPDATE/DELETE and enforces rules no matter which application writes (for example one active cycle per farm). A procedure runs only when called.

**View vs table?** A view stores a query, not data, so the dashboard always shows live figures and the report account can be given the view without access to the underlying tables.

**How do you prevent SQL injection?** All queries use parameters (`%s`), never string concatenation, and the app's MySQL account cannot alter or drop tables.

**How are passwords stored?** As bcrypt hashes in `password_hash`; the reporting account cannot read the `farmers` table at all.

**Show ACID in your project.** `start_crop_cycle` and `close_crop_cycle` run in a transaction with an exit handler that rolls back on any error, so a half-updated cycle can never be saved.

**Why `dedupe_key` on alerts?** Triggers and the daily job can fire repeatedly; the unique `(farm_id, dedupe_key)` plus `INSERT IGNORE` guarantees each alert is created once.

**What happens if a farmer is deleted?** `ON DELETE CASCADE` removes their farms and everything beneath them (soil tests, weather, cycles, expenses, alerts) in one statement.

**What is the weakness of your recommender?** It is rule-based with approximate ranges and weights, not trained on outcomes. Mention the dataset-validation step (comparing against the Kaggle crop recommendation labels) as the natural next improvement.
