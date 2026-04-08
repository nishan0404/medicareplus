import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

print("🤖 Training MediCare+ AI Symptom Checker Model...")

# Load dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, 'Training.csv'))

print(f"✅ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# Remove unnamed columns
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Separate features and target
X = df.drop('prognosis', axis=1)
y = df['prognosis']

# Save symptom columns for later use
symptom_columns = list(X.columns)
print(f"✅ Symptoms found: {len(symptom_columns)}")
print(f"✅ Diseases found: {len(y.unique())}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Random Forest model
print("⏳ Training Random Forest classifier...")
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    max_depth=10
)
model.fit(X_train, y_train)

# Test accuracy
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"✅ Model accuracy: {accuracy * 100:.2f}%")

# Save model and symptom columns
model_path = os.path.join(BASE_DIR, 'symptom_model.pkl')
columns_path = os.path.join(BASE_DIR, 'symptom_columns.pkl')

joblib.dump(model, model_path)
joblib.dump(symptom_columns, columns_path)

print(f"✅ Model saved to: {model_path}")
print(f"✅ Columns saved to: {columns_path}")
print("🎉 AI Model training complete!")