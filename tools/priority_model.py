"""
Wraps the trained ITSM XGBoost Priority Auto-Tag model (Task 3) + its
StandardScaler as plain functions, for use inside agents/priority_predictor.py.

FIXED: CI_CAT_OPTIONS and CATEGORY_OPTIONS below are the REAL values found
in the training CSV (verified directly against itsm_incident_ml.ipynb's own
dataframe output), listed in the alphabetical order LabelEncoder.fit()
actually produces. Earlier versions of this file used plausible-sounding
but fabricated category names (e.g. "Security", "Infrastructure") that
never appeared in training data at all -- every real incident silently
fell back to index 0 via the except-ValueError branch in _encode_label,
meaning CI_Cat and Category (the model's #1 and #4 most important features,
Category alone ~43% importance) were effectively constant for every
prediction the deployed app ever made.

STILL UNVERIFIED, NEEDS CONFIRMATION: CI_SUBCAT_OPTIONS and CLOSURE_OPTIONS
below are based on partial evidence (visible sample rows + prior analysis),
not an exhaustive value_counts() of the real column. Before trusting this
in production, run in the training notebook / Colab and paste the output:
    df['CI_Subcat'].value_counts()
    df['Closure_Code'].value_counts()
so the lists can be locked in against the complete, real vocabulary rather
than a partial sample.

IMPORTANT LIMITATION (documented on purpose, not hidden):
The model was trained on structured ticket fields. Four of them --
Closure_Code, Handle_Time_hrs, No_of_Reassignments, No_of_Related_Interactions --
are only known AFTER a ticket is resolved, so they don't exist yet for a
brand-new incident. This wrapper defaults those to neutral placeholders so a
fresh incident still gets a prediction, but accuracy on freshly-created
incidents will be lower than the 0.82 test accuracy reported for the original
(post-resolution) feature set -- and Priority 2 recall in particular (0.60
on the full feature set, per the notebook's own classification_report) will
likely be worse with these features neutralized. Say this plainly in the
README rather than implying equivalent performance.

CI_Subcat is also NOT collected by the current intake form even though it's
the #2 most important feature (~16.6%). It's defaulted to a single constant
regardless of the selected CI_Cat -- worth mapping a sensible default subcat
per CI_Cat (see CI_SUBCAT_DEFAULTS below, needs verification per the note
above) or adding a real form field.
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

# Real values confirmed directly against the training notebook's own
# dataframe output. Alphabetical order to match LabelEncoder.fit().
CI_CAT_OPTIONS = [
    'application', 'computer', 'database', 'displaydevice', 'hardware',
    'networkcomponents', 'officeelectronics', 'software', 'storage', 'subapplication',
]
CATEGORY_OPTIONS = ['complaint', 'incident', 'request for change', 'request for information']

# NEEDS VERIFICATION -- see module docstring. Best-available list, not
# confirmed against a full value_counts() of the real column yet.
CI_SUBCAT_OPTIONS = [
    'DataCenterEquipment', 'Desktop Application', 'Laptop', 'SAN',
    'Server Based Application', 'System Software', 'Web Based Application',
]
CLOSURE_OPTIONS = [
    'Data', 'Hardware', 'Inquiry', 'No error - works as designed', 'Operator error',
    'Other', 'Questions', 'Referred', 'Software', 'Unknown', 'User error',
    'User manual not used',
]

# Most-common CI_Subcat per CI_Cat (best-available; re-derive with
# df.groupby(['CI_Cat','CI_Subcat']).size() once the real CSV is at hand,
# and swap this in verified rather than partial).
CI_SUBCAT_DEFAULTS = {
    'application': 'Server Based Application',
    'subapplication': 'Web Based Application',
    'computer': 'Laptop',
    'storage': 'SAN',
    'hardware': 'DataCenterEquipment',
    'software': 'System Software',
    'database': 'Database',
    'displaydevice': 'Monitor',
    'officeelectronics': 'Printer',
    'networkcomponents': 'Network Component',
}

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
    ci_cat: str = "software",
    ci_subcat: str = None,
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
    if ci_subcat is None:
        ci_subcat = CI_SUBCAT_DEFAULTS.get(ci_cat, "Web Based Application")

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
