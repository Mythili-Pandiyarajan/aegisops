"""
AegisOps Priority Model Wrapper

Loads the trained ITSM XGBoost priority prediction model
and exposes it as an agent tool.

Important:
The original model was trained on resolved ITSM tickets.
For new incidents, resolution-time fields are unavailable,
so neutral defaults are used.
"""

import pickle
from pathlib import Path
from typing import Tuple


##############################################################
# Model paths
##############################################################

MODEL_DIR = (
    Path(__file__).resolve()
    .parent.parent
    / "models"
)

PRIORITY_MODEL_PATH = (
    MODEL_DIR / "itsm_priority_model.pkl"
)

SCALER_PATH = (
    MODEL_DIR / "itsm_scaler.pkl"
)



##############################################################
# Training feature order
##############################################################

FEATURE_COLS = [

    "CI_Cat",
    "CI_Subcat",
    "Category",
    "Closure_Code",

    "No_of_Reassignments",
    "No_of_Related_Interactions",

    "Handle_Time_hrs",

    "CI_Name_freq",

    "Open_Hour",
    "Open_DayOfWeek",
    "Open_Month",
    "Open_Year",

    "Is_Weekend",
    "Is_BusinessHour",

]



##############################################################
# Label values from training data
##############################################################

CI_CAT_OPTIONS = [

    "application",
    "computer",
    "database",
    "displaydevice",
    "hardware",
    "networkcomponents",
    "officeelectronics",
    "software",
    "storage",
    "subapplication",

]


CATEGORY_OPTIONS = [

    "complaint",
    "incident",
    "request for change",
    "request for information",

]



CI_SUBCAT_OPTIONS = [

    "DataCenterEquipment",
    "Desktop Application",
    "Laptop",
    "SAN",
    "Server Based Application",
    "System Software",
    "Web Based Application",

]



CLOSURE_OPTIONS = [

    "Data",
    "Hardware",
    "Inquiry",
    "No error - works as designed",
    "Operator error",
    "Other",
    "Questions",
    "Referred",
    "Software",
    "Unknown",
    "User error",
    "User manual not used",

]



##############################################################
# Default mappings
##############################################################

CI_SUBCAT_DEFAULTS = {


    "application":
        "Server Based Application",


    "subapplication":
        "Web Based Application",


    "computer":
        "Laptop",


    "storage":
        "SAN",


    "hardware":
        "DataCenterEquipment",


    "software":
        "System Software",


    "database":
        "Database",


    "displaydevice":
        "Desktop Application",


    "officeelectronics":
        "Printer",


    "networkcomponents":
        "Network Component",

}



##############################################################
# Priority labels
##############################################################

PRIORITY_LABELS = {

    2: "P2",
    3: "P3",
    4: "P4",
    5: "P5",

}



##############################################################
# Lazy loaded objects
##############################################################

_priority_model = None
_scaler = None




##############################################################
# Load model
##############################################################

def _load_models():

    global _priority_model
    global _scaler


    if (
        _priority_model is None
        or _scaler is None
    ):


        if not PRIORITY_MODEL_PATH.exists():

            raise FileNotFoundError(
                f"Missing model: {PRIORITY_MODEL_PATH}"
            )


        if not SCALER_PATH.exists():

            raise FileNotFoundError(
                f"Missing scaler: {SCALER_PATH}"
            )


        with open(
            PRIORITY_MODEL_PATH,
            "rb"
        ) as f:

            _priority_model = pickle.load(f)



        with open(
            SCALER_PATH,
            "rb"
        ) as f:

            _scaler = pickle.load(f)



    return (
        _priority_model,
        _scaler
    )




##############################################################
# Encode categorical values
##############################################################

def _encode_label(
        value,
        options
):


    if value is None:

        return 0



    value = str(
        value
    ).strip().lower()



    normalized = [

        str(x).strip().lower()

        for x in options

    ]



    try:

        return normalized.index(
            value
        )


    except ValueError:

        return 0





##############################################################
# Build features
##############################################################

def build_feature_vector(

        ci_cat="software",

        ci_subcat=None,

        category="incident",

        reassignments=0,

        interactions=1,

        ci_freq=50,

        open_hour=12,

        open_dow=0,

        open_month=1,

        open_year=2026,

        closure="Other",

        handle_time_hrs=0.0,

):



    if ci_subcat is None:

        ci_subcat = CI_SUBCAT_DEFAULTS.get(

            ci_cat,

            "Web Based Application"

        )



    return [

        _encode_label(
            ci_cat,
            CI_CAT_OPTIONS
        ),


        _encode_label(
            ci_subcat,
            CI_SUBCAT_OPTIONS
        ),


        _encode_label(
            category,
            CATEGORY_OPTIONS
        ),


        _encode_label(
            closure,
            CLOSURE_OPTIONS
        ),


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





##############################################################
# Predict Priority
##############################################################

def predict_priority(
        feature_kwargs: dict
) -> Tuple[str, float]:




    model, scaler = _load_models()



    row = build_feature_vector(
        **feature_kwargs
    )



    print("\n==============================")
    print("PRIORITY MODEL")
    print("==============================")

    print(
        "FEATURE VECTOR:",
        row
    )



    X_scaled = scaler.transform(
        [row]
    )



    raw_prediction = int(

        model.predict(
            X_scaled
        )[0]

    )



    print(
        "RAW MODEL OUTPUT:",
        raw_prediction
    )



    ##########################################################
    # Safe priority decoding
    ##########################################################

    if raw_prediction in PRIORITY_LABELS:

        priority_id = raw_prediction


    else:

        # fallback for encoded labels
        priority_id = raw_prediction + 2



    priority_id = max(

        2,

        min(

            5,

            priority_id

        )

    )



    priority = PRIORITY_LABELS.get(

        priority_id,

        "P5"

    )



    ##########################################################
    # Confidence
    ##########################################################

    confidence = 0.0



    if hasattr(
        model,
        "predict_proba"
    ):


        probabilities = model.predict_proba(

            X_scaled

        )[0]



        confidence = float(

            max(probabilities)

        )



    print(
        "FINAL PRIORITY:",
        priority
    )


    print(
        "CONFIDENCE:",
        confidence
    )



    return (

        priority,

        confidence

    )
