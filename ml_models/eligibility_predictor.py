# 3_ml_models/eligibility_predictor.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import json
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EligibilityPredictor:
    """Machine Learning model for predicting social support eligibility"""
    
    def __init__(self, model_type: str = 'random_forest'):
        self.model_type = model_type
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=6),
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'xgboost': XGBClassifier(random_state=42, max_depth=6, n_estimators=100),
            'svm': SVC(random_state=42, probability=True)
        }
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.selected_model = None
        self.model_metadata = {}
        self.is_trained = False
    
    def prepare_features(self, application_data: Dict) -> np.ndarray:
        """Prepare features from application data for ML model"""
        try:
            features = []
            
            # 1. Numerical features
            numerical_features = [
                application_data.get('monthly_income', 0),
                application_data.get('family_size', 1),
                application_data.get('dependents', 0),
                application_data.get('monthly_rent', 0),
                application_data.get('total_assets', 0),
                application_data.get('total_liabilities', 0),
                application_data.get('credit_score', 500)
            ]
            
            # 2. Categorical features encoding
            categorical_features = [
                self._encode_categorical('employment_status', 
                                       application_data.get('employment_status', 'Unknown')),
                self._encode_categorical('housing_type', 
                                       application_data.get('housing_type', 'Unknown')),
                self._encode_categorical('education_level', 
                                       application_data.get('education_level', 'Unknown')),
                self._encode_categorical('marital_status', 
                                       application_data.get('marital_status', 'Unknown'))
            ]
            
            # 3. Derived features
            family_size = max(application_data.get('family_size', 1), 1)
            monthly_income = max(application_data.get('monthly_income', 0), 0)
            total_liabilities = max(application_data.get('total_liabilities', 0), 0)
            
            derived_features = [
                monthly_income / family_size,  # Income per capita
                total_liabilities / max(monthly_income, 1),  # Debt-to-income ratio
                1 if application_data.get('employment_status') == 'Unemployed' else 0,
                1 if application_data.get('housing_type') == 'Rented' else 0,
                1 if application_data.get('family_size', 0) >= 4 else 0,  # Large family
                1 if application_data.get('dependents', 0) >= 2 else 0,   # Multiple dependents
                min(application_data.get('credit_score', 500) / 850, 1.0)  # Normalized credit score
            ]
            
            # Combine all features
            features = numerical_features + categorical_features + derived_features
            self.feature_names = self._get_feature_names()
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Feature preparation error: {str(e)}")
            # Return zero features as fallback
            return np.zeros((1, 20))
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for model interpretation"""
        numerical_names = [
            'monthly_income', 'family_size', 'dependents', 'monthly_rent',
            'total_assets', 'total_liabilities', 'credit_score'
        ]
        
        categorical_names = [
            'employment_status', 'housing_type', 'education_level', 'marital_status'
        ]
        
        derived_names = [
            'income_per_capita', 'debt_to_income_ratio', 'is_unemployed',
            'is_renting', 'large_family', 'multiple_dependents', 'credit_score_normalized'
        ]
        
        return numerical_names + categorical_names + derived_names
    
    def _encode_categorical(self, feature_name: str, value: str) -> int:
        """Encode categorical features consistently"""
        if feature_name not in self.label_encoders:
            # Initialize with possible values
            possible_values = {
                'employment_status': ['Employed', 'Unemployed', 'Self-Employed', 'Student', 'Retired', 'Unknown'],
                'housing_type': ['Rented', 'Owned', 'Living with Family', 'Government Housing', 'Unknown'],
                'education_level': ['No Formal Education', 'Primary', 'Secondary', 'Diploma', 
                                  'Bachelor', 'Master', 'PhD', 'Unknown'],
                'marital_status': ['Single', 'Married', 'Divorced', 'Widowed', 'Unknown']
            }
            self.label_encoders[feature_name] = LabelEncoder()
            self.label_encoders[feature_name].fit(possible_values.get(feature_name, []))
        
        try:
            return self.label_encoders[feature_name].transform([value])[0]
        except ValueError:
            # Handle unknown categories
            return 0  # Default to first category
    
    def train_models(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict:
        """Train multiple models and select the best performing one"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            best_score = 0
            best_model_name = None
            results = {}
            
            for name, model in self.models.items():
                logger.info(f"Training {name}...")
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
                
                results[name] = {
                    'accuracy': accuracy,
                    'cv_mean': np.mean(cv_scores),
                    'cv_std': np.std(cv_scores),
                    'classification_report': classification_report(y_test, y_pred, output_dict=True),
                    'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
                }
                
                logger.info(f"{name} - Accuracy: {accuracy:.4f}, CV: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
                # Update best model
                if accuracy > best_score:
                    best_score = accuracy
                    best_model_name = name
                    self.selected_model = model
            
            # Store model metadata
            self.model_metadata = {
                'best_model': best_model_name,
                'best_accuracy': best_score,
                'training_date': datetime.now().isoformat(),
                'feature_names': self.feature_names,
                'model_results': results,
                'training_set_size': len(X_train),
                'test_set_size': len(X_test)
            }
            
            self.is_trained = True
            
            logger.info(f"Best model: {best_model_name} with accuracy: {best_score:.4f}")
            return self.model_metadata
            
        except Exception as e:
            logger.error(f"Model training error: {str(e)}")
            raise
    
    def predict_eligibility(self, application_data: Dict) -> Dict:
        """Predict eligibility for a single application"""
        if not self.is_trained or self.selected_model is None:
            raise ValueError("Model not trained yet. Please train the model first.")
        
        try:
            # Prepare features
            features = self.prepare_features(application_data)
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.selected_model.predict(features_scaled)[0]
            probability = self.selected_model.predict_proba(features_scaled)[0]
            
            # Get feature importance if available
            feature_importance = self._get_feature_importance()
            
            return {
                'eligible': bool(prediction),
                'confidence': float(max(probability)),
                'probabilities': {
                    'eligible': float(probability[1]),
                    'not_eligible': float(probability[0])
                },
                'prediction_details': {
                    'model_used': self.model_metadata.get('best_model', 'unknown'),
                    'model_accuracy': self.model_metadata.get('best_accuracy', 0),
                    'feature_importance': feature_importance,
                    'prediction_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                'eligible': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _get_feature_importance(self) -> Dict:
        """Get feature importance from the trained model"""
        if not hasattr(self.selected_model, 'feature_importances_'):
            return {}
        
        try:
            importance_scores = self.selected_model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importance_scores))
            
            # Sort by importance
            sorted_importance = dict(sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            ))
            
            return sorted_importance
            
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {str(e)}")
            return {}
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model performance on test data"""
        if not self.is_trained:
            raise ValueError("Model not trained yet.")
        
        try:
            X_test_scaled = self.scaler.transform(X_test)
            y_pred = self.selected_model.predict(X_test_scaled)
            y_pred_proba = self.selected_model.predict_proba(X_test_scaled)
            
            evaluation = {
                'accuracy': accuracy_score(y_test, y_pred),
                'classification_report': classification_report(y_test, y_pred, output_dict=True),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
                'prediction_distribution': {
                    'eligible': int(sum(y_pred)),
                    'not_eligible': len(y_pred) - int(sum(y_pred))
                },
                'confidence_scores': {
                    'mean': float(np.mean(np.max(y_pred_proba, axis=1))),
                    'std': float(np.std(np.max(y_pred_proba, axis=1))),
                    'min': float(np.min(np.max(y_pred_proba, axis=1))),
                    'max': float(np.max(np.max(y_pred_proba, axis=1)))
                }
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Model evaluation error: {str(e)}")
            raise
    
    def save_model(self, filepath: str):
        """Save trained model and preprocessing objects"""
        if not self.is_trained:
            raise ValueError("No trained model to save.")
        
        try:
            model_data = {
                'model': self.selected_model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'feature_names': self.feature_names,
                'model_metadata': self.model_metadata,
                'model_type': self.model_type
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Model save error: {str(e)}")
            raise
    
    def load_model(self, filepath: str):
        """Load trained model and preprocessing objects"""
        try:
            model_data = joblib.load(filepath)
            
            self.selected_model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            self.model_metadata = model_data['model_metadata']
            self.model_type = model_data['model_type']
            self.is_trained = True
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Model load error: {str(e)}")
            raise
    
    def generate_synthetic_training_data(self, num_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for prototype"""
        np.random.seed(42)
        
        X = []
        y = []
        
        for i in range(num_samples):
            # Generate realistic synthetic applicant data
            applicant_data = self._generate_synthetic_applicant()
            features = self.prepare_features(applicant_data)[0]  # Get 1D array
            
            # Determine eligibility based on business rules
            is_eligible = self._determine_synthetic_eligibility(applicant_data)
            
            X.append(features)
            y.append(1 if is_eligible else 0)
        
        return np.array(X), np.array(y)
    
    def _generate_synthetic_applicant(self) -> Dict:
        """Generate synthetic applicant data"""
        # Realistic distributions for UAE social support context
        employment_options = ['Employed', 'Unemployed', 'Self-Employed', 'Student', 'Retired']
        employment_weights = [0.4, 0.3, 0.15, 0.1, 0.05]
        
        housing_options = ['Rented', 'Owned', 'Living with Family', 'Government Housing']
        housing_weights = [0.5, 0.2, 0.2, 0.1]
        
        education_options = ['No Formal Education', 'Primary', 'Secondary', 'Diploma', 'Bachelor', 'Master', 'PhD']
        education_weights = [0.1, 0.15, 0.3, 0.2, 0.15, 0.08, 0.02]
        
        marital_options = ['Single', 'Married', 'Divorced', 'Widowed']
        marital_weights = [0.3, 0.5, 0.1, 0.1]
        
        applicant = {
            'monthly_income': max(0, np.random.exponential(2000)),
            'family_size': np.random.randint(1, 8),
            'dependents': np.random.randint(0, 6),
            'monthly_rent': np.random.exponential(1000) if np.random.random() > 0.5 else 0,
            'total_assets': np.random.exponential(50000),
            'total_liabilities': np.random.exponential(20000),
            'credit_score': np.random.normal(650, 100),
            'employment_status': np.random.choice(employment_options, p=employment_weights),
            'housing_type': np.random.choice(housing_options, p=housing_weights),
            'education_level': np.random.choice(education_options, p=education_weights),
            'marital_status': np.random.choice(marital_options, p=marital_weights)
        }
        
        # Ensure credit score is within valid range
        applicant['credit_score'] = max(300, min(850, applicant['credit_score']))
        
        return applicant
    
    def _determine_synthetic_eligibility(self, applicant: Dict) -> bool:
        """Determine eligibility based on synthetic business rules"""
        score = 0
        
        # Income factor (40%)
        income_per_capita = applicant['monthly_income'] / max(applicant['family_size'], 1)
        if income_per_capita < 1500:
            score += 0.4
        elif income_per_capita < 3000:
            score += 0.2
        
        # Employment factor (25%)
        if applicant['employment_status'] == 'Unemployed':
            score += 0.25
        elif applicant['employment_status'] in ['Student', 'Retired']:
            score += 0.15
        
        # Family factor (20%)
        if applicant['family_size'] >= 4:
            score += 0.2
        elif applicant['family_size'] >= 2:
            score += 0.1
        
        # Housing factor (15%)
        if applicant['housing_type'] == 'Rented':
            score += 0.15
        elif applicant['housing_type'] == 'Government Housing':
            score += 0.1
        
        # Apply threshold
        return score >= 0.5

# Example usage and testing
if __name__ == "__main__":
    # Initialize predictor
    predictor = EligibilityPredictor(model_type='random_forest')
    
    # Generate and train on synthetic data
    print("Generating synthetic training data...")
    X, y = predictor.generate_synthetic_training_data(2000)
    
    print("Training models...")
    results = predictor.train_models(X, y)
    
    print(f"Best model: {results['best_model']}")
    print(f"Best accuracy: {results['best_accuracy']:.4f}")
    
    # Test prediction
    test_applicant = {
        'monthly_income': 1800,
        'family_size': 4,
        'dependents': 2,
        'monthly_rent': 1200,
        'total_assets': 15000,
        'total_liabilities': 8000,
        'credit_score': 620,
        'employment_status': 'Unemployed',
        'housing_type': 'Rented',
        'education_level': 'Secondary',
        'marital_status': 'Married'
    }
    
    prediction = predictor.predict_eligibility(test_applicant)
    print(f"Prediction: {prediction}")
    
    # Save model
    predictor.save_model('models/eligibility_predictor.joblib')