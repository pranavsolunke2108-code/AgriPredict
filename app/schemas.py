"""Pydantic request and response schemas for AgriPredict API."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# Supported enumerations matching agripredict_schema.sql
LanguageType = Literal["en", "mr", "hi"]
RoleType = Literal["farmer", "admin"]
SoilType = Literal["Black", "Red", "Alluvial", "Laterite", "Sandy", "Clay", "Loamy"]
IrrigationType = Literal["Rainfed", "Canal", "Well", "Drip", "Sprinkler"]


# -----------------------------------------------------------------------------
# Farmer / Authentication Schemas
# -----------------------------------------------------------------------------

class FarmerRegisterRequest(BaseModel):
    """Payload for POST /auth/register."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of farmer")
    phone: str = Field(..., min_length=10, max_length=15, description="Unique mobile number")
    email: Optional[EmailStr] = Field(None, max_length=100, description="Optional unique email address")
    password: str = Field(..., min_length=6, max_length=72, description="Password (6 to 72 characters)")
    district: Optional[str] = Field(None, max_length=60, description="District name")
    village: Optional[str] = Field(None, max_length=80, description="Village name")
    language: LanguageType = Field("en", description="Preferred language (en, mr, hi)")

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not cleaned.replace("+", "").isdigit() or len(cleaned) < 10:
            raise ValueError("Phone number must contain at least 10 digits")
        return cleaned

    @field_validator("email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str) and not v.strip():
            return None
        return v


class FarmerLoginRequest(BaseModel):
    """Payload for POST /auth/login.

    Accepts phone or email in 'identifier', 'phone_or_email', 'username', or 'phone'/'email'.
    """
    identifier: Optional[str] = None
    phone_or_email: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    password: str = Field(..., min_length=1, description="Account password")

    @model_validator(mode="after")
    def resolve_identifier(self) -> "FarmerLoginRequest":
        # Resolve which field provided the username/phone/email
        id_value = self.identifier or self.phone_or_email or self.username or self.phone or self.email
        if not id_value or not id_value.strip():
            raise ValueError("Must provide phone or email as login identifier")
        self.identifier = id_value.strip()
        return self


class FarmerResponse(BaseModel):
    """Profile data returned for a farmer (never reveals password_hash)."""
    farmer_id: int
    name: str
    phone: str
    email: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    language: LanguageType
    role: RoleType
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Alias for FarmerResponse
FarmerProfileResponse = FarmerResponse


class TokenResponse(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"
    farmer: Optional[FarmerResponse] = None


# -----------------------------------------------------------------------------
# Farm Schemas
# -----------------------------------------------------------------------------

class FarmCreateRequest(BaseModel):
    """Payload for POST /farms."""
    farm_name: str = Field(..., min_length=1, max_length=100, description="Name of the farm / plot")
    area_acres: float = Field(..., gt=0, le=10000.0, description="Farm area in acres (must be > 0)")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="GPS latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="GPS longitude (-180 to 180)")
    soil_type: Optional[SoilType] = Field(None, description="Soil classification")
    irrigation: IrrigationType = Field("Rainfed", description="Primary irrigation source")
    location_label: Optional[str] = Field(None, max_length=150, description="Readable location label e.g. Pune, Maharashtra")


class FarmUpdateRequest(BaseModel):
    """Payload for PUT /farms/{farm_id}."""
    farm_name: Optional[str] = Field(None, min_length=1, max_length=100)
    area_acres: Optional[float] = Field(None, gt=0, le=10000.0)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    soil_type: Optional[SoilType] = None
    irrigation: Optional[IrrigationType] = None
    location_label: Optional[str] = Field(None, max_length=150)


class FarmResponse(BaseModel):
    """Farm record response."""
    farm_id: int
    farmer_id: int
    farm_name: str
    area_acres: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[SoilType] = None
    irrigation: IrrigationType
    location_label: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Standard message response."""
    detail: str
    success: bool = True


class LanguageUpdateRequest(BaseModel):
    """Payload for PATCH /me/language."""
    language: LanguageType = Field(..., description="Preferred language: en, mr, or hi")


class FarmerAddressUpdateRequest(BaseModel):
    """Payload for PATCH /me/address."""
    district: Optional[str] = Field(None, max_length=60, description="Farmer district")
    village: Optional[str] = Field(None, max_length=80, description="Farmer village")


class GeoSuggestion(BaseModel):
    """Geocoding search suggestion."""
    display_name: str
    label: str
    lat: float
    lon: float
    address: Optional[Dict[str, Any]] = None


class GeoReverseResponse(BaseModel):
    """Reverse geocoding response."""
    display_name: str
    label: str
    lat: float
    lon: float
    address: Optional[Dict[str, Any]] = None
    warning: Optional[str] = None


# -----------------------------------------------------------------------------
# Soil Test Schemas
# -----------------------------------------------------------------------------

from datetime import date


class SoilTestCreateRequest(BaseModel):
    """Payload for POST /farms/{farm_id}/soil-tests."""
    test_date: Optional[date] = Field(None, description="Date sample was tested (default: today)")
    nitrogen: float = Field(..., ge=0.0, description="Nitrogen (N) content in kg/ha, must be >= 0")
    phosphorus: float = Field(..., ge=0.0, description="Phosphorus (P) content in kg/ha, must be >= 0")
    potassium: float = Field(..., ge=0.0, description="Potassium (K) content in kg/ha, must be >= 0")
    ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH (0.0 to 14.0)")
    moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Soil moisture percentage (0.0 to 100.0)")
    organic_carbon: Optional[float] = Field(None, ge=0.0, description="Organic carbon percentage (>= 0)")

    @model_validator(mode="after")
    def default_test_date(self) -> "SoilTestCreateRequest":
        if self.test_date is None:
            self.test_date = date.today()
        return self


class SoilTestResponse(BaseModel):
    """Soil test record response."""
    test_id: int
    farm_id: int
    test_date: date
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    moisture: Optional[float] = None
    organic_carbon: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Weather Schemas
# -----------------------------------------------------------------------------

class ManualWeatherCreateRequest(BaseModel):
    """Payload for manual daily weather entry."""
    record_date: Optional[date] = Field(None, description="Weather record date (default: today)")
    temperature: float = Field(..., ge=-50.0, le=65.0, description="Mean temperature in Celsius")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Mean relative humidity percentage (0-100)")
    rainfall_mm: float = Field(..., ge=0.0, le=2000.0, description="Total precipitation in mm")

    @model_validator(mode="after")
    def default_record_date(self) -> "ManualWeatherCreateRequest":
        if self.record_date is None:
            self.record_date = date.today()
        return self


class WeatherRecordResponse(BaseModel):
    """Weather entry response."""
    weather_id: int
    farm_id: int
    record_date: date
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rainfall_mm: Optional[float] = None
    source: Literal["api", "manual"]

    model_config = ConfigDict(from_attributes=True)


class WeatherSyncResponse(BaseModel):
    """Response returned when refreshing weather records from Open-Meteo API."""
    message: str
    records_synced: int
    cached: bool
    farm_id: int


# -----------------------------------------------------------------------------
# Recommendation Schemas
# -----------------------------------------------------------------------------

SeasonType = Literal["auto", "ALL", "Kharif", "Rabi", "Zaid"]


class RecommendationRequest(BaseModel):
    """Payload for POST /farms/{farm_id}/recommend."""
    test_id: Optional[int] = Field(None, description="Soil test ID to base recommendation on (default: latest)")
    season: Optional[SeasonType] = Field("auto", description="Target cropping season (auto, ALL, Kharif, Rabi, Zaid)")


class CropScoreBreakdown(BaseModel):
    """Detailed score breakdown for a recommended crop."""
    rank_no: int
    crop_id: Optional[int] = None
    crop_name: str
    season: str
    suitability: float
    ph_score: float
    temp_score: float
    humidity_score: float
    rain_score: float
    n_score: float
    p_score: float
    k_score: float
    prediction_id: Optional[int] = None
    econ_source: Optional[str] = None
    econ_year: Optional[int] = None


class WhyCropItem(BaseModel):
    """Single agronomic factor evaluation item for Why this crop."""
    param: str
    value: float
    ideal_min: Optional[float] = None
    ideal_max: Optional[float] = None
    status: str
    score: float
    weight: int


class WhyCropResponse(BaseModel):
    """Why this crop explanation response."""
    crop_id: int
    crop_name: str
    summary_level: Literal["strong", "moderate", "weak"]
    good_count: int
    items: List[WhyCropItem]
    tips: List[str]


class PublicWhyRequest(BaseModel):
    """Payload for public POST /public/why."""
    crop_id: int = Field(..., gt=0, description="Crop ID")
    ph: float = Field(..., description="Soil pH value (0.0 - 14.0)")
    n: float = Field(..., description="Soil Nitrogen (kg/ha >= 0)")
    p: float = Field(..., description="Soil Phosphorus (kg/ha >= 0)")
    k: float = Field(..., description="Soil Potassium (kg/ha >= 0)")
    temperature: float = Field(..., description="Ambient Temperature in °C (-10 to 60)")
    humidity: float = Field(..., description="Relative Humidity percentage (0 - 100)")
    rainfall: float = Field(..., description="30-day rainfall in mm (>= 0)")
    lang: Optional[Literal["en", "mr", "hi"]] = Field("en", description="Output language")


class RecommendationResponse(BaseModel):
    """Top 3 recommendations returned by the recommend_crops procedure."""
    farm_id: int
    test_id: int
    season: str
    weather_status: str
    recommendations: List[CropScoreBreakdown]


class PredictionItem(BaseModel):
    """Single crop prediction item within a historical recommendation run."""
    prediction_id: Optional[int] = None
    rank_no: int
    crop_id: int
    crop_name: str
    season: str
    suitability_score: float


class PredictionGroupResponse(BaseModel):
    """Historical recommendation run containing its top 3 crop recommendations."""
    predicted_on: datetime
    farm_id: int
    test_id: int
    weather_id: Optional[int] = None
    crops: List[PredictionItem]


# -----------------------------------------------------------------------------
# Phase 3: Crop Cycle Schemas
# -----------------------------------------------------------------------------

CropCycleStatus = Literal["Planned", "Growing", "Harvested", "Failed"]
ExpenseCategory = Literal["Seeds", "Fertilizer", "Pesticide", "Labour", "Irrigation", "Machinery", "Other"]


class CycleStartRequest(BaseModel):
    """Payload for starting a crop cycle: POST /farms/{farm_id}/cycles."""
    crop_id: int = Field(..., description="ID of the crop being planted")
    prediction_id: Optional[int] = Field(None, description="Optional prediction_id if started from recommendation")
    sowing_date: Optional[date] = Field(None, description="Date of sowing (defaults to today)")

    @model_validator(mode="after")
    def default_sowing(self) -> "CycleStartRequest":
        if self.sowing_date is None:
            self.sowing_date = date.today()
        return self


class CycleCloseRequest(BaseModel):
    """Payload for closing a crop cycle: POST /cycles/{cycle_id}/close."""
    status: Literal["Harvested", "Failed"] = Field(..., description="Closing status: Harvested or Failed")
    yield_kg: Optional[float] = Field(None, description="Total yield in kg (required for Harvested)")
    price_per_quintal: Optional[float] = Field(None, description="Selling price per quintal in currency")

    @model_validator(mode="after")
    def validate_harvest_fields(self) -> "CycleCloseRequest":
        if self.status == "Harvested":
            if self.yield_kg is None or self.yield_kg < 0:
                raise ValueError("A valid non-negative yield (in kg) is required for a harvested cycle")
        return self


class CycleResponse(BaseModel):
    """Crop cycle response details."""
    cycle_id: int
    farm_id: int
    crop_id: int
    crop_name: Optional[str] = None
    farm_name: Optional[str] = None
    prediction_id: Optional[int] = None
    sowing_date: Optional[date] = None
    expected_harvest: Optional[date] = None
    actual_harvest: Optional[date] = None
    status: str
    yield_kg: Optional[float] = None
    selling_price_per_quintal: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CycleLogItem(BaseModel):
    """Audit log entry from crop_cycle_log."""
    log_id: int
    cycle_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Phase 3: Expenses Schemas
# -----------------------------------------------------------------------------

class ExpenseCreateRequest(BaseModel):
    """Payload for POST /cycles/{cycle_id}/expenses."""
    category: ExpenseCategory = Field(..., description="Expense category")
    amount: float = Field(..., ge=0.0, description="Expense amount (must be >= 0)")
    expense_date: Optional[date] = Field(None, description="Date of expense (defaults to today)")
    notes: Optional[str] = Field(None, max_length=200, description="Notes/description of expense")

    @model_validator(mode="after")
    def default_expense_date(self) -> "ExpenseCreateRequest":
        if self.expense_date is None:
            self.expense_date = date.today()
        return self


class ExpenseResponse(BaseModel):
    """Expense item response."""
    expense_id: int
    cycle_id: int
    category: str
    amount: float
    expense_date: date
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Phase 3: Dashboard Views Schemas
# -----------------------------------------------------------------------------

class DashboardSummaryResponse(BaseModel):
    """Aggregate statistics from farmer_summary_view."""
    farmer_id: int
    name: str
    total_farms: int = 0
    active_cycles: int = 0
    completed_cycles: int = 0
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class CurrentStatusItem(BaseModel):
    """Row from current_status_view for active crop cycles."""
    farmer_id: int
    farm_id: int
    farm_name: str
    cycle_id: int
    crop_name: str
    status: str
    sowing_date: Optional[date] = None
    expected_harvest: Optional[date] = None
    days_since_sowing: Optional[int] = None
    days_until_sowing: Optional[int] = None
    days_to_harvest: Optional[int] = None
    progress_pct: float = 0.0
    current_stage: str
    current_task: Optional[str] = None
    expenses_so_far: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class HistoryItem(BaseModel):
    """Row from farmer_history_view for completed crop cycles."""
    farmer_id: int
    farm_id: int
    farm_name: str
    cycle_id: int
    crop_name: str
    status: str
    sowing_date: Optional[date] = None
    actual_harvest: Optional[date] = None
    yield_kg: Optional[float] = None
    selling_price_per_quintal: Optional[float] = None
    revenue: float = 0.0
    total_expenses: float = 0.0
    profit: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Phase 4: Fertilizer Advisory, Rotation Advice, Calendar & Alerts
# -----------------------------------------------------------------------------

AlertType = Literal["Rain", "Heat", "Frost", "Drought", "Pest", "Task", "Price"]


class FertilizerItem(BaseModel):
    """Individual fertilizer recommendation."""
    fertilizer: str
    kg_per_acre: float
    kg_for_farm: float
    estimated_cost: float


class FertilizerAdviceRequest(BaseModel):
    """Payload for POST /farms/{farm_id}/fertilizer-advice."""
    crop_id: int = Field(..., description="Crop to calculate fertilizer dosage for")
    test_id: Optional[int] = Field(None, description="Soil test ID (defaults to latest)")


class FertilizerAdviceResponse(BaseModel):
    """Response containing fertilizer requirements or sufficiency confirmation."""
    message: str
    note: Optional[str] = "Amounts are indicative and should be checked against local agriculture department guidance."
    farm_id: int
    crop_id: int
    test_id: int
    fertilizers: List[FertilizerItem]


class RotationAdviceItem(BaseModel):
    """Individual crop recommendation within crop rotation advice."""
    crop_id: int
    crop_name: str
    season: str
    is_in_season: bool
    duration_days: int
    reason: Optional[str] = None


class RotationAdviceResponse(BaseModel):
    """Response for GET /farms/{farm_id}/rotation-advice."""
    message: str
    farm_id: int
    advice: List[RotationAdviceItem]


class CropCalendarItem(BaseModel):
    """Stage timeline item from crop_calendar_view."""
    cycle_id: int
    farm_id: int
    crop_id: int
    crop_name: str
    stage_id: int
    stage_name: str
    start_day: int
    end_day: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    stage_status: Literal["Done", "Current", "Upcoming"]
    task: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    """Alert record response."""
    alert_id: int
    farm_id: int
    farm_name: Optional[str] = None
    alert_type: AlertType
    message: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class UnreadAlertCountResponse(BaseModel):
    """Count of unread alerts."""
    unread_count: int


# -----------------------------------------------------------------------------
# Phase 5: Profit Analytics & Market Prices Schemas
# -----------------------------------------------------------------------------

class CropProfitEstimateResponse(BaseModel):
    """Profit analysis for a single crop on a farm."""
    crop_id: int
    crop_name: str
    farm_id: int
    farm_area_acres: float
    duration_days: int
    price_district: Optional[str] = None
    price_per_quintal: Optional[float] = None
    price_date: Optional[date] = None
    avg_yield_q_per_acre: Optional[float] = None
    est_cost_per_acre: Optional[float] = None
    econ_source: Optional[str] = None
    econ_year: Optional[int] = None
    revenue_per_acre: Optional[float] = None
    profit_per_acre: Optional[float] = None
    profit_per_acre_per_month: Optional[float] = None
    profit_for_farm: Optional[float] = None
    message: Optional[str] = None


class RecommendationProfitItem(BaseModel):
    """Profit estimation item for a recommended crop."""
    prediction_id: Optional[int] = None
    rank_no: int
    suitability_score: float
    crop_id: int
    crop_name: str
    price_district: Optional[str] = None
    price_per_quintal: Optional[float] = None
    price_date: Optional[date] = None
    avg_yield_q_per_acre: Optional[float] = None
    est_cost_per_acre: Optional[float] = None
    econ_source: Optional[str] = None
    econ_year: Optional[int] = None
    revenue_per_acre: Optional[float] = None
    profit_per_acre: Optional[float] = None
    profit_per_acre_per_month: Optional[float] = None
    profit_for_farm: Optional[float] = None


class RecommendationProfitResponse(BaseModel):
    """Response for GET /farms/{farm_id}/profit-estimates."""
    farm_id: int
    message: str
    estimates: List[RecommendationProfitItem]


class MarketPriceItem(BaseModel):
    """Market price item from latest_prices_view."""
    price_id: Optional[int] = None
    crop_id: int
    crop_name: Optional[str] = None
    district: str
    price_per_quintal: float
    price_date: date


class MarketPriceCreateRequest(BaseModel):
    """Payload for creating / upserting market price."""
    crop_id: int
    district: str
    price_per_quintal: float = Field(..., gt=0, description="Mandi rate per quintal (must be > 0)")
    price_date: date


class MarketPriceHistoryPoint(BaseModel):
    """Historical market price trend record."""
    price_id: int
    crop_id: int
    crop_name: Optional[str] = None
    district: str
    price_per_quintal: float
    price_date: date


class CycleExpenseCategorySummary(BaseModel):
    """Category breakdown from cycle_expense_summary_view."""
    category: str
    category_total: float
    pct_of_cycle: Optional[float] = None


class FarmerCategoryExpenseSummary(BaseModel):
    """Overall farmer expense breakdown by category."""
    category: str
    total_amount: float


# -----------------------------------------------------------------------------
# Phase 5: Admin CRUD & Audit Log Schemas
# -----------------------------------------------------------------------------

class CropDetailResponse(BaseModel):
    """Full crop record including agronomic requirements, yield and cost."""
    crop_id: int
    crop_name: str
    season: Literal["Kharif", "Rabi", "Zaid", "Annual"]
    duration_days: int
    min_ph: Optional[float] = None
    max_ph: Optional[float] = None
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    min_rainfall: Optional[float] = None
    max_rainfall: Optional[float] = None
    n_required: Optional[int] = None
    p_required: Optional[int] = None
    k_required: Optional[int] = None
    avg_yield_q_per_acre: Optional[float] = None
    est_cost_per_acre: Optional[float] = None
    econ_source: Optional[str] = None
    econ_year: Optional[int] = None


class CropCreateUpdateRequest(BaseModel):
    """Admin payload to create or update a crop."""
    crop_name: str = Field(..., min_length=2, max_length=60)
    season: Literal["Kharif", "Rabi", "Zaid", "Annual"]
    duration_days: int = Field(..., gt=0)
    min_ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    max_ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    min_humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    min_rainfall: Optional[float] = Field(None, ge=0.0)
    max_rainfall: Optional[float] = Field(None, ge=0.0)
    n_required: Optional[int] = Field(None, ge=0)
    p_required: Optional[int] = Field(None, ge=0)
    k_required: Optional[int] = Field(None, ge=0)
    avg_yield_q_per_acre: Optional[float] = Field(None, ge=0.0)
    est_cost_per_acre: Optional[float] = Field(None, ge=0.0)
    econ_source: Optional[str] = Field(None, max_length=120)
    econ_year: Optional[int] = Field(None, ge=1990, le=2100)

    @model_validator(mode="after")
    def validate_ranges(self) -> "CropCreateUpdateRequest":
        if self.min_ph is not None and self.max_ph is not None and self.min_ph > self.max_ph:
            raise ValueError("min_ph cannot be greater than max_ph")
        if self.min_temp is not None and self.max_temp is not None and self.min_temp > self.max_temp:
            raise ValueError("min_temp cannot be greater than max_temp")
        if self.min_humidity is not None and self.max_humidity is not None and self.min_humidity > self.max_humidity:
            raise ValueError("min_humidity cannot be greater than max_humidity")
        if self.min_rainfall is not None and self.max_rainfall is not None and self.min_rainfall > self.max_rainfall:
            raise ValueError("min_rainfall cannot be greater than max_rainfall")
        return self


class DataQualityCropItem(BaseModel):
    """Crop summary for data quality assessment."""
    crop_id: int
    crop_name: str
    season: Optional[str] = None
    avg_yield_q_per_acre: Optional[float] = None
    est_cost_per_acre: Optional[float] = None
    econ_source: Optional[str] = None
    econ_year: Optional[int] = None
    has_price_data: bool = False


class DataQualityResponse(BaseModel):
    """Admin data quality report listing gaps in economic and price data."""
    missing_econ_source: List[DataQualityCropItem]
    missing_price_data: List[DataQualityCropItem]
    total_crops: int


class CropStageCreateUpdateRequest(BaseModel):
    """Admin payload to create or update a crop growth stage."""
    crop_id: int
    stage_name: str = Field(..., min_length=2, max_length=60)
    start_day: int = Field(..., ge=0)
    end_day: int = Field(..., ge=0)
    task: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def validate_days(self) -> "CropStageCreateUpdateRequest":
        if self.start_day > self.end_day:
            raise ValueError("end_day must be greater than or equal to start_day")
        return self


class CropStageDetailResponse(BaseModel):
    """Growth stage detail."""
    stage_id: int
    crop_id: int
    crop_name: Optional[str] = None
    stage_name: str
    start_day: int
    end_day: int
    task: Optional[str] = None


class FertilizerDetailResponse(BaseModel):
    """Fertilizer detail."""
    fert_id: int
    name: str
    n_pct: float
    p_pct: float
    k_pct: float
    price_per_kg: Optional[float] = None


class FertilizerCreateUpdateRequest(BaseModel):
    """Admin payload to create or update a fertilizer."""
    name: str = Field(..., min_length=2, max_length=60)
    n_pct: float = Field(0.0, ge=0.0, le=100.0)
    p_pct: float = Field(0.0, ge=0.0, le=100.0)
    k_pct: float = Field(0.0, ge=0.0, le=100.0)
    price_per_kg: Optional[float] = Field(None, ge=0.0)


class RotationRuleDetailResponse(BaseModel):
    """Rotation rule detail."""
    rule_id: int
    previous_crop_id: int
    previous_crop_name: Optional[str] = None
    recommended_crop_id: int
    recommended_crop_name: Optional[str] = None
    reason: Optional[str] = None


class RotationRuleCreateUpdateRequest(BaseModel):
    """Admin payload for crop rotation rules."""
    previous_crop_id: int
    recommended_crop_id: int
    reason: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def validate_crops(self) -> "RotationRuleCreateUpdateRequest":
        if self.previous_crop_id == self.recommended_crop_id:
            raise ValueError("previous_crop_id and recommended_crop_id cannot be identical")
        return self


class TranslationItem(BaseModel):
    """Translation entry."""
    text_key: str
    lang: LanguageType
    text: str


class TranslationCreateUpdateRequest(BaseModel):
    """Admin payload for translations."""
    text_key: str = Field(..., min_length=1, max_length=80)
    lang: LanguageType
    text: str = Field(..., min_length=1, max_length=255)


class UserActiveUpdateRequest(BaseModel):
    """Admin payload to activate/deactivate user."""
    is_active: bool


class AuditLogItem(BaseModel):
    """Audit log entry from admin_audit_log."""
    log_id: int
    table_name: str
    record_id: int
    action: str
    old_data: Optional[Union[dict, str]] = None
    new_data: Optional[Union[dict, str]] = None
    changed_by: str
    changed_at: datetime


class CsvUploadResponse(BaseModel):
    """Bulk market prices upload response."""
    total_rows: int
    imported: int
    errors: List[dict]




