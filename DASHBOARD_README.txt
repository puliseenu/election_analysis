ELECTION DATA ANALYSIS DASHBOARD
==================================

✅ SYSTEM STATUS: LIVE & RUNNING

Dashboard URL: http://192.168.0.165:8050
Local URL:     http://127.0.0.1:8050

PORT: 8050
HOST: 0.0.0.0 (Network Accessible)

=== FEATURES ===

1. IMPACT FACTOR ANALYSIS
   ├─ Vote Share Impact: 97.0% (Strongest Factor)
   ├─ Margin Impact: 38.1%
   ├─ Consistency Impact: 8.0%
   ├─ Age Impact: 6.1%
   └─ Incumbent Impact: 1.5%

2. CORRELATION ANALYSIS
   ├─ Vote Share ↔ Win: 0.751 (Strong)
   ├─ Votes Received ↔ Win: 0.703 (Strong)
   ├─ Consistency ↔ Win: 0.647 (Moderate)
   ├─ Incumbent Status ↔ Win: 0.438 (Moderate)
   └─ Same Party ↔ Win: 0.329 (Weak)

3. STATE-YEAR WISE SUMMARY (Always Classified)
   ├─ Winners by State & Year
   ├─ Total Candidates by State & Year
   ├─ Win Rate by State & Year
   ├─ Average Votes by State & Year
   ├─ Average Consistency by State & Year
   └─ Top 5 Performing State-Year Combinations

4. INTERACTIVE VISUALIZATIONS
   ├─ Impact Factors Bar Chart
   ├─ Correlation Heatmap
   ├─ State Performance Win Rates
   ├─ Temporal Trends (Win Rate vs Consistency)
   └─ Votes vs Winning Scatter Plot

5. FILTERING OPTIONS
   ├─ Filter by State
   ├─ Filter by Year
   └─ Real-time Updates

=== DATA SUMMARY ===

Total Candidates: 31,365
Total Winners: 3,294
Overall Win Rate: 10.50%

Average Votes (Winners): 74,252
Average Votes (Losers): 9,114

Average Consistency (Winners): 2.06 terms
Average Consistency (Losers): 0.11 terms

=== KEY FINDINGS ===

1. VOTE SHARE is the DOMINANT factor for winning
   - Logistic Regression Coefficient: 9.70 (100% impact)
   - Correlation: 0.751 (very strong)
   
2. CONSISTENCY shows MODERATE impact
   - Logistic Regression Coefficient: 0.77 (8% impact)
   - Correlation: 0.647
   - Winners average 2.06 terms vs Losers 0.11 terms
   
3. STATE PERFORMANCE VARIES
   - West Bengal: Highest win rate (14.47%)
   - Kerala: 12.90% win rate
   - Tamil Nadu: 6.91% win rate
   
4. TEMPORAL TRENDS
   - Win rate declining over years (2006: 12.9% → 2021: 9.0%)
   - Consistency decreasing (2006: 0.385 → 2021: 0.285)
   - Suggests expanding electoral field

=== QUALITY VS QUANTITY ===

"Quality (Consistency) vs Quantity (Participants)" Analysis:
- Vote share (quality indicator) has 97% impact
- While consistency has 8% impact
- Result: VOTE SHARE dominates over consistency
- Geographic factors matter more than individual experience

=== FILES GENERATED ===

Analysis Scripts:
├─ impact_analysis.py - Full statistical analysis
├─ analysis_dashboard.py - Interactive Dash dashboard
├─ dashboard_simple.py - Simple baseline dashboard
└─ convert_to_csv.py - Data conversion utility

Generated Visualizations:
├─ correlation_heatmap.html
├─ impact_factors.html
├─ state_win_rates.html
├─ temporal_trends.html
└─ votes_vs_win.html

Data Files:
├─ raw data/election_data.csv - Processed election data
└─ raw data/5state election 2026 merged my copy.xlsx - Original

=== ENVIRONMENT ===

Python: 3.13.12
Virtual Environment: .venv
Location: D:\BitsPhD\nagaraju_18_04_2026

Installed Packages:
├─ pandas
├─ plotly
├─ dash
├─ dash-bootstrap-components
├─ scikit-learn
└─ scipy

Requirements File: requirements.txt

=== QUICK START ===

From: D:\BitsPhD\nagaraju_18_04_2026

To start dashboard:
  python analysis_dashboard.py

Or using batch file:
  run_dashboard.bat

Access:
  Browser: http://192.168.0.165:8050

To run analysis only:
  python impact_analysis.py

=== FILTERS AVAILABLE ===

1. State Filter - Select specific state (or All)
2. Year Filter - Select specific year (or All)
3. All filters auto-update all visualizations

=== SUMMARY STATISTICS DISPLAY ===

Always classified by State & Year:
- Top 5 State-Year combinations by Win Rate
- Total Candidates per State-Year
- Winners per State-Year
- Win Rate percentage per State-Year
- Average Votes per State-Year
- Average Consistency per State-Year

Plus Overall Statistics:
- Total Records
- Total Winners
- Win Rate
- Average Votes
- Average Consistency

=== MODEL PERFORMANCE ===

Logistic Regression Model:
- AUC Score: 0.9999 (Excellent)
- Accuracy: Very High
- Primary Features: Vote Share, Margin, Consistency
- Features Used: 9 key electoral metrics

=== CONTACT & NOTES ===

Project: Election Data Analysis
Date: April 18, 2026
Status: ✅ Active & Running
Access: Network-wide via http://192.168.0.165:8050

Dashboard is continuously running on port 8050
All filters and visualizations update in real-time
State-Year classification always visible in summary panel
