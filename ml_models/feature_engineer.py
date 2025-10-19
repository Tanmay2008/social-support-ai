# 3_ml_models/feature_engineer.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering for social support eligibility prediction"""
    
    def __init__(self):
        self.feature_config = self._load_feature_config()
        self.derived_features = []
    
    def _load_feature_config(self) -> Dict:
        """Load feature engineering configuration"""
        return {
            'numerical_features': [
                'monthly_income', 'family_size', 'dependents', 'monthly_rent',
                'total_assets', 'total_liabilities', 'credit_score'
            ],
            'categorical_features': [
                'employment_status', 'housing_type', 'education_level', 'marital_status'
            ],
            'derived_features': [
                'income_per_capita', 'debt_to_income_ratio', 'asset_to_income_ratio',
                'is_unemployed', 'is_renting', 'has_dependents', 'large_family',
                'low_income', 'high_debt_burden', 'credit_score_category'
            ],
            'interaction_features': [
                'unemployed_low_income', 'renting_high_debt', 'large_family_low_income'
            ]
        }
    
    def engineer_features(self, application_data: Dict) -> Dict:
        """Engineer comprehensive features from application data"""
        try:
            features = {}
            
            # 1. Basic numerical features
            features.update(self._extract_numerical_features(application_data))
            
            # 2. Categorical features (already encoded by predictor)
            features.update(self._extract_categorical_features(application_data))
            
            # 3. Derived features
            features.update(self._create_derived_features(application_data, features))
            
            # 4. Interaction features
            features.update(self._create_interaction_features(features))
            
            # 5. Temporal features (if available)
            features.update(self._create_temporal_features(application_data))
            
            # 6. Risk assessment features
            features.update(self._create_risk_features(application_data, features))
            
            self.derived_features = list(features.keys())
            
            return features
            
        except Exception as e:
            logger.error(f"Feature engineering error: {str(e)}")
            return {}
    
    def _extract_numerical_features(self, application_data: Dict) -> Dict:
        """Extract and validate numerical features"""
        numerical_features = {}
        
        for feature in self.feature_config['numerical_features']:
            value = application_data.get(feature, 0)
            
            # Validate and clean numerical values
            if isinstance(value, (int, float)):
                numerical_features[feature] = max(0, float(value))
            else:
                numerical_features[feature] = 0.0
        
        return numerical_features
    
    def _extract_categorical_features(self, application_data: Dict) -> Dict:
        """Extract categorical features"""
        categorical_features = {}
        
        for feature in self.feature_config['categorical_features']:
            value = application_data.get(feature, 'Unknown')
            categorical_features[feature] = str(value)
        
        return categorical_features
    
    def _create_derived_features(self, application_data: Dict, base_features: Dict) -> Dict:
        """Create derived features from base features"""
        derived = {}
        
        # Income per capita
        monthly_income = base_features.get('monthly_income', 0)
        family_size = max(base_features.get('family_size', 1), 1)
        derived['income_per_capita'] = monthly_income / family_size
        
        # Debt-to-income ratio
        total_liabilities = base_features.get('total_liabilities', 0)
        derived['debt_to_income_ratio'] = total_liabilities / max(monthly_income, 1)
        
        # Asset-to-income ratio
        total_assets = base_features.get('total_assets', 0)
        derived['asset_to_income_ratio'] = total_assets / max(monthly_income, 1)
        
        # Binary flags
        derived['is_unemployed'] = 1 if application_data.get('employment_status') == 'Unemployed' else 0
        derived['is_renting'] = 1 if application_data.get('housing_type') == 'Rented' else 0
        derived['has_dependents'] = 1 if base_features.get('dependents', 0) > 0 else 0
        derived['large_family'] = 1 if family_size >= 4 else 0
        
        # Income categories
        derived['low_income'] = 1 if derived['income_per_capita'] < 2000 else 0
        derived['very_low_income'] = 1 if derived['income_per_capita'] < 1000 else 0
        
        # Debt burden
        derived['high_debt_burden'] = 1 if derived['debt_to_income_ratio'] > 0.5 else 0
        derived['very_high_debt_burden'] = 1 if derived['debt_to_income_ratio'] > 1.0 else 0
        
        # Credit score categories
        credit_score = base_features.get('credit_score', 500)
        if credit_score >= 750:
            derived['credit_score_category'] = 'excellent'
        elif credit_score >= 700:
            derived['credit_score_category'] = 'good'
        elif credit_score >= 650:
            derived['credit_score_category'] = 'fair'
        elif credit_score >= 600:
            derived['credit_score_category'] = 'poor'
        else:
            derived['credit_score_category'] = 'very_poor'
        
        return derived
    
    def _create_interaction_features(self, features: Dict) -> Dict:
        """Create interaction features between different feature types"""
        interaction = {}
        
        # Unemployment + Low income
        interaction['unemployed_low_income'] = (
            features.get('is_unemployed', 0) * features.get('low_income', 0)
        )
        
        # Renting + High debt burden
        interaction['renting_high_debt'] = (
            features.get('is_renting', 0) * features.get('high_debt_burden', 0)
        )
        
        # Large family + Low income
        interaction['large_family_low_income'] = (
            features.get('large_family', 0) * features.get('low_income', 0)
        )
        
        # Single parent (simplified)
        interaction['single_parent'] = (
            1 if (features.get('marital_status') in ['Single', 'Divorced', 'Widowed'] and 
                  features.get('has_dependents', 0) == 1) else 0
        )
        
        return interaction
    
    def _create_temporal_features(self, application_data: Dict) -> Dict:
        """Create temporal features if date information is available"""
        temporal = {}
        
        # Current date for reference
        current_date = datetime.now()
        
        # If application date is provided
        app_date_str = application_data.get('application_date')
        if app_date_str:
            try:
                app_date = datetime.fromisoformat(app_date_str.replace('Z', '+00:00'))
                days_since_application = (current_date - app_date).days
                temporal['days_since_application'] = days_since_application
                temporal['recent_application'] = 1 if days_since_application <= 30 else 0
            except:
                temporal['days_since_application'] = 0
                temporal['recent_application'] = 0
        
        # Seasonal features
        temporal['month'] = current_date.month
        temporal['quarter'] = (current_date.month - 1) // 3 + 1
        temporal['is_year_end'] = 1 if current_date.month in [11, 12] else 0
        
        return temporal
    
    def _create_risk_features(self, application_data: Dict, features: Dict) -> Dict:
        """Create risk assessment features"""
        risk = {}
        
        # Financial risk score (0-1, higher = more risk)
        financial_risk = 0.0
        
        # Income risk
        income_per_capita = features.get('income_per_capita', 0)
        if income_per_capita < 1000:
            financial_risk += 0.4
        elif income_per_capita < 2000:
            financial_risk += 0.2
        
        # Employment risk
        if features.get('is_unemployed', 0) == 1:
            financial_risk += 0.3
        
        # Debt risk
        debt_ratio = features.get('debt_to_income_ratio', 0)
        if debt_ratio > 1.0:
            financial_risk += 0.2
        elif debt_ratio > 0.5:
            financial_risk += 0.1
        
        # Family risk
        if features.get('large_family', 0) == 1 and features.get('low_income', 0) == 1:
            financial_risk += 0.1
        
        risk['financial_risk_score'] = min(financial_risk, 1.0)
        risk['high_risk_applicant'] = 1 if financial_risk > 0.6 else 0
        risk['medium_risk_applicant'] = 1 if 0.3 < financial_risk <= 0.6 else 0
        risk['low_risk_applicant'] = 1 if financial_risk <= 0.3 else 0
        
        return risk
    
    def get_feature_summary(self, features: Dict) -> Dict:
        """Generate summary statistics for features"""
        summary = {
            'total_features': len(features),
            'feature_categories': {},
            'statistics': {}
        }
        
        # Categorize features
        for feature, value in features.items():
            feature_type = self._categorize_feature(feature, value)
            if feature_type not in summary['feature_categories']:
                summary['feature_categories'][feature_type] = []
            summary['feature_categories'][feature_type].append(feature)
        
        # Basic statistics for numerical features
        numerical_features = summary['feature_categories'].get('numerical', [])
        if numerical_features:
            numerical_values = [features[feat] for feat in numerical_features 
                              if isinstance(features[feat], (int, float))]
            
            summary['statistics']['numerical'] = {
                'count': len(numerical_values),
                'mean': np.mean(numerical_values) if numerical_values else 0,
                'std': np.std(numerical_values) if numerical_values else 0,
                'min': min(numerical_values) if numerical_values else 0,
                'max': max(numerical_values) if numerical_values else 0
            }
        
        return summary
    
    def _categorize_feature(self, feature_name: str, value: Any) -> str:
        """Categorize feature based on name and value"""
        if isinstance(value, (int, float)):
            return 'numerical'
        elif isinstance(value, str):
            return 'categorical'
        elif isinstance(value, (bool, np.bool_)):
            return 'binary'
        else:
            return 'other'
    
    def validate_features(self, features: Dict) -> Tuple[bool, List[str]]:
        """Validate engineered features for quality and completeness"""
        issues = []
        
        # Check for missing critical features
        critical_features = ['monthly_income', 'family_size', 'employment_status']
        for feature in critical_features:
            if feature not in features or features[feature] is None:
                issues.append(f"Missing critical feature: {feature}")
        
        # Check for unrealistic values
        if features.get('monthly_income', 0) < 0:
            issues.append("Negative monthly income")
        
        if features.get('family_size', 0) <= 0:
            issues.append("Invalid family size")
        
        if features.get('credit_score', 0) < 300 or features.get('credit_score', 0) > 850:
            issues.append("Credit score out of valid range")
        
        # Check derived features
        debt_ratio = features.get('debt_to_income_ratio', 0)
        if debt_ratio > 10:  # Unusually high debt ratio
            issues.append("Extremely high debt-to-income ratio")
        
        income_per_capita = features.get('income_per_capita', 0)
        if income_per_capita > 50000:  # Unusually high income
            issues.append("Extremely high income per capita")
        
        return len(issues) == 0, issues
    
    def export_feature_importance(self, model, feature_names: List[str]) -> Dict:
        """Export feature importance from trained model"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance_scores = model.feature_importances_
                
                # Create feature importance dictionary
                importance_dict = dict(zip(feature_names, importance_scores))
                
                # Sort by importance
                sorted_importance = dict(sorted(
                    importance_dict.items(),
                    key=lambda x: x[1],
                    reverse=True
                ))
                
                return {
                    'feature_importance': sorted_importance,
                    'top_features': list(sorted_importance.keys())[:10],
                    'importance_summary': {
                        'total_features': len(feature_names),
                        'max_importance': max(importance_scores) if importance_scores else 0,
                        'min_importance': min(importance_scores) if importance_scores else 0,
                        'mean_importance': np.mean(importance_scores) if importance_scores else 0
                    }
                }
            else:
                return {'error': 'Model does not support feature importance'}
                
        except Exception as e:
            logger.error(f"Feature importance export error: {str(e)}")
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    # Test feature engineering
    engineer = FeatureEngineer()
    
    test_applicant = {
        'monthly_income': 2500,
        'family_size': 4,
        'dependents': 2,
        'monthly_rent': 1200,
        'total_assets': 30000,
        'total_liabilities': 15000,
        'credit_score': 680,
        'employment_status': 'Employed',
        'housing_type': 'Rented',
        'education_level': 'Secondary',
        'marital_status': 'Married',
        'application_date': '2024-01-15'
    }
    
    features = engineer.engineer_features(test_applicant)
    print("Engineered Features:")
    for feature, value in features.items():
        print(f"  {feature}: {value}")
    
    summary = engineer.get_feature_summary(features)
    print(f"\nFeature Summary: {summary}")
    
    is_valid, issues = engineer.validate_features(features)
    print(f"Features valid: {is_valid}")
    if issues:
        print(f"Issues: {issues}")