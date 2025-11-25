# train_model.py
# This script trains our statring prediction model.

import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib # for saving the model

# We are using a small, sample dataset to build the first version
# of our model. This simulates real-world data patterns.
# 'congestion_risk' is our target (1 = Yes, 0 = No)
sample_training_data = {
    'static_hazard_score': [8, 2, 5, 7, 1, 9, 3, 6], # manual road score (0-10)
    'active_reports':      [3, 0, 1, 2, 0, 4, 1, 2], # num of live reports
    'is_raining':          [1, 0, 1, 0, 0, 1, 1, 0], # 1 = Yes, 0 = No
    'hour_of_day':         [17, 10, 16, 8, 11, 18, 9, 14], # 5pm, 10am, etc.
    'congestion_risk':     [1, 0, 1, 0, 0, 1, 1, 0] # Did it get congested?
}

print("Loading sample training data...")
df = pd.DataFrame(sample_training_data)

# Define our features (X) and the target (y)
features = ['static_hazard_score', 'active_reports', 'is_raining', 'hour_of_day']
target = 'congestion_risk'

X = df[features]
y = df[target]

# Create the XGBoost model
model = XGBClassifier(
    use_label_encoder=False, 
    eval_metric='logloss',
    n_estimators=50, # small and fast
    random_state=42
)

# Train the model
print("Training the initial congestion model...")
model.fit(X, y)

# Save the trained model to a .pkl file
# This is the file our backend will load.
model_filename = 'congestion_model.pkl'
joblib.dump(model, model_filename)

print(f"Success! Model was trained and saved as '{model_filename}'")