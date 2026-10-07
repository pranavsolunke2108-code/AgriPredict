"""Pytest configuration and test database fixtures for AgriPredict."""

from datetime import date, datetime, timedelta, timezone
import json
import math
import re
import sqlite3
from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

from app import db
from app.db import DatabaseProcedureError
from app.main import app


class SQLiteTestCursor:
    """Cursor wrapper for SQLite that translates MySQL syntax, handles upserts, and emulates stored procedures."""
    _current_app_user: str = "admin:1"

    def __init__(self, raw_cursor: sqlite3.Cursor, dictionary: bool = True, conn: Optional[sqlite3.Connection] = None):
        self.raw_cursor = raw_cursor
        self.dictionary = dictionary
        self.conn = conn
        self._proc_results: List[Dict[str, Any]] = []

    @property
    def lastrowid(self):
        return self.raw_cursor.lastrowid

    @property
    def rowcount(self):
        return self.raw_cursor.rowcount

    def execute(self, query: str, params: Any = None):
        # 1. Handle SET @app_user session variable
        if re.match(r'^\s*SET\s+@app_user', query, flags=re.IGNORECASE):
            val = params[0] if params and len(params) > 0 else "admin:0"
            SQLiteTestCursor._current_app_user = str(val)
            return self

        # 2. Handle Stored Procedure calls
        if re.match(r'^\s*CALL\s+recommend_crops', query, flags=re.IGNORECASE):
            self._handle_recommend_crops(params)
            return self

        if re.match(r'^\s*CALL\s+start_crop_cycle', query, flags=re.IGNORECASE):
            self._handle_start_crop_cycle(params)
            return self

        if re.match(r'^\s*CALL\s+close_crop_cycle', query, flags=re.IGNORECASE):
            self._handle_close_crop_cycle(params)
            return self

        if re.match(r'^\s*CALL\s+recommend_fertilizer', query, flags=re.IGNORECASE):
            self._handle_recommend_fertilizer(params)
            return self

        if re.match(r'^\s*CALL\s+rotation_advice', query, flags=re.IGNORECASE):
            self._handle_rotation_advice(params)
            return self

        if re.match(r'^\s*CALL\s+generate_task_alerts', query, flags=re.IGNORECASE):
            self._handle_generate_task_alerts(params)
            return self

        if re.match(r'^\s*CALL\s+estimate_crop_profit', query, flags=re.IGNORECASE):
            self._handle_estimate_crop_profit(params)
            return self

        if re.match(r'^\s*CALL\s+profit_for_recommendations', query, flags=re.IGNORECASE):
            self._handle_profit_for_recommendations(params)
            return self

        # 3. Translate MySQL syntax to SQLite
        sqlite_query = query.replace("%s", "?")

        # Translate ON DUPLICATE KEY UPDATE to SQLite ON CONFLICT DO UPDATE SET
        if "ON DUPLICATE KEY UPDATE" in sqlite_query.upper():
            if "market_prices" in sqlite_query.lower():
                conflict_cols = "crop_id, district, price_date"
            elif "translations" in sqlite_query.lower():
                conflict_cols = "text_key, lang"
            else:
                conflict_cols = "farm_id, record_date"

            sqlite_query = re.sub(
                r'ON\s+DUPLICATE\s+KEY\s+UPDATE',
                f'ON CONFLICT({conflict_cols}) DO UPDATE SET',
                sqlite_query,
                flags=re.IGNORECASE,
            )
            sqlite_query = re.sub(r'VALUES\((\w+)\)', r'excluded.\1', sqlite_query, flags=re.IGNORECASE)

        # Translate DATE_SUB(CURRENT_DATE, INTERVAL ? DAY)
        sqlite_query = re.sub(
            r'DATE_SUB\(\s*(?:CURRENT_DATE|CURDATE\(\))\s*,\s*INTERVAL\s+\?\s+DAY\s*\)',
            "date('now', '-' || ? || ' days')",
            sqlite_query,
            flags=re.IGNORECASE,
        )
        sqlite_query = re.sub(r'\bCURRENT_DATE\b', "date('now')", sqlite_query, flags=re.IGNORECASE)
        sqlite_query = re.sub(r'\bCURDATE\(\)', "date('now')", sqlite_query, flags=re.IGNORECASE)

        # Ensure params is a tuple/list with dates converted to strings for SQLite
        cleaned_params = []
        for p in (params or ()):
            if isinstance(p, (date, datetime)):
                cleaned_params.append(p.isoformat())
            else:
                cleaned_params.append(p)

        # 4. Trigger simulation for audit logging and price surge alerts
        is_crop_update = bool(re.search(r'^\s*UPDATE\s+crops\s+SET', query, flags=re.IGNORECASE))
        is_crop_delete = bool(re.search(r'^\s*DELETE\s+FROM\s+crops\b', query, flags=re.IGNORECASE))
        is_price_delete = bool(re.search(r'^\s*DELETE\s+FROM\s+market_prices\b', query, flags=re.IGNORECASE))
        is_price_upsert = bool(re.search(r'^\s*INSERT\s+INTO\s+market_prices\b', query, flags=re.IGNORECASE))

        old_row_data = None
        crop_id_for_audit = None
        price_id_for_audit = None
        prev_price_val = None

        if is_crop_update and cleaned_params:
            crop_id_for_audit = cleaned_params[-1]
            old_r = self.raw_cursor.execute("SELECT * FROM crops WHERE crop_id = ?", (crop_id_for_audit,)).fetchone()
            if old_r:
                old_row_data = dict(old_r)

        elif is_crop_delete and cleaned_params:
            crop_id_for_audit = cleaned_params[0]
            old_r = self.raw_cursor.execute("SELECT * FROM crops WHERE crop_id = ?", (crop_id_for_audit,)).fetchone()
            if old_r:
                old_row_data = dict(old_r)

        elif is_price_delete and cleaned_params:
            price_id_for_audit = cleaned_params[0]
            old_r = self.raw_cursor.execute("SELECT * FROM market_prices WHERE price_id = ?", (price_id_for_audit,)).fetchone()
            if old_r:
                old_row_data = dict(old_r)

        elif is_price_upsert and len(cleaned_params) >= 3:
            prev_r = self.raw_cursor.execute(
                "SELECT price_per_quintal FROM market_prices WHERE crop_id = ? AND district = ? ORDER BY price_date DESC, price_id DESC LIMIT 1",
                (cleaned_params[0], cleaned_params[1])
            ).fetchone()
            if prev_r:
                prev_price_val = float(prev_r[0] if isinstance(prev_r, (list, tuple)) else prev_r["price_per_quintal"])

        res = self.raw_cursor.execute(sqlite_query, tuple(cleaned_params))

        # Perform audit insertions and alert triggers
        user = SQLiteTestCursor._current_app_user

        if is_crop_update and crop_id_for_audit:
            new_r = self.raw_cursor.execute("SELECT * FROM crops WHERE crop_id = ?", (crop_id_for_audit,)).fetchone()
            new_dict = dict(new_r) if new_r else None
            self.raw_cursor.execute(
                "INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by) VALUES (?, ?, 'UPDATE', ?, ?, ?)",
                ("crops", crop_id_for_audit, json.dumps(old_row_data) if old_row_data else None, json.dumps(new_dict) if new_dict else None, user)
            )
            if self.conn:
                self.conn.commit()

        elif is_crop_delete and crop_id_for_audit:
            self.raw_cursor.execute(
                "INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by) VALUES (?, ?, 'DELETE', ?, NULL, ?)",
                ("crops", crop_id_for_audit, json.dumps(old_row_data) if old_row_data else None, user)
            )
            if self.conn:
                self.conn.commit()

        elif is_price_delete and price_id_for_audit:
            self.raw_cursor.execute(
                "INSERT INTO admin_audit_log (table_name, record_id, action, old_data, new_data, changed_by) VALUES (?, ?, 'DELETE', ?, NULL, ?)",
                ("market_prices", price_id_for_audit, json.dumps(old_row_data) if old_row_data else None, user)
            )
            if self.conn:
                self.conn.commit()

        elif is_price_upsert and len(cleaned_params) >= 4 and prev_price_val is not None:
            new_price = float(cleaned_params[2])
            if new_price >= prev_price_val * 1.10:
                # Trigger price surge alert
                cycles = self.raw_cursor.execute(
                    """
                    SELECT cc.farm_id, c.crop_name
                    FROM crop_cycles cc
                    JOIN farms f ON cc.farm_id = f.farm_id
                    JOIN farmers fm ON f.farmer_id = fm.farmer_id
                    JOIN crops c ON cc.crop_id = c.crop_id
                    WHERE cc.crop_id = ? AND fm.district = ? AND cc.status IN ('Planned', 'Growing')
                    """,
                    (cleaned_params[0], cleaned_params[1])
                ).fetchall()
                for cy in cycles:
                    fid = cy[0] if isinstance(cy, (list, tuple)) else cy["farm_id"]
                    cname = cy[1] if isinstance(cy, (list, tuple)) else cy["crop_name"]
                    pct = round(((new_price - prev_price_val) / prev_price_val) * 100, 1)
                    msg = f"Price surge alert: {cname} mandi rate in {cleaned_params[1]} increased by {pct}% to Rs.{new_price}/q."
                    dedupe = f"price_{fid}_{cleaned_params[0]}_{cleaned_params[3]}"
                    self.raw_cursor.execute(
                        "INSERT OR IGNORE INTO alerts (farm_id, alert_type, message, dedupe_key) VALUES (?, 'Price', ?, ?)",
                        (fid, msg, dedupe)
                    )
                if self.conn:
                    self.conn.commit()

        return res

    def _handle_recommend_crops(self, params: Any):
        """Emulate the exact MySQL recommend_crops stored procedure logic for SQLite tests."""
        farm_id, test_id, season = params[0], params[1], params[2]

        # 1. Validate Soil Test
        check_test = self.raw_cursor.execute(
            """
            SELECT COUNT(*) AS cnt, nitrogen, phosphorus, potassium, ph
            FROM soil_tests
            WHERE test_id = ? AND farm_id = ?
              AND nitrogen IS NOT NULL AND phosphorus IS NOT NULL
              AND potassium IS NOT NULL AND ph IS NOT NULL
            """,
            (test_id, farm_id),
        ).fetchone()

        if not check_test or check_test[0] == 0:
            raise DatabaseProcedureError("Soil test not found for this farm, or N/P/K/pH is missing", sqlstate="45000")

        v_n = float(check_test[1])
        v_p = float(check_test[2])
        v_k = float(check_test[3])
        v_ph = float(check_test[4])

        # 2. Validate Weather Data (last 30 days)
        weather_row = self.raw_cursor.execute(
            """
            SELECT AVG(temperature), AVG(humidity), AVG(rainfall_mm) * 30, MAX(weather_id)
            FROM weather_records
            WHERE farm_id = ? AND record_date >= date('now', '-30 days')
            """,
            (farm_id,),
        ).fetchone()

        if not weather_row or weather_row[0] is None or weather_row[1] is None or weather_row[2] is None:
            raise DatabaseProcedureError("No recent weather data for this farm (need last 30 days)", sqlstate="45000")

        v_temp = float(weather_row[0])
        v_hum = float(weather_row[1])
        v_rain = float(weather_row[2])
        v_weather_id = weather_row[3]

        # 3. Determine season
        if not season or season == "auto":
            month = date.today().month
            if 6 <= month <= 10:
                v_season = "Kharif"
            elif month in (11, 12, 1, 2, 3):
                v_season = "Rabi"
            else:
                v_season = "Zaid"
        else:
            v_season = season

        # 4. Fetch crops matching season
        if v_season == "ALL":
            crops = self.raw_cursor.execute("SELECT * FROM crops").fetchall()
        else:
            crops = self.raw_cursor.execute(
                "SELECT * FROM crops WHERE season = ? OR season = 'Annual'",
                (v_season,),
            ).fetchall()

        scored = []
        for c in crops:
            c_dict = dict(c) if hasattr(c, "keys") else {
                "crop_id": c[0], "crop_name": c[1], "season": c[2], "duration_days": c[3],
                "min_ph": c[4], "max_ph": c[5], "min_temp": c[6], "max_temp": c[7],
                "min_humidity": c[8], "max_humidity": c[9], "min_rainfall": c[10],
                "max_rainfall": c[11], "n_required": c[12], "p_required": c[13], "k_required": c[14],
            }

            # pH score
            min_ph, max_ph = c_dict["min_ph"], c_dict["max_ph"]
            if min_ph <= v_ph <= max_ph:
                ph_score = 100.0
            else:
                dist = min(abs(v_ph - min_ph), abs(v_ph - max_ph))
                ph_score = max(0.0, 100.0 - 100.0 * dist / max(max_ph - min_ph, 1.0))

            # Temp score
            min_t, max_t = c_dict["min_temp"], c_dict["max_temp"]
            if min_t <= v_temp <= max_t:
                temp_score = 100.0
            else:
                dist = min(abs(v_temp - min_t), abs(v_temp - max_t))
                temp_score = max(0.0, 100.0 - 100.0 * dist / max(max_t - min_t, 1.0))

            # Humidity score
            min_h, max_h = c_dict["min_humidity"], c_dict["max_humidity"]
            if min_h <= v_hum <= max_h:
                hum_score = 100.0
            else:
                dist = min(abs(v_hum - min_h), abs(v_hum - max_h))
                hum_score = max(0.0, 100.0 - 100.0 * dist / max(max_h - min_h, 1.0))

            # Rain score
            min_r, max_r = c_dict["min_rainfall"], c_dict["max_rainfall"]
            if min_r <= v_rain <= max_r:
                rain_score = 100.0
            else:
                dist = min(abs(v_rain - min_r), abs(v_rain - max_r))
                rain_score = max(0.0, 100.0 - 100.0 * dist / max(max_r - min_r, 1.0))

            # N, P, K scores
            n_req = c_dict["n_required"] or 1
            n_score = (100.0 - 50.0 * (v_n - n_req) / n_req) if v_n >= n_req else (100.0 * v_n / n_req)
            n_score = max(0.0, min(100.0, n_score))

            p_req = c_dict["p_required"] or 1
            p_score = (100.0 - 50.0 * (v_p - p_req) / p_req) if v_p >= p_req else (100.0 * v_p / p_req)
            p_score = max(0.0, min(100.0, p_score))

            k_req = c_dict["k_required"] or 1
            k_score = (100.0 - 50.0 * (v_k - k_req) / k_req) if v_k >= k_req else (100.0 * v_k / k_req)
            k_score = max(0.0, min(100.0, k_score))

            total = round(
                ph_score * 0.15 + temp_score * 0.20 + hum_score * 0.10 +
                rain_score * 0.20 + n_score * 0.12 + p_score * 0.12 + k_score * 0.11,
                2
            )

            scored.append({
                "crop_id": c_dict["crop_id"],
                "crop_name": c_dict["crop_name"],
                "season": c_dict["season"],
                "suitability": total,
                "ph_score": round(ph_score, 2),
                "temp_score": round(temp_score, 2),
                "humidity_score": round(hum_score, 2),
                "rain_score": round(rain_score, 2),
                "n_score": round(n_score, 2),
                "p_score": round(p_score, 2),
                "k_score": round(k_score, 2),
            })

        scored.sort(key=lambda x: (x["suitability"], x["crop_name"]), reverse=True)
        top3 = scored[:3]
        for i, item in enumerate(top3):
            item["rank_no"] = i + 1

        # Insert into predictions
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for item in top3:
            self.raw_cursor.execute(
                """
                INSERT INTO predictions (farm_id, test_id, weather_id, crop_id, suitability_score, rank_no, predicted_on)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (farm_id, test_id, v_weather_id, item["crop_id"], item["suitability"], item["rank_no"], now_ts),
            )
        if self.conn:
            self.conn.commit()

        self._proc_results = top3

    def _handle_start_crop_cycle(self, params: Any):
        """Emulate start_crop_cycle procedure and trg_cycle_bi trigger."""
        farm_id = params[0]
        crop_id = params[1]
        prediction_id = params[2] if len(params) > 2 else None
        sowing_date = params[3] if len(params) > 3 else None

        f_row = self.raw_cursor.execute("SELECT 1 FROM farms WHERE farm_id = ?", (farm_id,)).fetchone()
        if not f_row:
            raise DatabaseProcedureError("Farm not found", sqlstate="45000")

        c_row = self.raw_cursor.execute("SELECT crop_id, duration_days FROM crops WHERE crop_id = ?", (crop_id,)).fetchone()
        if not c_row:
            raise DatabaseProcedureError("Crop not found", sqlstate="45000")
        duration_days = c_row[1] if isinstance(c_row, (list, tuple)) else c_row["duration_days"]

        # Check for existing active cycle on this farm (Trigger trg_cycle_bi)
        active_row = self.raw_cursor.execute(
            "SELECT 1 FROM crop_cycles WHERE farm_id = ? AND status IN ('Planned', 'Growing')",
            (farm_id,),
        ).fetchone()
        if active_row:
            raise DatabaseProcedureError("This farm already has an active crop cycle. Close it first.", sqlstate="45000")

        today_str = date.today().isoformat()
        sow_str = sowing_date.isoformat() if isinstance(sowing_date, (date, datetime)) else (str(sowing_date) if sowing_date else today_str)
        cycle_status = "Growing" if sow_str <= today_str else "Planned"

        try:
            sow_dt = date.fromisoformat(sow_str)
            exp_harvest = (sow_dt + timedelta(days=int(duration_days))).isoformat()
        except Exception:
            exp_harvest = None

        self.raw_cursor.execute(
            """
            INSERT INTO crop_cycles (farm_id, crop_id, prediction_id, sowing_date, expected_harvest, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (farm_id, crop_id, prediction_id, sow_str, exp_harvest, cycle_status),
        )
        new_cycle_id = self.raw_cursor.lastrowid

        # Insert audit log (Trigger trg_cycle_ai)
        self.raw_cursor.execute(
            "INSERT INTO crop_cycle_log (cycle_id, old_status, new_status) VALUES (?, NULL, ?)",
            (new_cycle_id, cycle_status),
        )
        if self.conn:
            self.conn.commit()

        self._proc_results = [{"cycle_id": new_cycle_id}]

    def _handle_close_crop_cycle(self, params: Any):
        """Emulate close_crop_cycle procedure and trg_cycle_bu/au triggers."""
        cycle_id = params[0]
        status = params[1]
        yield_kg = params[2] if len(params) > 2 else None
        price = params[3] if len(params) > 3 else None

        if status not in ("Harvested", "Failed"):
            raise DatabaseProcedureError("Status must be Harvested or Failed", sqlstate="45000")

        cycle_row = self.raw_cursor.execute("SELECT status FROM crop_cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()
        if not cycle_row:
            raise DatabaseProcedureError("Crop cycle not found", sqlstate="45000")

        old_status = cycle_row[0] if isinstance(cycle_row, (list, tuple)) else cycle_row["status"]
        if old_status in ("Harvested", "Failed"):
            raise DatabaseProcedureError("A closed crop cycle cannot be reopened.", sqlstate="45000")

        if status == "Harvested" and (yield_kg is None or float(yield_kg) < 0):
            raise DatabaseProcedureError("A valid yield is required for a harvested cycle", sqlstate="45000")

        today_str = date.today().isoformat()
        self.raw_cursor.execute(
            """
            UPDATE crop_cycles
            SET status = ?,
                yield_kg = CASE WHEN ? = 'Harvested' THEN ? ELSE yield_kg END,
                selling_price_per_quintal = CASE WHEN ? = 'Harvested' THEN ? ELSE selling_price_per_quintal END,
                actual_harvest = CASE WHEN ? = 'Harvested' THEN ? ELSE actual_harvest END
            WHERE cycle_id = ?
            """,
            (status, status, yield_kg, status, price, status, today_str, cycle_id),
        )

        if old_status != status:
            self.raw_cursor.execute(
                "INSERT INTO crop_cycle_log (cycle_id, old_status, new_status) VALUES (?, ?, ?)",
                (cycle_id, old_status, status),
            )
        if self.conn:
            self.conn.commit()

        updated_row = self.raw_cursor.execute("SELECT * FROM crop_cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()
        self._proc_results = [dict(updated_row) if hasattr(updated_row, "keys") else {}]

    def _handle_recommend_fertilizer(self, params: Any):
        """Emulate recommend_fertilizer procedure for SQLite tests."""
        farm_id = params[0]
        test_id = params[1]
        crop_id = params[2]

        f_row = self.raw_cursor.execute("SELECT area_acres FROM farms WHERE farm_id = ?", (farm_id,)).fetchone()
        if not f_row:
            raise DatabaseProcedureError("Farm not found", sqlstate="45000")
        area = float(f_row[0] if isinstance(f_row, (list, tuple)) else f_row["area_acres"])

        c_row = self.raw_cursor.execute("SELECT n_required, p_required, k_required FROM crops WHERE crop_id = ?", (crop_id,)).fetchone()
        if not c_row:
            raise DatabaseProcedureError("Crop not found", sqlstate="45000")
        req_n = float(c_row[0] if isinstance(c_row, (list, tuple)) else c_row["n_required"])
        req_p = float(c_row[1] if isinstance(c_row, (list, tuple)) else c_row["p_required"])
        req_k = float(c_row[2] if isinstance(c_row, (list, tuple)) else c_row["k_required"])

        t_row = self.raw_cursor.execute("SELECT nitrogen, phosphorus, potassium FROM soil_tests WHERE test_id = ? AND farm_id = ?", (test_id, farm_id)).fetchone()
        if not t_row:
            raise DatabaseProcedureError("Soil test not found for this farm", sqlstate="45000")
        soil_n = float(t_row[0] if isinstance(t_row, (list, tuple)) else t_row["nitrogen"])
        soil_p = float(t_row[1] if isinstance(t_row, (list, tuple)) else t_row["phosphorus"])
        soil_k = float(t_row[2] if isinstance(t_row, (list, tuple)) else t_row["potassium"])

        def_n = max(0.0, req_n - soil_n)
        def_p = max(0.0, req_p - soil_p)
        def_k = max(0.0, req_k - soil_k)

        dap_acre = round(def_p / 0.46, 2) if def_p > 0 else 0.0
        n_from_dap = dap_acre * 0.18
        rem_n = max(0.0, def_n - n_from_dap)
        urea_acre = round(rem_n / 0.46, 2) if rem_n > 0 else 0.0
        mop_acre = round(def_k / 0.60, 2) if def_k > 0 else 0.0

        results = []
        fert_prices = {"DAP": 27.0, "Urea": 6.0, "MOP (Potash)": 34.0}
        for fert, dose in [("DAP", dap_acre), ("Urea", urea_acre), ("MOP (Potash)", mop_acre)]:
            if dose > 0:
                kg_farm = round(dose * area, 2)
                cost = round(kg_farm * fert_prices.get(fert, 20.0), 2)
                results.append({
                    "fertilizer": fert,
                    "kg_per_acre": dose,
                    "kg_for_farm": kg_farm,
                    "estimated_cost": cost,
                })

        self._proc_results = results

    def _handle_rotation_advice(self, params: Any):
        """Emulate rotation_advice procedure for SQLite tests."""
        farm_id = params[0]

        f_row = self.raw_cursor.execute("SELECT 1 FROM farms WHERE farm_id = ?", (farm_id,)).fetchone()
        if not f_row:
            raise DatabaseProcedureError("Farm not found", sqlstate="45000")

        prev_row = self.raw_cursor.execute(
            """
            SELECT crop_id FROM crop_cycles
            WHERE farm_id = ? AND status IN ('Harvested', 'Failed')
            ORDER BY actual_harvest DESC, cycle_id DESC
            LIMIT 1
            """,
            (farm_id,),
        ).fetchone()

        if not prev_row:
            self._proc_results = []
            return

        prev_crop_id = prev_row[0] if isinstance(prev_row, (list, tuple)) else prev_row["crop_id"]

        month = date.today().month
        current_season = "Kharif" if 6 <= month <= 10 else ("Rabi" if month in (11, 12, 1, 2, 3) else "Zaid")

        rules = self.raw_cursor.execute(
            """
            SELECT
                c.crop_id,
                c.crop_name,
                c.season,
                CASE WHEN c.season = ? OR c.season = 'Annual' THEN 1 ELSE 0 END AS is_in_season,
                c.duration_days,
                r.reason
            FROM crop_rotation_rules r
            JOIN crops c ON c.crop_id = r.recommended_crop_id
            WHERE r.previous_crop_id = ?
            ORDER BY is_in_season DESC, c.crop_name ASC
            """,
            (current_season, prev_crop_id),
        ).fetchall()

        self._proc_results = [
            dict(r) if hasattr(r, "keys") else {
                "crop_id": r[0], "crop_name": r[1], "season": r[2],
                "is_in_season": bool(r[3]), "duration_days": r[4], "reason": r[5]
            }
            for r in rules
        ]

    def _handle_generate_task_alerts(self, params: Any):
        """Emulate generate_task_alerts procedure for SQLite tests."""
        days_ahead = int(params[0]) if params and len(params) > 0 and params[0] is not None else 2

        active_cycles = self.raw_cursor.execute(
            """
            SELECT cc.cycle_id, cc.farm_id, cc.crop_id, cc.sowing_date, c.crop_name
            FROM crop_cycles cc
            JOIN crops c ON c.crop_id = cc.crop_id
            WHERE cc.status = 'Growing' AND cc.sowing_date IS NOT NULL
            """
        ).fetchall()

        count = 0
        today = date.today()
        for c in active_cycles:
            cid = c[0] if isinstance(c, (list, tuple)) else c["cycle_id"]
            fid = c[1] if isinstance(c, (list, tuple)) else c["farm_id"]
            c_crop_id = c[2] if isinstance(c, (list, tuple)) else c["crop_id"]
            sow_str = c[3] if isinstance(c, (list, tuple)) else c["sowing_date"]
            c_name = c[4] if isinstance(c, (list, tuple)) else c["crop_name"]

            try:
                sow_dt = date.fromisoformat(str(sow_str))
                days_since = (today - sow_dt).days
            except Exception:
                continue

            stages = self.raw_cursor.execute(
                """
                SELECT stage_id, stage_name, start_day, end_day, task
                FROM crop_stages
                WHERE crop_id = ?
                """,
                (c_crop_id,),
            ).fetchall()

            for s in stages:
                sid = s[0] if isinstance(s, (list, tuple)) else s["stage_id"]
                sname = s[1] if isinstance(s, (list, tuple)) else s["stage_name"]
                start_day = s[2] if isinstance(s, (list, tuple)) else s["start_day"]
                end_day = s[3] if isinstance(s, (list, tuple)) else s["end_day"]
                task = s[4] if isinstance(s, (list, tuple)) else s["task"]

                if (start_day <= days_since <= end_day) or (days_since <= start_day <= days_since + days_ahead):
                    dedupe = f"task_{cid}_{sid}_{today.isoformat()}"
                    msg = f"{c_name} ({sname}): {task}"
                    self.raw_cursor.execute(
                        """
                        INSERT OR IGNORE INTO alerts (farm_id, alert_type, message, dedupe_key)
                        VALUES (?, 'Task', ?, ?)
                        """,
                        (fid, msg, dedupe),
                    )
                    count += 1

        if self.conn:
            self.conn.commit()
        self._proc_results = [{"alerts_generated": count}]

    def _handle_estimate_crop_profit(self, params: Any):
        """Emulate estimate_crop_profit procedure for SQLite tests."""
        farm_id = params[0]
        crop_id = params[1]

        f_row = self.raw_cursor.execute(
            """
            SELECT f.farm_id, f.farm_name, f.area_acres, fm.district
            FROM farms f
            JOIN farmers fm ON f.farmer_id = fm.farmer_id
            WHERE f.farm_id = ?
            """,
            (farm_id,)
        ).fetchone()
        if not f_row:
            raise DatabaseProcedureError("Farm not found", sqlstate="45000")

        c_row = self.raw_cursor.execute(
            "SELECT crop_id, crop_name, duration_days, avg_yield_q_per_acre, est_cost_per_acre FROM crops WHERE crop_id = ?",
            (crop_id,)
        ).fetchone()
        if not c_row:
            raise DatabaseProcedureError("Crop not found", sqlstate="45000")

        f_dict = dict(f_row) if hasattr(f_row, "keys") else {"farm_id": f_row[0], "farm_name": f_row[1], "area_acres": f_row[2], "district": f_row[3]}
        c_dict = dict(c_row) if hasattr(c_row, "keys") else {"crop_id": c_row[0], "crop_name": c_row[1], "duration_days": c_row[2], "avg_yield_q_per_acre": c_row[3], "est_cost_per_acre": c_row[4]}

        p_row = self.raw_cursor.execute(
            """
            SELECT price_per_quintal, price_date
            FROM market_prices
            WHERE crop_id = ? AND district = ?
            ORDER BY price_date DESC, price_id DESC
            LIMIT 1
            """,
            (crop_id, f_dict["district"])
        ).fetchone()

        is_district = 1
        if not p_row:
            p_row = self.raw_cursor.execute(
                """
                SELECT price_per_quintal, price_date
                FROM market_prices
                WHERE crop_id = ?
                ORDER BY price_date DESC, price_id DESC
                LIMIT 1
                """,
                (crop_id,)
            ).fetchone()
            is_district = 0

        yield_val = float(c_dict.get("avg_yield_q_per_acre") or 0)
        cost_val = float(c_dict.get("est_cost_per_acre") or 0)
        area_val = float(f_dict.get("area_acres") or 0)
        dur_val = int(c_dict.get("duration_days") or 100)

        if p_row:
            price_val = float(p_row[0] if isinstance(p_row, (list, tuple)) else p_row["price_per_quintal"])
            p_date = p_row[1] if isinstance(p_row, (list, tuple)) else p_row["price_date"]
            rev_acre = round(yield_val * price_val, 2)
            profit_acre = round(rev_acre - cost_val, 2)
            profit_month = round(profit_acre / (dur_val / 30.0), 2)
            tot_profit = round(profit_acre * area_val, 2)
        else:
            price_val = None
            p_date = None
            is_district = None
            rev_acre = None
            profit_acre = None
            profit_month = None
            tot_profit = None

        self._proc_results = [{
            "farm_id": f_dict["farm_id"],
            "farm_name": f_dict["farm_name"],
            "area_acres": area_val,
            "district": f_dict["district"],
            "crop_id": c_dict["crop_id"],
            "crop_name": c_dict["crop_name"],
            "duration_days": dur_val,
            "avg_yield_q_per_acre": yield_val if c_dict.get("avg_yield_q_per_acre") is not None else None,
            "est_cost_per_acre": cost_val if c_dict.get("est_cost_per_acre") is not None else None,
            "market_price_per_q": price_val,
            "price_date": p_date,
            "is_district_price": is_district,
            "gross_revenue_per_acre": rev_acre,
            "net_profit_per_acre": profit_acre,
            "profit_per_acre_per_month": profit_month,
            "total_farm_profit": tot_profit,
        }]

    def _handle_profit_for_recommendations(self, params: Any):
        """Emulate profit_for_recommendations procedure for SQLite tests."""
        farm_id = params[0]
        f_row = self.raw_cursor.execute(
            """
            SELECT f.farm_id, f.farm_name, f.area_acres, fm.district
            FROM farms f
            JOIN farmers fm ON f.farmer_id = fm.farmer_id
            WHERE f.farm_id = ?
            """,
            (farm_id,)
        ).fetchone()
        if not f_row:
            raise DatabaseProcedureError("Farm not found", sqlstate="45000")

        f_dict = dict(f_row) if hasattr(f_row, "keys") else {"farm_id": f_row[0], "farm_name": f_row[1], "area_acres": f_row[2], "district": f_row[3]}
        area_val = float(f_dict.get("area_acres") or 0)

        preds = self.raw_cursor.execute(
            """
            SELECT
                p.prediction_id,
                p.crop_id,
                c.crop_name,
                p.suitability_score,
                p.rank_no,
                c.season,
                c.duration_days,
                c.avg_yield_q_per_acre,
                c.est_cost_per_acre
            FROM predictions p
            JOIN crops c ON p.crop_id = c.crop_id
            WHERE p.farm_id = ?
            ORDER BY p.predicted_on DESC, p.rank_no ASC
            LIMIT 5
            """,
            (farm_id,)
        ).fetchall()

        if not preds:
            self._proc_results = []
            return

        results = []
        for r in preds:
            rd = dict(r) if hasattr(r, "keys") else {
                "prediction_id": r[0], "crop_id": r[1], "crop_name": r[2],
                "suitability_score": r[3], "rank_no": r[4], "season": r[5],
                "duration_days": r[6], "avg_yield_q_per_acre": r[7], "est_cost_per_acre": r[8]
            }
            c_id = rd["crop_id"]
            p_row = self.raw_cursor.execute(
                """
                SELECT price_per_quintal, price_date
                FROM market_prices
                WHERE crop_id = ? AND district = ?
                ORDER BY price_date DESC, price_id DESC
                LIMIT 1
                """,
                (c_id, f_dict["district"])
            ).fetchone()

            is_district = 1
            if not p_row:
                p_row = self.raw_cursor.execute(
                    """
                    SELECT price_per_quintal, price_date
                    FROM market_prices
                    WHERE crop_id = ?
                    ORDER BY price_date DESC, price_id DESC
                    LIMIT 1
                    """,
                    (c_id,)
                ).fetchone()
                is_district = 0

            yield_val = float(rd.get("avg_yield_q_per_acre") or 0)
            cost_val = float(rd.get("est_cost_per_acre") or 0)
            dur_val = int(rd.get("duration_days") or 100)

            if p_row:
                price_val = float(p_row[0] if isinstance(p_row, (list, tuple)) else p_row["price_per_quintal"])
                p_date = p_row[1] if isinstance(p_row, (list, tuple)) else p_row["price_date"]
                rev_acre = round(yield_val * price_val, 2)
                profit_acre = round(rev_acre - cost_val, 2)
                profit_month = round(profit_acre / (dur_val / 30.0), 2)
                tot_profit = round(profit_acre * area_val, 2)
            else:
                price_val = None
                p_date = None
                is_district = None
                rev_acre = None
                profit_acre = None
                profit_month = None
                tot_profit = None

            results.append({
                "recommendation_id": rd["prediction_id"],
                "prediction_id": rd["prediction_id"],
                "crop_id": c_id,
                "crop_name": rd["crop_name"],
                "confidence_score": rd["suitability_score"],
                "rank_order": rd["rank_no"],
                "season": rd["season"],
                "area_acres": area_val,
                "district": f_dict["district"],
                "avg_yield_q_per_acre": yield_val if rd.get("avg_yield_q_per_acre") is not None else None,
                "est_cost_per_acre": cost_val if rd.get("est_cost_per_acre") is not None else None,
                "market_price_per_q": price_val,
                "price_date": p_date,
                "is_district_price": is_district,
                "gross_revenue_per_acre": rev_acre,
                "net_profit_per_acre": profit_acre,
                "profit_per_acre_per_month": profit_month,
                "total_farm_profit": tot_profit,
            })

        self._proc_results = results

    def fetchone(self) -> Optional[Dict[str, Any]]:
        if self._proc_results:
            return self._proc_results.pop(0)
        row = self.raw_cursor.fetchone()
        if row is None:
            return None
        if self.dictionary:
            return dict(row)
        return row

    def fetchall(self) -> List[Any]:
        if self._proc_results:
            res = list(self._proc_results)
            self._proc_results = []
            return res
        rows = self.raw_cursor.fetchall()
        if self.dictionary:
            return [dict(r) for r in rows]
        return rows

    def nextset(self) -> bool:
        return False

    def close(self):
        self.raw_cursor.close()


class SQLiteTestConnection:
    """Connection wrapper for SQLite in tests."""

    def __init__(self, raw_conn: sqlite3.Connection):
        self.raw_conn = raw_conn

    def cursor(self, dictionary: bool = True):
        raw_cur = self.raw_conn.cursor()
        return SQLiteTestCursor(raw_cur, dictionary=dictionary, conn=self.raw_conn)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        pass


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS farmers (
    farmer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    phone          TEXT NOT NULL UNIQUE,
    email          TEXT UNIQUE,
    password_hash  TEXT NOT NULL,
    district       TEXT,
    village        TEXT,
    language       TEXT DEFAULT 'en',
    role           TEXT DEFAULT 'farmer',
    is_active      INTEGER DEFAULT 1,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farms (
    farm_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id    INTEGER NOT NULL,
    farm_name    TEXT NOT NULL,
    area_acres   REAL CHECK (area_acres > 0),
    latitude     REAL,
    longitude    REAL,
    soil_type    TEXT,
    irrigation   TEXT DEFAULT 'Rainfed',
    FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS soil_tests (
    test_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id        INTEGER NOT NULL,
    test_date      DATE NOT NULL,
    nitrogen       REAL CHECK (nitrogen >= 0),
    phosphorus     REAL CHECK (phosphorus >= 0),
    potassium      REAL CHECK (potassium >= 0),
    ph             REAL CHECK (ph BETWEEN 0 AND 14),
    moisture       REAL CHECK (moisture BETWEEN 0 AND 100),
    organic_carbon REAL,
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weather_records (
    weather_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id      INTEGER NOT NULL,
    record_date  DATE NOT NULL,
    temperature  REAL,
    humidity     REAL,
    rainfall_mm  REAL,
    source       TEXT DEFAULT 'api',
    UNIQUE (farm_id, record_date),
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crops (
    crop_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name      TEXT NOT NULL UNIQUE,
    season         TEXT NOT NULL,
    duration_days  INTEGER NOT NULL,
    min_ph REAL, max_ph REAL,
    min_temp REAL, max_temp REAL,
    min_humidity REAL, max_humidity REAL,
    min_rainfall REAL, max_rainfall REAL,
    n_required INTEGER, p_required INTEGER, k_required INTEGER,
    avg_yield_q_per_acre REAL,
    est_cost_per_acre REAL
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id           INTEGER NOT NULL,
    test_id           INTEGER NOT NULL,
    weather_id        INTEGER,
    crop_id           INTEGER NOT NULL,
    suitability_score REAL NOT NULL,
    rank_no           INTEGER NOT NULL,
    predicted_on      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES soil_tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id)
);

CREATE TABLE IF NOT EXISTS crop_cycles (
    cycle_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id                   INTEGER NOT NULL,
    crop_id                   INTEGER NOT NULL,
    prediction_id             INTEGER,
    sowing_date               DATE,
    expected_harvest          DATE,
    actual_harvest            DATE,
    status                    TEXT NOT NULL DEFAULT 'Planned',
    yield_kg                  REAL,
    selling_price_per_quintal REAL,
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS crop_cycle_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id    INTEGER NOT NULL,
    old_status  TEXT,
    new_status  TEXT NOT NULL,
    changed_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id) REFERENCES crop_cycles(cycle_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    expense_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id     INTEGER NOT NULL,
    category     TEXT NOT NULL,
    amount       REAL NOT NULL CHECK (amount >= 0),
    expense_date DATE NOT NULL,
    notes        TEXT,
    FOREIGN KEY (cycle_id) REFERENCES crop_cycles(cycle_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crop_stages (
    stage_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id    INTEGER NOT NULL,
    stage_name TEXT NOT NULL,
    start_day  INTEGER NOT NULL,
    end_day    INTEGER NOT NULL,
    task       TEXT,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS translations (
    text_key TEXT NOT NULL,
    lang     TEXT NOT NULL,
    text     TEXT NOT NULL,
    PRIMARY KEY (text_key, lang)
);

CREATE TABLE IF NOT EXISTS fertilizers (
    fert_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    n_pct        REAL NOT NULL DEFAULT 0.0,
    p_pct        REAL NOT NULL DEFAULT 0.0,
    k_pct        REAL NOT NULL DEFAULT 0.0,
    price_per_kg REAL
);

CREATE TABLE IF NOT EXISTS crop_rotation_rules (
    rule_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    previous_crop_id    INTEGER NOT NULL,
    recommended_crop_id INTEGER NOT NULL,
    reason              TEXT,
    FOREIGN KEY (previous_crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id        INTEGER NOT NULL,
    alert_type     TEXT NOT NULL,
    message        TEXT NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read        INTEGER NOT NULL DEFAULT 0,
    dedupe_key     TEXT UNIQUE,
    FOREIGN KEY (farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS market_prices (
    price_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id           INTEGER NOT NULL,
    district          TEXT NOT NULL,
    price_per_quintal REAL NOT NULL,
    price_date        DATE NOT NULL,
    UNIQUE (crop_id, district, price_date),
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id  INTEGER NOT NULL,
    action     TEXT NOT NULL,
    old_data   TEXT,
    new_data   TEXT,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER IF NOT EXISTS trg_weather_ai AFTER INSERT ON weather_records
BEGIN
    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Rain',
           'Heavy rainfall alert (' || NEW.rainfall_mm || ' mm) recorded on ' || NEW.record_date || '. Ensure adequate drainage in fields.',
           'rain_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.rainfall_mm IS NOT NULL AND NEW.rainfall_mm >= 50.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Heat',
           'High temperature alert (' || NEW.temperature || '°C) on ' || NEW.record_date || '. Ensure frequent light irrigation to prevent crop heat stress.',
           'heat_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature IS NOT NULL AND NEW.temperature >= 38.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Frost',
           'Frost warning (' || NEW.temperature || '°C) on ' || NEW.record_date || '. Protect sensitive crops from cold injury.',
           'frost_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature IS NOT NULL AND NEW.temperature <= 4.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Drought',
           'Dry weather / drought alert on ' || NEW.record_date || ' (Temp: ' || NEW.temperature || '°C, Humidity: ' || NEW.humidity || '%). Soil moisture conservation advised.',
           'drought_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature >= 35.0 AND NEW.humidity IS NOT NULL AND NEW.humidity < 25.0
      AND (NEW.rainfall_mm IS NULL OR NEW.rainfall_mm = 0);
END;

CREATE TRIGGER IF NOT EXISTS trg_weather_au AFTER UPDATE ON weather_records
BEGIN
    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Rain',
           'Heavy rainfall alert (' || NEW.rainfall_mm || ' mm) recorded on ' || NEW.record_date || '. Ensure adequate drainage in fields.',
           'rain_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.rainfall_mm IS NOT NULL AND NEW.rainfall_mm >= 50.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Heat',
           'High temperature alert (' || NEW.temperature || '°C) on ' || NEW.record_date || '. Ensure frequent light irrigation to prevent crop heat stress.',
           'heat_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature IS NOT NULL AND NEW.temperature >= 38.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Frost',
           'Frost warning (' || NEW.temperature || '°C) on ' || NEW.record_date || '. Protect sensitive crops from cold injury.',
           'frost_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature IS NOT NULL AND NEW.temperature <= 4.0;

    INSERT OR REPLACE INTO alerts (farm_id, alert_type, message, dedupe_key)
    SELECT NEW.farm_id, 'Drought',
           'Dry weather / drought alert on ' || NEW.record_date || ' (Temp: ' || NEW.temperature || '°C, Humidity: ' || NEW.humidity || '%). Soil moisture conservation advised.',
           'drought_' || NEW.farm_id || '_' || NEW.record_date
    WHERE NEW.temperature >= 35.0 AND NEW.humidity IS NOT NULL AND NEW.humidity < 25.0
      AND (NEW.rainfall_mm IS NULL OR NEW.rainfall_mm = 0);
END;

CREATE VIEW IF NOT EXISTS current_status_view AS
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
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > date('now') THEN NULL
    ELSE CAST((julianday('now') - julianday(cc.sowing_date)) AS INTEGER)
  END AS days_since_sowing,
  CASE
    WHEN cc.sowing_date > date('now') THEN CAST((julianday(cc.sowing_date) - julianday('now')) AS INTEGER)
    ELSE NULL
  END AS days_until_sowing,
  CASE
    WHEN cc.expected_harvest IS NULL THEN NULL
    ELSE CAST((julianday(cc.expected_harvest) - julianday('now')) AS INTEGER)
  END AS days_to_harvest,
  CASE
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > date('now') THEN 0.0
    ELSE ROUND(MIN(100.0, ((100.0 * (julianday('now') - julianday(cc.sowing_date))) / c.duration_days)), 1)
  END AS progress_pct,
  CASE
    WHEN cc.sowing_date IS NULL OR cc.sowing_date > date('now') THEN 'Not sown yet'
    ELSE COALESCE(
      (SELECT cs.stage_name
       FROM crop_stages cs
       WHERE cs.crop_id = cc.crop_id
         AND CAST((julianday('now') - julianday(cc.sowing_date)) AS INTEGER) BETWEEN cs.start_day AND cs.end_day
       LIMIT 1),
      'No stage data'
    )
  END AS current_stage,
  (SELECT cs.task
   FROM crop_stages cs
   WHERE cs.crop_id = cc.crop_id
     AND cc.sowing_date IS NOT NULL
     AND CAST((julianday('now') - julianday(cc.sowing_date)) AS INTEGER) BETWEEN cs.start_day AND cs.end_day
   LIMIT 1) AS current_task,
  COALESCE(
    (SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id),
    0.0
  ) AS expenses_so_far
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
WHERE cc.status IN ('Planned', 'Growing');

CREATE VIEW IF NOT EXISTS farmer_history_view AS
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
  ROUND(COALESCE(((cc.yield_kg / 100.0) * cc.selling_price_per_quintal), 0.0), 2) AS revenue,
  COALESCE(
    (SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id),
    0.0
  ) AS total_expenses,
  ROUND(
    COALESCE(((cc.yield_kg / 100.0) * cc.selling_price_per_quintal), 0.0) -
    COALESCE((SELECT SUM(e.amount) FROM expenses e WHERE e.cycle_id = cc.cycle_id), 0.0),
    2
  ) AS profit
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
WHERE cc.status IN ('Harvested', 'Failed');

CREATE VIEW IF NOT EXISTS farmer_summary_view AS
SELECT
  f.farmer_id AS farmer_id,
  f.name AS name,
  (SELECT COUNT(*) FROM farms x WHERE x.farmer_id = f.farmer_id) AS total_farms,
  (SELECT COUNT(*) FROM current_status_view v WHERE v.farmer_id = f.farmer_id) AS active_cycles,
  (SELECT COUNT(*) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id) AS completed_cycles,
  COALESCE((SELECT SUM(h.revenue) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0.0) AS total_revenue,
  COALESCE((SELECT SUM(h.total_expenses) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0.0) AS total_expenses,
  COALESCE((SELECT SUM(h.profit) FROM farmer_history_view h WHERE h.farmer_id = f.farmer_id), 0.0) AS net_profit
FROM farmers f
WHERE f.role = 'farmer';

CREATE VIEW IF NOT EXISTS crop_calendar_view AS
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
  CASE WHEN cc.sowing_date IS NOT NULL THEN date(cc.sowing_date, '+' || cs.start_day || ' days') ELSE NULL END AS start_date,
  CASE WHEN cc.sowing_date IS NOT NULL THEN date(cc.sowing_date, '+' || cs.end_day || ' days') ELSE NULL END AS end_date,
  CASE
    WHEN cc.sowing_date IS NULL THEN 'Upcoming'
    WHEN date('now') > date(cc.sowing_date, '+' || cs.end_day || ' days') THEN 'Done'
    WHEN date('now') < date(cc.sowing_date, '+' || cs.start_day || ' days') THEN 'Upcoming'
    ELSE 'Current'
  END AS stage_status,
  cs.task AS task
FROM crop_cycles cc
JOIN farms fm ON fm.farm_id = cc.farm_id
JOIN farmers f ON f.farmer_id = fm.farmer_id
JOIN crops c ON c.crop_id = cc.crop_id
JOIN crop_stages cs ON cs.crop_id = cc.crop_id;

CREATE VIEW IF NOT EXISTS latest_prices_view AS
SELECT
    mp.price_id,
    mp.crop_id,
    c.crop_name,
    mp.district,
    mp.price_per_quintal,
    mp.price_date
FROM market_prices mp
JOIN crops c ON mp.crop_id = c.crop_id
WHERE (mp.crop_id, mp.district, mp.price_date) IN (
    SELECT crop_id, district, MAX(price_date)
    FROM market_prices
    GROUP BY crop_id, district
);

CREATE VIEW IF NOT EXISTS cycle_expense_summary_view AS
SELECT
    f.farmer_id,
    c.farm_id,
    e.cycle_id,
    cr.crop_name,
    e.category,
    ROUND(SUM(e.amount), 2) AS category_total,
    ROUND(SUM(e.amount) / NULLIF(ct.total_cycle_expense, 0) * 100, 2) AS pct_of_cycle
FROM expenses e
JOIN crop_cycles c ON e.cycle_id = c.cycle_id
JOIN farms f ON c.farm_id = f.farm_id
JOIN crops cr ON c.crop_id = cr.crop_id
LEFT JOIN (
    SELECT cycle_id, SUM(amount) AS total_cycle_expense
    FROM expenses
    GROUP BY cycle_id
) ct ON e.cycle_id = ct.cycle_id
GROUP BY f.farmer_id, c.farm_id, e.cycle_id, cr.crop_name, e.category, ct.total_cycle_expense;

CREATE VIEW IF NOT EXISTS crop_localized_view AS
SELECT c.crop_id, c.crop_name, t.lang, t.text AS localized_name
FROM crops c
JOIN translations t
  ON t.text_key = 'crop_' || lower(replace(c.crop_name, ' ', '_'));
"""

CROPS_SEED_SQL = """
INSERT OR IGNORE INTO crops
(crop_id, crop_name, season, duration_days, min_ph, max_ph, min_temp, max_temp, min_humidity, max_humidity, min_rainfall, max_rainfall, n_required, p_required, k_required, avg_yield_q_per_acre, est_cost_per_acre)
VALUES
(1,  'Rice',        'Kharif', 120, 5.5, 7.0, 20, 30, 70, 90, 150, 300,  80, 48, 40,  25.00, 18000.00),
(2,  'Maize',       'Kharif', 100, 5.5, 7.0, 18, 27, 55, 75,  60, 110,  78, 48, 20,  28.00, 15000.00),
(3,  'Wheat',       'Rabi',   120, 6.0, 7.5, 12, 25, 40, 70,  30, 100, 100, 50, 40,  22.00, 16000.00),
(4,  'Soybean',     'Kharif', 100, 6.0, 7.0, 20, 30, 60, 85,  60, 120,  25, 60, 40,  12.00, 14000.00),
(5,  'Cotton',      'Kharif', 180, 5.8, 8.0, 21, 30, 60, 85,  60, 110, 118, 46, 20,  10.00, 22000.00),
(6,  'Sugarcane',   'Annual', 365, 6.5, 7.5, 20, 32, 60, 85,  75, 150, 120, 60, 60, 350.00, 45000.00),
(7,  'Chickpea',    'Rabi',   100, 6.0, 8.0, 15, 25, 15, 50,  60, 100,  40, 68, 80,   8.00, 12000.00),
(8,  'Pigeon Pea',  'Kharif', 150, 5.0, 7.0, 20, 32, 40, 65, 100, 200,  21, 68, 20,   7.00, 13000.00),
(9,  'Groundnut',   'Kharif', 110, 6.0, 7.0, 22, 30, 50, 75,  50, 100,  25, 50, 75,  10.00, 16000.00),
(10, 'Jowar',       'Kharif', 110, 6.0, 8.0, 25, 33, 40, 70,  40,  90,  80, 40, 40,  14.00, 11000.00),
(11, 'Bajra',       'Kharif',  85, 6.0, 8.0, 25, 35, 40, 65,  40,  80,  60, 30, 30,  12.00, 10000.00),
(12, 'Onion',       'Rabi',   120, 6.0, 7.5, 13, 28, 50, 75,  30,  80, 100, 50, 60,  80.00, 28000.00),
(13, 'Tomato',      'Rabi',   110, 6.0, 7.0, 18, 30, 55, 80,  40, 100, 100, 60, 80, 100.00, 32000.00),
(14, 'Moong',       'Zaid',    65, 6.2, 7.2, 25, 32, 65, 90,  30,  80,  21, 47, 20,   5.00, 10000.00),
(15, 'Urad',        'Kharif',  80, 6.5, 7.5, 25, 35, 55, 75,  50,  90,  40, 67, 19,   5.00, 10000.00),
(16, 'Lentil',      'Rabi',   110, 6.0, 7.5, 18, 30, 50, 75,  30,  70,  19, 68, 19,   6.00, 11000.00),
(17, 'Banana',      'Annual', 300, 5.5, 7.0, 24, 32, 70, 90,  80, 150, 100, 82, 50, 180.00, 50000.00),
(18, 'Grapes',      'Annual', 150, 5.5, 6.5, 20, 28, 65, 85,  50,  90,  23, 132, 200, 90.00, 65000.00),
(19, 'Watermelon',  'Zaid',    90, 6.0, 7.0, 22, 30, 70, 90,  40,  70, 100, 17, 50, 120.00, 25000.00),
(20, 'Mango',       'Annual', 150, 5.5, 7.5, 24, 35, 40, 65,  70, 120,  20, 27, 30,  50.00, 30000.00);

INSERT OR IGNORE INTO translations (text_key, lang, text) VALUES
('current_status', 'en', 'Current Status'),
('current_status', 'mr', 'सद्यस्थिती'),
('current_status', 'hi', 'वर्तमान स्थिति'),
('history', 'en', 'History'),
('history', 'mr', 'इतिहास'),
('history', 'hi', 'इतिहास'),
('login', 'en', 'Login'),
('login', 'mr', 'लॉगिन'),
('login', 'hi', 'लॉगिन'),
('my_farms', 'en', 'My Farms'),
('my_farms', 'mr', 'माझी शेती'),
('my_farms', 'hi', 'मेरे खेत'),
('recommend_crop', 'en', 'Recommend Crop'),
('recommend_crop', 'mr', 'पीक शिफारस'),
('recommend_crop', 'hi', 'फसल सिफारिश'),
('register', 'en', 'Register'),
('register', 'mr', 'नोंदणी करा'),
('register', 'hi', 'पंजीकरण करें'),
('crop_rice', 'en', 'Rice'),
('crop_rice', 'mr', 'भात'),
('crop_rice', 'hi', 'धान'),
('crop_cotton', 'en', 'Cotton'),
('crop_cotton', 'mr', 'कापूस'),
('crop_cotton', 'hi', 'कपास'),
('cat_seeds', 'en', 'Seeds'),
('cat_seeds', 'mr', 'बियाणे'),
('cat_seeds', 'hi', 'बीज'),
('alert_rain', 'en', 'Heavy Rain'),
('alert_rain', 'mr', 'मुसळधार पाऊस'),
('alert_rain', 'hi', 'भारी वर्षा'),
('season_kharif', 'en', 'Kharif'),
('season_kharif', 'mr', 'खरीप'),
('season_kharif', 'hi', 'खरीफ');

INSERT OR IGNORE INTO crop_stages (stage_id, crop_id, stage_name, start_day, end_day, task) VALUES
(1, 1, 'Vegetative', 0, 30, 'Apply Nitrogen & ensure adequate water standing'),
(2, 1, 'Reproductive', 31, 75, 'Monitor for stem borer and maintain water'),
(3, 1, 'Ripening', 76, 120, 'Drain excess water 10 days before harvest'),
(4, 3, 'Crown Root Initiation (CRI)', 0, 25, 'First critical irrigation (20-25 DAS) and top-dress 1/3 Nitrogen'),
(5, 3, 'Tillering & Jointing', 26, 60, 'Weed management and second top-dressing of Urea'),
(6, 3, 'Heading & Flowering', 61, 90, 'Crucial irrigation during flowering stage; watch for rust'),
(7, 3, 'Grain Filling & Maturity', 91, 120, 'Stop irrigation 10-15 days prior to harvesting');

INSERT OR IGNORE INTO fertilizers (fert_id, name, n_pct, p_pct, k_pct, price_per_kg) VALUES
(1, 'Urea', 46.00, 0.00, 0.00, 6.00),
(2, 'DAP', 18.00, 46.00, 0.00, 27.00),
(3, 'MOP (Potash)', 0.00, 0.00, 60.00, 34.00);

INSERT OR IGNORE INTO crop_rotation_rules (rule_id, previous_crop_id, recommended_crop_id, reason) VALUES
(1, 1, 7, 'Chickpea fixes atmospheric nitrogen depleted by paddy and breaks pest cycles'),
(2, 1, 16, 'Lentil improves soil fertility and requires low water post-paddy'),
(3, 3, 4, 'Soybean enriches nitrogen and breaks cereal monoculture'),
(4, 3, 14, 'Moong bean matures quickly in Zaid and restores nitrogen'),
(5, 5, 9, 'Groundnut replenishes soil nutrients heavily mined by cotton');
"""


@pytest.fixture(scope="session")
def sqlite_test_db():
    """Create a persistent in-memory SQLite database with full schema and seed data."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(CROPS_SEED_SQL)
    conn.commit()
    return conn


@pytest.fixture(autouse=True)
def setup_test_database(sqlite_test_db):
    """Reset test database tables (preserving seed crops and translations) before each test."""
    sqlite_test_db.execute("DELETE FROM admin_audit_log")
    sqlite_test_db.execute("DELETE FROM market_prices")
    sqlite_test_db.execute("DELETE FROM alerts")
    sqlite_test_db.execute("DELETE FROM crop_cycle_log")
    sqlite_test_db.execute("DELETE FROM expenses")
    sqlite_test_db.execute("DELETE FROM crop_cycles")
    sqlite_test_db.execute("DELETE FROM predictions")
    sqlite_test_db.execute("DELETE FROM weather_records")
    sqlite_test_db.execute("DELETE FROM soil_tests")
    sqlite_test_db.execute("DELETE FROM farms")
    sqlite_test_db.execute("DELETE FROM farmers")
    sqlite_test_db.commit()

    wrapper = SQLiteTestConnection(sqlite_test_db)
    db.set_connection_provider(lambda: wrapper)
    yield
    db.set_connection_provider(None)


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)

