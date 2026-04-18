import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ─────────────────────────────────────────────
# DATA LOAD & PREP
# ─────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(r"raw data/election_data.csv", low_memory=False)

# Numeric conversions
for col in ['Votes', 'Age', 'Vote_Share_Percentage', 'Margin', 'Margin_Percentage',
            'Turnout_Percentage', 'N_Cand', 'No_Terms', 'ENOP']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df['Criminal_Case']   = pd.to_numeric(df['Criminal Case'],  errors='coerce').fillna(0)
df['Total_Assets']    = pd.to_numeric(df['Total Assets'],   errors='coerce').fillna(0)
df['Liabilities']     = pd.to_numeric(df['Liabilities'],    errors='coerce').fillna(0)
df['won']             = pd.to_numeric(df['won'],            errors='coerce').fillna(0)
df['Year']            = pd.to_numeric(df['Year'],           errors='coerce')

education_order = ['Illiterate','Literate','8th Pass','10th Pass','11th Pass',
                   '12th Pass','Graduate','Graduate Professional','Post Graduate','Doctorate']
education_num   = {e: i for i, e in enumerate(education_order)}
df['Edu_Num']   = df['Education'].map(education_num).fillna(-1)

states   = sorted(df['State'].dropna().unique())
years    = sorted(df['Year'].dropna().unique().astype(int))
parties  = sorted(df['Party'].dropna().unique())
sexes    = sorted(df['Sex'].dropna().unique())

print(f"Data loaded: {len(df)} rows | States: {len(states)} | Years: {len(years)}")

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
C_WIN   = '#2ECC71'
C_LOSE  = '#E74C3C'
C_BLUE  = '#3498DB'
C_GOLD  = '#F39C12'
C_PURP  = '#9B59B6'
C_TEAL  = '#1ABC9C'
BG      = '#F0F2F5'
SIDEBAR = '#1E2A38'
STEXT   = '#FFFFFF'
SACTIVE = '#3498DB'

# ─────────────────────────────────────────────
# HELPER FILTER
# ─────────────────────────────────────────────
def apply_filters(state, year, party, sex):
    d = df.copy()
    if state and state != 'All':
        d = d[d['State'] == state]
    if year and year != 'All':
        d = d[d['Year'] == int(year)]
    if party and party != 'All':
        d = d[d['Party'] == party]
    if sex and sex != 'All':
        d = d[d['Sex'] == sex]
    return d

# ─────────────────────────────────────────────
# SIDEBAR STYLE
# ─────────────────────────────────────────────
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0, 'left': 0, 'bottom': 0,
    'width': '230px',
    'padding': '0',
    'backgroundColor': SIDEBAR,
    'overflowY': 'auto',
    'zIndex': 1000,
    'boxShadow': '2px 0 8px rgba(0,0,0,0.3)',
}
CONTENT_STYLE = {
    'marginLeft': '240px',
    'padding': '20px',
    'backgroundColor': BG,
    'minHeight': '100vh',
}

def nav_item(label, section_id, icon):
    return html.Div(
        id={'type': 'nav-btn', 'index': section_id},
        children=[html.Span(icon, style={'marginRight': '10px', 'fontSize': '16px'}), label],
        n_clicks=0,
        style={
            'padding': '14px 20px',
            'color': '#CBD5E0',
            'cursor': 'pointer',
            'fontSize': '14px',
            'fontWeight': '500',
            'borderLeft': '3px solid transparent',
            'transition': 'all 0.2s',
            'display': 'flex',
            'alignItems': 'center',
        }
    )

# ─────────────────────────────────────────────
# COMMON FILTER BAR
# ─────────────────────────────────────────────
def filter_bar():
    dd = {'fontSize': '13px'}
    return dbc.Row([
        dbc.Col([html.Label("State", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555'}),
                 dcc.Dropdown(id='f-state',
                     options=[{'label': 'All States', 'value': 'All'}] +
                             [{'label': s, 'value': s} for s in states],
                     value='All', clearable=False, style=dd)], width=3),
        dbc.Col([html.Label("Year", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555'}),
                 dcc.Dropdown(id='f-year',
                     options=[{'label': 'All Years', 'value': 'All'}] +
                             [{'label': str(y), 'value': str(y)} for y in years],
                     value='All', clearable=False, style=dd)], width=2),
        dbc.Col([html.Label("Party", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555'}),
                 dcc.Dropdown(id='f-party',
                     options=[{'label': 'All Parties', 'value': 'All'}] +
                             [{'label': p, 'value': p} for p in parties],
                     value='All', clearable=False, style=dd)], width=4),
        dbc.Col([html.Label("Sex", style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555'}),
                 dcc.Dropdown(id='f-sex',
                     options=[{'label': 'All', 'value': 'All'}] +
                             [{'label': s, 'value': s} for s in sexes],
                     value='All', clearable=False, style=dd)], width=2),
    ], className='mb-3 p-3 bg-white rounded shadow-sm', style={'margin': '0 0 16px 0'})

def section_header(title, subtitle=''):
    return html.Div([
        html.H4(title, style={'fontWeight': '700', 'color': '#1E2A38', 'margin': '0'}),
        html.P(subtitle, style={'color': '#777', 'fontSize': '13px', 'margin': '2px 0 0 0'}),
        html.Hr(style={'borderColor': '#ddd', 'margin': '12px 0'})
    ])

def kpi_card(label, value, color=C_BLUE, icon=''):
    return dbc.Col(
        html.Div([
            html.Div(icon, style={'fontSize': '28px'}),
            html.H3(value, style={'fontWeight': '800', 'color': color, 'margin': '4px 0 2px'}),
            html.P(label, style={'color': '#888', 'fontSize': '12px', 'margin': 0})
        ], style={
            'background': 'white', 'borderRadius': '10px', 'padding': '18px',
            'textAlign': 'center', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
            'borderTop': f'4px solid {color}'
        }), width=3
    )

# ─────────────────────────────────────────────
# APP INIT
# ─────────────────────────────────────────────
app = Dash(__name__,
           external_stylesheets=[dbc.themes.BOOTSTRAP,
                                  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'],
           suppress_callback_exceptions=True)

# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
sidebar = html.Div([
    # Logo / Title
    html.Div([
        html.Div('🗳', style={'fontSize': '32px', 'textAlign': 'center', 'paddingTop': '10px'}),
        html.H5("Election\nAnalysis", style={
            'color': STEXT, 'textAlign': 'center', 'fontWeight': '700',
            'fontSize': '15px', 'margin': '6px 0 4px', 'lineHeight': '1.3'
        }),
        html.P("5 States · 2006-2021", style={
            'color': '#8899AA', 'textAlign': 'center', 'fontSize': '11px', 'margin': '0 0 10px'
        }),
    ], style={'borderBottom': '1px solid #2D3F52', 'paddingBottom': '12px', 'marginBottom': '8px'}),

    # Nav Items
    nav_item("EDA Overview",          "eda",       "📊"),
    nav_item("State & Year Trends",   "trends",    "📈"),
    nav_item("Candidate Profile",     "candidate", "👤"),
    nav_item("Party Analysis",        "party",     "🏛"),
    nav_item("Impact Factors",        "impact",    "🎯"),
    nav_item("Education & Profession","edu_prof",  "🎓"),
    nav_item("Criminal & Finance",    "crime_fin", "⚖"),
    nav_item("Win Predictors",        "predict",   "🏆"),

    # Bottom info
    html.Div([
        html.P("31,365 Candidates", style={'color': '#8899AA', 'fontSize': '11px', 'margin': '2px 0'}),
        html.P("5 States · 4 Elections", style={'color': '#8899AA', 'fontSize': '11px', 'margin': '2px 0'}),
    ], style={'position': 'absolute', 'bottom': '16px', 'left': 0, 'right': 0, 'textAlign': 'center'})
], style=SIDEBAR_STYLE)

content = html.Div([
    dcc.Store(id='active-section', data='eda'),
    filter_bar(),
    html.Div(id='page-content'),
], style=CONTENT_STYLE)

app.layout = html.Div([
    sidebar,
    content,
], style={'fontFamily': 'Inter, sans-serif'})


# ─────────────────────────────────────────────
# SECTION: EDA OVERVIEW
# ─────────────────────────────────────────────
def build_eda(d):
    total     = len(d)
    winners   = int(d['won'].sum())
    win_rate  = winners / total * 100 if total else 0
    avg_votes = int(d['Votes'].mean()) if d['Votes'].notna().any() else 0
    avg_turn  = d['Turnout_Percentage'].mean() if d['Turnout_Percentage'].notna().any() else 0

    # ── Chart 1: Candidates by State
    s_count = d.groupby('State').agg(Total=('won','count'), Winners=('won','sum')).reset_index()
    s_count['Losers'] = s_count['Total'] - s_count['Winners']
    fig1 = go.Figure([
        go.Bar(name='Winners', x=s_count['State'], y=s_count['Winners'], marker_color=C_WIN),
        go.Bar(name='Losers',  x=s_count['State'], y=s_count['Losers'],  marker_color=C_LOSE),
    ])
    fig1.update_layout(barmode='stack', title='Candidates by State (Win/Loss)',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300,
                       legend=dict(orientation='h', y=-0.2))

    # ── Chart 2: Year-wise distribution
    y_count = d.groupby('Year').agg(Total=('won','count'), Winners=('won','sum')).reset_index()
    y_count['WinRate'] = y_count['Winners'] / y_count['Total'] * 100
    fig2 = go.Figure([
        go.Bar(name='Total',   x=y_count['Year'].astype(str), y=y_count['Total'],   marker_color=C_BLUE, opacity=0.6),
        go.Scatter(name='Win %', x=y_count['Year'].astype(str), y=y_count['WinRate'],
                   yaxis='y2', mode='lines+markers', line=dict(color=C_GOLD, width=2),
                   marker=dict(size=8)),
    ])
    fig2.update_layout(title='Year-wise Candidates & Win Rate',
                       yaxis2=dict(overlaying='y', side='right', title='Win Rate %', ticksuffix='%'),
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=50), height=300,
                       legend=dict(orientation='h', y=-0.2))

    # ── Chart 3: Sex distribution
    sex_grp = d.groupby('Sex').agg(Total=('won','count'), Won=('won','sum')).reset_index()
    sex_grp['WinRate'] = sex_grp['Won'] / sex_grp['Total'] * 100
    fig3 = go.Figure([
        go.Bar(x=sex_grp['Sex'], y=sex_grp['Total'],   name='Total',   marker_color=C_TEAL),
        go.Bar(x=sex_grp['Sex'], y=sex_grp['Won'],     name='Winners', marker_color=C_WIN),
    ])
    fig3.update_layout(barmode='group', title='Candidates by Sex',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300,
                       legend=dict(orientation='h', y=-0.2))

    # ── Chart 4: Votes distribution (histogram)
    v = d['Votes'].dropna()
    fig4 = go.Figure(go.Histogram(x=v, nbinsx=50, marker_color=C_BLUE, opacity=0.7))
    fig4.update_layout(title='Votes Distribution (All Candidates)',
                       xaxis_title='Votes', yaxis_title='Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # ── Chart 5: Vote Share % distribution winners vs losers
    won_vs  = d[d['won']==1]['Vote_Share_Percentage'].dropna()
    lost_vs = d[d['won']==0]['Vote_Share_Percentage'].dropna()
    fig5 = go.Figure([
        go.Histogram(x=won_vs,  name='Winners', marker_color=C_WIN,  opacity=0.7, nbinsx=40),
        go.Histogram(x=lost_vs, name='Losers',  marker_color=C_LOSE, opacity=0.5, nbinsx=40),
    ])
    fig5.update_layout(barmode='overlay', title='Vote Share % – Winners vs Losers',
                       xaxis_title='Vote Share %', yaxis_title='Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300,
                       legend=dict(orientation='h', y=-0.2))

    # ── Chart 6: Age distribution
    age_won  = d[d['won']==1]['Age'].dropna()
    age_lost = d[d['won']==0]['Age'].dropna()
    fig6 = go.Figure([
        go.Box(y=age_won,  name='Winners', marker_color=C_WIN),
        go.Box(y=age_lost, name='Losers',  marker_color=C_LOSE),
    ])
    fig6.update_layout(title='Age Distribution – Winners vs Losers',
                       yaxis_title='Age',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # ── Chart 7: Turnout by State
    turn = d.groupby('State')['Turnout_Percentage'].mean().reset_index().sort_values('Turnout_Percentage', ascending=True)
    fig7 = go.Figure(go.Bar(x=turn['Turnout_Percentage'], y=turn['State'],
                            orientation='h', marker_color=C_TEAL))
    fig7.update_layout(title='Average Turnout % by State',
                       xaxis_title='Turnout %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=120, r=10), height=300)

    # ── Chart 8: Candidate Type breakdown
    ct = d.groupby('Candidate_Type').agg(Total=('won','count'), Won=('won','sum')).reset_index()
    ct['WinRate'] = ct['Won'] / ct['Total'] * 100
    fig8 = go.Figure(go.Bar(x=ct['Candidate_Type'], y=ct['WinRate'],
                            marker_color=C_PURP,
                            text=ct['WinRate'].round(1).astype(str) + '%',
                            textposition='outside'))
    fig8.update_layout(title='Win Rate by Candidate Type',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=60, l=40, r=10), height=300)

    # ── Chart 9: N_Cand (competition) distribution
    nc = d['N_Cand'].dropna()
    fig9 = go.Figure(go.Histogram(x=nc, nbinsx=30, marker_color=C_GOLD, opacity=0.8))
    fig9.update_layout(title='Number of Candidates per Constituency',
                       xaxis_title='No. of Candidates', yaxis_title='Constituency Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # ── Chart 10: Margin % distribution
    m_won  = d[d['won']==1]['Margin_Percentage'].dropna()
    fig10 = go.Figure(go.Histogram(x=m_won, nbinsx=40, marker_color=C_WIN, opacity=0.8))
    fig10.update_layout(title='Victory Margin % Distribution (Winners)',
                        xaxis_title='Margin %', yaxis_title='Count',
                        paper_bgcolor='white', plot_bgcolor='white',
                        margin=dict(t=40, b=40, l=40, r=10), height=300)

    def card(fig):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=6,
                       className='mb-3')

    return html.Div([
        section_header("📊 EDA Overview",
                       f"Exploring {total:,} candidates across all dimensions"),
        # KPI row
        dbc.Row([
            kpi_card("Total Candidates",  f"{total:,}",          C_BLUE, '🗳'),
            kpi_card("Total Winners",     f"{winners:,}",        C_WIN,  '🏆'),
            kpi_card("Overall Win Rate",  f"{win_rate:.1f}%",    C_GOLD, '📊'),
            kpi_card("Avg Votes",         f"{avg_votes:,}",      C_TEAL, '🗟'),
        ], className='mb-3'),
        # Chart grid
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
        dbc.Row([card(fig5), card(fig6)]),
        dbc.Row([card(fig7), card(fig8)]),
        dbc.Row([card(fig9), card(fig10)]),
    ])


# ─────────────────────────────────────────────
# SECTION: STATE & YEAR TRENDS
# ─────────────────────────────────────────────
def build_trends(d):
    total = len(d)

    # State × Year heatmap
    sy = d.groupby(['State','Year']).agg(Total=('won','count'), Won=('won','sum')).reset_index()
    sy['WinRate'] = sy['Won'] / sy['Total'] * 100
    pivot = sy.pivot(index='State', columns='Year', values='WinRate').fillna(0)
    fig1 = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.astype(str), y=pivot.index,
        colorscale='RdYlGn', zmid=10,
        text=np.round(pivot.values, 1),
        texttemplate='%{text}%', textfont={'size': 11},
        colorbar=dict(title='Win Rate %')
    ))
    fig1.update_layout(title='Win Rate % – State × Year Heatmap',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=50, b=40, l=130, r=10), height=350)

    # Year-wise absolute numbers
    y_agg = d.groupby('Year').agg(
        Total=('won','count'), Won=('won','sum'),
        AvgVotes=('Votes','mean'), AvgTurnout=('Turnout_Percentage','mean')
    ).reset_index()
    y_agg['LostRate'] = (y_agg['Total']-y_agg['Won'])/y_agg['Total']*100
    y_agg['WinRate']  = y_agg['Won']/y_agg['Total']*100

    fig2 = go.Figure([
        go.Scatter(x=y_agg['Year'].astype(str), y=y_agg['AvgVotes'],
                   name='Avg Votes', mode='lines+markers',
                   line=dict(color=C_BLUE, width=2), marker=dict(size=8)),
    ])
    fig2.update_layout(title='Average Votes per Candidate Over Years',
                       yaxis_title='Avg Votes',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=300)

    fig3 = go.Figure([
        go.Scatter(x=y_agg['Year'].astype(str), y=y_agg['AvgTurnout'],
                   name='Avg Turnout %', mode='lines+markers',
                   line=dict(color=C_GOLD, width=2), marker=dict(size=8)),
    ])
    fig3.update_layout(title='Average Turnout % Over Years',
                       yaxis_title='Turnout %', yaxis_ticksuffix='%',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=300)

    # State win rate bar
    s_wr = d.groupby('State').agg(Total=('won','count'), Won=('won','sum')).reset_index()
    s_wr['WinRate'] = s_wr['Won'] / s_wr['Total'] * 100
    s_wr = s_wr.sort_values('WinRate', ascending=True)
    fig4 = go.Figure(go.Bar(x=s_wr['WinRate'], y=s_wr['State'],
                            orientation='h', marker_color=C_TEAL,
                            text=s_wr['WinRate'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig4.update_layout(title='Win Rate by State',
                       xaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=130, r=50), height=300)

    # Turnout by State × Year line
    sy_turn = d.groupby(['State','Year'])['Turnout_Percentage'].mean().reset_index()
    fig5 = go.Figure()
    for st in sy_turn['State'].unique():
        sub = sy_turn[sy_turn['State'] == st]
        fig5.add_trace(go.Scatter(x=sub['Year'].astype(str), y=sub['Turnout_Percentage'],
                                  name=st, mode='lines+markers', line=dict(width=2)))
    fig5.update_layout(title='Turnout % by State Over Years',
                       yaxis_title='Turnout %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=350,
                       legend=dict(orientation='h', y=-0.25))

    # Summary table
    sy_table = d.groupby(['State','Year']).agg(
        Candidates=('won','count'),
        Winners=('won','sum'),
        AvgAge=('Age','mean'),
        AvgVotes=('Votes','mean'),
        AvgTurnout=('Turnout_Percentage','mean'),
    ).reset_index()
    sy_table['WinRate'] = (sy_table['Winners'] / sy_table['Candidates'] * 100).round(1)
    sy_table['AvgAge']  = sy_table['AvgAge'].round(1)
    sy_table['AvgVotes']= sy_table['AvgVotes'].round(0).fillna(0).astype(int)
    sy_table['AvgTurnout'] = sy_table['AvgTurnout'].round(1)
    sy_table = sy_table.sort_values(['State','Year'])

    tbl = dbc.Table.from_dataframe(
        sy_table[['State','Year','Candidates','Winners','WinRate','AvgAge','AvgVotes','AvgTurnout']],
        striped=True, bordered=True, hover=True, size='sm',
        style={'fontSize': '12px'}
    )

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("📈 State & Year Trends",
                       f"Temporal & geographic patterns across {total:,} candidates"),
        dbc.Row([card(fig1, 12)]),
        dbc.Row([card(fig4), card(fig2)]),
        dbc.Row([card(fig3), card(fig5, 6)]),
        html.H5("State × Year Summary Table", className='mt-2 mb-2', style={'fontWeight':'700'}),
        html.Div(tbl, style={'overflowX':'auto', 'background':'white',
                             'borderRadius':'8px', 'padding':'10px',
                             'boxShadow':'0 2px 8px rgba(0,0,0,0.06)'})
    ])


# ─────────────────────────────────────────────
# SECTION: CANDIDATE PROFILE
# ─────────────────────────────────────────────
def build_candidate(d):
    total = len(d)

    # Age distribution
    fig1 = go.Figure([
        go.Histogram(x=d[d['won']==1]['Age'].dropna(), name='Winners',
                     nbinsx=30, marker_color=C_WIN, opacity=0.7),
        go.Histogram(x=d[d['won']==0]['Age'].dropna(), name='Losers',
                     nbinsx=30, marker_color=C_LOSE, opacity=0.5),
    ])
    fig1.update_layout(barmode='overlay', title='Age Distribution',
                       xaxis_title='Age', yaxis_title='Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300,
                       legend=dict(orientation='h', y=-0.25))

    # Age bin win rate
    bins = [20, 30, 40, 50, 60, 70, 85]
    labels = ['20-30','30-40','40-50','50-60','60-70','70+']
    d2 = d.copy()
    d2['AgeBin'] = pd.cut(d2['Age'], bins=bins, labels=labels)
    age_wr = d2.groupby('AgeBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    age_wr['WR'] = age_wr['W'] / age_wr['T'] * 100
    fig2 = go.Figure(go.Bar(x=age_wr['AgeBin'].astype(str), y=age_wr['WR'],
                            marker_color=C_PURP,
                            text=age_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig2.update_layout(title='Win Rate by Age Group',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # Incumbent / Recontest
    for col, label in [('Incumbent','Incumbent'), ('Recontest','Recontest'), ('Turncoat','Turncoat')]:
        d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0)

    inc_wr = d.groupby('Incumbent').agg(T=('won','count'), W=('won','sum')).reset_index()
    inc_wr['WR'] = inc_wr['W'] / inc_wr['T'] * 100
    inc_wr['Incumbent'] = inc_wr['Incumbent'].map({0:'Non-Incumbent', 1:'Incumbent'})
    fig3 = go.Figure(go.Bar(x=inc_wr['Incumbent'], y=inc_wr['WR'],
                            marker_color=[C_LOSE, C_WIN],
                            text=inc_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig3.update_layout(title='Win Rate: Incumbent vs Non-Incumbent',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # No_Terms scatter
    terms_wr = d.groupby('No_Terms').agg(T=('won','count'), W=('won','sum')).reset_index()
    terms_wr = terms_wr[terms_wr['T'] >= 20]
    terms_wr['WR'] = terms_wr['W'] / terms_wr['T'] * 100
    fig4 = go.Figure(go.Scatter(x=terms_wr['No_Terms'], y=terms_wr['WR'],
                                mode='lines+markers',
                                line=dict(color=C_GOLD, width=2), marker=dict(size=8)))
    fig4.update_layout(title='Win Rate by No. of Previous Terms',
                       xaxis_title='No. of Terms', yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # Turncoat
    tc_wr = d.groupby('Turncoat').agg(T=('won','count'), W=('won','sum')).reset_index()
    tc_wr['WR'] = tc_wr['W'] / tc_wr['T'] * 100
    tc_wr['Turncoat'] = tc_wr['Turncoat'].map({0:'Not Turncoat', 1:'Turncoat'})
    fig5 = go.Figure(go.Bar(x=tc_wr['Turncoat'], y=tc_wr['WR'],
                            marker_color=[C_BLUE, C_PURP],
                            text=tc_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig5.update_layout(title='Win Rate: Turncoat vs Loyal',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # Same Constituency / Same Party
    d['Same_Constituency'] = pd.to_numeric(d['Same_Constituency'], errors='coerce').fillna(0)
    d['Same_Party']        = pd.to_numeric(d['Same_Party'],        errors='coerce').fillna(0)
    sc_wr = d.groupby('Same_Constituency').agg(T=('won','count'), W=('won','sum')).reset_index()
    sc_wr['WR'] = sc_wr['W']/sc_wr['T']*100
    sc_wr['Same_Constituency'] = sc_wr['Same_Constituency'].map({0:'Different', 1:'Same Const.'})
    sp_wr = d.groupby('Same_Party').agg(T=('won','count'), W=('won','sum')).reset_index()
    sp_wr['WR'] = sp_wr['W']/sp_wr['T']*100
    sp_wr['Same_Party'] = sp_wr['Same_Party'].map({0:'Changed Party', 1:'Same Party'})

    fig6 = go.Figure([
        go.Bar(name='Same Const.', x=sc_wr['Same_Constituency'], y=sc_wr['WR'], marker_color=C_TEAL),
        go.Bar(name='Same Party',  x=sp_wr['Same_Party'],        y=sp_wr['WR'], marker_color=C_GOLD),
    ])
    fig6.update_layout(barmode='group', title='Win Rate: Loyalty Factors',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=60, l=40, r=10), height=300,
                       legend=dict(orientation='h', y=-0.3))

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("👤 Candidate Profile",
                       f"Age, experience, incumbency, loyalty across {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
        dbc.Row([card(fig5), card(fig6)]),
    ])


# ─────────────────────────────────────────────
# SECTION: PARTY ANALYSIS
# ─────────────────────────────────────────────
def build_party(d):
    total = len(d)

    party_agg = d.groupby('Party').agg(
        Total=('won','count'), Won=('won','sum'),
        AvgVotes=('Votes','mean'),
        AvgVoteShare=('Vote_Share_Percentage','mean'),
    ).reset_index()
    party_agg['WinRate'] = party_agg['Won'] / party_agg['Total'] * 100
    party_agg = party_agg[party_agg['Total'] >= 20]  # filter small parties

    top_by_wins = party_agg.sort_values('Won', ascending=False).head(15)
    top_by_wr   = party_agg[party_agg['Total'] >= 50].sort_values('WinRate', ascending=False).head(15)

    fig1 = go.Figure(go.Bar(
        x=top_by_wins['Won'], y=top_by_wins['Party'],
        orientation='h', marker_color=C_WIN,
        text=top_by_wins['Won'], textposition='outside'
    ))
    fig1.update_layout(title='Top 15 Parties by Total Wins',
                       xaxis_title='Total Wins',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=120, r=50), height=380)

    fig2 = go.Figure(go.Bar(
        x=top_by_wr['WinRate'], y=top_by_wr['Party'],
        orientation='h', marker_color=C_GOLD,
        text=top_by_wr['WinRate'].round(1).astype(str)+'%',
        textposition='outside'
    ))
    fig2.update_layout(title='Top 15 Parties by Win Rate (min 50 candidates)',
                       xaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=120, r=60), height=380)

    # Party Type
    pt_wr = d.groupby('Party_Type_TCPD').agg(T=('won','count'), W=('won','sum')).reset_index().dropna()
    pt_wr['WR'] = pt_wr['W']/pt_wr['T']*100
    pt_wr = pt_wr.sort_values('WR', ascending=False)
    fig3 = go.Figure(go.Bar(x=pt_wr['Party_Type_TCPD'], y=pt_wr['WR'],
                            marker_color=C_PURP,
                            text=pt_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig3.update_layout(title='Win Rate by Party Type',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=80, l=40, r=10), height=320)

    # Avg vote share top parties
    top_vs = party_agg.sort_values('AvgVoteShare', ascending=False).head(12)
    fig4 = go.Figure(go.Bar(
        x=top_vs['Party'], y=top_vs['AvgVoteShare'],
        marker_color=C_TEAL,
        text=top_vs['AvgVoteShare'].round(1).astype(str)+'%',
        textposition='outside'
    ))
    fig4.update_layout(title='Top 12 Parties by Avg Vote Share %',
                       yaxis_title='Avg Vote Share %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=100, l=40, r=10), height=360,
                       xaxis_tickangle=-45)

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("🏛 Party Analysis",
                       f"Party performance across {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
    ])


# ─────────────────────────────────────────────
# SECTION: IMPACT FACTORS
# ─────────────────────────────────────────────
def build_impact(d):
    from scipy.stats import pearsonr
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    total = len(d)

    features = {
        'Vote_Share_%':   'Vote_Share_Percentage',
        'Votes':          'Votes',
        'Margin_%':       'Margin_Percentage',
        'Margin':         'Margin',
        'Age':            'Age',
        'Turnout_%':      'Turnout_Percentage',
        'N_Cand':         'N_Cand',
        'No_Terms':       'No_Terms',
        'ENOP':           'ENOP',
        'Criminal_Cases': 'Criminal_Case',
        'Total_Assets':   'Total_Assets',
        'Liabilities':    'Liabilities',
    }

    corrs = []
    for label, col in features.items():
        try:
            sub = d[[col, 'won']].dropna()
            if len(sub) > 100:
                r, p = pearsonr(sub[col], sub['won'])
                corrs.append({'Feature': label, 'Correlation': r, 'p': p})
        except Exception:
            pass

    corr_df = pd.DataFrame(corrs).sort_values('Correlation', key=abs, ascending=False)
    colors_c = [C_WIN if r >= 0 else C_LOSE for r in corr_df['Correlation']]
    fig1 = go.Figure(go.Bar(
        x=corr_df['Correlation'], y=corr_df['Feature'],
        orientation='h', marker_color=colors_c,
        text=corr_df['Correlation'].round(3).astype(str),
        textposition='outside'
    ))
    fig1.update_layout(title='Pearson Correlation with Winning',
                       xaxis_title='Pearson r',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=120, r=60), height=380)

    # Logistic regression
    feat_cols = [features[k] for k in features]
    lr_d = d[feat_cols + ['won']].dropna()
    if len(lr_d) > 500:
        X = lr_d[feat_cols].values
        y = lr_d['won'].values
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        lr = LogisticRegression(max_iter=1000, C=0.1)
        lr.fit(Xs, y)
        coef_df = pd.DataFrame({'Feature': list(features.keys()), 'Coef': lr.coef_[0]})
        coef_df['Impact'] = np.abs(coef_df['Coef']) / np.abs(coef_df['Coef']).max() * 100
        coef_df = coef_df.sort_values('Impact', ascending=True)
        colors_lr = [C_WIN if c >= 0 else C_LOSE for c in coef_df['Coef']]
        fig2 = go.Figure(go.Bar(
            x=coef_df['Impact'], y=coef_df['Feature'],
            orientation='h', marker_color=colors_lr,
            text=coef_df['Impact'].round(1).astype(str)+'%',
            textposition='outside'
        ))
        fig2.update_layout(title='Relative Impact % (Logistic Regression)',
                           xaxis_title='Relative Impact %',
                           paper_bgcolor='white', plot_bgcolor='white',
                           margin=dict(t=40, b=40, l=120, r=60), height=380)
    else:
        fig2 = go.Figure()
        fig2.update_layout(title='Insufficient data for regression')

    # Vote Share vs Win Rate scatter
    d2 = d.copy()
    d2['VSbin'] = pd.cut(d2['Vote_Share_Percentage'], bins=range(0,105,5), labels=[f'{i}-{i+5}' for i in range(0,100,5)])
    vs_wr = d2.groupby('VSbin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    vs_wr['WR'] = vs_wr['W'] / vs_wr['T'] * 100
    fig3 = go.Figure(go.Scatter(x=vs_wr['VSbin'].astype(str), y=vs_wr['WR'],
                                mode='lines+markers', line=dict(color=C_BLUE, width=2),
                                marker=dict(size=6)))
    fig3.update_layout(title='Vote Share % vs Win Rate',
                       xaxis_title='Vote Share %', yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=80, l=60, r=10), height=320,
                       xaxis_tickangle=-45)

    # Margin vs win rate
    d2['Mbin'] = pd.cut(d2['Margin'], bins=10)
    m_wr = d2.groupby('Mbin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    m_wr['WR'] = m_wr['W'] / m_wr['T'] * 100
    fig4 = go.Figure(go.Bar(x=m_wr['Mbin'].astype(str), y=m_wr['WR'],
                            marker_color=C_GOLD))
    fig4.update_layout(title='Margin (Votes) vs Win Rate',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=80, l=60, r=10), height=320,
                       xaxis_tickangle=-45)

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("🎯 Impact Factors",
                       f"Statistical analysis of what drives election wins – {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
    ])


# ─────────────────────────────────────────────
# SECTION: EDUCATION & PROFESSION
# ─────────────────────────────────────────────
def build_edu_prof(d):
    total = len(d)

    # Education win rate
    edu_agg = d.groupby('Education').agg(T=('won','count'), W=('won','sum')).reset_index().dropna()
    edu_agg['WR']  = edu_agg['W'] / edu_agg['T'] * 100
    edu_agg['Num'] = edu_agg['Education'].map({e: i for i, e in enumerate(education_order)}).fillna(99)
    edu_agg = edu_agg[edu_agg['T'] >= 30].sort_values('Num')
    fig1 = go.Figure(go.Bar(x=edu_agg['Education'], y=edu_agg['WR'],
                            marker_color=C_BLUE,
                            text=edu_agg['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig1.update_layout(title='Win Rate by Education Level',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=120, l=40, r=10), height=360,
                       xaxis_tickangle=-30)

    # Education counts
    fig2 = go.Figure([
        go.Bar(name='Total',   x=edu_agg['Education'], y=edu_agg['T'],  marker_color=C_BLUE, opacity=0.7),
        go.Bar(name='Winners', x=edu_agg['Education'], y=edu_agg['W'],  marker_color=C_WIN),
    ])
    fig2.update_layout(barmode='group', title='Candidate Count by Education',
                       yaxis_title='Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=120, l=40, r=10), height=360,
                       xaxis_tickangle=-30, legend=dict(orientation='h', y=-0.45))

    # Profession win rate
    prof_agg = d.groupby('TCPD_Prof_Main').agg(T=('won','count'), W=('won','sum')).reset_index().dropna()
    prof_agg['WR'] = prof_agg['W'] / prof_agg['T'] * 100
    prof_agg = prof_agg[prof_agg['T'] >= 30].sort_values('WR', ascending=True)
    fig3 = go.Figure(go.Bar(
        x=prof_agg['WR'], y=prof_agg['TCPD_Prof_Main'],
        orientation='h', marker_color=C_TEAL,
        text=prof_agg['WR'].round(1).astype(str)+'%',
        textposition='outside'
    ))
    fig3.update_layout(title='Win Rate by Profession',
                       xaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=200, r=60), height=420)

    # Profession counts
    fig4 = go.Figure([
        go.Bar(name='Total',   x=prof_agg['TCPD_Prof_Main'], y=prof_agg['T'], marker_color=C_TEAL, opacity=0.7),
        go.Bar(name='Winners', x=prof_agg['TCPD_Prof_Main'], y=prof_agg['W'], marker_color=C_WIN),
    ])
    fig4.update_layout(barmode='group', title='Candidate Count by Profession',
                       yaxis_title='Count',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=160, l=40, r=10), height=420,
                       xaxis_tickangle=-45, legend=dict(orientation='h', y=-0.55))

    # Education × Sex
    edu_sex = d.groupby(['Education','Sex']).agg(T=('won','count'), W=('won','sum')).reset_index().dropna()
    edu_sex['WR'] = edu_sex['W'] / edu_sex['T'] * 100
    edu_sex = edu_sex[edu_sex['T'] >= 20]
    fig5 = go.Figure()
    for s in edu_sex['Sex'].unique():
        sub = edu_sex[edu_sex['Sex'] == s]
        fig5.add_trace(go.Bar(name=s, x=sub['Education'], y=sub['WR']))
    fig5.update_layout(barmode='group', title='Win Rate by Education & Sex',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=120, l=40, r=10), height=360,
                       xaxis_tickangle=-30, legend=dict(orientation='h', y=-0.45))

    # Edu summary table
    edu_tbl = edu_agg[['Education','T','W','WR']].copy()
    edu_tbl.columns = ['Education','Total','Winners','Win Rate %']
    edu_tbl['Win Rate %'] = edu_tbl['Win Rate %'].round(1)
    tbl = dbc.Table.from_dataframe(edu_tbl, striped=True, bordered=True, hover=True, size='sm',
                                   style={'fontSize':'12px'})

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("🎓 Education & Profession",
                       f"Impact of education level and professional background – {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
        dbc.Row([card(fig5, 6),
                 dbc.Col([
                     html.H6("Education Summary Table", className='mt-2 mb-1 fw-bold'),
                     html.Div(tbl, style={'overflowX':'auto'})
                 ], width=6)]),
    ])


# ─────────────────────────────────────────────
# SECTION: CRIMINAL & FINANCE
# ─────────────────────────────────────────────
def build_crime_fin(d):
    total = len(d)

    # Criminal cases bins
    d2 = d.copy()
    d2['CrimBin'] = pd.cut(d2['Criminal_Case'],
                           bins=[-1, 0, 1, 2, 3, 5, 100],
                           labels=['0 cases','1 case','2 cases','3 cases','4-5 cases','6+ cases'])
    cc_wr = d2.groupby('CrimBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    cc_wr['WR'] = cc_wr['W'] / cc_wr['T'] * 100
    fig1 = go.Figure(go.Bar(x=cc_wr['CrimBin'].astype(str), y=cc_wr['WR'],
                            marker_color=[C_BLUE, C_TEAL, C_GOLD, C_PURP, C_LOSE, '#C0392B'],
                            text=cc_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig1.update_layout(title='⚠ Criminal Cases vs Win Rate (PARADOX!)',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=50, b=40, l=60, r=10), height=320)

    # Criminal count distribution
    fig2 = go.Figure(go.Histogram(x=d2[d2['Criminal_Case'] <= 20]['Criminal_Case'],
                                  nbinsx=20, marker_color=C_LOSE, opacity=0.8))
    fig2.update_layout(title='Criminal Cases Distribution (0-20 range)',
                       xaxis_title='No. of Criminal Cases',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=40, r=10), height=300)

    # Total Assets bins
    d2['AssetBin'] = pd.cut(d2['Total_Assets'],
                            bins=[-1, 100000, 500000, 1000000, 5000000, 10000000, 1e12],
                            labels=['<1L','1-5L','5L-10L','10L-50L','50L-1Cr','1Cr+'])
    ast_wr = d2.groupby('AssetBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    ast_wr['WR'] = ast_wr['W'] / ast_wr['T'] * 100
    fig3 = go.Figure(go.Bar(x=ast_wr['AssetBin'].astype(str), y=ast_wr['WR'],
                            marker_color=C_GOLD,
                            text=ast_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig3.update_layout(title='Total Assets vs Win Rate',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    # Liabilities bins
    d2['LiabBin'] = pd.cut(d2['Liabilities'],
                           bins=[-1, 0, 100000, 500000, 1000000, 5000000, 1e12],
                           labels=['0','<1L','1-5L','5L-10L','10L-50L','50L+'])
    liab_wr = d2.groupby('LiabBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    liab_wr['WR'] = liab_wr['W'] / liab_wr['T'] * 100
    fig4 = go.Figure(go.Bar(x=liab_wr['LiabBin'].astype(str), y=liab_wr['WR'],
                            marker_color=C_TEAL,
                            text=liab_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig4.update_layout(title='Liabilities vs Win Rate',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    # Assets vs Criminal cases (winners)
    w_df = d2[d2['won']==1][['Total_Assets','Criminal_Case']].dropna()
    w_df = w_df[(w_df['Total_Assets'] < 5e7) & (w_df['Criminal_Case'] <= 20)]
    fig5 = go.Figure(go.Scatter(
        x=w_df['Criminal_Case'], y=w_df['Total_Assets'],
        mode='markers', marker=dict(color=C_WIN, opacity=0.3, size=5)))
    fig5.update_layout(title='Assets vs Criminal Cases (Winners)',
                       xaxis_title='Criminal Cases', yaxis_title='Total Assets (₹)',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=70, r=10), height=320)

    # Avg assets: winners vs losers
    avg_ast = d.groupby('won').agg(AvgAssets=('Total_Assets','mean'), AvgLiab=('Liabilities','mean')).reset_index()
    avg_ast['Label'] = avg_ast['won'].map({0:'Losers', 1:'Winners'})
    fig6 = go.Figure([
        go.Bar(name='Avg Assets',      x=avg_ast['Label'], y=avg_ast['AvgAssets'], marker_color=C_GOLD),
        go.Bar(name='Avg Liabilities', x=avg_ast['Label'], y=avg_ast['AvgLiab'],  marker_color=C_LOSE),
    ])
    fig6.update_layout(barmode='group', title='Avg Assets & Liabilities: Winners vs Losers',
                       yaxis_title='Amount (₹)',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=70, r=10), height=320,
                       legend=dict(orientation='h', y=-0.25))

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("⚖ Criminal Cases & Financial Analysis",
                       f"Criminal records, assets, and liabilities impact – {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig4)]),
        dbc.Row([card(fig5), card(fig6)]),
    ])


# ─────────────────────────────────────────────
# SECTION: WIN PREDICTORS
# ─────────────────────────────────────────────
def build_predict(d):
    total = len(d)

    # Deposit lost analysis
    d['Deposit_Lost'] = pd.to_numeric(d['Deposit_Lost'], errors='coerce').fillna(0)
    dep_wr = d.groupby('Deposit_Lost').agg(T=('won','count'), W=('won','sum')).reset_index()
    dep_wr['WR'] = dep_wr['W'] / dep_wr['T'] * 100
    dep_wr['Label'] = dep_wr['Deposit_Lost'].map({0:'Deposit Saved', 1:'Deposit Lost'})
    fig1 = go.Figure(go.Bar(x=dep_wr['Label'], y=dep_wr['WR'],
                            marker_color=[C_WIN, C_LOSE],
                            text=dep_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig1.update_layout(title='Win Rate: Deposit Saved vs Lost',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    # ENOP (effective number of parties) vs win rate
    d2 = d.copy()
    d2['ENOPbin'] = pd.cut(d2['ENOP'], bins=[0,2,3,4,5,6,20], labels=['<2','2-3','3-4','4-5','5-6','6+'])
    enop_wr = d2.groupby('ENOPbin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    enop_wr['WR'] = enop_wr['W'] / enop_wr['T'] * 100
    fig2 = go.Figure(go.Bar(x=enop_wr['ENOPbin'].astype(str), y=enop_wr['WR'],
                            marker_color=C_PURP,
                            text=enop_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig2.update_layout(title='Win Rate by Effective Number of Parties (ENOP)',
                       xaxis_title='ENOP Range', yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    # N_Cand (competition) vs win rate
    d2['Nbin'] = pd.cut(d2['N_Cand'], bins=[0,3,5,8,12,20,100],
                        labels=['2-3','4-5','6-8','9-12','13-20','20+'])
    nc_wr = d2.groupby('Nbin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    nc_wr['WR'] = nc_wr['W'] / nc_wr['T'] * 100
    fig3 = go.Figure(go.Bar(x=nc_wr['Nbin'].astype(str), y=nc_wr['WR'],
                            marker_color=C_TEAL,
                            text=nc_wr['WR'].round(1).astype(str)+'%',
                            textposition='outside'))
    fig3.update_layout(title='Win Rate by Competition Level (N_Cand)',
                       xaxis_title='No. of Candidates', yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    # Multi-factor: Incumbent × Education
    d['Incumbent'] = pd.to_numeric(d['Incumbent'], errors='coerce').fillna(0)
    inc_edu = d.groupby(['Incumbent','Education']).agg(T=('won','count'), W=('won','sum')).reset_index().dropna()
    inc_edu['WR'] = inc_edu['W'] / inc_edu['T'] * 100
    inc_edu = inc_edu[inc_edu['T'] >= 20]
    inc_edu['Inc_Label'] = inc_edu['Incumbent'].map({0:'Non-Inc', 1:'Incumbent'})
    fig4 = go.Figure()
    for il in inc_edu['Inc_Label'].unique():
        sub = inc_edu[inc_edu['Inc_Label'] == il]
        fig4.add_trace(go.Bar(name=il, x=sub['Education'], y=sub['WR']))
    fig4.update_layout(barmode='group', title='Win Rate: Incumbent × Education',
                       yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=120, l=60, r=10), height=380,
                       xaxis_tickangle=-30, legend=dict(orientation='h', y=-0.45))

    # Top combinations (State × Party) with high win rates
    sp = d.groupby(['State','Party']).agg(T=('won','count'), W=('won','sum')).reset_index()
    sp['WR'] = sp['W']/sp['T']*100
    sp = sp[(sp['T']>=20) & (sp['WR']>0)].sort_values('WR', ascending=False).head(15)
    sp['Label'] = sp['State'] + ' – ' + sp['Party']
    fig5 = go.Figure(go.Bar(
        x=sp['WR'], y=sp['Label'],
        orientation='h', marker_color=C_WIN,
        text=sp['WR'].round(1).astype(str)+'%',
        textposition='outside'
    ))
    fig5.update_layout(title='Top 15 State-Party Combos by Win Rate (min 20 candidates)',
                       xaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=200, r=60), height=420)

    # Contested vs win
    d2['ConBin'] = pd.cut(d2['Contested'], bins=[0,1,2,3,5,10,50],
                          labels=['1','2','3','4-5','6-10','10+'])
    con_wr = d2.groupby('ConBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
    con_wr['WR'] = con_wr['W'] / con_wr['T'] * 100
    fig6 = go.Figure(go.Scatter(x=con_wr['ConBin'].astype(str), y=con_wr['WR'],
                                mode='lines+markers', line=dict(color=C_BLUE, width=2),
                                marker=dict(size=8)))
    fig6.update_layout(title='Win Rate by No. of Times Contested',
                       xaxis_title='Times Contested', yaxis_title='Win Rate %',
                       paper_bgcolor='white', plot_bgcolor='white',
                       margin=dict(t=40, b=40, l=60, r=10), height=320)

    def card(fig, w=6):
        return dbc.Col(dcc.Graph(figure=fig, config={'displayModeBar': False}), width=w, className='mb-3')

    return html.Div([
        section_header("🏆 Win Predictors",
                       f"Multi-factor predictors and combinations – {total:,} candidates"),
        dbc.Row([card(fig1), card(fig2)]),
        dbc.Row([card(fig3), card(fig6)]),
        dbc.Row([card(fig4, 6), card(fig5, 6)]),
    ])


# ─────────────────────────────────────────────
# SECTION ROUTER
# ─────────────────────────────────────────────
SECTIONS = {
    'eda':       build_eda,
    'trends':    build_trends,
    'candidate': build_candidate,
    'party':     build_party,
    'impact':    build_impact,
    'edu_prof':  build_edu_prof,
    'crime_fin': build_crime_fin,
    'predict':   build_predict,
}


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
from dash import callback_context

@app.callback(
    Output('active-section', 'data'),
    [Input({'type': 'nav-btn', 'index': s}, 'n_clicks') for s in SECTIONS],
    prevent_initial_call=True
)
def update_active(*args):
    ctx = callback_context
    if not ctx.triggered:
        return 'eda'
    prop_id = ctx.triggered[0]['prop_id']
    import json
    try:
        key = json.loads(prop_id.split('.')[0])['index']
        return key
    except Exception:
        return 'eda'


@app.callback(
    Output('page-content', 'children'),
    Input('active-section', 'data'),
    Input('f-state', 'value'),
    Input('f-year',  'value'),
    Input('f-party', 'value'),
    Input('f-sex',   'value'),
)
def render_section(section, state, year, party, sex):
    d = apply_filters(state, year, party, sex)
    if len(d) < 5:
        return html.Div("⚠ Too few records for selected filters. Please broaden the selection.",
                        className='alert alert-warning')
    fn = SECTIONS.get(section or 'eda', build_eda)
    return fn(d)


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  Election Analysis Dashboard  –  MAIN")
    print("=" * 55)
    print(f"  Local:   http://127.0.0.1:8050")
    print(f"  Network: http://192.168.0.165:8050")
    print("=" * 55)
    app.run(host='0.0.0.0', port=8050, debug=False)
