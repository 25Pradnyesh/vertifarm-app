from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
import math

@dataclass
class MetricThresholdConfig:
    metric: str
    name: str
    unit: str
    physical_min: float
    physical_max: float
    optimal_min: float
    optimal_max: float
    warning_min: float
    warning_max: float
    hysteresis: float
    rec_low: str
    rec_high: str
    rec_normal: str

SENSOR_THRESHOLDS: Dict[str, MetricThresholdConfig] = {
    "temperature": MetricThresholdConfig(
        metric="temperature",
        name="Temperature",
        unit="°C",
        physical_min=-40.0,
        physical_max=100.0,
        optimal_min=20.0,
        optimal_max=30.0,
        warning_min=15.0,
        warning_max=35.0,
        hysteresis=0.5,
        rec_low="Temperature is below optimal. Check thermal curtains and activate supplemental heating.",
        rec_high="Temperature is elevated. Check ventilation systems, increase airflow, or activate cooling equipment.",
        rec_normal="Temperature is within optimal range for healthy canopy growth.",
    ),
    "humidity": MetricThresholdConfig(
        metric="humidity",
        name="Humidity",
        unit="%",
        physical_min=0.0,
        physical_max=100.0,
        optimal_min=60.0,
        optimal_max=80.0,
        warning_min=40.0,
        warning_max=90.0,
        hysteresis=1.0,
        rec_low="Humidity is too low. Activate greenhouse misting/humidifiers to avoid excessive crop transpiration.",
        rec_high="Humidity is elevated. Increase ventilation and exhaust fans to prevent fungal disease development.",
        rec_normal="Relative humidity is well balanced for transpiration and nutrient uptake.",
    ),
    "soilMoisture": MetricThresholdConfig(
        metric="soilMoisture",
        name="Soil Moisture",
        unit="%",
        physical_min=0.0,
        physical_max=100.0,
        optimal_min=40.0,
        optimal_max=60.0,
        warning_min=30.0,
        warning_max=75.0,
        hysteresis=1.0,
        rec_low="Irrigation is recommended to maintain optimal soil moisture for healthy plant growth.",
        rec_high="Soil moisture is oversaturated. Suspend irrigation cycle to prevent root rot and hypoxia.",
        rec_normal="Substrate moisture level is optimal for root zone respiration.",
    ),
    "ph": MetricThresholdConfig(
        metric="ph",
        name="Soil pH",
        unit="pH",
        physical_min=0.0,
        physical_max=14.0,
        optimal_min=6.0,
        optimal_max=7.0,
        warning_min=5.5,
        warning_max=7.5,
        hysteresis=0.1,
        rec_low="pH is acidic. Introduce pH-up or alkaline buffering to prevent micronutrient lockout.",
        rec_high="pH is slightly high. Add organic matter or pH down solution to lower the pH level.",
        rec_normal="Substrate pH provides optimal nutrient availability.",
    ),
    "tds": MetricThresholdConfig(
        metric="tds",
        name="TDS",
        unit="ppm",
        physical_min=0.0,
        physical_max=5000.0,
        optimal_min=500.0,
        optimal_max=800.0,
        warning_min=400.0,
        warning_max=1000.0,
        hysteresis=10.0,
        rec_low="Nutrient concentration is depleted. Replenish standard A+B nutrient reservoir dosage.",
        rec_high="Nutrient concentration is high. Dilute irrigation reservoir with clean fresh water.",
        rec_normal="TDS is in good range. Maintain current nutrient concentration.",
    ),
    "light": MetricThresholdConfig(
        metric="light",
        name="Light Intensity",
        unit="Lux",
        physical_min=0.0,
        physical_max=150000.0,
        optimal_min=1000.0,
        optimal_max=2000.0,
        warning_min=500.0,
        warning_max=3000.0,
        hysteresis=50.0,
        rec_low="Light intensity is insufficient for optimal photosynthesis. Activate supplemental grow lights.",
        rec_high="Light intensity too high. Deploy shade screens or reduce artificial lighting to prevent leaf scorch.",
        rec_normal="Photosynthetic photon flux is within target range.",
    ),
}

@dataclass
class ThresholdEvaluationResult:
    is_valid: bool
    status: str # "healthy" | "warning" | "critical" | "offline"
    severity: str # "critical" | "warning" | "info"
    status_label: str
    is_violation: bool
    violation_direction: Optional[str] # "low" | "high" | None
    title: str
    notification_body: str
    current_value_formatted: str
    threshold_value_formatted: str
    recommendation: str

def format_metric_value(metric: str, value: float) -> str:
    if metric == "ph":
        return f"{value:.2f}"
    if metric in ("tds", "light"):
        return f"{int(round(value)):,}"
    return f"{value:.1f}"

def evaluate_reading_threshold(
    metric: str,
    value: Any,
    active_violation_direction: Optional[str] = None
) -> ThresholdEvaluationResult:
    """
    Evaluates sensor reading against configured agronomic thresholds.
    Validates physical boundaries and non-finite numbers.
    Applies hysteresis margin when recovering from an active violation.
    """
    cfg = SENSOR_THRESHOLDS.get(metric)
    if not cfg:
        return ThresholdEvaluationResult(
            is_valid=False,
            status="offline",
            severity="info",
            status_label="Unknown Metric",
            is_violation=False,
            violation_direction=None,
            title="Unknown Metric",
            notification_body="",
            current_value_formatted=str(value),
            threshold_value_formatted="--",
            recommendation="",
        )

    # 1. Validate None / missing
    if value is None:
        return ThresholdEvaluationResult(
            is_valid=False,
            status="offline",
            severity="info",
            status_label="No Data",
            is_violation=False,
            violation_direction=None,
            title="Sensor Unavailable",
            notification_body="",
            current_value_formatted="--",
            threshold_value_formatted=f"{cfg.optimal_min}–{cfg.optimal_max} {cfg.unit}",
            recommendation="Verify sensor wiring and controller telemetry.",
        )

    # 2. Validate numeric and finite
    try:
        num = float(value)
    except (ValueError, TypeError):
        return ThresholdEvaluationResult(
            is_valid=False,
            status="offline",
            severity="info",
            status_label="Malformed",
            is_violation=False,
            violation_direction=None,
            title="Malformed Reading",
            notification_body="",
            current_value_formatted=str(value),
            threshold_value_formatted=f"{cfg.optimal_min}–{cfg.optimal_max} {cfg.unit}",
            recommendation="Check edge telemetry format.",
        )

    if not math.isfinite(num):
        return ThresholdEvaluationResult(
            is_valid=False,
            status="offline",
            severity="info",
            status_label="Non-finite",
            is_violation=False,
            violation_direction=None,
            title="Non-finite Reading",
            notification_body="",
            current_value_formatted="NaN",
            threshold_value_formatted=f"{cfg.optimal_min}–{cfg.optimal_max} {cfg.unit}",
            recommendation="Check sensor ADC reading.",
        )

    # 3. Validate physical bounds
    if not (cfg.physical_min <= num <= cfg.physical_max):
        return ThresholdEvaluationResult(
            is_valid=False,
            status="offline",
            severity="info",
            status_label="Out of Bounds",
            is_violation=False,
            violation_direction=None,
            title="Sensor Out of Bounds",
            notification_body="",
            current_value_formatted=f"{num} {cfg.unit}",
            threshold_value_formatted=f"[{cfg.physical_min}, {cfg.physical_max}] {cfg.unit}",
            recommendation="Reading exceeds physical hardware range.",
        )

    opt_min_str = format_metric_value(metric, cfg.optimal_min)
    opt_max_str = format_metric_value(metric, cfg.optimal_max)
    formatted_val = f"{format_metric_value(metric, num)} {cfg.unit}"

    # 4. Hysteresis check for active violation recovery
    if active_violation_direction == "high":
        recovery_limit = cfg.optimal_max - cfg.hysteresis
        if num > recovery_limit:
            is_crit = num > cfg.warning_max
            sev = "critical" if is_crit else "warning"
            return ThresholdEvaluationResult(
                is_valid=True,
                status=sev,
                severity=sev,
                status_label="Critical High" if is_crit else "High",
                is_violation=True,
                violation_direction="high",
                title=f"{cfg.name} is High",
                notification_body=f"High {cfg.name.lower()} detected: {formatted_val} — Normal range: {opt_min_str}–{opt_max_str} {cfg.unit}",
                current_value_formatted=formatted_val,
                threshold_value_formatted=f"> {opt_max_str} {cfg.unit}",
                recommendation=cfg.rec_high,
            )
    elif active_violation_direction == "low":
        recovery_limit = cfg.optimal_min + cfg.hysteresis
        if num < recovery_limit:
            is_crit = num < cfg.warning_min
            sev = "critical" if is_crit else "warning"
            return ThresholdEvaluationResult(
                is_valid=True,
                status=sev,
                severity=sev,
                status_label="Critical Low" if is_crit else "Low",
                is_violation=True,
                violation_direction="low",
                title=f"{cfg.name} is Low",
                notification_body=f"{cfg.name} too low: {formatted_val} — Minimum: {opt_min_str} {cfg.unit}",
                current_value_formatted=formatted_val,
                threshold_value_formatted=f"< {opt_min_str} {cfg.unit}",
                recommendation=cfg.rec_low,
            )

    # 5. Standard thresholds evaluation
    if num > cfg.warning_max:
        return ThresholdEvaluationResult(
            is_valid=True,
            status="critical",
            severity="critical",
            status_label="Critical High",
            is_violation=True,
            violation_direction="high",
            title=f"{cfg.name} is Critical",
            notification_body=f"{cfg.name} critical: {formatted_val} — Maximum: {opt_max_str} {cfg.unit}",
            current_value_formatted=formatted_val,
            threshold_value_formatted=f"> {opt_max_str} {cfg.unit}",
            recommendation=cfg.rec_high,
        )

    if num < cfg.warning_min:
        return ThresholdEvaluationResult(
            is_valid=True,
            status="critical",
            severity="critical",
            status_label="Critical Low",
            is_violation=True,
            violation_direction="low",
            title=f"{cfg.name} is Critical",
            notification_body=f"{cfg.name} critical: {formatted_val} — Minimum: {opt_min_str} {cfg.unit}",
            current_value_formatted=formatted_val,
            threshold_value_formatted=f"< {opt_min_str} {cfg.unit}",
            recommendation=cfg.rec_low,
        )

    if num > cfg.optimal_max:
        return ThresholdEvaluationResult(
            is_valid=True,
            status="warning",
            severity="warning",
            status_label="High",
            is_violation=True,
            violation_direction="high",
            title=f"{cfg.name} is High",
            notification_body=f"High {cfg.name.lower()} detected: {formatted_val} — Normal range: {opt_min_str}–{opt_max_str} {cfg.unit}",
            current_value_formatted=formatted_val,
            threshold_value_formatted=f"> {opt_max_str} {cfg.unit}",
            recommendation=cfg.rec_high,
        )

    if num < cfg.optimal_min:
        return ThresholdEvaluationResult(
            is_valid=True,
            status="warning",
            severity="warning",
            status_label="Low",
            is_violation=True,
            violation_direction="low",
            title=f"{cfg.name} is Low",
            notification_body=f"{cfg.name} too low: {formatted_val} — Minimum: {opt_min_str} {cfg.unit}",
            current_value_formatted=formatted_val,
            threshold_value_formatted=f"< {opt_min_str} {cfg.unit}",
            recommendation=cfg.rec_low,
        )

    # Healthy
    status_label = "Slightly Acidic" if (metric == "ph" and num < 6.8) else ("Optimal" if metric == "light" else "Normal")
    return ThresholdEvaluationResult(
        is_valid=True,
        status="healthy",
        severity="info",
        status_label=status_label,
        is_violation=False,
        violation_direction=None,
        title=f"{cfg.name} Normal",
        notification_body="",
        current_value_formatted=formatted_val,
        threshold_value_formatted=f"{opt_min_str}–{opt_max_str} {cfg.unit}",
        recommendation=cfg.rec_normal,
    )
