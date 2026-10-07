#!/usr/bin/env python3
"""Seed Demo Data for AgriPredict Showcase.

Creates:
  - 1 Demo Farmer (Ramesh Patil, phone: 9876543210, pass: Demo@1234, language: Marathi)
  - 2 Farms (Ganga Plot - 3.5 acres Loamy Drip, Yamuna Plot - 2.0 acres Black Canal)
  - Soil tests for both farms
  - 30 days of historical weather data
  - 1 Active Growing cycle (Cotton) with realistic input expenses & stage tracking
  - 1 Completed Harvested cycle (Soybean) with yield, selling price, expenses & profit
  - Real-time advisory & weather alerts

Safety constraint:
  Refuses to run if the database already contains more than 5 farmers.
"""

from datetime import date, timedelta
import random
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app import db
from app.security import hash_password

MAX_FARMERS_LIMIT = 5


def seed_demo_data():
    print("=" * 65)
    print("AgriPredict Demo Seeder")
    print("=" * 65)

    demo_phone = "9876543210"
    existing_demo = db.fetch_one("SELECT farmer_id FROM farmers WHERE phone = %s", (demo_phone,))

    # Clean up existing demo farmer if re-seeding
    if existing_demo:
        old_id = existing_demo.get("farmer_id") if isinstance(existing_demo, dict) else existing_demo[0]
        print(f"[*] Existing demo farmer found (ID #{old_id}). Cleaning up old records...")
        db.execute_query("DELETE FROM farmers WHERE farmer_id = %s", (old_id,), commit=True)
        print("[+] Previous demo records removed cleanly.")

    # 1. Safety check: Enforce the maximum of 5 farmers
    count_row = db.fetch_one("SELECT COUNT(*) AS total FROM farmers")
    current_count = count_row.get("total", 0) if isinstance(count_row, dict) else count_row[0]

    if current_count > MAX_FARMERS_LIMIT:
        print(f"\n[!] Error: Database already contains {current_count} farmers.")
        print(f"    Safety limit is {MAX_FARMERS_LIMIT} farmers. Refusing to seed demo data.\n")
        sys.exit(1)

    print(f"[+] Farmer count check passed ({current_count} existing, max {MAX_FARMERS_LIMIT}).")

    # 2. Insert Demo Farmer
    password_clear = "Demo@1234"
    password_hashed = hash_password(password_clear)
    farmer_query = """
        INSERT INTO farmers (name, phone, email, password_hash, district, village, language, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'farmer', 1)
    """
    farmer_params = (
        "Ramesh Patil",
        demo_phone,
        "ramesh.patil@agripredict.in",
        password_hashed,
        "Wardha",
        "Sevagram",
        "mr",
    )
    farmer_id = db.execute_insert(farmer_query, farmer_params)
    print(f"[+] Created Demo Farmer: Ramesh Patil (ID #{farmer_id}, Phone: {demo_phone}, Lang: Marathi)")

    # 3. Insert 2 Farms
    farm_query = """
        INSERT INTO farms (farmer_id, farm_name, area_acres, soil_type, irrigation, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    farm1_id = db.execute_insert(
        farm_query,
        (farmer_id, "Ganga Plot (Main Field)", 3.50, "Loamy", "Drip", 20.745300, 78.602200),
    )
    farm2_id = db.execute_insert(
        farm_query,
        (farmer_id, "Yamuna Plot (Canal Field)", 2.00, "Black", "Canal", 20.751000, 78.614000),
    )
    print(f"[+] Created Farm 1: Ganga Plot (ID #{farm1_id}, 3.5 acres, Loamy, Drip)")
    print(f"[+] Created Farm 2: Yamuna Plot (ID #{farm2_id}, 2.0 acres, Black, Canal)")

    today = date.today()

    # 4. Insert Soil Tests
    soil_query = """
        INSERT INTO soil_tests (farm_id, test_date, nitrogen, phosphorus, potassium, ph, moisture, organic_carbon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    soil1_date = today - timedelta(days=35)
    soil2_date = today - timedelta(days=20)
    db.execute_insert(soil_query, (farm1_id, soil1_date, 48.0, 24.0, 175.0, 6.8, 42.0, 0.65))
    db.execute_insert(soil_query, (farm2_id, soil2_date, 62.0, 32.0, 210.0, 7.2, 48.0, 0.72))
    print("[+] Recorded soil test chemistry for both farms.")

    # 5. Insert 30 Days of Historical Weather for Farm 1
    weather_query = """
        INSERT INTO weather_records (farm_id, record_date, temperature, humidity, rainfall_mm, source)
        VALUES (%s, %s, %s, %s, %s, 'api')
        ON DUPLICATE KEY UPDATE
            temperature = VALUES(temperature),
            humidity = VALUES(humidity),
            rainfall_mm = VALUES(rainfall_mm)
    """
    random.seed(42)  # Deterministic realistic demo data
    for i in range(30, 0, -1):
        rec_date = today - timedelta(days=i)
        temp = round(28.0 + random.uniform(-2.5, 4.5), 1)
        hum = round(62.0 + random.uniform(-8.0, 15.0), 1)
        rain = round(random.uniform(0.0, 14.0) if random.random() < 0.25 else 0.0, 1)
        db.execute_query(weather_query, (farm1_id, rec_date, temp, hum, rain), commit=False)
    db.execute_query("COMMIT", commit=False)
    print("[+] Inserted 30 days of weather telemetry for Farm 1.")

    # 6. Retrieve Crops
    cotton_row = db.fetch_one("SELECT crop_id, duration_days FROM crops WHERE crop_name = 'Cotton'")
    soybean_row = db.fetch_one("SELECT crop_id, duration_days FROM crops WHERE crop_name = 'Soybean'")

    cotton_id = cotton_row["crop_id"] if cotton_row else 1
    cotton_days = cotton_row["duration_days"] if cotton_row else 160

    soybean_id = soybean_row["crop_id"] if soybean_row else 2
    soybean_days = soybean_row["duration_days"] if soybean_row else 105

    # 7. Insert 1 Growing Cycle (Cotton on Farm 1)
    cotton_sowing = today - timedelta(days=45)
    cotton_harvest = cotton_sowing + timedelta(days=cotton_days)
    cycle_query = """
        INSERT INTO crop_cycles (farm_id, crop_id, sowing_date, expected_harvest, status)
        VALUES (%s, %s, %s, %s, 'Growing')
    """
    growing_cycle_id = db.execute_insert(
        cycle_query,
        (farm1_id, cotton_id, cotton_sowing, cotton_harvest),
    )
    print(f"[+] Started Growing Cycle: Cotton on Farm 1 (Cycle #{growing_cycle_id}, sown 45 days ago)")

    # Expenses for Growing Cycle
    exp_query = """
        INSERT INTO expenses (cycle_id, category, amount, expense_date, notes)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute_insert(exp_query, (growing_cycle_id, "Seeds", 3500.00, cotton_sowing, "Certified Bt-Cotton Hybrid seeds (2 packets)"))
    db.execute_insert(exp_query, (growing_cycle_id, "Fertilizer", 4800.00, today - timedelta(days=30), "DAP & Urea basal application"))
    db.execute_insert(exp_query, (growing_cycle_id, "Labour", 2400.00, today - timedelta(days=15), "Weeding and thinning labour"))
    print("    Logged 3 input expenses for Cotton cycle (Total: Rs 10,700)")

    # 8. Insert 1 Harvested Cycle (Soybean on Farm 2)
    soybean_sowing = today - timedelta(days=125)
    soybean_expected = soybean_sowing + timedelta(days=soybean_days)
    soybean_actual = today - timedelta(days=10)
    harvested_cycle_query = """
        INSERT INTO crop_cycles (farm_id, crop_id, sowing_date, expected_harvest, actual_harvest, status, yield_kg, selling_price_per_quintal)
        VALUES (%s, %s, %s, %s, %s, 'Harvested', %s, %s)
    """
    harvested_cycle_id = db.execute_insert(
        harvested_cycle_query,
        (farm2_id, soybean_id, soybean_sowing, soybean_expected, soybean_actual, 1800.00, 4850.00),
    )
    print(f"[+] Recorded Harvested Cycle: Soybean on Farm 2 (Cycle #{harvested_cycle_id}, Yield: 1800 kg @ Rs 4,850/q)")

    # Expenses for Harvested Cycle
    db.execute_insert(exp_query, (harvested_cycle_id, "Seeds", 2800.00, soybean_sowing, "JS-335 Certified seed bags"))
    db.execute_insert(exp_query, (harvested_cycle_id, "Fertilizer", 3600.00, today - timedelta(days=95), "NPK 10:26:26 & Rhizobium inoculant"))
    db.execute_insert(exp_query, (harvested_cycle_id, "Pesticide", 1500.00, today - timedelta(days=60), "Girdle beetle control spray"))
    db.execute_insert(exp_query, (harvested_cycle_id, "Labour", 4200.00, soybean_actual, "Harvesting & threshing crew"))
    db.execute_insert(exp_query, (harvested_cycle_id, "Machinery", 2000.00, soybean_actual, "Thresher and tractor rental"))
    print("    Logged 5 input expenses for Soybean cycle (Total: Rs 14,100, Revenue: Rs 87,300, Profit: Rs 73,200)")

    # 9. Insert Alerts
    alert_query = """
        INSERT INTO alerts (farm_id, alert_type, message, is_read, dedupe_key)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE message = VALUES(message)
    """
    db.execute_insert(
        alert_query,
        (farm1_id, "Heat", "Extreme Heat Warning: Expected temperature 39.5 deg C over next 48h. Schedule nighttime or drip irrigation.", 0, f"demo_heat_{farm1_id}_{today}"),
    )
    db.execute_insert(
        alert_query,
        (farm1_id, "Rain", "Heavy Rain Advisory: Thunderstorm activity forecast in Wardha district. Clear drainage channels.", 0, f"demo_rain_{farm1_id}_{today}"),
    )
    db.execute_insert(
        alert_query,
        (farm1_id, "Task", "Stage Task Due: Cotton Flowering Stage - Inspect for bollworms and apply recommended foliar spray.", 0, f"demo_task_{farm1_id}_{today}"),
    )
    db.execute_insert(
        alert_query,
        (farm2_id, "Price", "Market Price Alert: Soybean mandi rate at Wardha APMC reached Rs 4,920/q (above target).", 1, f"demo_price_{farm2_id}_{today}"),
    )
    print("[+] Created 4 field alerts (Heavy Rain, Extreme Heat, Stage Task, Market Price).")

    # 10. Summary
    print("\n" + "=" * 65)
    print("DEMO SEED COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    print("You can now log into the frontend and demo the entire AgriPredict app:")
    print("  Login URL:   http://localhost:8000/ui/login")
    print(f"  Phone:       {demo_phone}")
    print(f"  Password:    {password_clear}")
    print("  Language:    Marathi (mr) - with live Hindi / English switcher")
    print("  Dashboard:   Overview KPIs, Profit per cycle chart, Category pie chart")
    print("  Farms:       2 plots, Soil tests, Open-Meteo weather telemetry")
    print("  Crop Cycles: 1 active Cotton cycle (with stages & tasks), 1 harvested Soybean cycle")
    print("  Alerts:      4 active warnings (weather triggers, task schedules, market prices)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    seed_demo_data()
