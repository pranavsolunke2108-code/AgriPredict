"""Why this crop explanation service and calculation helpers."""

from typing import Any, Dict, List, Optional
from app import db
from app.schemas import WhyCropItem, WhyCropResponse
from app.i18n_defaults import DEFAULT_TRANSLATIONS


def get_localized_crop_name(crop_id: int, crop_name: str, lang: str = "en") -> str:
    """Resolve localized crop name for the given language."""
    if lang in ("mr", "hi"):
        try:
            row = db.fetch_one(
                "SELECT localized_name FROM crop_localized_view WHERE crop_id = %s AND lang = %s",
                (crop_id, lang),
            )
            if row and row.get("localized_name"):
                return str(row["localized_name"])
        except Exception:
            pass

        key = f"crop_{crop_name.lower().replace(' ', '_')}"
        clean = DEFAULT_TRANSLATIONS.get(lang, {}).get(key)
        if clean:
            return clean

    return crop_name


def build_why_crop_response(
    crop_id: int,
    crop_name: str,
    raw_rows: List[Dict[str, Any]],
    lang: str = "en",
) -> WhyCropResponse:
    """Build standardized WhyCropResponse from stored procedure evaluation rows.

    Procedures explain_crop_for_farm and explain_crop_fit return 7 rows:
    param_key, farm_value, ideal_min, ideal_max, status, score, weight.

    Calculation rules:
    - good_count: count of items where status is 'ideal' or 'ok'.
    - summary_level: 'strong' if good_count >= 5, 'moderate' if 3-4, 'weak' if <= 2.
    - tips:
      - 'why_tip_fertilizer' if any nutrient (nitrogen, phosphorus, potassium) is 'low' or 'very_low'.
      - 'why_tip_climate' if temperature, humidity or rainfall is not 'ideal'.
      - 'why_tip_ph' if ph is not 'ideal'.
    - Numbers rounded to 1 decimal place.
    """
    items: List[WhyCropItem] = []
    good_count = 0

    has_low_nutrient = False
    has_climate_issue = False
    has_ph_issue = False

    for r in raw_rows:
        param = str(r.get("param_key") or r.get("param") or "")
        val = round(float(r["farm_value"]), 1) if r.get("farm_value") is not None else 0.0
        imin = round(float(r["ideal_min"]), 1) if r.get("ideal_min") is not None else None
        imax = round(float(r["ideal_max"]), 1) if r.get("ideal_max") is not None else None
        status = str(r.get("status") or "ideal").lower()
        score = round(float(r["score"]), 1) if r.get("score") is not None else 0.0
        weight = int(r.get("weight") or 0)

        if status in ("ideal", "ok"):
            good_count += 1

        if param in ("nitrogen", "phosphorus", "potassium") and status in ("low", "very_low"):
            has_low_nutrient = True
        elif param in ("temperature", "humidity", "rainfall") and status != "ideal":
            has_climate_issue = True
        elif param == "ph" and status != "ideal":
            has_ph_issue = True

        items.append(
            WhyCropItem(
                param=param,
                value=val,
                ideal_min=imin,
                ideal_max=imax,
                status=status,
                score=score,
                weight=weight,
            )
        )

    # Determine summary level
    if good_count >= 5:
        summary_level = "strong"
    elif good_count >= 3:
        summary_level = "moderate"
    else:
        summary_level = "weak"

    # Select relevant tips
    tips: List[str] = []
    if has_low_nutrient:
        tips.append("why_tip_fertilizer")
    if has_climate_issue:
        tips.append("why_tip_climate")
    if has_ph_issue:
        tips.append("why_tip_ph")

    localized_name = get_localized_crop_name(crop_id, crop_name, lang)

    return WhyCropResponse(
        crop_id=crop_id,
        crop_name=localized_name,
        summary_level=summary_level,
        good_count=good_count,
        items=items,
        tips=tips,
    )
