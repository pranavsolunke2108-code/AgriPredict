-- =====================================================================
-- AgriPredict : Phase 6d - Multilingual content (English / Marathi / Hindi)
-- Run after phases 1-5:  mysql -u root -p agripredict < agripredict_phase6_translations.sql
-- Safe to re-run (ON DUPLICATE KEY UPDATE).
--
-- Contains: UI labels, expense categories, seasons, alert types, crop names,
-- and the view crop_localized_view (crop name in each language).
--
-- NOTES
--  * The text keys must match the keys your frontend asks for. If your UI uses
--    different keys, either rename them here or have the frontend use these
--    (the Antigravity prompt asks it to align the two).
--  * Please have a Marathi and a Hindi speaker (ideally a farmer or someone
--    from an agriculture background) review the wording before your demo;
--    agricultural terms vary by region.
-- =====================================================================

USE agripredict;

DROP VIEW IF EXISTS crop_localized_view;

INSERT INTO translations (text_key, lang, text) VALUES
-- navigation and general
('dashboard','en','Dashboard'),('dashboard','mr','डॅशबोर्ड'),('dashboard','hi','डैशबोर्ड'),
('logout','en','Logout'),('logout','mr','बाहेर पडा'),('logout','hi','लॉग आउट'),
('profile','en','Profile'),('profile','mr','प्रोफाइल'),('profile','hi','प्रोफ़ाइल'),
('language','en','Language'),('language','mr','भाषा'),('language','hi','भाषा'),
('save','en','Save'),('save','mr','जतन करा'),('save','hi','सहेजें'),
('cancel','en','Cancel'),('cancel','mr','रद्द करा'),('cancel','hi','रद्द करें'),
('delete','en','Delete'),('delete','mr','हटवा'),('delete','hi','हटाएं'),
('edit','en','Edit'),('edit','mr','संपादित करा'),('edit','hi','संपादित करें'),
('search','en','Search'),('search','mr','शोधा'),('search','hi','खोजें'),
('loading','en','Loading...'),('loading','mr','लोड होत आहे...'),('loading','hi','लोड हो रहा है...'),
('total','en','Total'),('total','mr','एकूण'),('total','hi','कुल'),
('no_data','en','No data available'),('no_data','mr','माहिती उपलब्ध नाही'),('no_data','hi','डेटा उपलब्ध नहीं है'),
('date','en','Date'),('date','mr','तारीख'),('date','hi','तारीख'),
('status','en','Status'),('status','mr','स्थिती'),('status','hi','स्थिति'),
-- farms and soil
('farms','en','Farms'),('farms','mr','शेते'),('farms','hi','खेत'),
('add_farm','en','Add Farm'),('add_farm','mr','शेत जोडा'),('add_farm','hi','खेत जोड़ें'),
('farm_name','en','Farm Name'),('farm_name','mr','शेताचे नाव'),('farm_name','hi','खेत का नाम'),
('area_acres','en','Area (acres)'),('area_acres','mr','क्षेत्रफळ (एकर)'),('area_acres','hi','क्षेत्रफल (एकड़)'),
('soil_type','en','Soil Type'),('soil_type','mr','मातीचा प्रकार'),('soil_type','hi','मिट्टी का प्रकार'),
('irrigation','en','Irrigation'),('irrigation','mr','सिंचन'),('irrigation','hi','सिंचाई'),
('soil_test','en','Soil Test'),('soil_test','mr','माती परीक्षण'),('soil_test','hi','मिट्टी परीक्षण'),
('nitrogen','en','Nitrogen (N)'),('nitrogen','mr','नायट्रोजन (N)'),('nitrogen','hi','नाइट्रोजन (N)'),
('phosphorus','en','Phosphorus (P)'),('phosphorus','mr','स्फुरद (P)'),('phosphorus','hi','फॉस्फोरस (P)'),
('potassium','en','Potassium (K)'),('potassium','mr','पालाश (K)'),('potassium','hi','पोटैशियम (K)'),
('ph','en','Soil pH'),('ph','mr','मातीचा pH'),('ph','hi','मिट्टी का pH'),
('moisture','en','Moisture (%)'),('moisture','mr','ओलावा (%)'),('moisture','hi','नमी (%)'),
-- weather
('weather','en','Weather'),('weather','mr','हवामान'),('weather','hi','मौसम'),
('temperature','en','Temperature'),('temperature','mr','तापमान'),('temperature','hi','तापमान'),
('humidity','en','Humidity'),('humidity','mr','आर्द्रता'),('humidity','hi','आर्द्रता'),
('rainfall','en','Rainfall'),('rainfall','mr','पाऊस'),('rainfall','hi','वर्षा'),
-- recommendation and advice
('recommend_crop','en','Recommend Crop'),('recommend_crop','mr','पिकाची शिफारस'),('recommend_crop','hi','फसल सुझाव'),
('suitability','en','Suitability'),('suitability','mr','योग्यता'),('suitability','hi','उपयुक्तता'),
('fertilizer_plan','en','Fertilizer Plan'),('fertilizer_plan','mr','खत नियोजन'),('fertilizer_plan','hi','उर्वरक योजना'),
('rotation_advice','en','What to grow next'),('rotation_advice','mr','पुढे कोणते पीक घ्यावे'),('rotation_advice','hi','आगे कौन सी फसल उगाएं'),
('crop_calendar','en','Crop Calendar'),('crop_calendar','mr','पीक दिनदर्शिका'),('crop_calendar','hi','फसल कैलेंडर'),
-- crop cycle
('start_cycle','en','Start this crop'),('start_cycle','mr','हे पीक सुरू करा'),('start_cycle','hi','यह फसल शुरू करें'),
('close_cycle','en','Close crop cycle'),('close_cycle','mr','पीक हंगाम बंद करा'),('close_cycle','hi','फसल चक्र बंद करें'),
('sowing_date','en','Sowing date'),('sowing_date','mr','पेरणीची तारीख'),('sowing_date','hi','बुवाई की तारीख'),
('expected_harvest','en','Expected harvest'),('expected_harvest','mr','अपेक्षित काढणी'),('expected_harvest','hi','अपेक्षित कटाई'),
('planned','en','Planned'),('planned','mr','नियोजित'),('planned','hi','योजनाबद्ध'),
('growing','en','Growing'),('growing','mr','वाढत आहे'),('growing','hi','बढ़ रही है'),
('harvested','en','Harvested'),('harvested','mr','काढणी झाली'),('harvested','hi','कटाई हो गई'),
('failed','en','Failed'),('failed','mr','अयशस्वी'),('failed','hi','विफल'),
('yield_kg','en','Yield (kg)'),('yield_kg','mr','उत्पादन (किलो)'),('yield_kg','hi','उपज (किलो)'),
-- money
('expenses','en','Expenses'),('expenses','mr','खर्च'),('expenses','hi','खर्च'),
('add_expense','en','Add Expense'),('add_expense','mr','खर्च जोडा'),('add_expense','hi','खर्च जोड़ें'),
('category','en','Category'),('category','mr','प्रकार'),('category','hi','श्रेणी'),
('amount','en','Amount (Rs)'),('amount','mr','रक्कम (₹)'),('amount','hi','राशि (₹)'),
('market_prices','en','Market Prices'),('market_prices','mr','बाजारभाव'),('market_prices','hi','बाज़ार भाव'),
('price_per_quintal','en','Price per quintal'),('price_per_quintal','mr','प्रति क्विंटल भाव'),('price_per_quintal','hi','प्रति क्विंटल भाव'),
('profit','en','Profit'),('profit','mr','नफा'),('profit','hi','लाभ'),
('revenue','en','Revenue'),('revenue','mr','उत्पन्न'),('revenue','hi','आय'),
-- expense categories
('cat_seeds','en','Seeds'),('cat_seeds','mr','बियाणे'),('cat_seeds','hi','बीज'),
('cat_fertilizer','en','Fertilizer'),('cat_fertilizer','mr','खत'),('cat_fertilizer','hi','उर्वरक'),
('cat_pesticide','en','Pesticide'),('cat_pesticide','mr','कीटकनाशक'),('cat_pesticide','hi','कीटनाशक'),
('cat_labour','en','Labour'),('cat_labour','mr','मजुरी'),('cat_labour','hi','मज़दूरी'),
('cat_irrigation','en','Irrigation'),('cat_irrigation','mr','सिंचन'),('cat_irrigation','hi','सिंचाई'),
('cat_machinery','en','Machinery'),('cat_machinery','mr','यंत्रसामग्री'),('cat_machinery','hi','मशीनरी'),
('cat_other','en','Other'),('cat_other','mr','इतर'),('cat_other','hi','अन्य'),
-- seasons
('season_kharif','en','Kharif'),('season_kharif','mr','खरीप'),('season_kharif','hi','खरीफ'),
('season_rabi','en','Rabi'),('season_rabi','mr','रब्बी'),('season_rabi','hi','रबी'),
('season_zaid','en','Zaid'),('season_zaid','mr','उन्हाळी'),('season_zaid','hi','जायद'),
('season_annual','en','Annual'),('season_annual','mr','बारमाही'),('season_annual','hi','वार्षिक'),
-- alerts
('alerts','en','Alerts'),('alerts','mr','सूचना'),('alerts','hi','सूचनाएँ'),
('mark_read','en','Mark as read'),('mark_read','mr','वाचले म्हणून चिन्हांकित करा'),('mark_read','hi','पढ़ा हुआ चिह्नित करें'),
('alert_rain','en','Rain'),('alert_rain','mr','पाऊस'),('alert_rain','hi','बारिश'),
('alert_heat','en','Heat'),('alert_heat','mr','उष्णता'),('alert_heat','hi','गर्मी'),
('alert_frost','en','Frost'),('alert_frost','mr','दंव'),('alert_frost','hi','पाला'),
('alert_drought','en','Drought'),('alert_drought','mr','दुष्काळ'),('alert_drought','hi','सूखा'),
('alert_pest','en','Pest'),('alert_pest','mr','कीड'),('alert_pest','hi','कीट'),
('alert_task','en','Task'),('alert_task','mr','कामे'),('alert_task','hi','कार्य'),
('alert_price','en','Price'),('alert_price','mr','भाव'),('alert_price','hi','मूल्य'),
-- earlier starter keys (refreshed so wording is consistent)
('login','en','Login'),('login','mr','लॉगिन'),('login','hi','लॉगिन'),
('register','en','Register'),('register','mr','नोंदणी करा'),('register','hi','पंजीकरण करें'),
('my_farms','en','My Farms'),('my_farms','mr','माझी शेती'),('my_farms','hi','मेरे खेत'),
('current_status','en','Current Status'),('current_status','mr','सध्याची स्थिती'),('current_status','hi','वर्तमान स्थिति'),
('history','en','History'),('history','mr','इतिहास'),('history','hi','इतिहास')
ON DUPLICATE KEY UPDATE text = VALUES(text);

-- Crop names: English rows come from the crops table itself
INSERT INTO translations (text_key, lang, text)
SELECT CONCAT('crop_', LOWER(REPLACE(crop_name, ' ', '_'))), 'en', crop_name
FROM crops
ON DUPLICATE KEY UPDATE text = VALUES(text);

INSERT INTO translations (text_key, lang, text)
SELECT CONCAT('crop_', LOWER(REPLACE(c.crop_name, ' ', '_'))), x.lang, x.local_name
FROM (
  SELECT 'Rice' AS n,'mr' AS lang,'भात' AS local_name UNION ALL SELECT 'Rice','hi','धान' UNION ALL
  SELECT 'Maize','mr','मका' UNION ALL SELECT 'Maize','hi','मक्का' UNION ALL
  SELECT 'Wheat','mr','गहू' UNION ALL SELECT 'Wheat','hi','गेहूं' UNION ALL
  SELECT 'Soybean','mr','सोयाबीन' UNION ALL SELECT 'Soybean','hi','सोयाबीन' UNION ALL
  SELECT 'Cotton','mr','कापूस' UNION ALL SELECT 'Cotton','hi','कपास' UNION ALL
  SELECT 'Sugarcane','mr','ऊस' UNION ALL SELECT 'Sugarcane','hi','गन्ना' UNION ALL
  SELECT 'Chickpea','mr','हरभरा' UNION ALL SELECT 'Chickpea','hi','चना' UNION ALL
  SELECT 'Pigeon Pea','mr','तूर' UNION ALL SELECT 'Pigeon Pea','hi','अरहर (तुअर)' UNION ALL
  SELECT 'Groundnut','mr','भुईमूग' UNION ALL SELECT 'Groundnut','hi','मूंगफली' UNION ALL
  SELECT 'Jowar','mr','ज्वारी' UNION ALL SELECT 'Jowar','hi','ज्वार' UNION ALL
  SELECT 'Bajra','mr','बाजरी' UNION ALL SELECT 'Bajra','hi','बाजरा' UNION ALL
  SELECT 'Onion','mr','कांदा' UNION ALL SELECT 'Onion','hi','प्याज' UNION ALL
  SELECT 'Tomato','mr','टोमॅटो' UNION ALL SELECT 'Tomato','hi','टमाटर' UNION ALL
  SELECT 'Moong','mr','मूग' UNION ALL SELECT 'Moong','hi','मूंग' UNION ALL
  SELECT 'Urad','mr','उडीद' UNION ALL SELECT 'Urad','hi','उड़द' UNION ALL
  SELECT 'Lentil','mr','मसूर' UNION ALL SELECT 'Lentil','hi','मसूर' UNION ALL
  SELECT 'Banana','mr','केळी' UNION ALL SELECT 'Banana','hi','केला' UNION ALL
  SELECT 'Grapes','mr','द्राक्षे' UNION ALL SELECT 'Grapes','hi','अंगूर' UNION ALL
  SELECT 'Watermelon','mr','कलिंगड' UNION ALL SELECT 'Watermelon','hi','तरबूज' UNION ALL
  SELECT 'Mango','mr','आंबा' UNION ALL SELECT 'Mango','hi','आम'
) x
JOIN crops c ON c.crop_name = x.n
ON DUPLICATE KEY UPDATE text = VALUES(text);

-- ---------------------------------------------------------------------
-- VIEW: crop_localized_view - crop name in every available language
--   usage: SELECT crop_id, localized_name FROM crop_localized_view WHERE lang = 'mr'
-- ---------------------------------------------------------------------
CREATE VIEW crop_localized_view AS
SELECT c.crop_id, c.crop_name, t.lang, t.text AS localized_name
FROM crops c
JOIN translations t
  ON t.text_key = CONCAT('crop_', LOWER(REPLACE(c.crop_name, ' ', '_')));

-- Coverage check: every key should exist in all three languages
SELECT text_key, COUNT(*) AS languages
FROM translations
GROUP BY text_key
HAVING COUNT(*) < 3;
