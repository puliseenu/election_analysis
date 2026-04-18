"""
ML Analysis Module for Election Victory Prediction
Trains 3-model ensemble and extracts feature importance via multiple methods
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, roc_curve, f1_score, precision_recall_curve,
    classification_report, confusion_matrix
)
from sklearn.inspection import permutation_importance

import xgboost as xgb
import lightgbm as lgb
import shap


class ElectionVictoryPredictor:
    """
    Trains ensemble of ML models for election victory prediction
    and extracts feature importance via multiple methods
    """
    
    def __init__(self, X_train, y_train, X_test=None, y_test=None, random_state=42):
        """
        Initialize predictor with training data
        
        Args:
            X_train: Feature matrix for training
            y_train: Target vector for training
            X_test: Feature matrix for testing (optional)
            y_test: Target vector for testing (optional)
            random_state: Random seed for reproducibility
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.random_state = random_state
        
        # Models will be stored here
        self.models = {}
        self.feature_importance_dict = {}
        self.model_performance = {}
        
        # Handle class imbalance
        self.class_weight = self._calculate_class_weight()
        
    def _calculate_class_weight(self):
        """Calculate appropriate class weight for imbalanced data"""
        n_samples = len(self.y_train)
        n_positive = self.y_train.sum()
        n_negative = n_samples - n_positive
        
        # scale_pos_weight for XGBoost: inverse ratio of negative to positive
        scale_pos_weight = n_negative / (n_positive + 1)
        
        print(f"Class Distribution: {n_negative} losses, {n_positive} wins")
        print(f"Class Weight (XGBoost scale_pos_weight): {scale_pos_weight:.2f}")
        
        return {'n_positive': n_positive, 'n_negative': n_negative, 
                'scale_pos_weight': scale_pos_weight}
    
    def train_xgboost(self, params=None):
        """Train XGBoost model with class imbalance handling"""
        
        if params is None:
            params = {
                'max_depth': 6,
                'learning_rate': 0.05,
                'n_estimators': 200,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'scale_pos_weight': self.class_weight['scale_pos_weight'],
                'random_state': self.random_state,
                'eval_metric': 'auc',
                'tree_method': 'hist'
            }
        
        print("\n" + "="*60)
        print("Training XGBoost Model...")
        print("="*60)
        
        model = xgb.XGBClassifier(**params)
        
        if self.X_test is not None:
            model.fit(
                self.X_train, self.y_train,
                eval_set=[(self.X_test, self.y_test)],
                verbose=False
            )
        else:
            model.fit(self.X_train, self.y_train, verbose=False)
        
        self.models['xgboost'] = model
        self._evaluate_model(model, 'xgboost')
        
        return model
    
    def train_lightgbm(self, params=None):
        """Train LightGBM model with class imbalance handling"""
        
        if params is None:
            params = {
                'num_leaves': 31,
                'learning_rate': 0.05,
                'n_estimators': 200,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'scale_pos_weight': self.class_weight['scale_pos_weight'],
                'random_state': self.random_state,
                'verbose': -1
            }
        
        print("\n" + "="*60)
        print("Training LightGBM Model...")
        print("="*60)
        
        model = lgb.LGBMClassifier(**params)
        model.fit(self.X_train, self.y_train)
        
        self.models['lightgbm'] = model
        self._evaluate_model(model, 'lightgbm')
        
        return model
    
    def train_logistic_regression(self, params=None):
        """Train Logistic Regression as baseline + interpretability"""
        
        print("\n" + "="*60)
        print("Training Logistic Regression Model...")
        print("="*60)
        
        # Scale features for logistic regression
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(self.X_train)
        
        # Calculate class weights
        n_samples = len(self.y_train)
        n_positive = self.y_train.sum()
        class_weight = {0: n_positive/n_samples, 1: (n_samples-n_positive)/n_samples}
        
        model = LogisticRegression(
            max_iter=1000,
            class_weight=class_weight,
            random_state=self.random_state,
            solver='lbfgs',
            n_jobs=-1
        )
        model.fit(X_train_scaled, self.y_train)
        
        # Store scaler for later use
        model.scaler = scaler
        
        self.models['logistic_regression'] = model
        
        # Manually evaluate (need to scale test data too)
        if self.X_test is not None:
            X_test_scaled = scaler.transform(self.X_test)
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            y_pred = model.predict(X_train_scaled)
            y_proba = model.predict_proba(X_train_scaled)[:, 1]
            self.y_test = self.y_train
        
        self._evaluate_model_manual(y_pred, y_proba, 'logistic_regression')
        
        return model
    
    def _evaluate_model(self, model, model_name):
        """Evaluate model and store performance metrics"""
        
        if self.X_test is not None:
            y_pred = model.predict(self.X_test)
            y_proba = model.predict_proba(self.X_test)[:, 1]
        else:
            y_pred = model.predict(self.X_train)
            y_proba = model.predict_proba(self.X_train)[:, 1]
            self.y_test = self.y_train
        
        self._evaluate_model_manual(y_pred, y_proba, model_name)
    
    def _evaluate_model_manual(self, y_pred, y_proba, model_name):
        """Manually evaluate predictions"""
        
        auc = roc_auc_score(self.y_test, y_proba)
        f1 = f1_score(self.y_test, y_pred)
        
        # ROC curve
        fpr, tpr, thresholds = roc_curve(self.y_test, y_proba)
        
        print(f"\n{model_name.upper()} Performance:")
        print(f"  AUC-ROC:       {auc:.4f}")
        print(f"  F1-Score:      {f1:.4f}")
        print(f"\nClassification Report:")
        print(classification_report(self.y_test, y_pred, 
                                   target_names=['Lost', 'Won']))
        
        self.model_performance[model_name] = {
            'auc': auc,
            'f1': f1,
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'thresholds': thresholds.tolist()
        }
    
    def extract_feature_importance_mdi(self, model_name):
        """Extract Mean Decrease Impurity (MDI) feature importance"""
        
        model = self.models[model_name]
        
        if model_name in ['xgboost', 'lightgbm']:
            # Tree-based models have built-in feature importance
            importance = model.feature_importances_
        else:
            # Logistic regression: use absolute coefficients
            importance = np.abs(model.coef_[0])
        
        # Normalize to sum to 1
        importance_normalized = importance / importance.sum()
        
        return importance_normalized
    
    def extract_feature_importance_shap(self, model_name):
        """Extract SHAP-based feature importance"""
        
        model = self.models[model_name]
        
        print(f"\nCalculating SHAP values for {model_name}...")
        
        try:
            if model_name == 'xgboost':
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(self.X_train)
                
                # Handle multi-class output (use positive class)
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
            
            elif model_name == 'lightgbm':
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(self.X_train)
                
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
            
            else:  # logistic_regression
                explainer = shap.KernelExplainer(
                    model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                    self.X_train.sample(min(100, len(self.X_train)))
                )
                shap_values = explainer.shap_values(self.X_train.sample(min(200, len(self.X_train))))
                
                if isinstance(shap_values, np.ndarray) and len(shap_values.shape) > 2:
                    shap_values = shap_values[:, :, 1]
            
            # Mean absolute SHAP values
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            importance_normalized = mean_abs_shap / mean_abs_shap.sum()
            
            return importance_normalized, shap_values
        
        except Exception as e:
            print(f"SHAP calculation failed for {model_name}: {str(e)}")
            return None, None
    
    def extract_feature_importance_permutation(self, model_name):
        """Extract permutation-based feature importance"""
        
        model = self.models[model_name]
        
        print(f"\nCalculating permutation importance for {model_name}...")
        
        try:
            if model_name == 'logistic_regression':
                # Need to scale test data
                X_test_scaled = model.scaler.transform(self.X_test)
            else:
                X_test_scaled = self.X_test
            
            perm_importance = permutation_importance(
                model, X_test_scaled, self.y_test,
                n_repeats=10, random_state=self.random_state, n_jobs=-1
            )
            
            importance_normalized = perm_importance.importances_mean
            importance_normalized = importance_normalized / importance_normalized.sum()
            
            return importance_normalized
        
        except Exception as e:
            print(f"Permutation importance failed for {model_name}: {str(e)}")
            return None
    
    def compare_feature_importance(self, feature_names):
        """
        Compare feature importance across all three methods
        Returns rankings for each method and consensus ranking
        """
        
        print("\n" + "="*60)
        print("COMPARING FEATURE IMPORTANCE ACROSS MODELS")
        print("="*60)
        
        importance_results = {}
        
        for model_name in self.models.keys():
            importance_results[model_name] = {}
            
            # MDI
            mdi = self.extract_feature_importance_mdi(model_name)
            importance_results[model_name]['mdi'] = mdi
            
            # SHAP
            shap_importance, shap_vals = self.extract_feature_importance_shap(model_name)
            if shap_importance is not None:
                importance_results[model_name]['shap'] = shap_importance
                self.feature_importance_dict[f'{model_name}_shap_values'] = shap_vals
            else:
                importance_results[model_name]['shap'] = mdi  # Fallback
            
            # Permutation (only if test set available)
            if self.X_test is not None:
                perm = self.extract_feature_importance_permutation(model_name)
                if perm is not None:
                    importance_results[model_name]['permutation'] = perm
            
            # Create ranking dataframe
            ranking_df = pd.DataFrame({
                'Feature': feature_names,
                'MDI': importance_results[model_name]['mdi'],
                'SHAP': importance_results[model_name]['shap']
            })
            
            if 'permutation' in importance_results[model_name]:
                ranking_df['Permutation'] = importance_results[model_name]['permutation']
            
            # Compute consensus rank
            ranking_df['MDI_Rank'] = ranking_df['MDI'].rank(ascending=False)
            ranking_df['SHAP_Rank'] = ranking_df['SHAP'].rank(ascending=False)
            if 'Permutation' in ranking_df.columns:
                ranking_df['Permutation_Rank'] = ranking_df['Permutation'].rank(ascending=False)
                ranking_df['Avg_Rank'] = ranking_df[['MDI_Rank', 'SHAP_Rank', 'Permutation_Rank']].mean(axis=1)
            else:
                ranking_df['Avg_Rank'] = ranking_df[['MDI_Rank', 'SHAP_Rank']].mean(axis=1)
            
            ranking_df = ranking_df.sort_values('Avg_Rank')
            
            print(f"\n{model_name.upper()} - Top 15 Features:")
            print(ranking_df.head(15)[['Feature', 'MDI', 'SHAP', 'Avg_Rank']].to_string(index=False))
            
            self.feature_importance_dict[f'{model_name}_ranking'] = ranking_df
        
        # Ensemble consensus ranking
        self._compute_ensemble_ranking(feature_names)
        
        return importance_results
    
    def _compute_ensemble_ranking(self, feature_names):
        """Compute consensus ranking across all models"""
        
        print("\n" + "="*60)
        print("ENSEMBLE CONSENSUS RANKING")
        print("="*60)
        
        consensus_df = pd.DataFrame({'Feature': feature_names})
        
        for model_name in self.models.keys():
            ranking_df = self.feature_importance_dict[f'{model_name}_ranking']
            # Map feature to rank
            feature_to_rank = dict(zip(ranking_df['Feature'], ranking_df['Avg_Rank']))
            consensus_df[f'{model_name}_rank'] = consensus_df['Feature'].map(feature_to_rank)
        
        # Compute ensemble average rank
        rank_cols = [col for col in consensus_df.columns if col.endswith('_rank')]
        consensus_df['Ensemble_Rank'] = consensus_df[rank_cols].mean(axis=1)
        consensus_df = consensus_df.sort_values('Ensemble_Rank')
        
        print("\nTop 15 Features (Ensemble Consensus):")
        print(consensus_df.head(15)[['Feature', 'Ensemble_Rank']].to_string(index=False))
        
        self.feature_importance_dict['ensemble_consensus'] = consensus_df
        
        return consensus_df
    
    def analyze_state_variations(self, df_full, state_col='State', target_col='won'):
        """Analyze feature importance by state"""
        
        print("\n" + "="*60)
        print("STATE-LEVEL FEATURE IMPORTANCE ANALYSIS")
        print("="*60)
        
        state_importance = {}
        
        unique_states = df_full[state_col].unique()
        
        for state in unique_states:
            state_mask = df_full[state_col] == state
            X_state = self.X_train[state_mask]
            y_state = self.y_train[state_mask]
            
            if len(y_state) < 100:  # Skip if too few samples
                continue
            
            print(f"\n{state} ({len(y_state)} candidates):")
            
            # Quick importance via XGBoost trained on state data
            model_state = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                scale_pos_weight=self.class_weight['scale_pos_weight'],
                random_state=self.random_state
            )
            model_state.fit(X_state, y_state)
            
            importance = model_state.feature_importances_
            state_importance[state] = importance
        
        self.feature_importance_dict['state_variations'] = state_importance
        
        return state_importance
    
    def save_models(self, output_dir='models'):
        """Save trained models and artifacts"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for model_name, model in self.models.items():
            filepath = output_path / f'{model_name}_model.pkl'
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            print(f"Saved {model_name} to {filepath}")
        
        # Save performance metrics
        perf_path = output_path / 'model_performance.json'
        with open(perf_path, 'w') as f:
            json.dump(
                {k: {k2: (v2.tolist() if isinstance(v2, np.ndarray) else v2) 
                      for k2, v2 in v.items()}
                 for k, v in self.model_performance.items()},
                f, indent=2
            )
        
        print(f"Saved performance metrics to {perf_path}")
    
    def get_feature_importance_summary(self):
        """Return summary dict for dashboard use"""
        
        summary = {
            'ensemble_consensus': self.feature_importance_dict.get('ensemble_consensus', None),
            'model_rankings': {
                k: v for k, v in self.feature_importance_dict.items()
                if 'ranking' in k
            },
            'model_performance': self.model_performance,
            'state_variations': self.feature_importance_dict.get('state_variations', {})
        }
        
        return summary


def run_full_ml_pipeline(csv_path, target_col='won', test_size=0.1, random_state=42):
    """
    Full ML pipeline from CSV to feature importance
    
    Args:
        csv_path: Path to election data CSV
        target_col: Name of target column
        test_size: Fraction for test set
        random_state: Random seed
        
    Returns:
        predictor: Trained ElectionVictoryPredictor object
        feature_summary: Feature importance summary
    """
    
    from src.feature_engineering import create_features_for_modeling
    
    print("Loading election data...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records with {len(df.columns)} columns")
    
    print("\nEngineering features...")
    X, y, feature_names, feature_descriptions = create_features_for_modeling(df, target_col)
    
    print(f"\nFinal feature matrix: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    # Create stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    
    print(f"\nTrain set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Initialize and train predictor
    predictor = ElectionVictoryPredictor(X_train, y_train, X_test, y_test, random_state)
    
    # Train all models
    predictor.train_xgboost()
    predictor.train_lightgbm()
    predictor.train_logistic_regression()
    
    # Compare feature importance
    importance_results = predictor.compare_feature_importance(feature_names)
    
    # State-level analysis
    predictor.analyze_state_variations(df, state_col='State', target_col=target_col)
    
    # Get summary
    feature_summary = predictor.get_feature_importance_summary()
    
    # Save artifacts
    predictor.save_models('models')
    
    return predictor, feature_summary, feature_names, feature_descriptions


if __name__ == '__main__':
    # Example usage
    csv_path = r'raw data/election_analysis_dataset.csv'
    predictor, summary, features, descriptions = run_full_ml_pipeline(csv_path)
