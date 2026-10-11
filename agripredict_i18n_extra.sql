-- ============================================================================
-- AgriPredict Unified Multilingual Translation Table
-- File: agripredict_i18n_extra.sql
-- Encoding: UTF-8 (without BOM)
--
-- Contains clean Devanagari replacements for all previously corrupted translations
-- and all newly audited UI strings for English (en), Marathi (mr), and Hindi (hi).
--
-- IMPORTANT REVIEW NOTE:
-- All Marathi (mr) and Hindi (hi) translations in this file are marked as
-- provisionally translated and REQUIRE USER / LINGUISTIC REVIEW before final sign-off.
--
-- Windows Import Command:
-- mysql -u root -p --default-character-set=utf8mb4 agripredict -e "source d:\Projects\Personal\AgriPredict\agripredict_i18n_extra.sql"
-- ============================================================================

INSERT INTO translations (text_key, lang, text) VALUES
('acres', 'en', 'Acres'),
('acres', 'mr', 'एकर'), -- [NEEDS REVIEW: Marathi]
('acres', 'hi', 'एकड़'), -- [NEEDS REVIEW: Hindi]
('action', 'en', 'Action'),
('action', 'mr', 'कृती'), -- [NEEDS REVIEW: Marathi]
('action', 'hi', 'कार्रवाई'), -- [NEEDS REVIEW: Hindi]
('active_cycles', 'en', 'Active Cycles'),
('active_cycles', 'mr', 'चालू पिके'), -- [NEEDS REVIEW: Marathi]
('active_cycles', 'hi', 'सक्रिय फसलें'), -- [NEEDS REVIEW: Hindi]
('add_expense', 'en', 'Add Expense'),
('add_expense', 'mr', 'खर्च जोडा'), -- [NEEDS REVIEW: Marathi]
('add_expense', 'hi', 'व्यय जोड़ें'), -- [NEEDS REVIEW: Hindi]
('add_farm', 'en', 'Add Farm'),
('add_farm', 'mr', 'शेती जोडा'), -- [NEEDS REVIEW: Marathi]
('add_farm', 'hi', 'खेत जोड़ें'), -- [NEEDS REVIEW: Hindi]
('add_farm_first', 'en', 'Add First Farm'),
('add_farm_first', 'mr', 'पहिले शेत जोडा'), -- [NEEDS REVIEW: Marathi]
('add_farm_first', 'hi', 'पहला खेत जोड़ें'), -- [NEEDS REVIEW: Hindi]
('add_first_farm_desc', 'en', 'Register your farm plot to get automated soil and weather recommendations.'),
('add_first_farm_desc', 'mr', 'माती आणि हवामानावर आधारित पीक सल्ल्यासाठी आपल्या शेताची नोंदणी करा.'), -- [NEEDS REVIEW: Marathi]
('add_first_farm_desc', 'hi', 'मिट्टी और मौसम आधारित फसल सलाह के लिए अपने खेत का पंजीकरण करें।'), -- [NEEDS REVIEW: Hindi]
('add_first_farm_title', 'en', 'Add Your First Farm'),
('add_first_farm_title', 'mr', 'आपली पहिली शेतजमीन जोडा'), -- [NEEDS REVIEW: Marathi]
('add_first_farm_title', 'hi', 'अपना पहला खेत जोड़ें'), -- [NEEDS REVIEW: Hindi]
('admin_panel', 'en', 'Admin Management Panel'),
('admin_panel', 'mr', 'प्रशासकीय नियंत्रण पॅनेल'), -- [NEEDS REVIEW: Marathi]
('admin_panel', 'hi', 'व्यवस्थापक नियंत्रण पैनल'), -- [NEEDS REVIEW: Hindi]
('alert_drought', 'en', 'Drought'),
('alert_drought', 'mr', 'दुष्काळ'), -- [NEEDS REVIEW: Marathi]
('alert_drought', 'hi', 'सूखा'), -- [NEEDS REVIEW: Hindi]
('alert_frost', 'en', 'Frost'),
('alert_frost', 'mr', 'धुके / दव'), -- [NEEDS REVIEW: Marathi]
('alert_frost', 'hi', 'पाला / अत्यधिक ठंड'), -- [NEEDS REVIEW: Hindi]
('alert_heat', 'en', 'Heat'),
('alert_heat', 'mr', 'उष्णतेची लाट'), -- [NEEDS REVIEW: Marathi]
('alert_heat', 'hi', 'लू / भीषण गर्मी'), -- [NEEDS REVIEW: Hindi]
('alert_pest', 'en', 'Pest'),
('alert_pest', 'mr', 'कीड प्रादुर्भाव'), -- [NEEDS REVIEW: Marathi]
('alert_pest', 'hi', 'कीट प्रकोप'), -- [NEEDS REVIEW: Hindi]
('alert_price', 'en', 'Price'),
('alert_price', 'mr', 'बाजार भाव वाढ'), -- [NEEDS REVIEW: Marathi]
('alert_price', 'hi', 'मूल्य चेतावनी'), -- [NEEDS REVIEW: Hindi]
('alert_rain', 'en', 'Rain'),
('alert_rain', 'mr', 'मुसळधार पाऊस'), -- [NEEDS REVIEW: Marathi]
('alert_rain', 'hi', 'भारी बारिश'), -- [NEEDS REVIEW: Hindi]
('alert_task', 'en', 'Task'),
('alert_task', 'mr', 'कृषी कार्य'), -- [NEEDS REVIEW: Marathi]
('alert_task', 'hi', 'कृषि कार्य'), -- [NEEDS REVIEW: Hindi]
('alerts', 'en', 'Alerts'),
('alerts', 'mr', 'सूचना'), -- [NEEDS REVIEW: Marathi]
('alerts', 'hi', 'अलर्ट'), -- [NEEDS REVIEW: Hindi]
('alerts_sub', 'en', 'Weather advisories, stage reminders, and price movement notifications'),
('alerts_sub', 'mr', 'हवामान इशारे, कामांचे स्मरण आणि बाजार भाव सूचना'), -- [NEEDS REVIEW: Marathi]
('alerts_sub', 'hi', 'मौसम सलाह, चरण अनुस्मारक और मूल्य उतार-चढ़ाव सूचनाएं'), -- [NEEDS REVIEW: Hindi]
('all_alerts_read', 'en', 'All alerts marked as read.'),
('all_alerts_read', 'mr', 'सर्व सूचना वाचल्या म्हणून चिन्हांकित केल्या.'), -- [NEEDS REVIEW: Marathi]
('all_alerts_read', 'hi', 'सभी सूचनाएं पढ़ी गईं के रूप में चिह्नित की गईं।'), -- [NEEDS REVIEW: Hindi]
('all_commodities', 'en', 'All Commodities'),
('all_commodities', 'mr', 'सर्व शेतमाल'), -- [NEEDS REVIEW: Marathi]
('all_commodities', 'hi', 'सभी वस्तुएं'), -- [NEEDS REVIEW: Hindi]
('all_farms', 'en', 'All Farms'),
('all_farms', 'mr', 'सर्व शेती'), -- [NEEDS REVIEW: Marathi]
('all_farms', 'hi', 'सभी खेत'), -- [NEEDS REVIEW: Hindi]
('all_farms_sub', 'en', 'Manage your farm plots, soil health metrics, and GPS locations'),
('all_farms_sub', 'mr', 'आपली शेतजमीन, माती आरोग्य व जीपीएस स्थानांचे व्यवस्थापन करा'), -- [NEEDS REVIEW: Marathi]
('all_farms_sub', 'hi', 'अपने खेत के भूखंड, मृदा स्वास्थ्य और जीपीएस स्थानों का प्रबंधन करें'), -- [NEEDS REVIEW: Hindi]
('all_seasons_opt', 'en', 'All Seasons'),
('all_seasons_opt', 'mr', 'सर्व हंगाम'), -- [NEEDS REVIEW: Marathi]
('all_seasons_opt', 'hi', 'सभी मौसम'), -- [NEEDS REVIEW: Hindi]
('already_have_account', 'en', 'Already have an account?'),
('already_have_account', 'mr', 'आधीच खाते आहे का?'), -- [NEEDS REVIEW: Marathi]
('already_have_account', 'hi', 'क्या आपके पास पहले से खाता है?'), -- [NEEDS REVIEW: Hindi]
('amount', 'en', 'Amount'),
('amount', 'mr', 'रक्कम'), -- [NEEDS REVIEW: Marathi]
('amount', 'hi', 'राशि'), -- [NEEDS REVIEW: Hindi]
('area_acres', 'en', 'Area (acres)'),
('area_acres', 'mr', 'क्षेत्रफळ (एकर)'), -- [NEEDS REVIEW: Marathi]
('area_acres', 'hi', 'क्षेत्र (एकड़)'), -- [NEEDS REVIEW: Hindi]
('auto_season_opt', 'en', 'Auto (Today\'s Season)'),
('auto_season_opt', 'mr', 'आपोआप (आजचा हंगाम)'), -- [NEEDS REVIEW: Marathi]
('auto_season_opt', 'hi', 'स्वतः (आज का मौसम)'), -- [NEEDS REVIEW: Hindi]
('back_to_dashboard', 'en', 'Back to Dashboard'),
('back_to_dashboard', 'mr', 'डॅशबोर्डवर परत जा'), -- [NEEDS REVIEW: Marathi]
('back_to_dashboard', 'hi', 'डैशबोर्ड पर वापस जाएं'), -- [NEEDS REVIEW: Hindi]
('cancel', 'en', 'Cancel'),
('cancel', 'mr', 'रद्द करा'), -- [NEEDS REVIEW: Marathi]
('cancel', 'hi', 'रद्द करें'), -- [NEEDS REVIEW: Hindi]
('cancel_btn', 'en', 'Cancel'),
('cancel_btn', 'mr', 'रद्द करा'), -- [NEEDS REVIEW: Marathi]
('cancel_btn', 'hi', 'रद्द करें'), -- [NEEDS REVIEW: Hindi]
('cat_fertilizer', 'en', 'Fertilizer'),
('cat_fertilizer', 'mr', 'खते'), -- [NEEDS REVIEW: Marathi]
('cat_fertilizer', 'hi', 'उर्वरक'), -- [NEEDS REVIEW: Hindi]
('cat_irrigation', 'en', 'Irrigation'),
('cat_irrigation', 'mr', 'सिंचन'), -- [NEEDS REVIEW: Marathi]
('cat_irrigation', 'hi', 'सिंचाई'), -- [NEEDS REVIEW: Hindi]
('cat_labour', 'en', 'Labour'),
('cat_labour', 'mr', 'मजुरी'), -- [NEEDS REVIEW: Marathi]
('cat_labour', 'hi', 'मजदूरी'), -- [NEEDS REVIEW: Hindi]
('cat_machinery', 'en', 'Machinery'),
('cat_machinery', 'mr', 'यंत्रसामग्री'), -- [NEEDS REVIEW: Marathi]
('cat_machinery', 'hi', 'मशीनरी'), -- [NEEDS REVIEW: Hindi]
('cat_other', 'en', 'Other'),
('cat_other', 'mr', 'इतर'), -- [NEEDS REVIEW: Marathi]
('cat_other', 'hi', 'अन्य'), -- [NEEDS REVIEW: Hindi]
('cat_pesticide', 'en', 'Pesticide'),
('cat_pesticide', 'mr', 'कीटकनाशके'), -- [NEEDS REVIEW: Marathi]
('cat_pesticide', 'hi', 'कीटनाशक'), -- [NEEDS REVIEW: Hindi]
('cat_seeds', 'en', 'Seeds'),
('cat_seeds', 'mr', 'बियाणे'), -- [NEEDS REVIEW: Marathi]
('cat_seeds', 'hi', 'बीज'), -- [NEEDS REVIEW: Hindi]
('category', 'en', 'Category'),
('category', 'mr', 'वर्ग / प्रकार'), -- [NEEDS REVIEW: Marathi]
('category', 'hi', 'श्रेणी'), -- [NEEDS REVIEW: Hindi]
('check_top_crops', 'en', 'Check Top 3 Crops'),
('check_top_crops', 'mr', 'शीर्ष ३ पिके तपासा'), -- [NEEDS REVIEW: Marathi]
('check_top_crops', 'hi', 'शीर्ष 3 फसलें जांचें'), -- [NEEDS REVIEW: Hindi]
('close', 'en', 'Close'),
('close', 'mr', 'बंद करा'), -- [NEEDS REVIEW: Marathi]
('close', 'hi', 'बंद करें'), -- [NEEDS REVIEW: Hindi]
('close_cycle', 'en', 'Close Cycle'),
('close_cycle', 'mr', 'हंगाम समाप्त करा'), -- [NEEDS REVIEW: Marathi]
('close_cycle', 'hi', 'फसल चक्र समाप्त करें'), -- [NEEDS REVIEW: Hindi]
('close_cycle_desc', 'en', 'Record final harvest yield and revenue to calculate overall plot profitability and complete this cycle.'),
('close_cycle_desc', 'mr', 'अंतिम उत्पादन आणि नफा नोंदवून हा हंगाम पूर्ण करा.'), -- [NEEDS REVIEW: Marathi]
('close_cycle_desc', 'hi', 'अंतिम उपज और आय दर्ज करके इस फसल चक्र को पूरा करें।'), -- [NEEDS REVIEW: Hindi]
('complete_and_close_cycle', 'en', 'Complete & Close Cycle'),
('complete_and_close_cycle', 'mr', 'हंगाम पूर्ण करून बंद करा'), -- [NEEDS REVIEW: Marathi]
('complete_and_close_cycle', 'hi', 'फसल चक्र पूरा करके बंद करें'), -- [NEEDS REVIEW: Hindi]
('completed_cycles', 'en', 'Completed Cycles'),
('completed_cycles', 'mr', 'पूर्ण झालेले हंगाम'), -- [NEEDS REVIEW: Marathi]
('completed_cycles', 'hi', 'पूर्ण फसल चक्र'), -- [NEEDS REVIEW: Hindi]
('coordinates', 'en', 'Coordinates'),
('coordinates', 'mr', 'अक्षांश-रेखांश'), -- [NEEDS REVIEW: Marathi]
('coordinates', 'hi', 'निर्देशांक'), -- [NEEDS REVIEW: Hindi]
('crop_advisory', 'en', 'Crop Advisory & Suitability'),
('crop_advisory', 'mr', 'पीक सल्ला व उपयुक्तता'), -- [NEEDS REVIEW: Marathi]
('crop_advisory', 'hi', 'फसल सलाह और उपयुक्तता'), -- [NEEDS REVIEW: Hindi]
('crop_advisory_sub', 'en', 'Stored procedure recommendation ranking based on current farm soil'),
('crop_advisory_sub', 'mr', 'सध्याच्या शेत मातीवर आधारित शिफारस क्रमवारी'), -- [NEEDS REVIEW: Marathi]
('crop_advisory_sub', 'hi', 'वर्तमान खेत की मिट्टी के आधार पर सिफारिश रैंकिंग'), -- [NEEDS REVIEW: Hindi]
('crop_bajra', 'en', 'Bajra'),
('crop_bajra', 'mr', 'बाजरी'), -- [NEEDS REVIEW: Marathi]
('crop_bajra', 'hi', 'बाजरा'), -- [NEEDS REVIEW: Hindi]
('crop_banana', 'en', 'Banana'),
('crop_banana', 'mr', 'केळी'), -- [NEEDS REVIEW: Marathi]
('crop_banana', 'hi', 'केला'), -- [NEEDS REVIEW: Hindi]
('crop_calendar', 'en', 'Crop Calendar'),
('crop_calendar', 'mr', 'पीक वेळापत्रक'), -- [NEEDS REVIEW: Marathi]
('crop_calendar', 'hi', 'फसल कैलेंडर'), -- [NEEDS REVIEW: Hindi]
('crop_chickpea', 'en', 'Chickpea'),
('crop_chickpea', 'mr', 'हरभरा'), -- [NEEDS REVIEW: Marathi]
('crop_chickpea', 'hi', 'चना'), -- [NEEDS REVIEW: Hindi]
('crop_cotton', 'en', 'Cotton'),
('crop_cotton', 'mr', 'कापूस'), -- [NEEDS REVIEW: Marathi]
('crop_cotton', 'hi', 'कपास'), -- [NEEDS REVIEW: Hindi]
('crop_expenses_subtitle', 'en', 'Category analytics from cycle_expense_summary_view and itemized input logs'),
('crop_expenses_subtitle', 'mr', 'खर्च वर्गीकरण आणि तपशीलवार नोंदी'), -- [NEEDS REVIEW: Marathi]
('crop_expenses_subtitle', 'hi', 'व्यय वर्गीकरण और विस्तृत प्रविष्टियां'), -- [NEEDS REVIEW: Hindi]
('crop_expenses_title', 'en', 'Crop Expenses & Spend Breakdown'),
('crop_expenses_title', 'mr', 'पीक खर्च आणि वर्गीकरण'), -- [NEEDS REVIEW: Marathi]
('crop_expenses_title', 'hi', 'फसल खर्च और मदवार विवरण'), -- [NEEDS REVIEW: Hindi]
('crop_grapes', 'en', 'Grapes'),
('crop_grapes', 'mr', 'द्राक्षे'), -- [NEEDS REVIEW: Marathi]
('crop_grapes', 'hi', 'अंगूर'), -- [NEEDS REVIEW: Hindi]
('crop_groundnut', 'en', 'Groundnut'),
('crop_groundnut', 'mr', 'भुईमूग'), -- [NEEDS REVIEW: Marathi]
('crop_groundnut', 'hi', 'मूंगफली'), -- [NEEDS REVIEW: Hindi]
('crop_jowar', 'en', 'Jowar'),
('crop_jowar', 'mr', 'ज्वारी'), -- [NEEDS REVIEW: Marathi]
('crop_jowar', 'hi', 'ज्वार'), -- [NEEDS REVIEW: Hindi]
('crop_lentil', 'en', 'Lentil'),
('crop_lentil', 'mr', 'मसूर'), -- [NEEDS REVIEW: Marathi]
('crop_lentil', 'hi', 'मसूर'), -- [NEEDS REVIEW: Hindi]
('crop_maize', 'en', 'Maize'),
('crop_maize', 'mr', 'मका'), -- [NEEDS REVIEW: Marathi]
('crop_maize', 'hi', 'मक्का'), -- [NEEDS REVIEW: Hindi]
('crop_mango', 'en', 'Mango'),
('crop_mango', 'mr', 'आंबा'), -- [NEEDS REVIEW: Marathi]
('crop_mango', 'hi', 'आम'), -- [NEEDS REVIEW: Hindi]
('crop_moong', 'en', 'Moong'),
('crop_moong', 'mr', 'मूग'), -- [NEEDS REVIEW: Marathi]
('crop_moong', 'hi', 'मूंग'), -- [NEEDS REVIEW: Hindi]
('crop_onion', 'en', 'Onion'),
('crop_onion', 'mr', 'कांदा'), -- [NEEDS REVIEW: Marathi]
('crop_onion', 'hi', 'प्याज'), -- [NEEDS REVIEW: Hindi]
('crop_pigeon_pea', 'en', 'Pigeon Pea'),
('crop_pigeon_pea', 'mr', 'तूर'), -- [NEEDS REVIEW: Marathi]
('crop_pigeon_pea', 'hi', 'अरहर'), -- [NEEDS REVIEW: Hindi]
('crop_rice', 'en', 'Rice'),
('crop_rice', 'mr', 'भात (तांदूळ)'), -- [NEEDS REVIEW: Marathi]
('crop_rice', 'hi', 'चावल / धान'), -- [NEEDS REVIEW: Hindi]
('crop_soybean', 'en', 'Soybean'),
('crop_soybean', 'mr', 'सोयाबीन'), -- [NEEDS REVIEW: Marathi]
('crop_soybean', 'hi', 'सोयाबीन'), -- [NEEDS REVIEW: Hindi]
('crop_sugarcane', 'en', 'Sugarcane'),
('crop_sugarcane', 'mr', 'ऊस'), -- [NEEDS REVIEW: Marathi]
('crop_sugarcane', 'hi', 'गन्ना'), -- [NEEDS REVIEW: Hindi]
('crop_tomato', 'en', 'Tomato'),
('crop_tomato', 'mr', 'टोमॅटो'), -- [NEEDS REVIEW: Marathi]
('crop_tomato', 'hi', 'टमाटर'), -- [NEEDS REVIEW: Hindi]
('crop_urad', 'en', 'Urad'),
('crop_urad', 'mr', 'उडीद'), -- [NEEDS REVIEW: Marathi]
('crop_urad', 'hi', 'उड़द'), -- [NEEDS REVIEW: Hindi]
('crop_watermelon', 'en', 'Watermelon'),
('crop_watermelon', 'mr', 'कलिंगड'), -- [NEEDS REVIEW: Marathi]
('crop_watermelon', 'hi', 'तरबूज'), -- [NEEDS REVIEW: Hindi]
('crop_wheat', 'en', 'Wheat'),
('crop_wheat', 'mr', 'गहू'), -- [NEEDS REVIEW: Marathi]
('crop_wheat', 'hi', 'गेहूं'), -- [NEEDS REVIEW: Hindi]
('crops_supported_stat', 'en', 'Crops Supported'),
('crops_supported_stat', 'mr', 'समर्थित पिके'), -- [NEEDS REVIEW: Marathi]
('crops_supported_stat', 'hi', 'समर्थित फसलें'), -- [NEEDS REVIEW: Hindi]
('current_status', 'en', 'Current Status'),
('current_status', 'mr', 'सद्यस्थिती'), -- [NEEDS REVIEW: Marathi]
('current_status', 'hi', 'वर्तमान स्थिति'), -- [NEEDS REVIEW: Hindi]
('current_status_sub', 'en', 'Live operational metrics of your ongoing crop seasons'),
('current_status_sub', 'mr', 'आपल्या चालू पीक हंगामाचे थेट विश्लेषण'), -- [NEEDS REVIEW: Marathi]
('current_status_sub', 'hi', 'आपके चालू फसल मौसम का वास्तविक समय विवरण'), -- [NEEDS REVIEW: Hindi]
('cycle_closed_success', 'en', 'Crop cycle closed successfully!'),
('cycle_closed_success', 'mr', 'पीक हंगाम यशस्वीरित्या बंद केला!'), -- [NEEDS REVIEW: Marathi]
('cycle_closed_success', 'hi', 'फसल चक्र सफलतापूर्वक समाप्त किया गया!'), -- [NEEDS REVIEW: Hindi]
('cycle_started_success', 'en', 'New crop cycle started successfully!'),
('cycle_started_success', 'mr', 'नवीन पीक यशस्वीरित्या सुरू केले!'), -- [NEEDS REVIEW: Marathi]
('cycle_started_success', 'hi', 'नई फसल सफलतापूर्वक शुरू की गई!'), -- [NEEDS REVIEW: Hindi]
('cycle_summary', 'en', 'Cycle summary'),
('cycle_summary', 'mr', 'हंगामाचा सारांश'), -- [NEEDS REVIEW: Marathi]
('cycle_summary', 'hi', 'फसल चक्र सारांश'), -- [NEEDS REVIEW: Hindi]
('dashboard', 'en', 'Dashboard'),
('dashboard', 'mr', 'डॅशबोर्ड'), -- [NEEDS REVIEW: Marathi]
('dashboard', 'hi', 'डैशबोर्ड'), -- [NEEDS REVIEW: Hindi]
('date', 'en', 'Date'),
('date', 'mr', 'तारीख'), -- [NEEDS REVIEW: Marathi]
('date', 'hi', 'तारीख'), -- [NEEDS REVIEW: Hindi]
('days_duration', 'en', 'days'),
('days_duration', 'mr', 'दिवस'), -- [NEEDS REVIEW: Marathi]
('days_duration', 'hi', 'दिन'), -- [NEEDS REVIEW: Hindi]
('days_remaining', 'en', 'days left'),
('days_remaining', 'mr', 'दिवस शिल्लक'), -- [NEEDS REVIEW: Marathi]
('days_remaining', 'hi', 'दिन शेष'), -- [NEEDS REVIEW: Hindi]
('delete', 'en', 'Delete'),
('delete', 'mr', 'हटवा'), -- [NEEDS REVIEW: Marathi]
('delete', 'hi', 'हटाएं'), -- [NEEDS REVIEW: Hindi]
('delete_farm_confirm', 'en', 'Are you sure you want to delete this farm?'),
('delete_farm_confirm', 'mr', 'आपण खरोखर हे शेत हटवू इच्छिता का?'), -- [NEEDS REVIEW: Marathi]
('delete_farm_confirm', 'hi', 'क्या आप वाकई इस खेत को हटाना चाहते हैं?'), -- [NEEDS REVIEW: Hindi]
('district', 'en', 'District'),
('district', 'mr', 'जिल्हा'), -- [NEEDS REVIEW: Marathi]
('district', 'hi', 'जिला'), -- [NEEDS REVIEW: Hindi]
('dont_have_account', 'en', 'Don\'t have an account?'),
('dont_have_account', 'mr', 'अद्याप खाते नाही का?'), -- [NEEDS REVIEW: Marathi]
('dont_have_account', 'hi', 'क्या आपका खाता नहीं है?'), -- [NEEDS REVIEW: Hindi]
('drag_pin_hint', 'en', 'Drag pin or click map to set farm location'),
('drag_pin_hint', 'mr', 'शेताचे स्थान निश्चित करण्यासाठी पिन हलवा किंवा नकाशावर क्लिक करा'), -- [NEEDS REVIEW: Marathi]
('drag_pin_hint', 'hi', 'खेत की स्थिति सेट करने के लिए पिन खींचें या मानचित्र पर क्लिक करें'), -- [NEEDS REVIEW: Hindi]
('economics_note_desc', 'en', 'Revenue, cost, and profit projections are calculated based on typical historical regional yield rates and modal market prices. Actual outcomes vary by weather and farming practices.'),
('economics_note_desc', 'mr', 'उत्पन्न, खर्च आणि नफ्याचे अंदाज स्थानिक सरासरी उत्पादन आणि बाजारभावावर आधारित आहेत. प्रत्यक्ष निकाल हवामान आणि शेती पद्धतींनुसार बदलू शकतात.'), -- [NEEDS REVIEW: Marathi]
('economics_note_desc', 'hi', 'राजस्व, लागत और लाभ के अनुमान क्षेत्रीय औसत उपज और मंडी भावों पर आधारित हैं। वास्तविक परिणाम मौसम और खेती के तरीकों पर निर्भर करते हैं।'), -- [NEEDS REVIEW: Hindi]
('economics_note_title', 'en', 'Indicative Financial Estimation'),
('economics_note_title', 'mr', 'अंदाजे आर्थिक अंदाज'), -- [NEEDS REVIEW: Marathi]
('economics_note_title', 'hi', 'अनुमानित वित्तीय आकलन'), -- [NEEDS REVIEW: Hindi]
('edit', 'en', 'Edit'),
('edit', 'mr', 'संपादित करा'), -- [NEEDS REVIEW: Marathi]
('edit', 'hi', 'संपादित करें'), -- [NEEDS REVIEW: Hindi]
('edit_farm', 'en', 'Edit Farm'),
('edit_farm', 'mr', 'शेत संपादित करा'), -- [NEEDS REVIEW: Marathi]
('edit_farm', 'hi', 'खेत संपादित करें'), -- [NEEDS REVIEW: Hindi]
('email_address', 'en', 'Email Address'),
('email_address', 'mr', 'ईमेल पत्ता'), -- [NEEDS REVIEW: Marathi]
('email_address', 'hi', 'ईमेल पता'), -- [NEEDS REVIEW: Hindi]
('enter_coords_manually', 'en', 'Enter coordinates manually'),
('enter_coords_manually', 'mr', 'अक्षांश-रेखांश स्वतः प्रविष्ट करा'), -- [NEEDS REVIEW: Marathi]
('enter_coords_manually', 'hi', 'निर्देशांक मैन्युअल रूप से दर्ज करें'), -- [NEEDS REVIEW: Hindi]
('expected_harvest', 'en', 'Expected Harvest'),
('expected_harvest', 'mr', 'अपेक्षित काढणी'), -- [NEEDS REVIEW: Marathi]
('expected_harvest', 'hi', 'अपेक्षित कटाई'), -- [NEEDS REVIEW: Hindi]
('expense_added_success', 'en', 'Expense recorded successfully!'),
('expense_added_success', 'mr', 'खर्च यशस्वीरित्या नोंदवला!'), -- [NEEDS REVIEW: Marathi]
('expense_added_success', 'hi', 'व्यय सफलतापूर्वक दर्ज किया गया!'), -- [NEEDS REVIEW: Hindi]
('expense_deleted', 'en', 'Expense deleted successfully!'),
('expense_deleted', 'mr', 'खर्च हटवला गेला!'), -- [NEEDS REVIEW: Marathi]
('expense_deleted', 'hi', 'खर्च हटा दिया गया!'), -- [NEEDS REVIEW: Hindi]
('expenses', 'en', 'Expenses'),
('expenses', 'mr', 'खर्च'), -- [NEEDS REVIEW: Marathi]
('expenses', 'hi', 'व्यय'), -- [NEEDS REVIEW: Hindi]
('expenses_by_cat', 'en', 'Expenses by Category'),
('expenses_by_cat', 'mr', 'वर्गवारीनुसार खर्च'), -- [NEEDS REVIEW: Marathi]
('expenses_by_cat', 'hi', 'श्रेणी अनुसार व्यय'), -- [NEEDS REVIEW: Hindi]
('failed', 'en', 'Failed'),
('failed', 'mr', 'अयशस्वी'), -- [NEEDS REVIEW: Marathi]
('failed', 'hi', 'असफल'), -- [NEEDS REVIEW: Hindi]
('farm_added_success', 'en', 'Farm added successfully!'),
('farm_added_success', 'mr', 'शेत यशस्वीरित्या जोडले!'), -- [NEEDS REVIEW: Marathi]
('farm_added_success', 'hi', 'खेत सफलतापूर्वक जोड़ा गया!'), -- [NEEDS REVIEW: Hindi]
('farm_deleted_success', 'en', 'Farm deleted successfully!'),
('farm_deleted_success', 'mr', 'शेत यशस्वीरित्या हटवले!'), -- [NEEDS REVIEW: Marathi]
('farm_deleted_success', 'hi', 'खेत सफलतापूर्वक हटा दिया गया!'), -- [NEEDS REVIEW: Hindi]
('farm_name', 'en', 'Farm Name'),
('farm_name', 'mr', 'शेताचे नाव'), -- [NEEDS REVIEW: Marathi]
('farm_name', 'hi', 'खेत का नाम'), -- [NEEDS REVIEW: Hindi]
('farm_name_placeholder', 'en', 'e.g. Ganga Mala, Survey 42'),
('farm_name_placeholder', 'mr', 'उदा. गंगा मळा, गट क्र. ४२'), -- [NEEDS REVIEW: Marathi]
('farm_name_placeholder', 'hi', 'उदा. गंगा माला, खसरा 42'), -- [NEEDS REVIEW: Hindi]
('farm_updated_success', 'en', 'Farm updated successfully!'),
('farm_updated_success', 'mr', 'शेत यशस्वीरित्या अपडेट केले!'), -- [NEEDS REVIEW: Marathi]
('farm_updated_success', 'hi', 'खेत सफलतापूर्वक अपडेट किया गया!'), -- [NEEDS REVIEW: Hindi]
('farming_overview', 'en', 'Farming Overview'),
('farming_overview', 'mr', 'शेती आढावा'), -- [NEEDS REVIEW: Marathi]
('farming_overview', 'hi', 'कृषि अवलोकन'), -- [NEEDS REVIEW: Hindi]
('farming_overview_sub', 'en', 'Real-time aggregate analytics from your farm records'),
('farming_overview_sub', 'mr', 'आपल्या शेती नोंदींचे थेट विश्लेषण'), -- [NEEDS REVIEW: Marathi]
('farming_overview_sub', 'hi', 'आपके कृषि रिकॉर्ड का वास्तविक समय विश्लेषण'), -- [NEEDS REVIEW: Hindi]
('farms', 'en', 'Farms'),
('farms', 'mr', 'शेती'), -- [NEEDS REVIEW: Marathi]
('farms', 'hi', 'खेत'), -- [NEEDS REVIEW: Hindi]
('feature_alerts_desc', 'en', 'Early alerts for rainstorms, heatwaves, frost, and mandi rate surges.'),
('feature_alerts_desc', 'mr', 'वादळी पाऊस, उष्णतेची लाट, धुके आणि बाजार भाव वाढीसाठी पूर्वसूचना.'), -- [NEEDS REVIEW: Marathi]
('feature_alerts_desc', 'hi', 'बारिश, लू, पाला और मंडी दरों में उछाल के लिए पूर्व अलर्ट।'), -- [NEEDS REVIEW: Hindi]
('feature_calendar_desc', 'en', 'Daily activity schedules and timely task reminders across crop lifecycle stages.'),
('feature_calendar_desc', 'mr', 'पिकाच्या प्रत्येक टप्प्यानुसार दैनंदिन कामांचे वेळापत्रक आणि वेळेवर सूचना.'), -- [NEEDS REVIEW: Marathi]
('feature_calendar_desc', 'hi', 'फसल जीवनचक्र चरणों में दैनिक गतिविधि कार्यक्रम और समय पर कार्य अनुस्मारक।'), -- [NEEDS REVIEW: Hindi]
('feature_fert_desc', 'en', 'Custom fertilizer dosage calculated from soil deficits to prevent over-spending.'),
('feature_fert_desc', 'mr', 'अतिरिक्त खर्च टाळण्यासाठी मातीच्या गरजेनुसार अचूक खत मात्रा.'), -- [NEEDS REVIEW: Marathi]
('feature_fert_desc', 'hi', 'अनावश्यक खर्च से बचने के लिए मिट्टी के घाटे से गणना की गई कस्टम उर्वरक खुराक।'), -- [NEEDS REVIEW: Hindi]
('feature_i18n_desc', 'en', 'Seamless experience in English, Marathi, and Hindi for grassroots farmers.'),
('feature_i18n_desc', 'mr', 'शेतकऱ्यांसाठी इंग्रजी, मराठी आणि हिंदीमध्ये सुलभ अनुभव.'), -- [NEEDS REVIEW: Marathi]
('feature_i18n_desc', 'hi', 'भारतीय किसानों के लिए अंग्रेजी, मराठी और हिंदी में सहज अनुभव।'), -- [NEEDS REVIEW: Hindi]
('feature_profit_desc', 'en', 'Projected revenue and cost estimations before investing your capital.'),
('feature_profit_desc', 'mr', 'भांडवल गुंतवण्यापूर्वी अंदाजित महसूल आणि उत्पादन खर्च अंदाज.'), -- [NEEDS REVIEW: Marathi]
('feature_profit_desc', 'hi', 'अपनी पूंजी लगाने से पहले अनुमानित आय और लागत का विश्लेषण।'), -- [NEEDS REVIEW: Hindi]
('feature_recommend_desc', 'en', 'Scientific crop matching based on N-P-K, pH, temperature, humidity, and rainfall.'),
('feature_recommend_desc', 'mr', 'नत्र-स्फुरद-पालाश (N-P-K), सामू, तापमान, आर्द्रता आणि पावसावर आधारित अचूक पीक जुळणी.'), -- [NEEDS REVIEW: Marathi]
('feature_recommend_desc', 'hi', 'नाइट्रोजन, फास्फोरस, पोटाश (एन-पी-के), पीएच, तापमान, आर्द्रता और वर्षा पर आधारित वैज्ञानिक फसल मिलान।'), -- [NEEDS REVIEW: Hindi]
('features', 'en', 'Features'),
('features', 'mr', 'वैशिष्ट्ये'), -- [NEEDS REVIEW: Marathi]
('features', 'hi', 'विशेषताएं'), -- [NEEDS REVIEW: Hindi]
('features_sub', 'en', 'Comprehensive smart farm management engineered with precision agronomics.'),
('features_sub', 'mr', 'अचूक कृषिशास्त्रासह डिझाइन केलेले सर्वसमावेशक स्मार्ट शेती व्यवस्थापन.'), -- [NEEDS REVIEW: Marathi]
('features_sub', 'hi', 'सटीक कृषि विज्ञान के साथ डिज़ाइन किया गया व्यापक स्मार्ट फार्म प्रबंधन।'), -- [NEEDS REVIEW: Hindi]
('fertilizer_plan', 'en', 'Fertilizer Plan'),
('fertilizer_plan', 'mr', 'खत व्यवस्थापन'), -- [NEEDS REVIEW: Marathi]
('fertilizer_plan', 'hi', 'उर्वरक योजना'), -- [NEEDS REVIEW: Hindi]
('fertilizer_plan_subtitle', 'en', 'Tailored nutrient dosage recommendations calculated from soil chemistry'),
('fertilizer_plan_subtitle', 'mr', 'माती परीक्षणावर आधारित संतुलित खत मात्रा शिफारसी'), -- [NEEDS REVIEW: Marathi]
('fertilizer_plan_subtitle', 'hi', 'मिट्टी परीक्षण पर आधारित संतुलित खाद की सिफारिशें'), -- [NEEDS REVIEW: Hindi]
('fertilizer_plan_title', 'en', 'Fertilizer Plan & Nutrient Dosage'),
('fertilizer_plan_title', 'mr', 'खत व्यवस्थापन आणि पोषक घटक'), -- [NEEDS REVIEW: Marathi]
('fertilizer_plan_title', 'hi', 'उर्वरक योजना और पोषक तत्व मात्रा'), -- [NEEDS REVIEW: Hindi]
('fill_profile_district_village', 'en', 'Your profile has no district/village set. Auto-fill from this address?'),
('fill_profile_district_village', 'mr', 'आपल्या प्रोफाइलमध्ये जिल्हा/गाव सेट नाही. या पत्त्यावरून भरावे का?'), -- [NEEDS REVIEW: Marathi]
('fill_profile_district_village', 'hi', 'आपकी प्रोफ़ाइल में जिला/गांव सेट नहीं है। क्या इस पते से स्वतः भरें?'), -- [NEEDS REVIEW: Hindi]
('fill_profile_prompt', 'en', 'Update your profile district/village with this location?'),
('fill_profile_prompt', 'mr', 'आपल्या प्रोफाइलमधील जिल्हा आणि गाव या स्थानानुसार अपडेट करावे का?'), -- [NEEDS REVIEW: Marathi]
('fill_profile_prompt', 'hi', 'क्या इस स्थान से अपनी प्रोफ़ाइल का जिला और गांव अपडेट करना चाहते हैं?'), -- [NEEDS REVIEW: Hindi]
('filter_by_crop', 'en', 'Filter by crop...'),
('filter_by_crop', 'mr', 'पिकानुसार शोधा...'), -- [NEEDS REVIEW: Marathi]
('filter_by_crop', 'hi', 'फसल अनुसार खोजें...'), -- [NEEDS REVIEW: Hindi]
('filter_commodity', 'en', 'Filter Commodity'),
('filter_commodity', 'mr', 'शेतमाल निवडा'), -- [NEEDS REVIEW: Marathi]
('filter_commodity', 'hi', 'वस्तु चुनें'), -- [NEEDS REVIEW: Hindi]
('full_name', 'en', 'Full Name'),
('full_name', 'mr', 'पूर्ण नाव'), -- [NEEDS REVIEW: Marathi]
('full_name', 'hi', 'पूरा नाम'), -- [NEEDS REVIEW: Hindi]
('geo_permission_denied', 'en', 'Location permission denied. Please allow location access or search above.'),
('geo_permission_denied', 'mr', 'स्थान परवानगी नाकारली. कृपया स्थान परवानगी द्या किंवा शोध वापरा.'), -- [NEEDS REVIEW: Marathi]
('geo_permission_denied', 'hi', 'स्थान अनुमति अस्वीकृत। कृपया स्थान अनुमति दें या ऊपर खोजें।'), -- [NEEDS REVIEW: Hindi]
('geo_timeout', 'en', 'Location request timed out. Please try again or search.'),
('geo_timeout', 'mr', 'स्थान विनंतीची वेळ संपली. कृपया पुन्हा प्रयत्न करा.'), -- [NEEDS REVIEW: Marathi]
('geo_timeout', 'hi', 'स्थान अनुरोध समय समाप्त। कृपया पुनः प्रयास करें।'), -- [NEEDS REVIEW: Hindi]
('geo_unavailable', 'en', 'Location information is unavailable. Please search for your village/city.'),
('geo_unavailable', 'mr', 'स्थान माहिती उपलब्ध नाही. कृपया गाव/शहर शोधा.'), -- [NEEDS REVIEW: Marathi]
('geo_unavailable', 'hi', 'स्थान की जानकारी अनुपलब्ध है। कृपया अपना गांव/शहर खोजें।'), -- [NEEDS REVIEW: Hindi]
('get_started_free', 'en', 'Get Started Free'),
('get_started_free', 'mr', 'मोफत सुरुवात करा'), -- [NEEDS REVIEW: Marathi]
('get_started_free', 'hi', 'मुफ्त शुरुआत करें'), -- [NEEDS REVIEW: Hindi]
('gps', 'en', 'GPS'),
('gps', 'mr', 'जीपीएस'), -- [NEEDS REVIEW: Marathi]
('gps', 'hi', 'जीपीएस'), -- [NEEDS REVIEW: Hindi]
('growing', 'en', 'Growing'),
('growing', 'mr', 'वाढीच्या टप्प्यात'), -- [NEEDS REVIEW: Marathi]
('growing', 'hi', 'विकासशील'), -- [NEEDS REVIEW: Hindi]
('growth_stages_calendar', 'en', 'Growth Stages Calendar & Tasks'),
('growth_stages_calendar', 'mr', 'पीक वाढीचे टप्पे आणि कामे'), -- [NEEDS REVIEW: Marathi]
('growth_stages_calendar', 'hi', 'फसल वृद्धि के चरण और कार्य'), -- [NEEDS REVIEW: Hindi]
('growth_stages_subtitle', 'en', 'Real-time stage timeline from crop_calendar_view with tasks and dates'),
('growth_stages_subtitle', 'mr', 'कॅलेंडरनुसार पीक वाढीचे टप्पे, तारखा आणि नियोजित कामे'), -- [NEEDS REVIEW: Marathi]
('growth_stages_subtitle', 'hi', 'कैलेंडर अनुसार फसल वृद्धि के चरण, तिथियां और कार्य'), -- [NEEDS REVIEW: Hindi]
('harvest_countdown', 'en', 'Harvest Countdown'),
('harvest_countdown', 'mr', 'काढणी उलटी गिनती'), -- [NEEDS REVIEW: Marathi]
('harvest_countdown', 'hi', 'कटाई की उलटी गिनती'), -- [NEEDS REVIEW: Hindi]
('harvest_history_sub', 'en', 'Financial track records and yield outcomes from completed cycles'),
('harvest_history_sub', 'mr', 'पूर्ण झालेल्या हंगामांचे आर्थिक व उत्पादन रेकॉर्ड'), -- [NEEDS REVIEW: Marathi]
('harvest_history_sub', 'hi', 'पूर्ण फसल चक्रों के वित्तीय और उपज परिणाम'), -- [NEEDS REVIEW: Hindi]
('harvest_yield', 'en', 'Harvest Yield'),
('harvest_yield', 'mr', 'काढणी उत्पादन'), -- [NEEDS REVIEW: Marathi]
('harvest_yield', 'hi', 'कटाई की उपज'), -- [NEEDS REVIEW: Hindi]
('harvested', 'en', 'Harvested'),
('harvested', 'mr', 'काढणी झाली'), -- [NEEDS REVIEW: Marathi]
('harvested', 'hi', 'कटाई हो गई'), -- [NEEDS REVIEW: Hindi]
('hero_subtitle', 'en', 'AI-driven crop suitability, soil health advisories, dynamic fertilizer plans, and mandi alerts built for Indian farmers.'),
('hero_subtitle', 'mr', 'भारतीय शेतकऱ्यांसाठी AI आधारित पीक शिफारसी, माती आरोग्य सल्ला, खत नियोजन आणि बाजार भाव सूचना.'), -- [NEEDS REVIEW: Marathi]
('hero_subtitle', 'hi', 'भारतीय किसानों के लिए एआई-संचालित फसल उपयुक्तता, मृदा स्वास्थ्य सलाह, गतिशील उर्वरक योजना और मंडी अलर्ट।'), -- [NEEDS REVIEW: Hindi]
('hero_title', 'en', 'Smart Agriculture, Better Yields, Maximized Profits'),
('hero_title', 'mr', 'स्मार्ट शेती, उत्तम उत्पादन, जास्तीत जास्त नफा'), -- [NEEDS REVIEW: Marathi]
('hero_title', 'hi', 'स्मार्ट कृषि, बेहतर पैदावार, अधिकतम लाभ'), -- [NEEDS REVIEW: Hindi]
('history', 'en', 'History'),
('history', 'mr', 'इतिहास'), -- [NEEDS REVIEW: Marathi]
('history', 'hi', 'इतिहास'), -- [NEEDS REVIEW: Hindi]
('how_it_works', 'en', 'How It Works'),
('how_it_works', 'mr', 'हे कसे कार्य करते'), -- [NEEDS REVIEW: Marathi]
('how_it_works', 'hi', 'यह कैसे काम करता है'), -- [NEEDS REVIEW: Hindi]
('how_it_works_sub', 'en', 'Four easy steps from soil testing to high-profit market harvest.'),
('how_it_works_sub', 'mr', 'माती परीक्षणापासून ते भरघोस नफ्यापर्यंत चार सोप्या पायऱ्या.'), -- [NEEDS REVIEW: Marathi]
('how_it_works_sub', 'hi', 'मिट्टी परीक्षण से लेकर अधिक लाभ वाली फसल तक चार आसान चरण।'), -- [NEEDS REVIEW: Hindi]
('humidity', 'en', 'Humidity'),
('humidity', 'mr', 'आर्द्रता'), -- [NEEDS REVIEW: Marathi]
('humidity', 'hi', 'आर्द्रता'), -- [NEEDS REVIEW: Hindi]
('in_season_badge', 'en', 'In Season'),
('in_season_badge', 'mr', 'हंगामात उपयुक्त'), -- [NEEDS REVIEW: Marathi]
('in_season_badge', 'hi', 'मौसम अनुकूल'), -- [NEEDS REVIEW: Hindi]
('irrigation', 'en', 'Irrigation'),
('irrigation', 'mr', 'सिंचन'), -- [NEEDS REVIEW: Marathi]
('irrigation', 'hi', 'सिंचाई'), -- [NEEDS REVIEW: Hindi]
('language', 'en', 'Language'),
('language', 'mr', 'भाषा'), -- [NEEDS REVIEW: Marathi]
('language', 'hi', 'भाषा'), -- [NEEDS REVIEW: Hindi]
('languages_supported_stat', 'en', 'Languages (EN | MR | HI)'),
('languages_supported_stat', 'mr', 'उपलब्ध भाषा (इंग्रजी | मराठी | हिंदी)'), -- [NEEDS REVIEW: Marathi]
('languages_supported_stat', 'hi', 'उपलब्ध भाषाएं (अंग्रेजी | मराठी | हिंदी)'), -- [NEEDS REVIEW: Hindi]
('latitude', 'en', 'Latitude'),
('latitude', 'mr', 'अक्षांश'), -- [NEEDS REVIEW: Marathi]
('latitude', 'hi', 'अक्षांश'), -- [NEEDS REVIEW: Hindi]
('loading', 'en', 'Loading...'),
('loading', 'mr', 'लोड होत आहे...'), -- [NEEDS REVIEW: Marathi]
('loading', 'hi', 'लोड हो रहा है...'), -- [NEEDS REVIEW: Hindi]
('loading_active_cycles', 'en', 'Loading active cycles...'),
('loading_active_cycles', 'mr', 'चालू पिके लोड होत आहेत...'), -- [NEEDS REVIEW: Marathi]
('loading_active_cycles', 'hi', 'सक्रिय फसलें लोड हो रही हैं...'), -- [NEEDS REVIEW: Hindi]
('loading_farms', 'en', 'Loading farms...'),
('loading_farms', 'mr', 'शेती लोड होत आहे...'), -- [NEEDS REVIEW: Marathi]
('loading_farms', 'hi', 'खेत लोड हो रहे हैं...'), -- [NEEDS REVIEW: Hindi]
('loc_denied', 'en', 'Location access was denied. Please search or pick on map.'),
('loc_denied', 'mr', 'स्थान परवानगी नाकारली. कृपया शोधा किंवा नकाशावर निवडा.'), -- [NEEDS REVIEW: Marathi]
('loc_denied', 'hi', 'स्थान पहुंच अस्वीकृत। कृपया खोजें या मानचित्र पर चुनें।'), -- [NEEDS REVIEW: Hindi]
('loc_timeout', 'en', 'Location request timed out. Please try again or search.'),
('loc_timeout', 'mr', 'वेळ संपली. कृपया पुन्हा प्रयत्न करा किंवा शोधा.'), -- [NEEDS REVIEW: Marathi]
('loc_timeout', 'hi', 'समय समाप्त। कृपया पुनः प्रयास करें।'), -- [NEEDS REVIEW: Hindi]
('loc_unavailable', 'en', 'Current location unavailable. Please search or pick on map.'),
('loc_unavailable', 'mr', 'स्थान अनुपलब्ध. कृपया शोधा किंवा नकाशावर निवडा.'), -- [NEEDS REVIEW: Marathi]
('loc_unavailable', 'hi', 'स्थान अनुपलब्ध। कृपया खोजें या मानचित्र पर चुनें।'), -- [NEEDS REVIEW: Hindi]
('locating', 'en', 'Detecting location...'),
('locating', 'mr', 'स्थान शोधत आहे...'), -- [NEEDS REVIEW: Marathi]
('locating', 'hi', 'स्थान का पता लगाया जा रहा है...'), -- [NEEDS REVIEW: Hindi]
('location', 'en', 'Location'),
('location', 'mr', 'स्थान'), -- [NEEDS REVIEW: Marathi]
('location', 'hi', 'स्थान'), -- [NEEDS REVIEW: Hindi]
('location_label', 'en', 'Location Label'),
('location_label', 'mr', 'स्थानाचे नाव'), -- [NEEDS REVIEW: Marathi]
('location_label', 'hi', 'स्थान का नाम'), -- [NEEDS REVIEW: Hindi]
('location_out_of_india', 'en', 'Note: Coordinates appear to be outside India (Lat: 6°-38° N, Lon: 68°-98° E)'),
('location_out_of_india', 'mr', 'सूचना: अक्षांश-रेखांश भारताबाहेरील वाटत आहेत'), -- [NEEDS REVIEW: Marathi]
('location_out_of_india', 'hi', 'सूचना: निर्देशांक भारत से बाहर प्रतीत होते हैं'), -- [NEEDS REVIEW: Hindi]
('log_id', 'en', 'Log ID'),
('log_id', 'mr', 'नोंद क्रमांक'), -- [NEEDS REVIEW: Marathi]
('log_id', 'hi', 'लॉग आईडी'), -- [NEEDS REVIEW: Hindi]
('login', 'en', 'Login'),
('login', 'mr', 'लॉगिन'), -- [NEEDS REVIEW: Marathi]
('login', 'hi', 'लॉगिन'), -- [NEEDS REVIEW: Hindi]
('login_sub', 'en', 'Sign in to your farmer account to manage crops and plots'),
('login_sub', 'mr', 'आपल्या शेतीचे व्यवस्थापन करण्यासाठी शेतकरी खात्यात लॉगिन करा'), -- [NEEDS REVIEW: Marathi]
('login_sub', 'hi', 'अपनी फसलों और खेतों का प्रबंधन करने के लिए किसान खाते में लॉगिन करें'), -- [NEEDS REVIEW: Hindi]
('logout', 'en', 'Logout'),
('logout', 'mr', 'लॉगआउट'), -- [NEEDS REVIEW: Marathi]
('logout', 'hi', 'लॉगआउट'), -- [NEEDS REVIEW: Hindi]
('longitude', 'en', 'Longitude'),
('longitude', 'mr', 'रेखांश'), -- [NEEDS REVIEW: Marathi]
('longitude', 'hi', 'रेखांश'), -- [NEEDS REVIEW: Hindi]
('mandi_highlights', 'en', 'Live Mandi Price Highlights'),
('mandi_highlights', 'mr', 'थेट कृषी उत्पन्न बाजार भाव'), -- [NEEDS REVIEW: Marathi]
('mandi_highlights', 'hi', 'ताजा मंडी भाव हाइलाइट्स'), -- [NEEDS REVIEW: Hindi]
('map_instruction', 'en', 'Click map or drag pin to set farm location'),
('map_instruction', 'mr', 'शेताचे स्थान निवडण्यासाठी नकाशावर क्लिक करा किंवा पिन हलवा'), -- [NEEDS REVIEW: Marathi]
('map_instruction', 'hi', 'खेत का स्थान सेट करने के लिए मानचित्र पर क्लिक करें या पिन खींचें'), -- [NEEDS REVIEW: Hindi]
('mark_all_read', 'en', 'Mark All as Read'),
('mark_all_read', 'mr', 'सर्व वाचले म्हणून खूण करा'), -- [NEEDS REVIEW: Marathi]
('mark_all_read', 'hi', 'सभी को पढ़ा गया चिह्नित करें'), -- [NEEDS REVIEW: Hindi]
('mark_read', 'en', 'Mark as read'),
('mark_read', 'mr', 'वाचले म्हणून खूण करा'), -- [NEEDS REVIEW: Marathi]
('mark_read', 'hi', 'पढ़ा गया चिह्नित करें'), -- [NEEDS REVIEW: Hindi]
('market_prices', 'en', 'Market Prices'),
('market_prices', 'mr', 'बाजार भाव'), -- [NEEDS REVIEW: Marathi]
('market_prices', 'hi', 'मंडी भाव'), -- [NEEDS REVIEW: Hindi]
('market_prices_sub', 'en', 'Live and recent APMC mandi wholesale rates across Maharashtra'),
('market_prices_sub', 'mr', 'महाराष्ट्रातील थेट आणि ताजे कृषी उत्पन्न बाजार भाव'), -- [NEEDS REVIEW: Marathi]
('market_prices_sub', 'hi', 'महाराष्ट्र भर में लाइव और हालिया एपीएमसी थोक मंडी दरें'), -- [NEEDS REVIEW: Hindi]
('match_rank', 'en', 'Match'),
('match_rank', 'mr', 'जुळणी'), -- [NEEDS REVIEW: Marathi]
('match_rank', 'hi', 'मिलान'), -- [NEEDS REVIEW: Hindi]
('mobile_number', 'en', 'Mobile Number'),
('mobile_number', 'mr', 'मोबाईल क्रमांक'), -- [NEEDS REVIEW: Marathi]
('mobile_number', 'hi', 'मोबाइल नंबर'), -- [NEEDS REVIEW: Hindi]
('moisture', 'en', 'Moisture (%)'),
('moisture', 'mr', 'ओलावा (%)'), -- [NEEDS REVIEW: Marathi]
('moisture', 'hi', 'नमी (%)'), -- [NEEDS REVIEW: Hindi]
('my_farms', 'en', 'My Farms'),
('my_farms', 'mr', 'माझी शेते'), -- [NEEDS REVIEW: Marathi]
('my_farms', 'hi', 'मेरे खेत'), -- [NEEDS REVIEW: Hindi]
('my_farms_sub', 'en', 'Manage your farm plots, soil metrics, and location mapping'),
('my_farms_sub', 'mr', 'आपली शेतजमीन, माती घटक आणि स्थानांचे व्यवस्थापन करा'), -- [NEEDS REVIEW: Marathi]
('my_farms_sub', 'hi', 'अपने खेत, मिट्टी के घटक और स्थान का प्रबंधन करें'), -- [NEEDS REVIEW: Hindi]
('net_profit', 'en', 'Net Profit'),
('net_profit', 'mr', 'निव्वळ नफा'), -- [NEEDS REVIEW: Marathi]
('net_profit', 'hi', 'शुद्ध लाभ'), -- [NEEDS REVIEW: Hindi]
('new_status', 'en', 'New Status'),
('new_status', 'mr', 'नवीन स्थिती'), -- [NEEDS REVIEW: Marathi]
('new_status', 'hi', 'नई स्थिति'), -- [NEEDS REVIEW: Hindi]
('nitrogen', 'en', 'Nitrogen (N)'),
('nitrogen', 'mr', 'नत्र (N)'), -- [NEEDS REVIEW: Marathi]
('nitrogen', 'hi', 'नाइट्रोजन (N)'), -- [NEEDS REVIEW: Hindi]
('nitrogen_label', 'en', 'Nitrogen N (kg/ha)'),
('nitrogen_label', 'mr', 'नत्र N (किलो/हेक्टर)'), -- [NEEDS REVIEW: Marathi]
('nitrogen_label', 'hi', 'नाइट्रोजन N (किग्रा/हे.)'), -- [NEEDS REVIEW: Hindi]
('no_active_cycles', 'en', 'No Active Crop Cycles'),
('no_active_cycles', 'mr', 'कोणतेही चालू पीक नाही'), -- [NEEDS REVIEW: Marathi]
('no_active_cycles', 'hi', 'कोई सक्रिय फसल चक्र नहीं है'), -- [NEEDS REVIEW: Hindi]
('no_active_cycles_desc', 'en', 'You don\'t have any ongoing crop cycles. Start a cycle directly or visit your farms to get crop recommendations.'),
('no_active_cycles_desc', 'mr', 'सध्या कोणताही पीक हंगाम चालू नाही. थेट नवीन पीक सुरू करा किंवा शिफारसी मिळवण्यासाठी शेती विभागात जा.'), -- [NEEDS REVIEW: Marathi]
('no_active_cycles_desc', 'hi', 'वर्तमान में कोई फसल चक्र सक्रिय नहीं है। सीधे नई फसल शुरू करें या सिफारिशें देखने के लिए खेत अनुभाग पर जाएं।'), -- [NEEDS REVIEW: Hindi]
('no_alerts_desc', 'en', 'Your crops and weather conditions are stable. Automated notifications will appear here when weather warnings or scheduled stage tasks trigger.'),
('no_alerts_desc', 'mr', 'आपली पिके आणि हवामान सध्या स्थिर आहे. हवामानाचा इशारा किंवा नियोजित कामे आल्यास येथे सूचना दिसतील.'), -- [NEEDS REVIEW: Marathi]
('no_alerts_desc', 'hi', 'आपकी फसलें और मौसम की स्थिति सामान्य है। मौसम चेतावनी या निर्धारित कार्य होने पर यहाँ सूचनाएं दिखाई देंगी।'), -- [NEEDS REVIEW: Hindi]
('no_alerts_found', 'en', 'No Alerts Found'),
('no_alerts_found', 'mr', 'कोणतीही सूचना नाही'), -- [NEEDS REVIEW: Marathi]
('no_alerts_found', 'hi', 'कोई चेतावनी नहीं मिली'), -- [NEEDS REVIEW: Hindi]
('no_alerts_message', 'en', 'You have no unread alerts at this time.'),
('no_alerts_message', 'mr', 'आपल्याकडे सध्या कोणतीही न वाचलेली सूचना नाही.'), -- [NEEDS REVIEW: Marathi]
('no_alerts_message', 'hi', 'इस समय आपके पास कोई अपठित अलर्ट नहीं है।'), -- [NEEDS REVIEW: Hindi]
('no_data', 'en', 'No data available'),
('no_data', 'mr', 'माहिती उपलब्ध नाही'), -- [NEEDS REVIEW: Marathi]
('no_data', 'hi', 'कोई डेटा उपलब्ध नहीं'), -- [NEEDS REVIEW: Hindi]
('no_farms_desc', 'en', 'Add your farm plot details to get personalized crop recommendations.'),
('no_farms_desc', 'mr', 'वैयक्तिक पीक शिफारसी मिळवण्यासाठी आपल्या शेताची माहिती जोडा.'), -- [NEEDS REVIEW: Marathi]
('no_farms_desc', 'hi', 'व्यक्तिगत फसल सिफारिशें प्राप्त करने के लिए अपने खेत का विवरण जोड़ें।'), -- [NEEDS REVIEW: Hindi]
('no_farms_msg', 'en', 'You have no farms registered yet.'),
('no_farms_msg', 'mr', 'आपल्याकडे अद्याप कोणतीही शेती नोंदवलेली नाही.'), -- [NEEDS REVIEW: Marathi]
('no_farms_msg', 'hi', 'आपके पास अभी तक कोई खेत पंजीकृत नहीं है।'), -- [NEEDS REVIEW: Hindi]
('no_farms_yet', 'en', 'No Farms Added Yet'),
('no_farms_yet', 'mr', 'अद्याप शेती जोडलेली नाही'), -- [NEEDS REVIEW: Marathi]
('no_farms_yet', 'hi', 'अभी तक कोई खेत नहीं जोड़ा गया'), -- [NEEDS REVIEW: Hindi]
('no_gps_recorded', 'en', 'No GPS Recorded'),
('no_gps_recorded', 'mr', 'जीपीएस नोंदवले नाही'), -- [NEEDS REVIEW: Marathi]
('no_gps_recorded', 'hi', 'जीपीएस दर्ज नहीं है'), -- [NEEDS REVIEW: Hindi]
('no_locations_found', 'en', 'No matching locations found in India'),
('no_locations_found', 'mr', 'भारतात जुळणारे कोणतेही स्थान आढळले नाही'), -- [NEEDS REVIEW: Marathi]
('no_locations_found', 'hi', 'भारत में कोई मिलता-जुलता स्थान नहीं मिला'), -- [NEEDS REVIEW: Hindi]
('no_recs_desc', 'en', 'No crops matched your soil and weather criteria. Try updating soil test values.'),
('no_recs_desc', 'mr', 'आपल्या माती आणि हवामानाच्या निकषांशी जुळणारे पीक सापडले नाही. माती परीक्षण माहिती तपासा.'), -- [NEEDS REVIEW: Marathi]
('no_recs_desc', 'hi', 'आपकी मिट्टी और मौसम के अनुसार कोई फसल नहीं मिली। मिट्टी परीक्षण के मान अपडेट करें।'), -- [NEEDS REVIEW: Hindi]
('no_recs_matched', 'en', 'No Matching Crops Found'),
('no_recs_matched', 'mr', 'कोणतीही जुळणारी पिके आढळली नाहीत'), -- [NEEDS REVIEW: Marathi]
('no_recs_matched', 'hi', 'कोई मेल खाने वाली फसल नहीं मिली'), -- [NEEDS REVIEW: Hindi]
('no_unread_alerts', 'en', 'No Unread Alerts'),
('no_unread_alerts', 'mr', 'नवीन सूचना नाहीत'), -- [NEEDS REVIEW: Marathi]
('no_unread_alerts', 'hi', 'कोई नई चेतावनी नहीं है'), -- [NEEDS REVIEW: Hindi]
('no_unread_desc', 'en', 'All your field and weather notifications have been reviewed.'),
('no_unread_desc', 'mr', 'आपल्या शेतातील सर्व हवामान व पीक सूचना वाचल्या गेल्या आहेत.'), -- [NEEDS REVIEW: Marathi]
('no_unread_desc', 'hi', 'आपके खेत और मौसम की सभी सूचनाएं देखी जा चुकी हैं।'), -- [NEEDS REVIEW: Hindi]
('notes', 'en', 'Notes'),
('notes', 'mr', 'टीप'), -- [NEEDS REVIEW: Marathi]
('notes', 'hi', 'टिप्पणी'), -- [NEEDS REVIEW: Hindi]
('organic_carbon', 'en', 'Organic Carbon (%)'),
('organic_carbon', 'mr', 'सेंद्रिय कर्ब (%)'), -- [NEEDS REVIEW: Marathi]
('organic_carbon', 'hi', 'जैविक कार्बन (%)'), -- [NEEDS REVIEW: Hindi]
('overdue', 'en', 'overdue'),
('overdue', 'mr', 'उशीर झाला'), -- [NEEDS REVIEW: Marathi]
('overdue', 'hi', 'विलंबित'), -- [NEEDS REVIEW: Hindi]
('password', 'en', 'Password'),
('password', 'mr', 'पासवर्ड'), -- [NEEDS REVIEW: Marathi]
('password', 'hi', 'पासवर्ड'), -- [NEEDS REVIEW: Hindi]
('ph', 'en', 'Soil pH'),
('ph', 'mr', 'सामू (pH)'), -- [NEEDS REVIEW: Marathi]
('ph', 'hi', 'मृदा पीएच (pH)'), -- [NEEDS REVIEW: Hindi]
('phone_or_email', 'en', 'Phone Number or Email'),
('phone_or_email', 'mr', 'फोन नंबर किंवा ईमेल'), -- [NEEDS REVIEW: Marathi]
('phone_or_email', 'hi', 'फ़ोन नंबर या ईमेल'), -- [NEEDS REVIEW: Hindi]
('phosphorus', 'en', 'Phosphorus (P)'),
('phosphorus', 'mr', 'स्फुरद (P)'), -- [NEEDS REVIEW: Marathi]
('phosphorus', 'hi', 'फास्फोरस (P)'), -- [NEEDS REVIEW: Hindi]
('phosphorus_label', 'en', 'Phosphorus P (kg/ha)'),
('phosphorus_label', 'mr', 'स्फुरद P (किलो/हेक्टर)'), -- [NEEDS REVIEW: Marathi]
('phosphorus_label', 'hi', 'फास्फोरस P (किग्रा/हे.)'), -- [NEEDS REVIEW: Hindi]
('placeholder_create_password', 'en', 'Create a secure password (min 6 chars)'),
('placeholder_create_password', 'mr', 'सुरक्षित पासवर्ड तयार करा (किमान ६ अक्षरे)'), -- [NEEDS REVIEW: Marathi]
('placeholder_create_password', 'hi', 'सुरक्षित पासवर्ड बनाएं (कम से कम 6 अक्षर)'), -- [NEEDS REVIEW: Hindi]
('placeholder_district', 'en', 'e.g. Pune, Nashik, Latur'),
('placeholder_district', 'mr', 'उदा. पुणे, नाशिक, लातूर'), -- [NEEDS REVIEW: Marathi]
('placeholder_district', 'hi', 'उदा. पुणे, नासिक, लातूर'), -- [NEEDS REVIEW: Hindi]
('placeholder_mobile', 'en', '10-digit Indian mobile number'),
('placeholder_mobile', 'mr', '१० अंकी मोबाईल क्रमांक'), -- [NEEDS REVIEW: Marathi]
('placeholder_mobile', 'hi', '१० अंकों का मोबाइल नंबर'), -- [NEEDS REVIEW: Hindi]
('placeholder_name', 'en', 'Enter farmer\'s full name'),
('placeholder_name', 'mr', 'शेतकऱ्याचे पूर्ण नाव टाका'), -- [NEEDS REVIEW: Marathi]
('placeholder_name', 'hi', 'किसान का पूरा नाम दर्ज करें'), -- [NEEDS REVIEW: Hindi]
('placeholder_password', 'en', 'Enter your password'),
('placeholder_password', 'mr', 'आपला पासवर्ड टाका'), -- [NEEDS REVIEW: Marathi]
('placeholder_password', 'hi', 'अपना पासवर्ड दर्ज करें'), -- [NEEDS REVIEW: Hindi]
('placeholder_phone_or_email', 'en', 'e.g. 9876543210 or farmer@agri.in'),
('placeholder_phone_or_email', 'mr', 'उदा. ९८७६५४३२१० किंवा farmer@agri.in'), -- [NEEDS REVIEW: Marathi]
('placeholder_phone_or_email', 'hi', 'उदा. 9876543210 या farmer@agri.in'), -- [NEEDS REVIEW: Hindi]
('placeholder_village', 'en', 'e.g. Khed, Baramati'),
('placeholder_village', 'mr', 'उदा. खेड, बारामती'), -- [NEEDS REVIEW: Marathi]
('placeholder_village', 'hi', 'उदा. खेड, बारामती'), -- [NEEDS REVIEW: Hindi]
('planned', 'en', 'Planned'),
('planned', 'mr', 'नियोजित'), -- [NEEDS REVIEW: Marathi]
('planned', 'hi', 'नियोजित'), -- [NEEDS REVIEW: Hindi]
('potassium', 'en', 'Potassium (K)'),
('potassium', 'mr', 'पालाश (K)'), -- [NEEDS REVIEW: Marathi]
('potassium', 'hi', 'पोटेशियम (K)'), -- [NEEDS REVIEW: Hindi]
('potassium_label', 'en', 'Potassium K (kg/ha)'),
('potassium_label', 'mr', 'पालाश K (किलो/हेक्टर)'), -- [NEEDS REVIEW: Marathi]
('potassium_label', 'hi', 'पोटेशियम K (किग्रा/हे.)'), -- [NEEDS REVIEW: Hindi]
('preferred_language', 'en', 'Three Languages'),
('preferred_language', 'mr', 'तीन भाषा'), -- [NEEDS REVIEW: Marathi]
('preferred_language', 'hi', 'तीन भाषाएं'), -- [NEEDS REVIEW: Hindi]
('prev_status', 'en', 'Previous Status'),
('prev_status', 'mr', 'मागील स्थिती'), -- [NEEDS REVIEW: Marathi]
('prev_status', 'hi', 'पिछली स्थिति'), -- [NEEDS REVIEW: Hindi]
('price_per_quintal', 'en', 'Price per quintal'),
('price_per_quintal', 'mr', 'प्रति क्विंटल भाव'), -- [NEEDS REVIEW: Marathi]
('price_per_quintal', 'hi', 'प्रति क्विंटल मूल्य'), -- [NEEDS REVIEW: Hindi]
('profile', 'en', 'Profile'),
('profile', 'mr', 'प्रोफाइल'), -- [NEEDS REVIEW: Marathi]
('profile', 'hi', 'प्रोफ़ाइल'), -- [NEEDS REVIEW: Hindi]
('profile_updated', 'en', 'Profile district and village updated successfully!'),
('profile_updated', 'mr', 'जिल्हा आणि गाव यशस्वीरित्या अपडेट केले!'), -- [NEEDS REVIEW: Marathi]
('profile_updated', 'hi', 'जिला और गांव सफलतापूर्वक अपडेट किया गया!'), -- [NEEDS REVIEW: Hindi]
('profit', 'en', 'Profit'),
('profit', 'mr', 'नफा'), -- [NEEDS REVIEW: Marathi]
('profit', 'hi', 'लाभ'), -- [NEEDS REVIEW: Hindi]
('profit_per_cycle', 'en', 'Profit per Completed Cycle (Rs)'),
('profit_per_cycle', 'mr', 'प्रति पीक निव्वळ नफा (रु.)'), -- [NEEDS REVIEW: Marathi]
('profit_per_cycle', 'hi', 'प्रति फसल शुद्ध लाभ (रु.)'), -- [NEEDS REVIEW: Hindi]
('quick_actions', 'en', 'Quick Actions'),
('quick_actions', 'mr', 'जलद कृती'), -- [NEEDS REVIEW: Marathi]
('quick_actions', 'hi', 'त्वरित कार्य'), -- [NEEDS REVIEW: Hindi]
('rainfall', 'en', 'Rainfall'),
('rainfall', 'mr', 'पर्जन्यमान'), -- [NEEDS REVIEW: Marathi]
('rainfall', 'hi', 'वर्षा'), -- [NEEDS REVIEW: Hindi]
('recommend_crop', 'en', 'Recommend Crop'),
('recommend_crop', 'mr', 'पीक शिफारस'), -- [NEEDS REVIEW: Marathi]
('recommend_crop', 'hi', 'फसल सिफारिश'), -- [NEEDS REVIEW: Hindi]
('recommendations_stat', 'en', 'Recommendations Made'),
('recommendations_stat', 'mr', 'दिलेल्या एकूण शिफारसी'), -- [NEEDS REVIEW: Marathi]
('recommendations_stat', 'hi', 'कुल दी गई सिफारिशें'), -- [NEEDS REVIEW: Hindi]
('recommended_next_step', 'en', 'Recommended Next Step'),
('recommended_next_step', 'mr', 'पुढील शिफारस केलेले पाऊल'), -- [NEEDS REVIEW: Marathi]
('recommended_next_step', 'hi', 'अनुशंसित अगला कदम'), -- [NEEDS REVIEW: Hindi]
('record_expense', 'en', 'Record Expense'),
('record_expense', 'mr', 'खर्चाची नोंद करा'), -- [NEEDS REVIEW: Marathi]
('record_expense', 'hi', 'खर्च दर्ज करें'), -- [NEEDS REVIEW: Hindi]
('refresh', 'en', 'Refresh'),
('refresh', 'mr', 'ताजे करा'), -- [NEEDS REVIEW: Marathi]
('refresh', 'hi', 'ताज़ा करें'), -- [NEEDS REVIEW: Hindi]
('refresh_data', 'en', 'Refresh Data'),
('refresh_data', 'mr', 'माहिती ताजी करा'), -- [NEEDS REVIEW: Marathi]
('refresh_data', 'hi', 'डेटा रीफ्रेश करें'), -- [NEEDS REVIEW: Hindi]
('refresh_plan', 'en', 'Refresh Plan'),
('refresh_plan', 'mr', 'योजना ताजी करा'), -- [NEEDS REVIEW: Marathi]
('refresh_plan', 'hi', 'योजना ताज़ा करें'), -- [NEEDS REVIEW: Hindi]
('register', 'en', 'Register'),
('register', 'mr', 'नोंदणी करा'), -- [NEEDS REVIEW: Marathi]
('register', 'hi', 'पंजीकरण करें'), -- [NEEDS REVIEW: Hindi]
('register_sub', 'en', 'Create your farmer account to get personalized advisories'),
('register_sub', 'mr', 'वैयक्तिक पीक सल्ल्यासाठी आपले शेतकरी खाते तयार करा'), -- [NEEDS REVIEW: Marathi]
('register_sub', 'hi', 'व्यक्तिगत फसल सलाह के लिए अपना किसान खाता बनाएं'), -- [NEEDS REVIEW: Hindi]
('revenue', 'en', 'Revenue'),
('revenue', 'mr', 'उत्पन्न'), -- [NEEDS REVIEW: Marathi]
('revenue', 'hi', 'आय'), -- [NEEDS REVIEW: Hindi]
('rotation_advice', 'en', 'What to grow next'),
('rotation_advice', 'mr', 'पुढील पीक कोणते घ्यावे'), -- [NEEDS REVIEW: Marathi]
('rotation_advice', 'hi', 'आगे क्या उगाएं'), -- [NEEDS REVIEW: Hindi]
('sample_data', 'en', 'Sample data'),
('sample_data', 'mr', 'नमुना माहिती'), -- [NEEDS REVIEW: Marathi]
('sample_data', 'hi', 'नमूना डेटा'), -- [NEEDS REVIEW: Hindi]
('sample_mandi_sub', 'en', 'Sample modal rates across key Maharashtra agricultural produce market committees.'),
('sample_mandi_sub', 'mr', 'महाराष्ट्रातील प्रमुख कृषी उत्पन्न बाजार समित्यांमधील नमुना दर.'), -- [NEEDS REVIEW: Marathi]
('sample_mandi_sub', 'hi', 'महाराष्ट्र की प्रमुख कृषि उपज मंडी समितियों में नमूना थोक दरें।'), -- [NEEDS REVIEW: Hindi]
('save', 'en', 'Save'),
('save', 'mr', 'जतन करा'), -- [NEEDS REVIEW: Marathi]
('save', 'hi', 'सहेजें'), -- [NEEDS REVIEW: Hindi]
('save_farm_btn', 'en', 'Save Farm'),
('save_farm_btn', 'mr', 'शेत जतन करा'), -- [NEEDS REVIEW: Marathi]
('save_farm_btn', 'hi', 'खेत सहेजें'), -- [NEEDS REVIEW: Hindi]
('search', 'en', 'Search'),
('search', 'mr', 'शोधा'), -- [NEEDS REVIEW: Marathi]
('search', 'hi', 'खोजें'), -- [NEEDS REVIEW: Hindi]
('search_location', 'en', 'Search village, town or city'),
('search_location', 'mr', 'गाव, तालुका किंवा शहर शोधा'), -- [NEEDS REVIEW: Marathi]
('search_location', 'hi', 'गांव, कस्बा या शहर खोजें'), -- [NEEDS REVIEW: Hindi]
('search_location_placeholder', 'en', 'Search village, town or city...'),
('search_location_placeholder', 'mr', 'गाव, तालुका किंवा शहर शोधा...'), -- [NEEDS REVIEW: Marathi]
('search_location_placeholder', 'hi', 'गांव, कस्बा या शहर खोजें...'), -- [NEEDS REVIEW: Hindi]
('searching', 'en', 'Searching...'),
('searching', 'mr', 'शोधत आहे...'), -- [NEEDS REVIEW: Marathi]
('searching', 'hi', 'खोज जारी है...'), -- [NEEDS REVIEW: Hindi]
('season_annual', 'en', 'Annual'),
('season_annual', 'mr', 'वार्षिक'), -- [NEEDS REVIEW: Marathi]
('season_annual', 'hi', 'वार्षिक'), -- [NEEDS REVIEW: Hindi]
('season_filter', 'en', 'Season Filter'),
('season_filter', 'mr', 'हंगाम निवडा'), -- [NEEDS REVIEW: Marathi]
('season_filter', 'hi', 'मौसम चुनें'), -- [NEEDS REVIEW: Hindi]
('season_kharif', 'en', 'Kharif'),
('season_kharif', 'mr', 'खरीप'), -- [NEEDS REVIEW: Marathi]
('season_kharif', 'hi', 'खरीफ'), -- [NEEDS REVIEW: Hindi]
('season_rabi', 'en', 'Rabi'),
('season_rabi', 'mr', 'रब्बी'), -- [NEEDS REVIEW: Marathi]
('season_rabi', 'hi', 'रबी'), -- [NEEDS REVIEW: Hindi]
('season_zaid', 'en', 'Zaid'),
('season_zaid', 'mr', 'उन्हाळी (झायेद)'), -- [NEEDS REVIEW: Marathi]
('season_zaid', 'hi', 'जायद'), -- [NEEDS REVIEW: Hindi]
('select_crop', 'en', 'Select Crop'),
('select_crop', 'mr', 'पीक निवडा'), -- [NEEDS REVIEW: Marathi]
('select_crop', 'hi', 'फसल चुनें'), -- [NEEDS REVIEW: Hindi]
('select_farm', 'en', 'Select Farm'),
('select_farm', 'mr', 'शेत निवडा'), -- [NEEDS REVIEW: Marathi]
('select_farm', 'hi', 'खेत चुनें'), -- [NEEDS REVIEW: Hindi]
('smart_agri_badge', 'en', 'Smart Agriculture Engine'),
('smart_agri_badge', 'mr', 'स्मार्ट शेती तंत्रज्ञान'), -- [NEEDS REVIEW: Marathi]
('smart_agri_badge', 'hi', 'स्मार्ट कृषि इंजन'), -- [NEEDS REVIEW: Hindi]
('soft_warning_outside_india', 'en', 'Coordinates appear to be outside India (expected lat 6-38, lon 68-98)'),
('soft_warning_outside_india', 'mr', 'अक्षांश-रेखांश भारताबाहेरील वाटत आहेत (अपेक्षित अक्षांश 6-38, रेखांश 68-98)'), -- [NEEDS REVIEW: Marathi]
('soft_warning_outside_india', 'hi', 'निर्देशांक भारत के बाहर प्रतीत होते हैं (अपेक्षित अक्षांश 6-38, देशांतर 68-98)'), -- [NEEDS REVIEW: Hindi]
('soil_health_card', 'en', 'Soil Health Parameters'),
('soil_health_card', 'mr', 'माती परीक्षण घटक'), -- [NEEDS REVIEW: Marathi]
('soil_health_card', 'hi', 'मृदा स्वास्थ्य पैरामीटर'), -- [NEEDS REVIEW: Hindi]
('soil_ph_label', 'en', 'Soil pH (0.0 - 14.0)'),
('soil_ph_label', 'mr', 'माती सामू pH (०.० - १४.०)'), -- [NEEDS REVIEW: Marathi]
('soil_ph_label', 'hi', 'मृदा पीएच pH (0.0 - 14.0)'), -- [NEEDS REVIEW: Hindi]
('soil_ph_range', 'en', 'Soil pH (0 - 14)'),
('soil_ph_range', 'mr', 'माती सामू (० - १४)'), -- [NEEDS REVIEW: Marathi]
('soil_ph_range', 'hi', 'मृदा पीएच (0 - 14)'), -- [NEEDS REVIEW: Hindi]
('soil_test', 'en', 'Soil Test'),
('soil_test', 'mr', 'माती परीक्षण'), -- [NEEDS REVIEW: Marathi]
('soil_test', 'hi', 'मृदा परीक्षण'), -- [NEEDS REVIEW: Hindi]
('soil_type', 'en', 'Soil Type'),
('soil_type', 'mr', 'मातीचा प्रकार'), -- [NEEDS REVIEW: Marathi]
('soil_type', 'hi', 'मिट्टी का प्रकार'), -- [NEEDS REVIEW: Hindi]
('sowing_date', 'en', 'Sowing date'),
('sowing_date', 'mr', 'पेरणी दिनांक'), -- [NEEDS REVIEW: Marathi]
('sowing_date', 'hi', 'बुवाई की तारीख'), -- [NEEDS REVIEW: Hindi]
('sowing_date_label', 'en', 'Sowing Date'),
('sowing_date_label', 'mr', 'पेरणी दिनांक'), -- [NEEDS REVIEW: Marathi]
('sowing_date_label', 'hi', 'बुवाई की तारीख'), -- [NEEDS REVIEW: Hindi]
('sowing_now', 'en', 'Sowing Now'),
('sowing_now', 'mr', 'सध्याची पेरणी'), -- [NEEDS REVIEW: Marathi]
('sowing_now', 'hi', 'वर्तमान बुवाई'), -- [NEEDS REVIEW: Hindi]
('sowing_now_subtitle', 'en', 'Crops best suited for sowing in the current season and year-round perennials.'),
('sowing_now_subtitle', 'mr', 'सध्याच्या हंगामात पेरणीसाठी योग्य पिके आणि बारमाही पिके.'), -- [NEEDS REVIEW: Marathi]
('sowing_now_subtitle', 'hi', 'वर्तमान मौसम और बारहमासी फसलों के लिए सबसे उपयुक्त फसलें।'), -- [NEEDS REVIEW: Hindi]
('sown_date', 'en', 'Sown Date'),
('sown_date', 'mr', 'पेरणी तारीख'), -- [NEEDS REVIEW: Marathi]
('sown_date', 'hi', 'बुआई की तारीख'), -- [NEEDS REVIEW: Hindi]
('spend_by_category', 'en', 'Spend by Category'),
('spend_by_category', 'mr', 'प्रवर्गानुसार खर्च'), -- [NEEDS REVIEW: Marathi]
('spend_by_category', 'hi', 'श्रेणी अनुसार खर्च'), -- [NEEDS REVIEW: Hindi]
('start_cycle', 'en', 'Start this crop'),
('start_cycle', 'mr', 'हे पीक सुरू करा'), -- [NEEDS REVIEW: Marathi]
('start_cycle', 'hi', 'यह फसल शुरू करें'), -- [NEEDS REVIEW: Hindi]
('start_cycle_btn', 'en', 'Start Cycle'),
('start_cycle_btn', 'mr', 'हंगाम सुरू करा'), -- [NEEDS REVIEW: Marathi]
('start_cycle_btn', 'hi', 'फसल चक्र शुरू करें'), -- [NEEDS REVIEW: Hindi]
('start_cycle_desc', 'en', 'Begin tracking crop growth stages, fertilizer applications, and field expenses.'),
('start_cycle_desc', 'mr', 'पिकाचे टप्पे, खतांचे डोस आणि शेती खर्चाचा मागोवा घेणे सुरू करा.'), -- [NEEDS REVIEW: Marathi]
('start_cycle_desc', 'hi', 'फसल के चरणों, खाद की खुराक और खर्चों की निगरानी शुरू करें।'), -- [NEEDS REVIEW: Hindi]
('start_cycle_title', 'en', 'Start Crop Cycle'),
('start_cycle_title', 'mr', 'नवीन पीक हंगाम सुरू करा'), -- [NEEDS REVIEW: Marathi]
('start_cycle_title', 'hi', 'नई फसल चक्र शुरू करें'), -- [NEEDS REVIEW: Hindi]
('start_new_cycle', 'en', 'Start New Cycle'),
('start_new_cycle', 'mr', 'नवीन पीक सुरू करा'), -- [NEEDS REVIEW: Marathi]
('start_new_cycle', 'hi', 'नई फसल शुरू करें'), -- [NEEDS REVIEW: Hindi]
('start_this_crop', 'en', 'Start This Crop'),
('start_this_crop', 'mr', 'हे पीक सुरू करा'), -- [NEEDS REVIEW: Marathi]
('start_this_crop', 'hi', 'यह फसल शुरू करें'), -- [NEEDS REVIEW: Hindi]
('status', 'en', 'Status'),
('status', 'mr', 'स्थिती'), -- [NEEDS REVIEW: Marathi]
('status', 'hi', 'स्थिति'), -- [NEEDS REVIEW: Hindi]
('status_audit_log', 'en', 'Status Audit Log'),
('status_audit_log', 'mr', 'स्थिती इतिहास नोंद'), -- [NEEDS REVIEW: Marathi]
('status_audit_log', 'hi', 'स्थिति इतिहास लॉग'), -- [NEEDS REVIEW: Hindi]
('status_audit_subtitle', 'en', 'Audit trail of status transitions from crop_cycle_log'),
('status_audit_subtitle', 'mr', 'पीक स्थिती बदलांचा संपूर्ण इतिहास'), -- [NEEDS REVIEW: Marathi]
('status_audit_subtitle', 'hi', 'फसल स्थिति परिवर्तनों का संपूर्ण इतिहास'), -- [NEEDS REVIEW: Hindi]
('step_1_desc', 'en', 'Pick your village on the interactive map and enter basic soil test N-P-K and pH levels.'),
('step_1_desc', 'mr', 'नकाशावर आपले गाव निवडा आणि माती तपासणीचे N-P-K व pH प्रमाण टाका.'), -- [NEEDS REVIEW: Marathi]
('step_1_desc', 'hi', 'मानचित्र पर अपना गांव चुनें और बुनियादी मिट्टी परीक्षण एन-पी-के और पीएच स्तर दर्ज करें।'), -- [NEEDS REVIEW: Hindi]
('step_1_title', 'en', 'Enter Soil & Location'),
('step_1_title', 'mr', 'माती व स्थान प्रविष्ट करा'), -- [NEEDS REVIEW: Marathi]
('step_1_title', 'hi', 'मिट्टी और स्थान दर्ज करें'), -- [NEEDS REVIEW: Hindi]
('step_2_desc', 'en', 'Advanced database scoring algorithms rank the top crops best suited for your plot.'),
('step_2_desc', 'mr', 'आमचे अल्गोरिदम आपल्या जमिनीसाठी सर्वोत्तम योग्य पिकांची क्रमवारी ठरवते.'), -- [NEEDS REVIEW: Marathi]
('step_2_desc', 'hi', 'उन्नत डेटाबेस स्कोरिंग एल्गोरिदम आपके खेत के लिए सबसे उपयुक्त फसलों को रैंक करता है।'), -- [NEEDS REVIEW: Hindi]
('step_2_title', 'en', 'Get Top Suitability'),
('step_2_title', 'mr', 'शीर्ष उपयुक्तता मिळवा'), -- [NEEDS REVIEW: Marathi]
('step_2_title', 'hi', 'शीर्ष उपयुक्तता प्राप्त करें'), -- [NEEDS REVIEW: Hindi]
('step_3_desc', 'en', 'Receive stage-by-stage task notifications, irrigation schedules, and nutrient dosages.'),
('step_3_desc', 'mr', 'प्रत्येक टप्प्यावर कामाच्या सूचना, पाणी व्यवस्थापन आणि खतांचे डोस मिळवा.'), -- [NEEDS REVIEW: Marathi]
('step_3_desc', 'hi', 'चरण-दर-चरण कार्य सूचनाएं, सिंचाई कार्यक्रम और पोषक तत्वों की खुराक प्राप्त करें।'), -- [NEEDS REVIEW: Hindi]
('step_3_title', 'en', 'Follow Stage Advisories'),
('step_3_title', 'mr', 'टप्प्यानुसार सल्ल्याचे पालन करा'), -- [NEEDS REVIEW: Marathi]
('step_3_title', 'hi', 'चरण-वार सलाह का पालन करें'), -- [NEEDS REVIEW: Hindi]
('step_4_desc', 'en', 'Monitor local APMC mandi commodity rates and record expenses for maximum return on investment.'),
('step_4_desc', 'mr', 'स्थानिक कृषी उत्पन्न बाजार समित्यांचे भाव पहा आणि जास्तीत जास्त नफ्यासाठी खर्चाची नोंद ठेवा.'), -- [NEEDS REVIEW: Marathi]
('step_4_desc', 'hi', 'स्थानीय एपीएमसी मंडी दरों पर नजर रखें और अधिकतम लाभ के लिए खर्च रिकॉर्ड करें।'), -- [NEEDS REVIEW: Hindi]
('step_4_title', 'en', 'Track Mandis & Profit'),
('step_4_title', 'mr', 'बाजार भाव व नफा ट्रॅक करा'), -- [NEEDS REVIEW: Marathi]
('step_4_title', 'hi', 'मंडी भाव और लाभ ट्रैक करें'), -- [NEEDS REVIEW: Hindi]
('suitability', 'en', 'Suitability'),
('suitability', 'mr', 'उपयुक्तता'), -- [NEEDS REVIEW: Marathi]
('suitability', 'hi', 'उपयुक्तता'), -- [NEEDS REVIEW: Hindi]
('temperature', 'en', 'Temperature'),
('temperature', 'mr', 'तापमान'), -- [NEEDS REVIEW: Marathi]
('temperature', 'hi', 'तापमान'), -- [NEEDS REVIEW: Hindi]
('timestamp', 'en', 'Timestamp'),
('timestamp', 'mr', 'वेळ / दिनांक'), -- [NEEDS REVIEW: Marathi]
('timestamp', 'hi', 'समय / दिनांक'), -- [NEEDS REVIEW: Hindi]
('top_crops_heading', 'en', 'Recommended Crops for Your Farm'),
('top_crops_heading', 'mr', 'आपल्या शेतासाठी शिफारस केलेली पिके'), -- [NEEDS REVIEW: Marathi]
('top_crops_heading', 'hi', 'आपके खेत के लिए अनुशंसित फसलें'), -- [NEEDS REVIEW: Hindi]
('total', 'en', 'Total'),
('total', 'mr', 'एकूण'), -- [NEEDS REVIEW: Marathi]
('total', 'hi', 'कुल'), -- [NEEDS REVIEW: Hindi]
('total_expenses', 'en', 'Total Expenses'),
('total_expenses', 'mr', 'एकूण खर्च'), -- [NEEDS REVIEW: Marathi]
('total_expenses', 'hi', 'कुल खर्च'), -- [NEEDS REVIEW: Hindi]
('total_farms', 'en', 'Total Farms'),
('total_farms', 'mr', 'एकूण शेते'), -- [NEEDS REVIEW: Marathi]
('total_farms', 'hi', 'कुल खेत'), -- [NEEDS REVIEW: Hindi]
('total_revenue', 'en', 'Total Revenue'),
('total_revenue', 'mr', 'एकूण उत्पन्न'), -- [NEEDS REVIEW: Marathi]
('total_revenue', 'hi', 'कुल आय'), -- [NEEDS REVIEW: Hindi]
('try_it_now', 'en', 'Try It Now'),
('try_it_now', 'mr', 'आत्ताच वापरून पहा'), -- [NEEDS REVIEW: Marathi]
('try_it_now', 'hi', 'अभी आज़माएं'), -- [NEEDS REVIEW: Hindi]
('try_it_subtitle', 'en', 'Enter your soil & weather parameters for instant top-3 crop recommendations without registration.'),
('try_it_subtitle', 'mr', 'नोंदणी न करता तात्काळ शीर्ष ३ पीक शिफारसींसाठी आपल्या माती व हवामानाचे निकष टाका.'), -- [NEEDS REVIEW: Marathi]
('try_it_subtitle', 'hi', 'पंजीकरण के बिना त्वरित शीर्ष 3 फसल सिफारिशों के लिए अपनी मिट्टी और मौसम पैरामीटर दर्ज करें।'), -- [NEEDS REVIEW: Hindi]
('try_quick_check', 'en', 'Try a Quick Crop Check'),
('try_quick_check', 'mr', 'त्वरित पीक चाचणी घ्या'), -- [NEEDS REVIEW: Marathi]
('try_quick_check', 'hi', 'त्वरित फसल जांच करें'), -- [NEEDS REVIEW: Hindi]
('update_profile', 'en', 'Update Profile'),
('update_profile', 'mr', 'प्रोफाइल अपडेट करा'), -- [NEEDS REVIEW: Marathi]
('update_profile', 'hi', 'प्रोफ़ाइल अपडेट करें'), -- [NEEDS REVIEW: Hindi]
('update_profile_btn', 'en', 'Save to Profile'),
('update_profile_btn', 'mr', 'प्रोफाइलमध्ये जतन करा'), -- [NEEDS REVIEW: Marathi]
('update_profile_btn', 'hi', 'प्रोफ़ाइल में सहेजें'), -- [NEEDS REVIEW: Hindi]
('use_current_location', 'en', 'Use my current location'),
('use_current_location', 'mr', 'माझे सध्याचे स्थान वापरा'), -- [NEEDS REVIEW: Marathi]
('use_current_location', 'hi', 'मेरा वर्तमान स्थान उपयोग करें'), -- [NEEDS REVIEW: Hindi]
('view_calendar', 'en', 'View Lifecycle Calendar'),
('view_calendar', 'mr', 'वेळापत्रक पहा'), -- [NEEDS REVIEW: Marathi]
('view_calendar', 'hi', 'जीवनचक्र कैलेंडर देखें'), -- [NEEDS REVIEW: Hindi]
('view_fertilizer_plan', 'en', 'View Fertilizer Plan'),
('view_fertilizer_plan', 'mr', 'खत नियोजन पहा'), -- [NEEDS REVIEW: Marathi]
('view_fertilizer_plan', 'hi', 'उर्वरक योजना देखें'), -- [NEEDS REVIEW: Hindi]
('village', 'en', 'Village / Town'),
('village', 'mr', 'गाव / शहर'), -- [NEEDS REVIEW: Marathi]
('village', 'hi', 'गांव / कस्बा'), -- [NEEDS REVIEW: Hindi]
('weather', 'en', 'Weather'),
('weather', 'mr', 'हवामान'), -- [NEEDS REVIEW: Marathi]
('weather', 'hi', 'मौसम'), -- [NEEDS REVIEW: Hindi]
('weather_refreshed', 'en', 'Weather records refreshed successfully!'),
('weather_refreshed', 'mr', 'हवामान माहिती ताजी केली!'), -- [NEEDS REVIEW: Marathi]
('weather_refreshed', 'hi', 'मौसम डेटा रीफ्रेश किया गया!'), -- [NEEDS REVIEW: Hindi]
('what_to_grow_next', 'en', 'What to Grow Next'),
('what_to_grow_next', 'mr', 'पुढे काय पिकवायचे'), -- [NEEDS REVIEW: Marathi]
('what_to_grow_next', 'hi', 'आगे क्या उगाएं'), -- [NEEDS REVIEW: Hindi]
('yield_kg', 'en', 'Yield (kg)'),
('yield_kg', 'mr', 'उत्पादन (किलो)'), -- [NEEDS REVIEW: Marathi]
('yield_kg', 'hi', 'पैदावार (किग्रा)'), -- [NEEDS REVIEW: Hindi]
ON DUPLICATE KEY UPDATE text = VALUES(text);
