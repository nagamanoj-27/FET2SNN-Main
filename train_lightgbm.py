import io
import pickle
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------
# 1. HARDCODED MULTI-PAPER DATASET
# ---------------------------------------------------------
csv_data = """Paper,Spacer_Config,I_ON_mA,I_OFF_pA,SS_mV_dec,DIBL_mV_V,V_TH_V,Temp_C,Energy_spike_fJ,Latency_ms,Accuracy_Percent
Lakshmana_2026,Si3N4+HfO2,0.163,9.991,66.738,29.23,0.347,25,0.82,12.5,93.0
Lakshmana_2026,SiO2+HfO2,0.158,8.705,66.293,26.153,0.347,25,0.79,13.2,92.5
Lakshmana_2026,HfO2_single,0.169,13.235,68.414,33.384,0.344,25,0.95,10.8,91.2
Lakshmana_2026,Si3N4_single,0.117,9.810,71.884,34.461,0.359,25,0.68,18.5,87.3
Lakshmana_2026,SiO2_single,0.093,9.106,71.159,33.846,0.371,25,0.55,22.1,84.6
Lakshmana_2026,Vacuum_single,0.064,7.608,74.678,26.153,0.395,25,0.45,28.3,78.2
Lakshmana_2026,HfO2+Si3N4,0.118,13.891,70.123,38.461,0.352,25,0.72,17.2,88.5
Lakshmana_2026,SiO2+Si3N4,0.115,9.112,68.362,30.769,0.359,25,0.70,16.8,89.1
Lakshmana_2026,HfO2+SiO2,0.097,13.500,71.863,36.923,0.356,25,0.60,20.5,85.9
Lakshmana_2026,Si3N4+SiO2,0.095,10.582,70.066,35.384,0.363,25,0.58,21.0,86.2
Neurocomputing_2026,GAA_FNSFET,0.024,0.001,65.0,28.0,0.380,25,4.88,8.2,94.0
PhysicaScripta_2025,GAA_NSFET,0.018,0.0005,63.5,26.5,0.390,25,0.80,7.5,96.1
SolidStateElectronics_2025,GAA_NSFET,0.022,0.0008,64.2,27.1,0.385,25,2.10,9.0,93.5
SolidStateElectronics_2025,GAA_NSFET,0.022,0.0012,64.5,27.3,0.383,125,2.87,6.2,91.8
ArXiv_2025,QUEST_SNN,0.030,0.002,60.0,25.0,0.400,25,15.0,5.0,89.6
ArXiv_2025,Edge_SNN,0.028,0.0015,61.0,26.0,0.395,25,12.0,4.5,88.2
IEEE_Access_2024,AxonHillock,0.010,0.0002,70.0,30.0,0.410,25,0.000156,0.1,85.0"""

# Read into pandas DataFrame
df = pd.read_csv(io.StringIO(csv_data))

print("=== Raw Dataset ===")
print(df.info())
print(f"Dataset shape: {df.shape}\n")

# ---------------------------------------------------------
# 2. FEATURE ENGINEERING & PREPROCESSING
# ---------------------------------------------------------
# Features and Targets selection
feature_cols = ['Spacer_Config', 'I_ON_mA', 'I_OFF_pA', 'SS_mV_dec', 'DIBL_mV_V', 'V_TH_V', 'Temp_C']
target_cols = ['Energy_spike_fJ', 'Latency_ms', 'Accuracy_Percent']

X = df[feature_cols].copy()
y = df[target_cols].copy()

# Label encode the categorical variable 'Spacer_Config'
# To make it robust, we save the encoder for future prediction pipelines
encoder = LabelEncoder()
X['Spacer_Config_encoded'] = encoder.fit_transform(X['Spacer_Config'])

# Drop the raw text column for model training
X_train = X.drop(columns=['Spacer_Config'])

# ---------------------------------------------------------
# 3. ROBUST EVALUATION: K-FOLD CROSS-VALIDATION
# ---------------------------------------------------------
# Given the small sample size (N=17), we use 3-Fold Cross-Validation.
# LightGBM requires custom hyperparameters to train on tiny datasets without underfitting/failing leaf counts.
kf = KFold(n_splits=3, shuffle=True, random_state=42)

# Specific hyperparameters tailored for micro-datasets:
# - min_child_samples: 1 or 2 is critical to allow splitting on small row counts.
# - num_leaves: low (7 or 15) to prevent extreme overfitting.
# - learning_rate: moderate (0.05) to ensure steady convergence.
lgb_params = {
    'objective': 'regression',
    'metric': 'mae',
    'min_child_samples': 2,
    'num_leaves': 7,
    'learning_rate': 0.05,
    'n_estimators': 80,
    'boosting_type': 'gbdt',
    'verbosity': -1,
    'random_state': 42
}

cv_results = {}

print("=== Running 3-Fold Cross-Validation ===")
for target in target_cols:
    y_target = y[target]
    r2_scores = []
    mae_scores = []
    
    for train_idx, val_idx in kf.split(X_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_target.iloc[train_idx], y_target.iloc[val_idx]
        
        # Instantiate and fit Regressor
        model = lgb.LGBMRegressor(**lgb_params)
        model.fit(X_tr, y_tr)
        
        preds = model.predict(X_val)
        
        r2_scores.append(r2_score(y_val, preds))
        mae_scores.append(mean_absolute_error(y_val, preds))
        
    avg_r2 = np.mean(r2_scores)
    avg_mae = np.mean(mae_scores)
    
    cv_results[target] = {'R2': avg_r2, 'MAE': avg_mae}
    print(f"Target: {target:<18} | Mean R²: {avg_r2:8.4f} | Mean MAE: {avg_mae:8.4f}")

print("\nCross-Validation finished.\n")

# ---------------------------------------------------------
# 4. FINAL PIPELINE TRAINING ON COMPLETED DATASET
# ---------------------------------------------------------
print("=== Training Final Models on Complete Dataset ===")
final_models = {}

for target in target_cols:
    y_target = y[target]
    model = lgb.LGBMRegressor(**lgb_params)
    model.fit(X_train, y_target)
    final_models[target] = model
    
    # Quick sanity check on train metrics
    train_preds = model.predict(X_train)
    train_r2 = r2_score(y_target, train_preds)
    train_mae = mean_absolute_error(y_target, train_preds)
    print(f"Model [{target:<18}] -> Train R²: {train_r2:.4f} | Train MAE: {train_mae:.4f}")

# ---------------------------------------------------------
# 5. SERIALIZE MODELS AND ENCODERS
# ---------------------------------------------------------
# We wrap models and the label encoder in a single metadata dict to guarantee pipeline consistency.
pipeline_bundle = {
    'models': final_models,
    'label_encoder': encoder,
    'features': X_train.columns.tolist()
}

model_filename = "lgb_nanosheet_snn_pipeline.pkl"
with open(model_filename, 'wb') as f:
    pickle.dump(pipeline_bundle, f)

print(f"\nSuccessfully serialized the final pipeline bundle to '{model_filename}'!\n")

# ---------------------------------------------------------
# 6. INFERENCE SIMULATOR PIPELINE
# ---------------------------------------------------------
def predict_snn_performance(spacer_config, i_on, i_off, ss, dibl, v_th, temp):
    """
    Inference function utilizing the saved pipeline bundle.
    Handles categorical encoding safely and runs multi-target predictions.
    """
    # Load pipeline
    with open(model_filename, 'rb') as f:
        bundle = pickle.load(f)
        
    models = bundle['models']
    le = bundle['label_encoder']
    
    # Categorical encoding handling
    try:
        encoded_spacer = le.transform([spacer_config])[0]
    except ValueError:
        # Fallback for unseen configurations
        print(f"Warning: Spacer configuration '{spacer_config}' unseen in training data. Defaulting to mode encoding.")
        encoded_spacer = le.transform([le.classes_[0]])[0]
        
    # Prepare input DataFrame with matched feature headers
    input_data = pd.DataFrame([{
        'I_ON_mA': i_on,
        'I_OFF_pA': i_off,
        'SS_mV_dec': ss,
        'DIBL_mV_V': dibl,
        'V_TH_V': v_th,
        'Temp_C': temp,
        'Spacer_Config_encoded': encoded_spacer
    }])
    
    # Ensure correct feature alignment
    input_data = input_data[bundle['features']]
    
    predictions = {}
    for target, model in models.items():
        predictions[target] = model.predict(input_data)[0]
        
    return predictions

# ---------------------------------------------------------
# 7. INFERENCE TEST RUN
# ---------------------------------------------------------
print("=== Running Sample Target Inference ===")
# Example inputs representing a high-performance Dual-k config
sample_prediction = predict_snn_performance(
    spacer_config="SiO2+HfO2",
    i_on=0.150,
    i_off=8.0,
    ss=65.5,
    dibl=27.0,
    v_th=0.350,
    temp=25
)

for target, val in sample_prediction.items():
    print(f"Predicted SNN {target:<18}: {val:.4f}")
