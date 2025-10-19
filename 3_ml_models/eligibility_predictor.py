# 3_ml_models/eligibility_predictor.py
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import numpy as np
import joblib
import json

class EligibilityPredictor:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'logistic_regression': LogisticRegression(random_state=42),
            'xgboost': XGBClassifier(random_state=42)
        }
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.selected_model = None
        self.feature_importance = {}
    
    def prepare_features(self, application_data: Dict) -> np.ndarray:
        """Prepare features from application data for ML model"""
        features = []
        
        # Numerical features
        numerical_features = [
            application_data.get('monthly_income', 0),
            application_data.get('family_size', 1),
            application_data.get('dependents', 0),
            application_data.get('monthly_rent', 0),
            application_data.get('total_assets', 0),
            application_data.get('total_liabilities', 0),
            application_data.get('credit_score', 500)
        ]
        
        # Categorical features encoding
        categorical_features = [
            self.encode_categorical('employment_status', application_data.get('employment_status', 'Unknown')),
            self.encode_categorical('housing_type', application_data.get('housing_type', 'Unknown')),
            self.encode_categorical('education_level', application_data.get('education_level', 'Unknown')),
            self.encode_categorical('marital_status', application_data.get('marital_status', 'Unknown'))
        ]
        
        # Derived features
        derived_features = [
            application_data.get('monthly_income', 0) / max(application_data.get('family_size', 1), 1),  # Income per capita
            application_data.get('total_liabilities', 0) / max(application_data.get('monthly_income', 1), 1),  # Debt-to-income ratio
            1 if application_data.get('employment_status') == 'Unemployed' else 0,  # Unemployment flag
            1 if application_data.get('housing_type') == 'Rented' else 0  # Renting flag
        ]
        
        features = numerical_features + categorical_features + derived_features
        return np.array(features).reshape(1, -1)
    
    def encode_categorical(self, feature_name: str, value: str) -> int:
        """Encode categorical features"""
        if feature_name not in self.label_encoders:
            self.label_encoders[feature_name] = LabelEncoder()
            # Pre-fit with possible values (in real scenario, fit on training data)
            possible_values = {
                'employment_status': ['Employed', 'Unemployed', 'Self-Employed', 'Student', 'Retired'],
                'housing_type': ['Rented', 'Owned', 'Living with Family', 'Government Housing'],
                'education_level': ['No Formal', 'Primary', 'Secondary', 'Diploma', 'Bachelor', 'Master', 'PhD'],
                'marital_status': ['Single', 'Married', 'Divorced', 'Widowed']
            }
            self.label_encoders[feature_name].fit(possible_values.get(feature_name, []))
        
        try:
            return self.label_encoders[feature_name].transform([value])[0]
        except:
            return 0  # Default encoding for unknown values
    
    def train_models(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train multiple models and select the best one"""
        best_score = 0
        best_model_name = None
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        for name, model in self.models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_train_scaled)
            score = accuracy_score(y_train, y_pred)
            
            if score > best_score:
                best_score = score
                best_model_name = name
                self.selected_model = model
            
            print(f"{name} - Training Accuracy: {score:.4f}")
        
        # Store feature importance for the best model
        if hasattr(self.selected_model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                range(len(self.selected_model.feature_importances_)),
                self.selected_model.feature_importances_
            ))
        
        return best_model_name, best_score
    
    def predict_eligibility(self, application_data: Dict) -> Dict:
        """Predict eligibility for a single application"""
        if self.selected_model is None:
            raise ValueError("No model trained yet. Please train the model first.")
        
        features = self.prepare_features(application_data)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.selected_model.predict(features_scaled)[0]
        probability = self.selected_model.predict_proba(features_scaled)[0]
        
        return {
            'eligible': bool(prediction),
            'confidence': float(max(probability)),
            'probabilities': {
                'eligible': float(probability[1]),
                'not_eligible': float(probability[0])
            },
            'feature_importance': self.feature_importance
        }
    
    def generate_synthetic_training_data(self, num_samples: int = 1000) -> tuple:
        """Generate synthetic training data for prototype"""
        np.random.seed(42)
        
        X = []
        y = []
        
        for i in range(num_samples):
            # Generate realistic synthetic data
            monthly_income = np.random.exponential(2000)
            family_size = np.random.randint(1, 8)
            dependents = max(0, family_size - 2)
            monthly_rent = np.random.exponential(1000) if np.random.random() > 0.5 else 0
            total_assets = np.random.exponential(50000)
            total_liabilities = np.random.exponential(20000)
            credit_score = np.random.normal(650, 100)
            
            # Eligibility criteria (business rules)
            income_per_capita = monthly_income / family_size
            debt_to_income = total_liabilities / max(monthly_income, 1)
            
            # Simple eligibility rule for synthetic data
            is_eligible = (
                income_per_capita < 1500 and  # Low income per capita
                debt_to_income < 5 and       # Reasonable debt load
                credit_score > 500 and       # Minimum credit score
                family_size >= 1             # At least one family member
            )
            
            features = [
                monthly_income, family_size, dependents, monthly_rent,
                total_assets, total_liabilities, credit_score,
                np.random.choice([0, 1, 2, 3]),  # employment_status
                np.random.choice([0, 1, 2, 3]),  # housing_type
                np.random.choice([0, 1, 2, 3, 4, 5, 6]),  # education_level
                np.random.choice([0, 1, 2, 3]),  # marital_status
                income_per_capita,
                debt_to_income,
                1 if monthly_income < 1000 else 0,  # low income flag
                1 if monthly_rent > 0 else 0        # renting flag
            ]
            
            X.append(features)
            y.append(1 if is_eligible else 0)
        
        return np.array(X), np.array(y)

# Example usage
if __name__ == "__main__":
    predictor = EligibilityPredictor()
    
    # Generate and train on synthetic data
    X, y = predictor.generate_synthetic_training_data(1000)
    best_model, score = predictor.train_models(X, y)
    
    print(f"Best model: {best_model} with accuracy: {score:.4f}")
    
    # Save the trained model
    joblib.dump(predictor, 'models/eligibility_predictor.joblib')