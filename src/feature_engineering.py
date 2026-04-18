"""
Feature Engineering Module for Election Victory Prediction
Generates 15+ strategic dummy/composite variables optimized for ML models
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


class ElectionFeatureEngineer:
    """
    Transforms raw election data into ML-ready features with strategic interactions
    and composite variables designed from election consultant perspective
    """
    
    def __init__(self, df):
        """Initialize with raw election dataframe"""
        self.df = df.copy()
        self.engineered_df = None
        self.feature_names = []
        self.scaler = StandardScaler()
        
    def handle_missing_values(self):
        """Handle domain-specific missing values (99 encoded as missing)"""
        # Replace 99 with NaN in binary flag columns
        binary_cols = ['Turncoat_', 'Incumbent_', 'Recontest_', 'Same_Constituency_', 
                      'Same_Party_', 'Deposit_Lost_']
        for col in binary_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].replace(99, np.nan)
                # Forward fill with 0 (conservative: assume not true if missing)
                self.df[col] = self.df[col].fillna(0).astype(int)
        
        # For numeric columns, use median/mean imputation
        numeric_cols = ['Criminal Case', 'Age', 'Total Assets', 'Liabilities']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                self.df[col] = self.df[col].fillna(self.df[col].median())
        
        return self
    
    def create_tier1_critical_features(self):
        """TIER 1: Create critical incumbent + financial features"""
        
        # 1. INCUMBENT ADVANTAGE TIERS (3-way interaction)
        # Strongest predictor: Incumbent + Same_Constituency + Same_Party
        self.df['incumbent_strongest'] = (
            self.df['Incumbent_'].astype(int) & 
            self.df['Same_Constituency_'].astype(int) & 
            self.df['Same_Party_'].astype(int)
        ).astype(int)
        
        # Strong: Incumbent + Same_Constituency (even different party)
        self.df['incumbent_strong'] = (
            self.df['Incumbent_'].astype(int) & 
            self.df['Same_Constituency_'].astype(int)
        ).astype(int)
        
        # Medium: Incumbent + Same_Party (different constituency)
        self.df['incumbent_medium'] = (
            self.df['Incumbent_'].astype(int) & 
            self.df['Same_Party_'].astype(int)
        ).astype(int)
        
        # 2. FINANCIAL STRENGTH METRICS
        self.df['Total Assets'] = pd.to_numeric(self.df['Total Assets'], errors='coerce').fillna(0)
        self.df['Liabilities'] = pd.to_numeric(self.df['Liabilities'], errors='coerce').fillna(0)
        
        # Net worth (campaign financial muscle)
        self.df['net_assets'] = self.df['Total Assets'] - self.df['Liabilities']
        self.df['net_assets'] = self.df['net_assets'].clip(lower=0)  # No negative net worth
        
        # Asset-to-Liability ratio (financial stability)
        self.df['asset_liability_ratio'] = (
            self.df['Total Assets'] / (self.df['Liabilities'] + 1)
        ).replace([np.inf, -np.inf], 0)
        
        # Financial tier (binned: poor, middle, wealthy)
        self.df['asset_tier'] = pd.cut(
            self.df['Total Assets'], 
            bins=[0, 5e6, 25e6, np.inf],
            labels=['low_asset', 'medium_asset', 'high_asset'],
            include_lowest=True
        ).cat.codes
        
        # 3. VOTE SHARE NORMALIZED (efficiency metric)
        # Vote_Share_Percentage / N_Cand (higher = less opposition split)
        self.df['N_Cand'] = pd.to_numeric(self.df['N_Cand'], errors='coerce').fillna(1)
        self.df['vote_efficiency'] = (
            self.df['Vote_Share_Percentage'] / (self.df['N_Cand'].clip(lower=1))
        )
        
        # 4. CRIMINAL HISTORY SEVERITY
        self.df['Criminal Case'] = pd.to_numeric(self.df['Criminal Case'], errors='coerce').fillna(0)
        self.df['has_criminal_case'] = (self.df['Criminal Case'] > 0).astype(int)
        self.df['criminal_severity'] = pd.cut(
            self.df['Criminal Case'],
            bins=[-1, 0, 5, np.inf],
            labels=['none', 'low', 'high'],
            include_lowest=True
        ).cat.codes
        
        self.feature_names.extend([
            'incumbent_strongest', 'incumbent_strong', 'incumbent_medium',
            'net_assets', 'asset_liability_ratio', 'asset_tier',
            'vote_efficiency', 'has_criminal_case', 'criminal_severity'
        ])
        
        return self
    
    def create_tier2_high_value_interactions(self):
        """TIER 2: Create high-value interaction features"""
        
        # 1. POLITICAL EXPERIENCE COMPOSITE
        self.df['times_contested'] = self.df.groupby('Candidate')['Candidate'].transform('count')
        self.df['is_repeat_candidate'] = (self.df['times_contested'] > 1).astype(int)
        self.df['political_experience'] = (
            self.df['is_repeat_candidate'] * self.df['times_contested']
        )
        
        # No_Terms = career length in politics
        self.df['No_Terms'] = pd.to_numeric(self.df['No_Terms'], errors='coerce').fillna(0)
        
        # 2. YOUTH + EDUCATION ADVANTAGE (modern voter appeal)
        self.df['Age'] = pd.to_numeric(self.df['Age'], errors='coerce').fillna(self.df['Age'].median())
        self.df['education_class'] = pd.to_numeric(self.df['education_class'], errors='coerce').fillna(0)
        self.df['young_educated'] = (
            (self.df['Age'] < 35) & (self.df['education_class'] >= 15)
        ).astype(int)
        
        # 3. TURNCOAT RISK (party switcher penalty)
        self.df['Turncoat_'] = pd.to_numeric(self.df['Turncoat_'], errors='coerce').fillna(0)
        self.df['Same_Party_'] = pd.to_numeric(self.df['Same_Party_'], errors='coerce').fillna(0)
        self.df['turncoat_risk'] = (
            self.df['Turncoat_'] & (~self.df['Same_Party_'].astype(bool))
        ).astype(int)
        
        # 4. MARGIN VS TURNOUT EFFICIENCY
        self.df['Margin_Percentage'] = pd.to_numeric(self.df['Margin_Percentage'], errors='coerce').fillna(0)
        self.df['Turnout_Percentage'] = pd.to_numeric(self.df['Turnout_Percentage'], errors='coerce').fillna(50)
        self.df['margin_to_turnout_ratio'] = (
            (self.df['Margin_Percentage'] + 1) / (self.df['Turnout_Percentage'] + 1)
        ).replace([np.inf, -np.inf], 0)
        
        # 5. GENDER ENCODED (Female candidate flag for interaction analysis)
        self.df['Sex'] = self.df['Sex'].fillna('M')
        self.df['is_female'] = (self.df['Sex'] == 'F').astype(int)
        self.df['is_other_gender'] = (self.df['Sex'] == 'O').astype(int)
        
        self.feature_names.extend([
            'times_contested', 'is_repeat_candidate', 'political_experience',
            'young_educated', 'turncoat_risk', 'margin_to_turnout_ratio',
            'is_female', 'is_other_gender'
        ])
        
        return self
    
    def create_tier3_secondary_interactions(self):
        """TIER 3: Secondary interactions and derived features"""
        
        # 1. EDUCATION ORDINAL (keep as-is; don't one-hot)
        # Already encoded 0-22 (Illiterate=0, Doctorate=22)
        # Just ensure numeric
        self.df['education_level'] = pd.to_numeric(
            self.df['education_class'], errors='coerce'
        ).fillna(0)
        
        # 2. PROFESSION ENCODED (keep ordinal 1-17)
        self.df['TCPD_Prof_Main_'] = pd.to_numeric(
            self.df['TCPD_Prof_Main_'], errors='coerce'
        ).fillna(0)
        
        # 3. PARTY ENCODED (0-99; will handle high-cardinality separately)
        self.df['Party_'] = pd.to_numeric(self.df['Party_'], errors='coerce').fillna(0)
        
        # 4. DEPOSIT LOST FLAG (turnout proxy; low vote share)
        self.df['Deposit_Lost_'] = pd.to_numeric(self.df['Deposit_Lost_'], errors='coerce').fillna(0)
        self.df['deposit_forfeiture_indicator'] = self.df['Deposit_Lost_'].astype(int)
        
        # 5. CONSTITUENCY TYPE (SC vs GEN; binary)
        if 'Constituency_Type' in self.df.columns:
            self.df['is_reserved_sc'] = (self.df['Constituency_Type'] == 'SC').astype(int)
        else:
            self.df['is_reserved_sc'] = 0
        
        # 6. VOTE SHARE BRACKETS (categorical → ordinal)
        self.df['Vote_Share_Percentage'] = pd.to_numeric(
            self.df['Vote_Share_Percentage'], errors='coerce'
        ).fillna(0)
        self.df['vote_share_bracket'] = pd.cut(
            self.df['Vote_Share_Percentage'],
            bins=[0, 10, 20, 30, 40, 50, 100],
            labels=['very_low', 'low', 'medium', 'high', 'very_high', 'winning'],
            include_lowest=True
        ).cat.codes
        
        # 7. ENOP - Effective Number of Parties (competitiveness)
        self.df['ENOP'] = pd.to_numeric(self.df['ENOP'], errors='coerce').fillna(3)
        self.df['competition_level'] = pd.cut(
            self.df['ENOP'],
            bins=[0, 2, 3, 4, 10],
            labels=['low', 'medium', 'high', 'very_high'],
            include_lowest=True
        ).cat.codes
        
        self.feature_names.extend([
            'education_level', 'TCPD_Prof_Main_', 'Party_',
            'deposit_forfeiture_indicator', 'is_reserved_sc',
            'vote_share_bracket', 'competition_level'
        ])
        
        return self
    
    def handle_categorical_encoding(self):
        """Target encode high-cardinality features (Party_) by win rate"""
        
        # Calculate win rate by Party
        if 'Party_' in self.df.columns and 'won' in self.df.columns:
            party_win_rate = self.df.groupby('Party_')['won'].agg(['mean', 'count']).reset_index()
            party_win_rate.columns = ['Party_', 'party_win_rate', 'party_count']
            
            # Smooth with global mean (Laplace smoothing for small groups)
            global_win_rate = self.df['won'].mean()
            party_win_rate['party_win_rate_smoothed'] = (
                (party_win_rate['party_win_rate'] * party_win_rate['party_count'] + global_win_rate) /
                (party_win_rate['party_count'] + 1)
            )
            
            self.df = self.df.merge(
                party_win_rate[['Party_', 'party_win_rate_smoothed']], 
                on='Party_', 
                how='left'
            )
            self.df['party_win_rate_target_encoded'] = self.df['party_win_rate_smoothed']
            self.feature_names.append('party_win_rate_target_encoded')
        
        return self
    
    def scale_numeric_features(self):
        """Scale numerical features for tree-based models (improves convergence)"""
        
        numeric_features = [
            'net_assets', 'asset_liability_ratio', 'vote_efficiency',
            'margin_to_turnout_ratio', 'Age', 'No_Terms'
        ]
        
        numeric_features = [f for f in numeric_features if f in self.df.columns]
        
        if numeric_features:
            self.df[numeric_features] = self.scaler.fit_transform(
                self.df[numeric_features].fillna(0)
            )
        
        return self
    
    def create_feature_matrix(self, target_col='won'):
        """Create final feature matrix for ML models"""
        
        # Select only engineered features + target
        feature_cols = [col for col in self.feature_names if col in self.df.columns]
        
        # Ensure target exists
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe")
        
        # Clean target variable (0/1 only)
        self.df[target_col] = pd.to_numeric(self.df[target_col], errors='coerce')
        self.df[target_col] = self.df[target_col].replace(99, np.nan)
        
        # Remove rows with missing target
        self.engineered_df = self.df[feature_cols + [target_col]].dropna(subset=[target_col])
        
        return self.engineered_df
    
    def fit_transform(self, target_col='won'):
        """Full pipeline: create features → scale → return matrix"""
        
        self.handle_missing_values()
        self.create_tier1_critical_features()
        self.create_tier2_high_value_interactions()
        self.create_tier3_secondary_interactions()
        self.handle_categorical_encoding()
        self.scale_numeric_features()
        
        return self.create_feature_matrix(target_col)
    
    def get_feature_names(self):
        """Return list of engineered feature names"""
        return self.feature_names
    
    def get_feature_descriptions(self):
        """Return descriptions of engineered features for interpretability"""
        descriptions = {
            'incumbent_strongest': 'Incumbent + Same Constituency + Same Party (CRITICAL)',
            'incumbent_strong': 'Incumbent + Same Constituency',
            'incumbent_medium': 'Incumbent + Same Party',
            'net_assets': 'Net Worth (Total Assets - Liabilities)',
            'asset_liability_ratio': 'Financial Stability Ratio (Assets / Liabilities)',
            'asset_tier': 'Financial Tier (0=low, 1=medium, 2=high)',
            'vote_efficiency': 'Vote Share / Number of Candidates (lower opposition split)',
            'has_criminal_case': 'Binary: Has any criminal case',
            'criminal_severity': 'Criminal Case Severity (0=none, 1=low, 2=high)',
            'times_contested': 'Total number of elections contested',
            'is_repeat_candidate': 'Binary: Contested in previous elections',
            'political_experience': 'Repeat Candidate × Times Contested',
            'young_educated': 'Age < 35 AND Education >= Graduate',
            'turncoat_risk': 'Turncoat AND Not Same Party',
            'margin_to_turnout_ratio': 'Victory Margin / Voter Turnout (efficiency)',
            'is_female': 'Binary: Female candidate',
            'is_other_gender': 'Binary: Other gender',
            'education_level': 'Education Class (0=Illiterate, 22=Doctorate)',
            'TCPD_Prof_Main_': 'Profession Code (1-17)',
            'Party_': 'Party Code (0-99)',
            'deposit_forfeiture_indicator': 'Candidate lost security deposit',
            'is_reserved_sc': 'Scheduled Caste reserved constituency',
            'vote_share_bracket': 'Vote Share Categorical (0-5 scale)',
            'competition_level': 'ENOP - Competitiveness Level',
            'party_win_rate_target_encoded': 'Target-encoded Party Win Rate'
        }
        return descriptions


def create_features_for_modeling(df, target_col='won'):
    """
    Convenience function to apply all feature engineering in one call
    
    Args:
        df: Raw election dataframe
        target_col: Name of target variable column
        
    Returns:
        X: Feature matrix (exclude target)
        y: Target vector
        feature_names: List of feature names
        feature_descriptions: Dict of feature descriptions
    """
    engineer = ElectionFeatureEngineer(df)
    engineered_data = engineer.fit_transform(target_col)
    
    feature_names = engineer.get_feature_names()
    feature_descriptions = engineer.get_feature_descriptions()
    
    X = engineered_data.drop(columns=[target_col])
    y = engineered_data[target_col]
    
    return X, y, feature_names, feature_descriptions
