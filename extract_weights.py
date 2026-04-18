"""Extract ensemble weights for WFS formula"""
import pickle, numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
from src.feature_engineering import create_features_for_modeling

df = pd.read_csv(r'raw data/election_analysis_dataset.csv')
X, y, feat_names, _ = create_features_for_modeling(df, 'won')

with open('models/logistic_regression_model.pkl', 'rb') as f:
    lr = pickle.load(f)
with open('models/xgboost_model.pkl', 'rb') as f:
    xgb_m = pickle.load(f)
with open('models/lightgbm_model.pkl', 'rb') as f:
    lgb_m = pickle.load(f)

lr_abs  = np.abs(lr.coef_[0])
lr_norm  = lr_abs / lr_abs.sum()
xgb_norm = xgb_m.feature_importances_ / xgb_m.feature_importances_.sum()
lgb_norm = lgb_m.feature_importances_ / lgb_m.feature_importances_.sum()
ensemble = (lr_norm + xgb_norm + lgb_norm) / 3

combined = pd.DataFrame({
    'Feature': feat_names,
    'LR_weight': lr_norm,
    'XGB_weight': xgb_norm,
    'LGB_weight': lgb_norm,
    'Ensemble_weight': ensemble,
    'LR_coef': lr.coef_[0]
}).sort_values('Ensemble_weight', ascending=False)

print('ENSEMBLE WEIGHTS (top 15):')
print(combined.head(15).to_string(index=False))

print('\nINTERCEPT:', lr.intercept_[0])

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)
probs = lr.predict_proba(lr.scaler.transform(X_te))[:, 1]
print(f'LR AUC on test: {roc_auc_score(y_te, probs):.4f}')

combined.to_csv('models/ensemble_weights.csv', index=False)
print('Saved to models/ensemble_weights.csv')
