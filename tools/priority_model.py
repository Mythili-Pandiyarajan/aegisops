"""
Wraps the trained ITSM XGBoost Priority Auto-Tag model (Task 3) + its
StandardScaler as plain functions, for use inside agents/priority_predictor.py.

Confirmed directly against Mythili-Pandiyarajan/ITSM-Incident-ML-Prediction/app.py
so predictions here match what the ITSM Streamlit app produces -- same
FEATURE_COLS order, same index-based categorical encoding, same y_min=2 shift.

IMPORTANT LIMITATION (documented on purpose, not hidden):
The model was trained on structured ticket fields. Four of them --
Closure_Code, Handle_Time_hrs, No_of_Reassignments, No_of_Related_Interactions --
are only known AFTER a ticket is resolved, so they don't exist yet for a
brand-new incident. This wrapper defaults those to neutral placeholders so a
fresh incident still gets a prediction, but accuracy on freshly-created
incidents will be lower than the 0.82 test accuracy reported for the original
(post-resolution) feature set. Say this plainly in the README rather than
implying equivalent performance.
"""

import pickle
from pathlib import Path
from typing import Tuple

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
PRIORITY_MODEL_PATH = MODEL_DIR / "itsm_priority_model.pkl"
SCALER_PATH = MODEL_DIR / "itsm_scaler.pkl"

FEATURE_COLS = [
    'CI_Cat', 'CI_Subcat', 'Category', 'Closure_Code',
    'No_of_Reassignments', 'No_of_Related_Interactions',
    'Handle_Time_hrs', 'CI_Name_freq',
    'Open_Hour', 'Open_DayOfWeek', 'Open_Month', 'Open_Year',
    'Is_Weekend', 'Is_BusinessHour'
]

CI_CAT_OPTIONS = ['Hardware', 'Software', 'Network', 'Database', 'Security', 'Application', 'Infrastructure']
CI_SUBCAT_OPTIONS = ['Web Based Application', 'Desktop App', 'Server', 'Router', 'Switch', 'Storage', 'VM', 'Firewall']
CATEGORY_OPTIONS = ['incident', 'problem', 'change', 'service request']
CLOSURE_OPTIONS = ['Resolved', 'Closed', 'Cancelled', 'Other', 'Duplicate']

PRIORITY_LABELS = {2: 'P2', 3: 'P3', 4: 'P4', 5: 'P5'}

_priority_model = None
_scaler = None


def _load_models():
    global _priority_model, _scaler
    if _priority_model is None or _scaler is None:
        if not PRIORITY_MODEL_PATH.exists() or not SCALER_PATH.exists():
            raise FileNotFoundError(
                f"Expected {PRIORITY_MODEL_PATH.name} and {SCALER_PATH.name} in {MODEL_DIR}."
            )
        with open(PRIORITY_MODEL_PATH, "rb") as f:
            _priority_model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            _scaler = pickle.load(f)
    return _priority_model, _scaler


def _encode_label(val: str, options: list) -> int:
    try:
        return options.index(val)
    except ValueError:
        return 0


def build_feature_vector(
    ci_cat: str = "Software",
    ci_subcat: str = "Web Based Application",
    category: str = "incident",
    reassignments: int = 0,
    interactions: int = 1,
    ci_freq: int = 50,
    open_hour: int = 12,
    open_dow: int = 0,
    open_month: int = 1,
    open_year: int = 2026,
    closure: str = "Other",              # unknown at creation time -- placeholder
    handle_time_hrs: float = 0.0,        # unknown at creation time -- placeholder
) -> list:
    return [
        _encode_label(ci_cat, CI_CAT_OPTIONS),
        _encode_label(ci_subcat, CI_SUBCAT_OPTIONS),
        _encode_label(category, CATEGORY_OPTIONS),
        _encode_label(closure, CLOSURE_OPTIONS),
        reassignments,
        interactions,
        handle_time_hrs,
        ci_freq,
        open_hour,
        open_dow,
        open_month,
        open_year,
        1 if open_dow >= 5 else 0,
        1 if 9 <= open_hour <= 18 else 0,
    ]


def predict_priority(feature_kwargs: dict) -> Tuple[str, float]:
    """
    feature_kwargs: any subset of build_feature_vector's keyword args.
    Returns (priority_label like "P3", confidence 0-1).
    """
    model, scaler = _load_models()

    row = build_feature_vector(**feature_kwargs)
    X_scaled = scaler.transform([row])

    y_min = 2
    raw_pred = int(model.predict(X_scaled)[0])
    priority = max(2, min(5, raw_pred + y_min))

    confidence = 0.0
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_scaled)[0]
        confidence = float(max(proba))

    return PRIORITY_LABELS.get(priority, f"P{priority}"), confidence
