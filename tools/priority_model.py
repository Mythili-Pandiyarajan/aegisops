"""
Wraps the trained ITSM XGBoost Priority Auto-Tag model (Task 3) + its
StandardScaler as plain functions, for use inside agents/priority_predictor.py.

FIXED FOR REAL (see itsm_incident_ml.ipynb, cell 45): the four categorical
option lists below are now the ACTUAL LabelEncoder.classes_ values from
training -- i.e. df[col].fillna('Unknown').astype(str), sorted -- verified
directly against itsm_data.csv, not guessed or reconstructed from a UI
mockup. The previous version of this file (see priority_model_original.py)
had lists like ['Application','Database','Hardware',...] for CI_Cat and
['change','incident','problem','service request'] for Category -- neither
of which occurs anywhere in the real training data. Because LabelEncoder
was fit directly on the messy raw column values (lowercase category names
like 'application'/'subapplication', ticket types like 'request for
information', Closure_Code values like 'No error - works as designed'),
every one of those four features was almost certainly being silently
encoded as a near-constant value for every prediction. This file replaces
those lists with the verified real classes.

IMPORTANT LIMITATION (documented on purpose, not hidden):
The model was trained on structured ticket fields. Four of them --
Closure_Code, Handle_Time_hrs, No_of_Reassignments, No_of_Related_Interactions --
are only known AFTER a ticket is resolved, so they don't exist yet for a
brand-new incident. This wrapper defaults those to neutral placeholders so a
fresh incident still gets a prediction, but accuracy on freshly-created
incidents will be lower than the 0.82 test accuracy reported for the original
(post-resolution) feature set. Say this plainly in the README rather than
implying equivalent performance.

NOTE: Priority class 1 was dropped during training (only 3 samples in the
whole 46k-row dataset -- not enough to model reliably). The trained model
can only ever output P2-P5; there is no P1 in PRIORITY_LABELS on purpose.

NOTE: CI_Subcat is collected via a CI_Cat -> most-common-subcat default
mapping in the Streamlit app (CI_SUBCAT_DEFAULTS), rather than a single
global constant, since it's the #2 most important feature (~16.6%) and a
single hardcoded constant biased every prediction toward whatever category
that placeholder subcat is most associated with in training data.
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

# Verified against itsm_data.csv: sorted(df[col].fillna('Unknown').astype(str).unique())
# This is exactly what sklearn's LabelEncoder.fit() produces as .classes_ --
# do not reorder or hand-edit these; regenerate from the CSV if the training
# data ever changes.
CI_CAT_OPTIONS = [
    'Phone', 'Unknown', 'application', 'applicationcomponent', 'computer',
    'database', 'displaydevice', 'hardware', 'networkcomponents',
    'officeelectronics', 'software', 'storage', 'subapplication',
]

CI_SUBCAT_OPTIONS = [
    'Application Server', 'Automation Software', 'Banking Device', 'Citrix',
    'Client Based Application', 'Controller', 'DataCenterEquipment', 'Database',
    'Database Software', 'Desktop', 'Desktop Application', 'ESX Cluster',
    'ESX Server', 'Encryption', 'Exchange', 'Firewall', 'IPtelephony',
    'Instance', 'Iptelephony', 'KVM Switches', 'Keyboard', 'Laptop', 'Lines',
    'Linux Server', 'MQ Queue Manager', 'MigratieDummy', 'Modem', 'Monitor',
    'Neoview Server', 'Net Device', 'Network Component', 'NonStop Harddisk',
    'NonStop Server', 'NonStop Storage', 'Number', 'Omgeving', 'Oracle Server',
    'Printer', 'Protocol', 'RAC Service', 'Router', 'SAN', 'SAP', 'Scanner',
    'Security Software', 'Server Based Application', 'SharePoint Farm',
    'Standard Application', 'Switch', 'System Software', 'Tape Library',
    'Thin Client', 'UPS', 'Unix Server', 'Unknown', 'VDI', 'VMWare',
    'Virtual Tape Server', 'Web Based Application', 'Windows Server',
    'Windows Server in extern beheer', 'X86 Server', 'zOS Cluster',
    'zOS Server', 'zOS Systeem',
]

CATEGORY_OPTIONS = ['complaint', 'incident', 'request for change', 'request for information']

CLOSURE_OPTIONS = [
    'Data', 'Hardware', 'Inquiry', 'Kwaliteit van de output',
    'No error - works as designed', 'Operator error', 'Other', 'Overig',
    'Questions', 'Referred', 'Software', 'Unknown', 'User error',
    'User manual not used',
]

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
    """
    Look up val's training-time encoded index. Falls back to the index of
    'Unknown' (a real class the encoder was trained on, from filled NaNs)
    rather than a hardcoded 0 -- 0 is just whatever happens to sort first
    alphabetically for that column, which is not a meaningful default.
    """
    try:
        return options.index(val)
    except ValueError:
        return options.index("Unknown") if "Unknown" in options else 0


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
