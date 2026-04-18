#!/usr/bin/env python
"""
ELECTION ANALYTICS DASHBOARD - MOBILE RESPONSIVE
- Login / Register / Admin approval
- 11-tab sidebar (10 analytics + 1 admin panel)
- Global filters: State, Year, Constituency_Name, Constituency_Type
- Full mobile responsiveness with hamburger menu
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from src.auth import AuthDB

# ── Database ──────────────────────────────────────────────────────────────────
auth_db = AuthDB('auth.db')

# ── Load Data ─────────────────────────────────────────────────────────────────
print("[LOAD] Reading election data...")
try:
    df = pd.read_csv(r"raw data/election_data.csv", low_memory=False)
    for col in ['Votes', 'Age', 'Vote_Share_Percentage', 'Margin',
                'Margin_Percentage', 'No_Terms', 'Turnout_Percentage',
                'N_Cand', 'ENOP', 'Criminal Case', 'Total Assets', 'Liabilities']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['won'] = pd.to_numeric(df['won'], errors='coerce').fillna(0)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    print(f"[LOAD] Loaded {len(df)} records, {df['State'].nunique()} states")
except Exception as e:
    print(f"[ERROR] {e}")
    df = pd.DataFrame()

# ── xlsx fallback (corrupt cells in xlsx; use CSV for all analysis) ──────────
df_xlsx = df.copy()
print("[INFO] Deep analysis tabs powered by CSV data")

ALL_STATES = sorted(df['State'].dropna().unique().tolist())
ALL_YEARS  = sorted(df['Year'].dropna().unique().astype(int).tolist())
ALL_CTYPES = sorted(df['Constituency_Type'].dropna().unique().tolist()) if 'Constituency_Type' in df.columns else []
ALL_CNAMES = sorted(df['Constituency_Name'].dropna().unique().tolist()) if 'Constituency_Name' in df.columns else []

# ── App ───────────────────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

# Mobile-responsive CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {%favicon%}
        {%css%}
        <style>
            * {
                -webkit-tap-highlight-color: transparent;
                box-sizing: border-box;
            }
            body {
                margin: 0;
                padding: 0;
                overflow-x: hidden;
            }
            /* Mobile-first responsive design */
            @media (max-width: 768px) {
                .sidebar-nav { display: none !important; }
                .sidebar-nav.show { display: block !important; }
                .dashboard-body { flex-direction: column; }
                .filter-row { flex-wrap: wrap; }
                .filter-col { min-width: 100%; margin-bottom: 10px; }
                .chart-container { padding: 10px !important; }
                h1, h2, h3, h4, h5 { font-size: 1.1em !important; }
                input, button, select { font-size: 16px; padding: 12px; }
                .kpi-card { min-width: 100%; }
                .navbar { flex-wrap: wrap; }
                .topbar-title { font-size: 1em !important; }
                .logout-btn { width: 100%; margin-top: 5px; }
            }
            @media (max-width: 480px) {
                h1, h2 { font-size: 1em !important; }
                input, button { font-size: 16px; padding: 14px; }
                .sidebar-nav { width: 100% !important; position: absolute; 
                               top: 60px; left: 0; background: #1E2A38; 
                               z-index: 1000; border-radius: 0; }
                .chart-container { padding: 5px !important; }
            }
            .hamburger-btn {
                display: none;
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 10px 15px;
            }
            @media (max-width: 768px) {
                .hamburger-btn { display: block; }
            }
            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 999;
            }
            .sidebar-overlay.show { display: block; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

C = {
    'primary': '#2C3E50', 'accent':  '#3498DB', 'success': '#27AE60',
    'danger':  '#E74C3C', 'warning': '#E67E22', 'purple':  '#9B59B6',
    'teal':    '#1ABC9C', 'light':   '#F4F6F9', 'sidebar': '#1E2A38',
    'white':   '#FFFFFF',
}
PT = 'plotly_white'

TABS = [
    ('tab-overview',  '📊 Overview'),
    ('tab-state',     '🗺️ State Analysis'),
    ('tab-party',     '🏛️ Party Analysis'),
    ('tab-candidate', '👤 Candidate Profile'),
    ('tab-trends',    '📈 Year Trends'),
    ('tab-turnout',   '🗳️ Voter Turnout'),
    ('tab-winloss',   '🏆 Win / Loss'),
    ('tab-financial', '💰 Financial Profile'),
    ('tab-criminal',  '⚖️ Criminal Cases'),
    ('tab-incumbent', '🔄 Incumbent & Recontest'),
    ('tab-predictors','🎯 Win Predictors'),
    ('tab-evolution', '📍 Constituency Trends'),
    ('tab-insights',  '🔬 Deep Insights'),
    ('tab-admin',     '🛡️ Admin Panel'),
]

FIELD = {
    'width': '100%', 'padding': '14px 16px', 'fontSize': '15px',
    'border': '1.5px solid #CCC', 'borderRadius': '8px', 'outline': 'none',
    'marginBottom': '18px', 'boxSizing': 'border-box', 'height': '52px',
}
BTN = {
    'width': '100%', 'padding': '15px', 'fontSize': '15px',
    'fontWeight': '700', 'border': 'none', 'borderRadius': '8px',
    'cursor': 'pointer', 'letterSpacing': '1px',
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def apply_filters(states, years, cname, ctypes):
    d = df.copy()
    if states:
        d = d[d['State'].isin(states)]
    if years:
        d = d[d['Year'].isin(years)]
    if cname:
        d = d[d['Constituency_Name'] == cname]
    if ctypes:
        d = d[d['Constituency_Type'].isin(ctypes)]
    return d


def sec(text, badge=None):
    ch = [html.Span(text)]
    if badge:
        ch.append(html.Span(badge, style={
            'fontSize': '12px', 'marginLeft': '10px',
            'backgroundColor': C['accent'], 'color': 'white',
            'padding': '2px 8px', 'borderRadius': '12px', 'fontWeight': '600'}))
    return html.H5(ch, style={
        'color': C['primary'], 'fontWeight': '700',
        'borderBottom': f'2px solid {C["accent"]}',
        'paddingBottom': '8px', 'marginBottom': '20px', 'marginTop': '8px'})


def kpi(value, label, color):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H3(str(value), style={'color': color, 'fontWeight': '800',
                                    'margin': '0', 'fontSize': '1.9em'}),
        html.P(label, style={'color': '#666', 'margin': '4px 0 0',
                              'fontSize': '12px', 'textTransform': 'uppercase',
                              'letterSpacing': '0.5px'}),
    ]), style={'borderLeft': f'4px solid {color}', 'borderRadius': '8px',
               'height': '90px'}), xs=12, sm=6, md=3, className='mb-3')


def efig(msg='No data for selected filters'):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref='paper', yref='paper',
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=13, color='#999'))
    fig.update_layout(template=PT, height=300,
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


# ── Chart builders ────────────────────────────────────────────────────────────

def build_overview(d):
    total   = len(d)
    winners = int(d['won'].sum())
    win_pct = round(winners / total * 100, 1) if total else 0

    tp = (d[d['won'] == 1].groupby('Party').size()
          .sort_values(ascending=False).head(10).reset_index(name='Wins'))
    f1 = px.bar(tp, x='Party', y='Wins', color='Wins',
                color_continuous_scale='Blues', template=PT,
                title='Top 10 Parties by Wins') if len(tp) else efig()

    yr = d.groupby('Year').size().reset_index(name='Candidates')
    f2 = px.line(yr, x='Year', y='Candidates', markers=True, template=PT,
                 title='Candidates per Year',
                 color_discrete_sequence=[C['accent']]) if len(yr) > 1 else efig()

    sx = d['Sex'].value_counts().reset_index()
    sx.columns = ['Sex', 'Count']
    f3 = px.pie(sx, names='Sex', values='Count', hole=0.45, template=PT,
                title='Gender Split',
                color_discrete_sequence=[C['accent'], C['warning'], C['teal']]) if len(sx) else efig()

    wl = d['won'].value_counts().rename({0.0: 'Lost', 1.0: 'Won'})
    f4 = px.pie(values=wl.values, names=wl.index, hole=0.45,
                color_discrete_sequence=[C['success'], C['danger']],
                template=PT, title='Win / Loss Overall') if len(wl) else efig()

    for f in [f1, f2, f3, f4]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([
        sec('Overview', f'{total:,} records'),
        dbc.Row([kpi(f'{total:,}', 'Total Candidates', C['accent']),
                 kpi(f'{winners:,}', 'Total Winners', C['success']),
                 kpi(d['State'].nunique(), 'States', C['purple']),
                 kpi(d['Party'].nunique(), 'Parties', C['warning'])]),
        dbc.Row([kpi(f'{win_pct}%', 'Win Rate', C['danger']),
                 kpi(d['Year'].nunique(), 'Election Years', C['teal']),
                 kpi(d['Constituency_Name'].nunique(), 'Constituencies', C['primary']),
                 kpi(d['Candidate'].nunique() if 'Candidate' in d.columns else '-',
                     'Unique Candidates', C['sidebar'])]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                 dbc.Col(dcc.Graph(figure=f2), md=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                 dbc.Col(dcc.Graph(figure=f4), md=6)]),
    ])


def build_state(d):
    sw = (d[d['won'] == 1].groupby('State').size()
          .sort_values(ascending=False).reset_index(name='Winners'))
    f1 = px.bar(sw, x='Winners', y='State', orientation='h', color='Winners',
                color_continuous_scale='Teal', template=PT,
                title='Winners by State', height=400) if len(sw) else efig()
    f1.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=40))

    to = d.groupby('State')['Turnout_Percentage'].mean().dropna().sort_values(ascending=False).reset_index()
    f2 = px.bar(to, x='State', y='Turnout_Percentage', color='Turnout_Percentage',
                color_continuous_scale='Viridis', template=PT,
                title='Avg Voter Turnout by State') if len(to) else efig()
    f2.update_layout(xaxis_tickangle=-35, margin=dict(t=40, b=60))

    cs = d.groupby('State').size().sort_values(ascending=False).reset_index(name='Candidates')
    f3 = px.treemap(cs, path=['State'], values='Candidates', color='Candidates',
                    color_continuous_scale='Blues', template=PT,
                    title='Candidates by State') if len(cs) else efig()
    f3.update_layout(margin=dict(t=40))

    wr = d.groupby('State').agg(Total=('won', 'count'), Wins=('won', 'sum')).reset_index()
    wr['WinRate'] = round(wr['Wins'] / wr['Total'] * 100, 1)
    f4 = px.bar(wr.sort_values('WinRate', ascending=False), x='State', y='WinRate',
                color='WinRate', color_continuous_scale='RdYlGn', template=PT,
                title='Win Rate % by State') if len(wr) else efig()
    f4.update_layout(xaxis_tickangle=-35, margin=dict(t=40, b=60))

    return html.Div([sec('State Analysis'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)])])


def build_party(d):
    t15 = d['Party'].value_counts().head(15).reset_index()
    t15.columns = ['Party', 'Candidates']
    f1 = px.bar(t15, x='Candidates', y='Party', orientation='h', color='Candidates',
                color_continuous_scale='Blues', template=PT,
                title='Top 15 Parties by Candidates', height=450) if len(t15) else efig()
    f1.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=40))

    pw = d[d['won'] == 1]['Party'].value_counts().head(15).reset_index()
    pw.columns = ['Party', 'Wins']
    f2 = px.bar(pw, x='Wins', y='Party', orientation='h', color='Wins',
                color_continuous_scale='Greens', template=PT,
                title='Top 15 Parties by Wins', height=450) if len(pw) else efig()
    f2.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=40))

    pwr = d.groupby('Party').agg(Total=('won', 'count'), Wins=('won', 'sum')).reset_index()
    pwr = pwr[pwr['Total'] >= max(10, len(d) // 500)]
    pwr['WinRate'] = round(pwr['Wins'] / pwr['Total'] * 100, 1)
    f3 = px.bar(pwr.sort_values('WinRate', ascending=False).head(20),
                x='Party', y='WinRate', color='WinRate',
                color_continuous_scale='RdYlGn', template=PT,
                title='Win Rate % by Party') if len(pwr) else efig()
    f3.update_layout(xaxis_tickangle=-45, margin=dict(t=40, b=100))

    pt = d['Party_Type_TCPD'].value_counts().reset_index() if 'Party_Type_TCPD' in d.columns else pd.DataFrame()
    if len(pt):
        pt.columns = ['PartyType', 'Count']
        f4 = px.pie(pt, names='PartyType', values='Count', hole=0.4, template=PT,
                    title='Party Type Distribution')
    else:
        f4 = efig()
    f4.update_layout(margin=dict(t=40))

    return html.Div([sec('Party Analysis'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=8),
                              dbc.Col(dcc.Graph(figure=f4), md=4)])])


def build_candidate(d):
    a = d.dropna(subset=['Age']) if 'Age' in d.columns else pd.DataFrame()
    f1 = px.histogram(a, x='Age', nbins=40,
                      color_discrete_sequence=[C['accent']], template=PT,
                      title='Age Distribution') if len(a) else efig()
    f1.update_layout(margin=dict(t=40))

    f2 = px.box(d.dropna(subset=['Age', 'Sex']), x='Sex', y='Age', color='Sex',
                template=PT, title='Age by Gender',
                color_discrete_sequence=[C['accent'], C['warning']]) if len(a) else efig()
    f2.update_layout(margin=dict(t=40))

    gy = d.groupby(['Year', 'Sex']).size().reset_index(name='Count')
    f3 = px.bar(gy, x='Year', y='Count', color='Sex', barmode='stack',
                template=PT, title='Gender per Year') if len(gy) else efig()
    f3.update_layout(margin=dict(t=40))

    gw = d.groupby('Sex').agg(Total=('won', 'count'), Wins=('won', 'sum')).reset_index()
    gw['WinRate'] = round(gw['Wins'] / gw['Total'] * 100, 1)
    f4 = px.bar(gw, x='Sex', y='WinRate', color='Sex', text='WinRate',
                template=PT, title='Win Rate by Gender',
                color_discrete_sequence=[C['accent'], C['warning']]) if len(gw) else efig()
    f4.update_traces(texttemplate='%{text}%', textposition='outside')
    f4.update_layout(margin=dict(t=40))

    edu = d['MyNeta_education'].value_counts().head(12).reset_index() if 'MyNeta_education' in d.columns else pd.DataFrame()
    if len(edu):
        edu.columns = ['Education', 'Count']
        f5 = px.bar(edu, x='Count', y='Education', orientation='h', color='Count',
                    color_continuous_scale='Purples', template=PT,
                    title='Education Level', height=400)
        f5.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=40))
    else:
        f5 = efig()

    prof = d['TCPD_Prof_Main'].value_counts().head(12).reset_index() if 'TCPD_Prof_Main' in d.columns else pd.DataFrame()
    if len(prof):
        prof.columns = ['Profession', 'Count']
        f6 = px.bar(prof, x='Count', y='Profession', orientation='h', color='Count',
                    color_continuous_scale='Oranges', template=PT,
                    title='Candidate Profession', height=400)
        f6.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=40))
    else:
        f6 = efig()

    return html.Div([sec('Candidate Profile'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=6),
                              dbc.Col(dcc.Graph(figure=f6), md=6)])])


def build_trends(d):
    def ln(data, x, y, title, color):
        return px.line(data, x=x, y=y, markers=True, template=PT, title=title,
                       color_discrete_sequence=[color]) if len(data) > 1 else efig()

    yr = d.groupby('Year').size().reset_index(name='Candidates')
    f1 = px.area(yr, x='Year', y='Candidates', template=PT,
                 title='Candidates per Year',
                 color_discrete_sequence=[C['accent']]) if len(yr) > 1 else efig()

    yw = d[d['won'] == 1].groupby('Year').size().reset_index(name='Winners')
    f2 = px.bar(yw, x='Year', y='Winners', color='Winners',
                color_continuous_scale='Greens', template=PT,
                title='Winners per Year') if len(yw) else efig()

    ag = d.groupby('Year')['Age'].mean().dropna().reset_index()
    f3 = ln(ag, 'Year', 'Age', 'Avg Candidate Age over Years', C['purple'])

    mg = d.groupby('Year')['Margin'].mean().dropna().reset_index()
    f4 = ln(mg, 'Year', 'Margin', 'Avg Victory Margin over Years', C['warning'])

    pdy = d.groupby('Year')['Party'].nunique().reset_index(name='Parties')
    f5 = px.bar(pdy, x='Year', y='Parties', color='Parties',
                color_continuous_scale='Viridis', template=PT,
                title='Unique Parties per Year') if len(pdy) else efig()

    fem = d[d['Sex'] == 'F'].groupby('Year').size().reset_index(name='Female')
    f6 = px.area(fem, x='Year', y='Female', template=PT,
                 title='Female Candidates per Year',
                 color_discrete_sequence=[C['warning']]) if len(fem) > 1 else efig()

    for f in [f1, f2, f3, f4, f5, f6]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([sec('Election Year Trends'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=6),
                              dbc.Col(dcc.Graph(figure=f6), md=6)])])


def build_turnout(d):
    f1 = px.histogram(d.dropna(subset=['Turnout_Percentage']),
                      x='Turnout_Percentage', nbins=40,
                      color_discrete_sequence=[C['teal']], template=PT,
                      title='Turnout % Distribution') if d['Turnout_Percentage'].notna().any() else efig()

    ty = d.groupby('Year')['Turnout_Percentage'].mean().dropna().reset_index()
    f2 = px.line(ty, x='Year', y='Turnout_Percentage', markers=True, template=PT,
                 title='Avg Turnout % per Year',
                 color_discrete_sequence=[C['teal']]) if len(ty) > 1 else efig()

    s2 = d.dropna(subset=['Turnout_Percentage', 'Vote_Share_Percentage'])
    s2 = s2.sample(min(3000, len(s2)), random_state=42) if len(s2) else s2
    f3 = px.scatter(s2, x='Turnout_Percentage', y='Vote_Share_Percentage',
                    color='won', opacity=0.5, template=PT,
                    title='Turnout vs Vote Share',
                    color_discrete_map={0.0: C['danger'], 1.0: C['success']},
                    labels={'won': 'Won'}) if len(s2) else efig()

    ct = d.groupby('Constituency_Type')['Turnout_Percentage'].mean().dropna().reset_index() if 'Constituency_Type' in d.columns else pd.DataFrame()
    f4 = px.bar(ct, x='Constituency_Type', y='Turnout_Percentage', color='Turnout_Percentage',
                color_continuous_scale='Teal', template=PT,
                title='Avg Turnout by Constituency Type') if len(ct) else efig()

    top_s = d['State'].value_counts().head(8).index
    ts = d[d['State'].isin(top_s)].dropna(subset=['Turnout_Percentage'])
    f5 = px.box(ts, x='State', y='Turnout_Percentage', color='State', template=PT,
                title='Turnout Distribution by State') if len(ts) else efig()
    f5.update_layout(showlegend=False, xaxis_tickangle=-30)

    for f in [f1, f2, f3, f4, f5]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([sec('Voter Turnout Analysis'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=12)])])


def build_winloss(d):
    wins = d[d['won'] == 1].dropna(subset=['Margin'])
    f1 = px.histogram(wins, x='Margin', nbins=50,
                      color_discrete_sequence=[C['success']], template=PT,
                      title='Victory Margin Distribution') if len(wins) else efig()

    ms = wins.groupby('State')['Margin_Percentage'].mean().dropna().sort_values(ascending=False).reset_index()
    f2 = px.bar(ms, x='State', y='Margin_Percentage', color='Margin_Percentage',
                color_continuous_scale='RdYlGn', template=PT,
                title='Avg Victory Margin % by State') if len(ms) else efig()
    f2.update_layout(xaxis_tickangle=-35)

    f3 = px.box(d.dropna(subset=['Vote_Share_Percentage']),
                x='won', y='Vote_Share_Percentage', color='won', template=PT,
                title='Vote Share: Winners vs Losers',
                color_discrete_map={0.0: C['danger'], 1.0: C['success']},
                labels={'won': 'Result'}) if d['Vote_Share_Percentage'].notna().any() else efig()

    if 'Deposit_Lost' in d.columns:
        dl = d['Deposit_Lost'].value_counts().reset_index()
        dl.columns = ['Status', 'Count']
        f4 = px.pie(dl, names='Status', values='Count', hole=0.4, template=PT,
                    title='Deposit Lost') if len(dl) else efig()
    else:
        f4 = efig()

    nc = d.groupby('N_Cand').agg(WinRate=('won', 'mean')).reset_index().dropna()
    nc['WinRate'] = round(nc['WinRate'] * 100, 1)
    nc = nc[nc['N_Cand'] <= 30]
    f5 = px.scatter(nc, x='N_Cand', y='WinRate', size='WinRate', template=PT,
                    title='Win Rate vs # Candidates',
                    color_discrete_sequence=[C['accent']]) if len(nc) else efig()

    top10 = wins.nlargest(10, 'Margin')[['Candidate', 'Party', 'State', 'Year', 'Margin']] if len(wins) >= 10 else wins[['Candidate', 'Party', 'State', 'Year', 'Margin']] if len(wins) else pd.DataFrame()
    f6 = px.bar(top10, x='Margin', y='Candidate', orientation='h', color='Margin',
                color_continuous_scale='Greens', template=PT,
                title='Top 10 Biggest Margins',
                hover_data=['Party', 'State', 'Year']) if len(top10) else efig()
    f6.update_layout(yaxis={'categoryorder': 'total ascending'})

    for f in [f1, f2, f3, f4, f5, f6]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([sec('Win / Loss Analysis'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=6),
                              dbc.Col(dcc.Graph(figure=f6), md=6)])])


def build_financial(d):
    dff = d.dropna(subset=['Total Assets'])
    dff = dff[dff['Total Assets'] > 0].copy()
    dff['Assets_Cr'] = dff['Total Assets'] / 1e7

    f1 = px.histogram(dff, x='Assets_Cr', nbins=60, log_y=True,
                      color_discrete_sequence=[C['warning']], template=PT,
                      title='Assets Distribution (Crores, log)') if len(dff) else efig()

    f2 = px.box(dff[dff['Assets_Cr'] < 100], x='won', y='Assets_Cr', color='won',
                template=PT, title='Assets (Cr): Winners vs Losers',
                color_discrete_map={0.0: C['danger'], 1.0: C['success']},
                labels={'won': 'Result'}) if len(dff) else efig()

    pa = dff.groupby('Party')['Assets_Cr'].mean().sort_values(ascending=False).head(12).reset_index()
    f3 = px.bar(pa, x='Assets_Cr', y='Party', orientation='h', color='Assets_Cr',
                color_continuous_scale='Oranges', template=PT,
                title='Avg Assets (Cr) — Top 12 Parties', height=400) if len(pa) else efig()
    f3.update_layout(yaxis={'categoryorder': 'total ascending'})

    dfl = d.dropna(subset=['Liabilities'])
    dfl = dfl[dfl['Liabilities'] > 0].copy()
    dfl['Liab_Cr'] = dfl['Liabilities'] / 1e7
    f4 = px.histogram(dfl[dfl['Liab_Cr'] < 50], x='Liab_Cr', nbins=50,
                      color_discrete_sequence=[C['danger']], template=PT,
                      title='Liabilities Distribution (Crores)') if len(dfl) else efig()

    s = dff[dff['Assets_Cr'] < 200].dropna(subset=['Vote_Share_Percentage'])
    s = s.sample(min(2000, len(s)), random_state=1) if len(s) else s
    f5 = px.scatter(s, x='Assets_Cr', y='Vote_Share_Percentage', color='won',
                    opacity=0.5, template=PT, title='Assets vs Vote Share',
                    color_discrete_map={0.0: C['danger'], 1.0: C['success']},
                    labels={'won': 'Won'}) if len(s) else efig()

    sa = dff.groupby('State')['Assets_Cr'].mean().sort_values(ascending=False).reset_index()
    f6 = px.bar(sa, x='State', y='Assets_Cr', color='Assets_Cr',
                color_continuous_scale='YlOrBr', template=PT,
                title='Avg Assets (Cr) by State') if len(sa) else efig()
    f6.update_layout(xaxis_tickangle=-35)

    for f in [f1, f2, f3, f4, f5, f6]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([sec('Financial Profile'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=6),
                              dbc.Col(dcc.Graph(figure=f6), md=6)])])


def build_criminal(d):
    col = 'Criminal Case'
    if col not in d.columns:
        return html.Div([sec('Criminal Cases'), html.P('Column not available.')])
    dfc = d.dropna(subset=[col]).copy()
    dfc['Has_Case'] = dfc[col] > 0

    hc = dfc['Has_Case'].value_counts().rename({True: 'Has Cases', False: 'No Cases'})
    f1 = px.pie(values=hc.values, names=hc.index, hole=0.4,
                color_discrete_sequence=[C['danger'], C['success']], template=PT,
                title='Candidates with Criminal Cases') if len(hc) else efig()

    dfc['Cases_Bin'] = pd.cut(dfc[col], bins=[-1, 0, 1, 3, 5, 1000],
                               labels=['0', '1', '2-3', '4-5', '6+'])
    cb = dfc.groupby('Cases_Bin', observed=True).agg(
        Total=('won', 'count'), Wins=('won', 'sum')).reset_index()
    cb['WinRate'] = round(cb['Wins'] / cb['Total'] * 100, 1)
    f2 = px.bar(cb, x='Cases_Bin', y='WinRate', color='WinRate', text='WinRate',
                color_continuous_scale='RdYlGn', template=PT,
                title='Win Rate by # Criminal Cases') if len(cb) else efig()
    f2.update_traces(texttemplate='%{text}%', textposition='outside')

    pcc = dfc[dfc['Has_Case']].groupby('Party').size().sort_values(
        ascending=False).head(10).reset_index(name='WithCases')
    f3 = px.bar(pcc, x='WithCases', y='Party', orientation='h', color='WithCases',
                color_continuous_scale='Reds', template=PT,
                title='Top 10 Parties — Candidates with Cases', height=380) if len(pcc) else efig()
    f3.update_layout(yaxis={'categoryorder': 'total ascending'})

    st_c = dfc.groupby('State').agg(
        Total=('Has_Case', 'count'), Cases=('Has_Case', 'sum')).reset_index()
    st_c['CasePct'] = round(st_c['Cases'] / st_c['Total'] * 100, 1)
    f4 = px.bar(st_c.sort_values('CasePct', ascending=False),
                x='State', y='CasePct', color='CasePct',
                color_continuous_scale='Reds', template=PT,
                title='% Candidates with Cases by State') if len(st_c) else efig()
    f4.update_layout(xaxis_tickangle=-35)

    cy = dfc.groupby('Year').agg(
        Total=('Has_Case', 'count'), Cases=('Has_Case', 'sum')).reset_index()
    cy['CasePct'] = round(cy['Cases'] / cy['Total'] * 100, 1)
    f5 = px.line(cy, x='Year', y='CasePct', markers=True, template=PT,
                 title='% with Criminal Cases over Years',
                 color_discrete_sequence=[C['danger']]) if len(cy) > 1 else efig()

    for f in [f1, f2, f3, f4, f5]:
        f.update_layout(margin=dict(t=40, b=20))
    return html.Div([sec('Criminal Cases Analysis'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=4),
                              dbc.Col(dcc.Graph(figure=f2), md=8)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=12)])])


def build_incumbent(d):
    def wrbar(col, title):
        if col not in d.columns:
            return efig(f'{col} not available')
        g = d.groupby(col).agg(Total=('won', 'count'), Wins=('won', 'sum')).reset_index()
        g['WinRate'] = round(g['Wins'] / g['Total'] * 100, 1)
        f = px.bar(g, x=col, y='WinRate', color='WinRate', text='WinRate',
                   color_continuous_scale='RdYlGn', template=PT, title=title)
        f.update_traces(texttemplate='%{text}%', textposition='outside')
        f.update_layout(margin=dict(t=40))
        return f

    f1 = wrbar('Incumbent',         'Win Rate: Incumbent')
    f2 = wrbar('Recontest',         'Win Rate: Recontest')
    f3 = wrbar('Turncoat',          'Win Rate: Turncoat')
    f4 = wrbar('Same_Constituency', 'Win Rate: Same Constituency')

    nt = d['No_Terms'].dropna()
    f5 = px.histogram(nt[nt <= 10], x='No_Terms', nbins=10,
                      color_discrete_sequence=[C['purple']], template=PT,
                      title='Number of Terms Distribution') if len(nt) else efig()
    f5.update_layout(margin=dict(t=40))

    tw = d.groupby('No_Terms').agg(Total=('won', 'count'),
                                    Wins=('won', 'sum')).reset_index().dropna()
    tw['WinRate'] = round(tw['Wins'] / tw['Total'] * 100, 1)
    tw = tw[tw['No_Terms'] <= 10]
    f6 = px.line(tw, x='No_Terms', y='WinRate', markers=True, template=PT,
                 title='Win Rate by # Terms',
                 color_discrete_sequence=[C['purple']]) if len(tw) > 1 else efig()
    f6.update_layout(margin=dict(t=40))

    return html.Div([sec('Incumbent & Recontest'),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f1), md=6),
                              dbc.Col(dcc.Graph(figure=f2), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f3), md=6),
                              dbc.Col(dcc.Graph(figure=f4), md=6)]),
                     dbc.Row([dbc.Col(dcc.Graph(figure=f5), md=6),
                              dbc.Col(dcc.Graph(figure=f6), md=6)])])


def build_admin_panel(current_user):
    if not current_user or current_user.get('role') != 'admin':
        return html.Div([html.H5('Access Denied', style={'color': C['danger']}),
                         html.P('Only administrators can access this panel.')])

    pending   = auth_db.get_pending_users()
    all_users = auth_db.get_all_users()

    if pending:
        opts = [{'label': f"{u['username']} — {u['email']} (registered {(u.get('created_at') or '')[:10]})",
                 'value': u['id']} for u in pending]
        pend_block = dbc.Card(dbc.CardBody([
            html.H6(f'Pending Approvals ({len(pending)})',
                    style={'color': C['warning'], 'fontWeight': '700',
                           'marginBottom': '14px', 'fontSize': '15px'}),
            html.Label('Select User to Act On:',
                       style={'fontWeight': '600', 'marginBottom': '6px',
                              'display': 'block'}),
            dcc.Dropdown(id='admin-user-select', options=opts,
                         placeholder='Choose a pending user...',
                         style={'marginBottom': '14px', 'fontSize': '14px'}),
            dbc.Row([
                dbc.Col(html.Button('APPROVE ACCESS', id='btn-admin-approve',
                                    n_clicks=0,
                                    style={'width': '100%', 'padding': '11px',
                                           'backgroundColor': C['success'],
                                           'color': 'white', 'border': 'none',
                                           'borderRadius': '8px', 'fontWeight': '700',
                                           'cursor': 'pointer', 'fontSize': '14px'}), md=6),
                dbc.Col(html.Button('REJECT', id='btn-admin-reject', n_clicks=0,
                                    style={'width': '100%', 'padding': '11px',
                                           'backgroundColor': C['danger'],
                                           'color': 'white', 'border': 'none',
                                           'borderRadius': '8px', 'fontWeight': '700',
                                           'cursor': 'pointer', 'fontSize': '14px'}), md=6),
            ]),
            html.Div(id='admin-action-msg',
                     style={'marginTop': '12px', 'fontWeight': '600',
                            'textAlign': 'center', 'minHeight': '20px',
                            'fontSize': '14px'}),
        ]), style={'borderLeft': f'4px solid {C["warning"]}',
                   'marginBottom': '24px', 'borderRadius': '8px'})
    else:
        pend_block = html.Div([
            dbc.Alert('No pending registrations — all users have been reviewed.',
                      color='success', style={'marginBottom': '16px'}),
            # Hidden placeholders so callbacks always find these IDs
            dcc.Dropdown(id='admin-user-select', options=[],
                         style={'display': 'none'}),
            html.Button(id='btn-admin-approve', n_clicks=0,
                        style={'display': 'none'}),
            html.Button(id='btn-admin-reject', n_clicks=0,
                        style={'display': 'none'}),
            html.Div(id='admin-action-msg', style={'display': 'none'}),
        ])

    SC = {'approved': C['success'], 'pending': C['warning'], 'rejected': C['danger']}
    rows = []
    for i, u in enumerate(all_users):
        sc = SC.get(u['status'], '#888')
        rows.append(html.Tr([
            html.Td(u['id'],       style={'padding': '9px 12px'}),
            html.Td(u['username'], style={'padding': '9px 12px', 'fontWeight': '700'}),
            html.Td(u['email'],    style={'padding': '9px 12px'}),
            html.Td(u['role'],     style={'padding': '9px 12px'}),
            html.Td(html.Span(u['status'].upper(),
                              style={'backgroundColor': sc, 'color': 'white',
                                     'padding': '3px 10px', 'borderRadius': '12px',
                                     'fontSize': '11px', 'fontWeight': '700'}),
                    style={'padding': '9px 12px'}),
            html.Td((u.get('created_at') or '')[:16],
                    style={'padding': '9px 12px', 'fontSize': '12px', 'color': '#888'}),
            html.Td(u.get('approved_by') or '—',
                    style={'padding': '9px 12px', 'fontSize': '12px'}),
        ], style={'backgroundColor': 'white' if i % 2 == 0 else '#FAFAFA',
                  'borderBottom': '1px solid #EEE'}))

    table = html.Div(html.Table([
        html.Thead(html.Tr([
            html.Th(h, style={'padding': '10px 12px',
                               'backgroundColor': C['sidebar'],
                               'color': 'white', 'fontWeight': '600',
                               'fontSize': '13px', 'whiteSpace': 'nowrap'})
            for h in ['ID', 'Username', 'Email', 'Role',
                      'Status', 'Registered', 'Approved By']
        ])),
        html.Tbody(rows if rows else html.Tr(
            html.Td('No users registered yet.', colSpan=7,
                    style={'textAlign': 'center', 'padding': '20px', 'color': '#888'})
        ))
    ], style={'width': '100%', 'borderCollapse': 'collapse',
              'border': '1px solid #EEE'}),
        style={'overflowX': 'auto', 'borderRadius': '8px',
               'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'})

    return html.Div([
        sec('Admin Panel — User Management', f'{len(all_users)} users'),
        pend_block,
        html.H6('All Registered Users',
                style={'fontWeight': '700', 'color': C['primary'],
                       'marginBottom': '12px', 'marginTop': '8px'}),
        table,
    ])


# ── Deep Analysis: Win Predictors ────────────────────────────────────────────
def build_win_predictors(d):
    WC = '#27AE60'; LC = '#E74C3C'

    # Binary parameter win rates
    bin_cols = [('Incumbent','Incumbent'),('Recontest','Recontest'),
                ('Turncoat','Turncoat'),('Deposit_Lost','Deposit Lost'),
                ('Same_Constituency','Same Constituency'),('Same_Party','Same Party')]
    rows = []
    for col, label in bin_cols:
        if col not in d.columns: continue
        g = d.groupby(col).agg(T=('won','count'), W=('won','sum')).reset_index()
        g['WR'] = round(g['W']/g['T']*100,1)
        for _, r in g.iterrows():
            rows.append({'Parameter': label, 'Value': str(r[col]),
                         'WinRate': r['WR'], 'Count': r['T']})
    if rows:
        sdf = pd.DataFrame(rows)
        f_bin = px.bar(sdf, x='WinRate', y='Parameter', color='Value',
                       barmode='group', orientation='h', text='WinRate',
                       template=PT, title='Win Rate % by Key Binary Parameters',
                       height=400, hover_data=['Count'],
                       color_discrete_sequence=[WC, LC, C['accent'], C['warning'], C['purple']])
        f_bin.update_traces(texttemplate='%{text}%', textposition='outside')
        f_bin.update_layout(margin=dict(t=45,l=160))
    else:
        f_bin = efig()

    # Age group win rate
    da = d.dropna(subset=['Age']).copy()
    da['Age'] = pd.to_numeric(da['Age'], errors='coerce').dropna()
    da = da.dropna(subset=['Age'])
    if len(da) > 50:
        da['AgeGroup'] = pd.cut(da['Age'], bins=[0,30,40,50,60,70,120],
                                labels=['<30','30-40','40-50','50-60','60-70','70+'])
        ag = da.groupby('AgeGroup', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
        ag['WR'] = round(ag['W']/ag['T']*100,1)
        f_age = px.bar(ag, x='AgeGroup', y='WR', color='WR', text='WR',
                       color_continuous_scale='RdYlGn', template=PT,
                       title='Win Rate by Age Group')
        f_age.update_traces(texttemplate='%{text}%', textposition='outside')
        f_age.update_layout(margin=dict(t=40))
    else:
        f_age = efig()

    # Criminal cases
    if 'Criminal Case' in d.columns:
        dc = d.copy(); dc['Criminal Case'] = pd.to_numeric(dc['Criminal Case'], errors='coerce')
        dc = dc.dropna(subset=['Criminal Case'])
        dc['CaseBin'] = pd.cut(dc['Criminal Case'], bins=[-1,0,1,2,4,10000],
                               labels=['0','1','2','3-4','5+'])
        cg = dc.groupby('CaseBin', observed=True).agg(T=('won','count'), W=('won','sum')).reset_index()
        cg['WR'] = round(cg['W']/cg['T']*100,1)
        f_crim = px.bar(cg, x='CaseBin', y='WR', color='WR', text='WR',
                        color_continuous_scale='RdYlGn', template=PT,
                        title='Win Rate by Criminal Cases')
        f_crim.update_traces(texttemplate='%{text}%', textposition='outside')
        f_crim.update_layout(margin=dict(t=40))
    else:
        f_crim = efig()

    # Wealth quintiles
    if 'Total Assets' in d.columns:
        dw = d.copy(); dw['Total Assets'] = pd.to_numeric(dw['Total Assets'], errors='coerce')
        dw = dw[dw['Total Assets'] > 0].dropna(subset=['Total Assets'])
        dw['Assets_Cr'] = dw['Total Assets']/1e7
        dw['WBin'] = pd.qcut(dw['Assets_Cr'], q=5, duplicates='drop',
                              labels=['Very Low','Low','Medium','High','Very High'])
        wg = dw.groupby('WBin', observed=True).agg(T=('won','count'), W=('won','sum'),
                                                     Avg=('Assets_Cr','mean')).reset_index()
        wg['WR'] = round(wg['W']/wg['T']*100,1)
        f_wealth = px.bar(wg, x='WBin', y='WR', color='WR', text='WR',
                          color_continuous_scale='YlOrBr', template=PT,
                          title='Win Rate by Wealth Level (Asset Quintiles)',
                          hover_data=['Avg'])
        f_wealth.update_traces(texttemplate='%{text}%', textposition='outside')
        f_wealth.update_layout(margin=dict(t=40))
    else:
        f_wealth = efig()

    # No_Terms line
    if 'No_Terms' in d.columns:
        dn = d.copy(); dn['No_Terms'] = pd.to_numeric(dn['No_Terms'], errors='coerce')
        dn = dn[(dn['No_Terms'] >= 0) & (dn['No_Terms'] <= 10)].dropna(subset=['No_Terms'])
        ntg = dn.groupby('No_Terms').agg(T=('won','count'), W=('won','sum')).reset_index()
        ntg['WR'] = round(ntg['W']/ntg['T']*100,1)
        f_terms = go.Figure()
        f_terms.add_bar(x=ntg['No_Terms'], y=ntg['T'], name='Total', yaxis='y2',
                        opacity=0.3, marker_color=C['purple'])
        f_terms.add_scatter(x=ntg['No_Terms'], y=ntg['WR'], name='Win Rate %',
                            mode='lines+markers', line=dict(color=WC, width=3),
                            marker=dict(size=9))
        f_terms.update_layout(template=PT, title='Win Rate by No. of Terms Served',
                               yaxis=dict(title='Win Rate %'),
                               yaxis2=dict(overlaying='y', side='right', title='# Candidates'),
                               margin=dict(t=40), legend=dict(x=0.7, y=1))
    else:
        f_terms = efig()

    # Education
    if 'MyNeta_education' in d.columns:
        eg = d.groupby('MyNeta_education').agg(T=('won','count'), W=('won','sum')).reset_index()
        eg = eg[eg['T'] >= 15]; eg['WR'] = round(eg['W']/eg['T']*100,1)
        eg = eg.sort_values('WR')
        f_edu = px.bar(eg, x='WR', y='MyNeta_education', orientation='h', color='WR',
                       color_continuous_scale='RdYlGn', text='WR',
                       template=PT, title='Win Rate by Education', height=420)
        f_edu.update_traces(texttemplate='%{text}%', textposition='outside')
        f_edu.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=40,l=180))
    else:
        f_edu = efig()

    # Vote share histogram W vs L
    if 'Vote_Share_Percentage' in d.columns:
        dv = d.dropna(subset=['Vote_Share_Percentage']).copy()
        dv['Result'] = dv['won'].map({1.0:'Winner',0.0:'Loser'})
        f_vs = px.histogram(dv, x='Vote_Share_Percentage', color='Result',
                            barmode='overlay', nbins=50, opacity=0.7,
                            template=PT, title='Vote Share Distribution: Winners vs Losers',
                            color_discrete_map={'Winner':WC,'Loser':LC})
        f_vs.update_layout(margin=dict(t=40))
    else:
        f_vs = efig()

    # Party x State heatmap
    psw = d.groupby(['State','Party'])['won'].agg(['mean','count']).reset_index()
    psw.columns = ['State','Party','WR','Count']
    psw = psw[psw['Count'] >= 15]; psw['WR'] = round(psw['WR']*100,1)
    top_p = psw.groupby('Party')['Count'].sum().nlargest(12).index
    psw2 = psw[psw['Party'].isin(top_p)]
    if len(psw2) > 4:
        piv = psw2.pivot(index='Party', columns='State', values='WR').fillna(0)
        f_heat = px.imshow(piv, text_auto=True, color_continuous_scale='RdYlGn',
                           template=PT, aspect='auto',
                           title='Win Rate % — Top Parties × States')
        f_heat.update_layout(margin=dict(t=50,l=100))
    else:
        f_heat = efig()

    total = len(d)
    wins  = int(d['won'].sum())
    inc_wr = '-'
    if 'Incumbent' in d.columns:
        gi = d.groupby('Incumbent').agg(T=('won','count'), W=('won','sum')).reset_index()
        gi['WR'] = round(gi['W']/gi['T']*100,1)
        r1 = gi[gi['Incumbent']==1]
        inc_wr = f"{r1.iloc[0]['WR']}%" if len(r1) else '-'

    return html.Div([
        html.H4('🎯 What Parameters Drive WINNING?',
                style={'color':C['primary'],'fontWeight':'900','marginBottom':'4px'}),
        html.P(f'Analysing {total:,} election records from {d["State"].nunique()} states. '
               'Win Rate = % of candidates with that attribute who won seats.',
               style={'color':'#666','fontSize':'14px','marginBottom':'20px'}),
        dbc.Row([
            kpi(f'{wins:,}', 'Total Winners', C['success']),
            kpi(f'{round(wins/total*100,1)}%', 'Overall Win Rate', C['accent']),
            kpi(inc_wr, 'Incumbent Win Rate', C['purple']),
            kpi(f'{d["Party"].nunique()}', 'Parties Analysed', C['warning']),
        ]),
        sec('Binary Parameter Impact'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_bin), md=12)]),
        sec('Age & Vote Share Distribution'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_age), xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_vs),  xs=12, md=6)]),
        sec('Criminal Cases & Wealth Impact'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_crim),   xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_wealth), xs=12, md=6)]),
        sec('Experience (Terms) & Education'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_terms), xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_edu),   xs=12, md=6)]),
        sec('Party × State Win Rate Heatmap'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_heat), xs=12)]),
    ])


# ── Deep Analysis: Constituency Evolution ─────────────────────────────────────
def build_constituency_evolution(d):
    if 'Constituency_Name' not in d.columns or 'Year' not in d.columns:
        return html.Div(html.P('Required columns not found.'))

    winners = d[d['won'] == 1].copy()
    winners['Year'] = pd.to_numeric(winners['Year'], errors='coerce')

    # Terms per constituency
    tc = winners.groupby('Constituency_Name')['Year'].nunique()
    tc_df = tc.value_counts().reset_index()
    tc_df.columns = ['Terms','Constituencies']
    f_tc = px.bar(tc_df, x='Terms', y='Constituencies', color='Constituencies',
                  color_continuous_scale='Blues', text='Constituencies',
                  template=PT, title='Election Terms of Data per Constituency')
    f_tc.update_traces(textposition='outside')
    f_tc.update_layout(margin=dict(t=40))

    # Repeat winners
    if 'Candidate' in winners.columns:
        rep = winners.groupby(['Constituency_Name','Candidate'])['Year'].nunique()
        rep = rep[rep > 1].reset_index(name='TimesWon').sort_values('TimesWon', ascending=False)
        f_rep = px.bar(rep.head(20), x='TimesWon', y='Candidate', orientation='h',
                       color='TimesWon', color_continuous_scale='Greens',
                       template=PT, title='Top 20 Repeat Winners (Same Constituency)',
                       hover_data=['Constituency_Name'], height=500)
        f_rep.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=40))
    else:
        f_rep = efig()

    # Constituency swing
    years_s = sorted(winners['Year'].dropna().unique())
    swing_rows = []
    if len(years_s) >= 2:
        pivot = winners.pivot_table(index='Constituency_Name', columns='Year',
                                    values='Party', aggfunc='first')
        for i in range(len(years_s)-1):
            y1, y2 = years_s[i], years_s[i+1]
            if y1 in pivot.columns and y2 in pivot.columns:
                pair = pivot[[y1, y2]].dropna()
                swing_rows.append({'Transition': f"{int(y1)}→{int(y2)}",
                                   'Held': (pair[y1]==pair[y2]).sum(),
                                   'Swung': (pair[y1]!=pair[y2]).sum()})
    if swing_rows:
        sdf = pd.DataFrame(swing_rows)
        sm = sdf.melt(id_vars='Transition', value_vars=['Held','Swung'],
                      var_name='Result', value_name='Count')
        f_swing = px.bar(sm, x='Transition', y='Count', color='Result', barmode='group',
                         text='Count', template=PT,
                         title='Constituency: Party Hold vs Swing Between Elections',
                         color_discrete_map={'Held':C['success'],'Swung':C['danger']})
        f_swing.update_traces(textposition='outside')
        f_swing.update_layout(margin=dict(t=40))
    else:
        f_swing = efig('Need ≥ 2 election years')

    # Party diversity per constituency
    pdiv = winners.groupby('Constituency_Name').apply(
        lambda x: x['Party'].nunique() if 'Party' in x.columns else 0
    ).reset_index(name='UniqueParties')
    ph = pdiv['UniqueParties'].value_counts().reset_index()
    ph.columns = ['UniqueParties','Constituencies']
    f_pie = px.pie(ph, names='UniqueParties', values='Constituencies', hole=0.4,
                   template=PT,
                   title='Party Variety per Constituency (1 = same party always won)',
                   color_discrete_sequence=px.colors.qualitative.Set2)
    f_pie.update_layout(margin=dict(t=60))

    # Margin % trend
    if 'Margin_Percentage' in winners.columns:
        mg = winners.groupby('Year')['Margin_Percentage'].agg(['mean','median']).reset_index()
        mg.columns = ['Year','Mean%','Median%']
        f_mg = px.line(mg, x='Year', y=['Mean%','Median%'], markers=True,
                       template=PT, title='Victory Margin % Trend over Years',
                       color_discrete_sequence=[C['success'], C['accent']])
        f_mg.update_layout(margin=dict(t=40))
    else:
        f_mg = efig()

    # Incumbent win rate by year
    if 'Incumbent' in d.columns:
        inc_yr = d.groupby(['Year','Incumbent']).agg(T=('won','count'), W=('won','sum')).reset_index()
        inc_yr['WR'] = round(inc_yr['W']/inc_yr['T']*100,1)
        inc_yr['Incumbent'] = inc_yr['Incumbent'].astype(str)
        f_inc = px.line(inc_yr, x='Year', y='WR', color='Incumbent', markers=True,
                        template=PT, title='Incumbent vs Non-Incumbent Win Rate over Years',
                        color_discrete_sequence=[C['success'],C['danger'],C['accent']])
        f_inc.update_layout(margin=dict(t=40))
    else:
        f_inc = efig()

    # Winner vote share band by year
    if 'Vote_Share_Percentage' in winners.columns:
        vs = winners.groupby('Year')['Vote_Share_Percentage'].agg(['mean','min','max']).reset_index()
        vs.columns = ['Year','Avg','Min','Max']
        f_vs = go.Figure()
        f_vs.add_scatter(x=vs['Year'], y=vs['Max'], name='Max', mode='lines',
                         line=dict(color=C['success'], dash='dot'))
        f_vs.add_scatter(x=vs['Year'], y=vs['Avg'], name='Avg', mode='lines+markers',
                         line=dict(color=C['accent'], width=3), marker=dict(size=8))
        f_vs.add_scatter(x=vs['Year'], y=vs['Min'], name='Min', mode='lines',
                         line=dict(color=C['danger'], dash='dot'))
        f_vs.update_layout(template=PT, title='Winner Vote Share % — Min/Avg/Max by Year',
                           margin=dict(t=40))
    else:
        f_vs = efig()

    # Voter roll growth
    if 'Electors' in d.columns:
        top10 = d['Constituency_Name'].value_counts().head(8).index
        ec = d[d['Constituency_Name'].isin(top10)].groupby(
            ['Constituency_Name','Year'])['Electors'].max().reset_index()
        f_el = px.line(ec, x='Year', y='Electors', color='Constituency_Name',
                       markers=True, template=PT,
                       title='Voter Roll Growth — Top 8 Constituencies', height=380)
        f_el.update_layout(margin=dict(t=40), legend=dict(font=dict(size=10)))
    else:
        f_el = efig()

    return html.Div([
        html.H4('📍 Constituency Evolution — Multi-Term Tracking',
                style={'color':C['primary'],'fontWeight':'900','marginBottom':'4px'}),
        html.P('How constituencies, winners, parties and margins evolved across election cycles.',
               style={'color':'#666','fontSize':'14px','marginBottom':'20px'}),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_tc),    xs=12, md=4),
                 dbc.Col(dcc.Graph(figure=f_pie),   xs=12, md=4),
                 dbc.Col(dcc.Graph(figure=f_swing), xs=12, md=4)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_rep), xs=12, md=7),
                 dbc.Col(dcc.Graph(figure=f_mg),  xs=12, md=5)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_inc), xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_vs),  xs=12, md=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_el),  xs=12)]),
    ])


# ── Deep Analysis: Deep Insights (Winner DNA) ─────────────────────────────────
def build_deep_insights(d):
    WC = '#27AE60'; LC = '#E74C3C'
    winners = d[d['won'] == 1].copy()
    losers  = d[d['won'] == 0].copy()

    NUM_COLS = ['Age','Vote_Share_Percentage','Votes','Margin','Turnout_Percentage',
                'No_Terms','N_Cand','ENOP','Criminal Case','Total Assets','Liabilities']
    stats = []
    for col in NUM_COLS:
        if col not in d.columns: continue
        w = pd.to_numeric(winners[col], errors='coerce').dropna()
        l = pd.to_numeric(losers[col],  errors='coerce').dropna()
        if len(w) < 10 or len(l) < 10: continue
        stats.append({'Metric': col.replace('_',' '), 'W_Mean': round(w.mean(),2),
                      'L_Mean': round(l.mean(),2), 'Gap': round(w.mean()-l.mean(),2)})

    if stats:
        sdf = pd.DataFrame(stats).sort_values('Gap', key=abs, ascending=False)
        f_gap = px.bar(sdf, x='Gap', y='Metric', orientation='h', color='Gap',
                       color_continuous_scale='RdYlGn', text='Gap',
                       template=PT, title='Winner vs Loser Gap (Winner Mean − Loser Mean)',
                       height=400)
        f_gap.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        f_gap.update_layout(margin=dict(t=50,l=200))

        sm = sdf.melt(id_vars='Metric', value_vars=['W_Mean','L_Mean'],
                      var_name='Group', value_name='Value')
        sm['Group'] = sm['Group'].map({'W_Mean':'Winner','L_Mean':'Loser'})
        f_cmp = px.bar(sm, x='Value', y='Metric', color='Group', barmode='group',
                       orientation='h', template=PT,
                       title='Mean Values — Winners vs Losers',
                       color_discrete_map={'Winner':WC,'Loser':LC}, height=400)
        f_cmp.update_layout(margin=dict(t=50,l=200))
    else:
        f_gap = efig(); f_cmp = efig()

    # Scatter Age vs Vote Share
    sc1 = d.dropna(subset=['Age','Vote_Share_Percentage']).copy()
    sc1['Age'] = pd.to_numeric(sc1['Age'], errors='coerce')
    sc1 = sc1.dropna(subset=['Age']).sample(min(3000,len(sc1)), random_state=7)
    sc1['Result'] = sc1['won'].map({1.0:'Winner',0.0:'Loser'})
    f_sc1 = px.scatter(sc1, x='Age', y='Vote_Share_Percentage', color='Result',
                       opacity=0.45, template=PT,
                       title='Age vs Vote Share % — Winners vs Losers',
                       color_discrete_map={'Winner':WC,'Loser':LC})
    f_sc1.update_layout(margin=dict(t=40))

    # Scatter Assets vs Vote Share
    if 'Total Assets' in d.columns:
        sc2 = d.dropna(subset=['Total Assets','Vote_Share_Percentage']).copy()
        sc2['Total Assets'] = pd.to_numeric(sc2['Total Assets'], errors='coerce')
        sc2 = sc2[sc2['Total Assets'] > 0]
        sc2['Assets_Cr'] = sc2['Total Assets']/1e7
        sc2 = sc2[sc2['Assets_Cr'] < 500].sample(min(2500,len(sc2)), random_state=3)
        sc2['Result'] = sc2['won'].map({1.0:'Winner',0.0:'Loser'})
        f_sc2 = px.scatter(sc2, x='Assets_Cr', y='Vote_Share_Percentage', color='Result',
                           opacity=0.45, template=PT,
                           title='Wealth (Cr) vs Vote Share — Winners vs Losers',
                           color_discrete_map={'Winner':WC,'Loser':LC})
        f_sc2.update_layout(margin=dict(t=40))
    else:
        f_sc2 = efig()

    # Violin by gender
    dv = d.dropna(subset=['Vote_Share_Percentage','Sex']).copy()
    dv['Result'] = dv['won'].map({1.0:'Winner',0.0:'Loser'})
    f_vio = px.violin(dv, x='Sex', y='Vote_Share_Percentage', color='Result',
                      box=True, template=PT,
                      title='Vote Share by Gender & Result',
                      color_discrete_map={'Winner':WC,'Loser':LC})
    f_vio.update_layout(margin=dict(t=40))

    # Box: No_Terms vs Vote Share
    if 'No_Terms' in d.columns:
        dn = d.copy(); dn['No_Terms'] = pd.to_numeric(dn['No_Terms'], errors='coerce')
        dn = dn[(dn['No_Terms'] >= 0) & (dn['No_Terms'] <= 8)].dropna()
        dn['Result'] = dn['won'].map({1.0:'Winner',0.0:'Loser'})
        f_nt = px.box(dn, x='No_Terms', y='Vote_Share_Percentage', color='Result',
                      template=PT, title='Vote Share by Terms Served & Result',
                      color_discrete_map={'Winner':WC,'Loser':LC})
        f_nt.update_layout(margin=dict(t=40))
    else:
        f_nt = efig()

    # KPI cards
    avg_wvs  = round(winners['Vote_Share_Percentage'].mean(),1) if 'Vote_Share_Percentage' in winners.columns else '-'
    avg_lvs  = round(losers['Vote_Share_Percentage'].mean(),1)  if 'Vote_Share_Percentage' in losers.columns  else '-'
    avg_wage = round(winners['Age'].mean(),1) if 'Age' in winners.columns else '-'
    avg_lage = round(losers['Age'].mean(),1)  if 'Age' in losers.columns  else '-'
    inc_wr = '-'
    if 'Incumbent' in d.columns:
        gi = d.groupby('Incumbent').agg(T=('won','count'), W=('won','sum')).reset_index()
        gi['WR'] = round(gi['W']/gi['T']*100,1)
        r1 = gi[gi['Incumbent']==1]
        inc_wr = f"{r1.iloc[0]['WR']}%" if len(r1) else '-'

    return html.Div([
        html.H4('🔬 Deep Insights — Winner DNA vs Loser Profile',
                style={'color':C['primary'],'fontWeight':'900','marginBottom':'4px'}),
        html.P('Multi-dimensional statistical comparison between winning and losing candidates.',
               style={'color':'#666','fontSize':'14px','marginBottom':'20px'}),
        dbc.Row([
            kpi(f'{avg_wvs}%',  'Avg Winner Vote Share', C['success']),
            kpi(f'{avg_lvs}%',  'Avg Loser Vote Share',  C['danger']),
            kpi(f'{avg_wage}',  'Avg Winner Age',        C['accent']),
            kpi(f'{avg_lage}',  'Avg Loser Age',         C['warning']),
        ]),
        dbc.Row([
            kpi(inc_wr,             'Incumbent Win Rate',  C['purple']),
            kpi(f'{len(winners):,}','Total Winners',       C['success']),
            kpi(f'{len(losers):,}', 'Total Losers',        C['danger']),
            kpi(f'{len(d):,}',      'Total Records',       C['teal']),
        ]),
        sec('Key Parameter Gap: Winner Mean − Loser Mean'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_gap), xs=12)]),
        sec('Side-by-Side Mean Comparison'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_cmp), xs=12)]),
        sec('Multi-dimensional Scatter Analysis'),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_sc1), xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_sc2), xs=12, md=6)]),
        dbc.Row([dbc.Col(dcc.Graph(figure=f_vio), xs=12, md=6),
                 dbc.Col(dcc.Graph(figure=f_nt),  xs=12, md=6)]),
    ])


# ── Filter bar (mobile-responsive) ────────────────────────────────────────────
def filter_bar():
    ds = {'fontSize': '13px', 'borderRadius': '6px', 'width': '100%'}
    lbl = {'fontSize': '11px', 'fontWeight': '700', 'color': '#8AABB8',
           'letterSpacing': '1px', 'marginBottom': '4px', 'display': 'block'}
    return html.Div([
        dbc.Row([
            dbc.Col([html.Label('STATE', style=lbl),
                     dcc.Dropdown(id='filter-state',
                                  options=[{'label': s, 'value': s}
                                           for s in ALL_STATES],
                                  multi=True, placeholder='All States',
                                  style=ds, clearable=True)],
                    xs=12, sm=6, md=3, className='mb-2 mb-md-0'),
            dbc.Col([html.Label('YEAR', style=lbl),
                     dcc.Dropdown(id='filter-year',
                                  options=[{'label': str(y), 'value': y}
                                           for y in ALL_YEARS],
                                  multi=True, placeholder='All Years',
                                  style=ds, clearable=True)],
                    xs=12, sm=6, md=2, className='mb-2 mb-md-0'),
            dbc.Col([html.Label('CONSTITUENCY', style=lbl),
                     dcc.Dropdown(id='filter-const-name',
                                  options=[{'label': c, 'value': c}
                                           for c in ALL_CNAMES],
                                  placeholder='All Constituencies',
                                  style=ds, clearable=True, searchable=True)],
                    xs=12, sm=6, md=4, className='mb-2 mb-md-0'),
            dbc.Col([html.Label('TYPE', style=lbl),
                     dcc.Dropdown(id='filter-const-type',
                                  options=[{'label': t, 'value': t}
                                           for t in ALL_CTYPES],
                                  multi=True, placeholder='All Types',
                                  style=ds, clearable=True)],
                    xs=12, sm=6, md=2, className='mb-2 mb-md-0'),
            dbc.Col([html.Label('\u00A0',
                                style={**lbl, 'color': 'transparent'}),
                     html.Button('RESET', id='btn-reset-filters',
                                 n_clicks=0,
                                 style={'width': '100%', 'padding': '7px',
                                        'backgroundColor': '#445566',
                                        'color': 'white', 'border': 'none',
                                        'borderRadius': '6px',
                                        'fontWeight': '700',
                                        'fontSize': '12px',
                                        'cursor': 'pointer'})],
                    xs=12, sm=12, md=1, className='mb-2 mb-md-0'),
        ], className='g-2'),
    ], style={'backgroundColor': '#253545', 'padding': '12px 8px',
              'borderBottom': '1px solid #1a2535', 'overflowX': 'auto'})



# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='session-store', data=None),
    dcc.Store(id='active-tab',    data='tab-overview'),
    dcc.Store(id='admin-refresh', data=0),

    # LOGIN
    html.Div(id='page-login', children=[
        html.Div([
            html.H1('ELECTION ANALYTICS',
                    style={'textAlign': 'center', 'color': C['primary'],
                           'fontWeight': '900', 'fontSize': '2.6em',
                           'marginBottom': '8px'}),
            html.P('Secure Authentication Portal',
                   style={'textAlign': 'center', 'color': '#888',
                          'marginBottom': '36px', 'fontSize': '15px'}),
            dbc.Card([dbc.CardBody([
                html.Label('Username', style={'fontWeight': '700', 'fontSize': '14px',
                                              'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='login-username', type='text', value='',
                          placeholder='Enter your username',
                          debounce=False, style=FIELD),
                html.Label('Password', style={'fontWeight': '700', 'fontSize': '14px',
                                              'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='login-password', type='password', value='',
                          placeholder='Enter your password',
                          debounce=False, style=FIELD),
                html.Div(id='login-error',
                         style={'color': C['danger'], 'fontWeight': '600',
                                'marginBottom': '14px', 'minHeight': '22px',
                                'textAlign': 'center', 'fontSize': '14px'}),
                html.Button('LOGIN', id='btn-login', n_clicks=0,
                            style={**BTN, 'backgroundColor': C['accent'],
                                   'color': 'white', 'marginBottom': '20px'}),
                html.Hr(style={'margin': '10px 0 18px'}),
                html.P('New user? Create an account',
                       style={'textAlign': 'center', 'color': '#888',
                              'marginBottom': '14px', 'fontSize': '14px'}),
                html.Button('REGISTER', id='btn-goto-register', n_clicks=0,
                            style={**BTN, 'backgroundColor': C['warning'],
                                   'color': 'white'}),
            ])], style={'boxShadow': '0 6px 24px rgba(0,0,0,0.10)',
                        'borderRadius': '12px'}),
        ], style={'maxWidth': '480px', 'margin': '80px auto', 'padding': '0 20px'}),
    ], style={'display': 'block', 'backgroundColor': C['light'], 'minHeight': '100vh'}),

    # REGISTER
    html.Div(id='page-register', children=[
        html.Div([
            html.H1('ELECTION ANALYTICS',
                    style={'textAlign': 'center', 'color': C['primary'],
                           'fontWeight': '900', 'fontSize': '2.6em',
                           'marginBottom': '8px'}),
            html.P('Create New Account',
                   style={'textAlign': 'center', 'color': '#888',
                          'marginBottom': '36px', 'fontSize': '15px'}),
            dbc.Card([dbc.CardBody([
                html.Label('Username', style={'fontWeight': '700', 'fontSize': '14px',
                                              'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='reg-username', type='text', value='',
                          placeholder='Choose a username',
                          debounce=False, style=FIELD),
                html.Label('Email', style={'fontWeight': '700', 'fontSize': '14px',
                                           'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='reg-email', type='email', value='',
                          placeholder='your@email.com',
                          debounce=False, style=FIELD),
                html.Label('Password (min 8 chars)',
                           style={'fontWeight': '700', 'fontSize': '14px',
                                  'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='reg-password', type='password', value='',
                          placeholder='Choose a strong password',
                          debounce=False, style=FIELD),
                html.Label('Confirm Password',
                           style={'fontWeight': '700', 'fontSize': '14px',
                                  'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(id='reg-password2', type='password', value='',
                          placeholder='Repeat your password',
                          debounce=False, style=FIELD),
                html.Div(id='register-msg',
                         style={'fontWeight': '600', 'marginBottom': '14px',
                                'minHeight': '22px', 'textAlign': 'center',
                                'fontSize': '14px'}),
                html.Button('CREATE ACCOUNT', id='btn-register', n_clicks=0,
                            style={**BTN, 'backgroundColor': C['success'],
                                   'color': 'white', 'marginBottom': '16px'}),
                html.Hr(style={'margin': '10px 0 18px'}),
                html.Button('BACK TO LOGIN', id='btn-goto-login', n_clicks=0,
                            style={**BTN, 'backgroundColor': '#888',
                                   'color': 'white'}),
            ])], style={'boxShadow': '0 6px 24px rgba(0,0,0,0.10)',
                        'borderRadius': '12px'}),
        ], style={'maxWidth': '480px', 'margin': '60px auto', 'padding': '0 20px'}),
    ], style={'display': 'none', 'backgroundColor': C['light'], 'minHeight': '100vh'}),

    # DASHBOARD
    html.Div(id='page-dashboard', children=[
        # Mobile sidebar overlay
        html.Div(id='sidebar-overlay', className='sidebar-overlay',
                 style={'display': 'none'}),

        # Topbar with hamburger
        html.Div([
            html.Button('☰', id='hamburger-btn', n_clicks=0,
                        style={'display': 'none', 'background': 'none',
                               'border': 'none', 'color': 'white',
                               'fontSize': '24px', 'cursor': 'pointer',
                               'padding': '10px 15px'}),
            html.H3('ELECTION ANALYTICS DASHBOARD',
                    style={'color': 'white', 'margin': '0',
                           'fontWeight': '800', 'fontSize': '1.15em',
                           'flex': '1', 'minWidth': '0'}),
            html.Span(id='dash-welcome',
                      style={'color': '#9BBBD4', 'marginRight': '10px',
                             'fontSize': '13px', 'whiteSpace': 'nowrap'}),
            html.Button('LOGOUT', id='btn-logout', n_clicks=0,
                        style={'padding': '7px 15px', 'fontWeight': '700',
                               'backgroundColor': C['danger'],
                               'color': 'white', 'border': 'none',
                               'borderRadius': '6px', 'cursor': 'pointer',
                               'fontSize': '13px'}),
        ], style={'backgroundColor': C['sidebar'], 'padding': '14px 8px',
                  'display': 'flex', 'alignItems': 'center',
                  'boxShadow': '0 2px 8px rgba(0,0,0,0.4)',
                  'flexWrap': 'wrap', 'gap': '10px'}),

        # Filter bar
        filter_bar(),

        # Body
        html.Div([
            # Sidebar nav (collapsible on mobile)
            html.Div([
                html.Div('NAVIGATION',
                         style={'color': '#5A7A8A', 'fontSize': '10px',
                                'fontWeight': '700',
                                'padding': '14px 14px 8px',
                                'letterSpacing': '2px'}),
                html.Div(id='sidebar-nav'),
            ], id='sidebar-container', className='sidebar-nav',
              style={'width': '200px', 'minWidth': '200px',
                     'backgroundColor': C['sidebar'],
                     'minHeight': 'calc(100vh - 110px)',
                     'overflowY': 'auto', 'flexShrink': '0'}),
            # Content pane
            html.Div(id='dash-content',
                     style={'flex': '1', 'padding': '24px 15px',
                            'overflowY': 'auto', 'backgroundColor': C['light'],
                            'minHeight': 'calc(100vh - 110px)',
                            'maxWidth': '100%'}),
        ], className='dashboard-body',
           style={'display': 'flex', 'flexDirection': 'row'}),

        # Hidden nav buttons (always in DOM for callback safety)
        html.Div([html.Button(id=f'nav-{tid}', n_clicks=0,
                              style={'display': 'none'}) for tid, _ in TABS],
                 style={'display': 'none'}),
    ], style={'display': 'none'}),

], style={'fontFamily': 'Segoe UI, Arial, sans-serif'})


# ── CB 0: Mobile hamburger menu ───────────────────────────────────────────────
@app.callback(
    Output('sidebar-container', 'className'),
    Output('sidebar-overlay', 'className'),
    Input('hamburger-btn', 'n_clicks'),
    Input('sidebar-overlay', 'n_clicks'),
    State('sidebar-container', 'className'),
    prevent_initial_call=True,
)
def toggle_mobile_menu(hm_clicks, overlay_clicks, current_class):
    ctx = callback_context
    if not ctx.triggered:
        return current_class or 'sidebar-nav', ''
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    is_open = 'show' in (current_class or '')
    if trigger == 'hamburger-btn':
        new_class = 'sidebar-nav' if is_open else 'sidebar-nav show'
        overlay_class = '' if is_open else 'sidebar-overlay show'
        return new_class, overlay_class
    if trigger == 'sidebar-overlay':
        return 'sidebar-nav', ''
    return current_class or 'sidebar-nav', ''



@app.callback(
    Output('page-login',    'style'),
    Output('page-register', 'style'),
    Output('page-dashboard','style'),
    Output('login-error',   'children'),
    Output('register-msg',  'children'),
    Output('register-msg',  'style'),
    Output('dash-welcome',  'children'),
    Output('session-store', 'data'),
    Output('login-username','value'),
    Output('login-password','value'),
    Output('sidebar-nav',   'children'),

    Input('btn-login',         'n_clicks'),
    Input('btn-goto-register', 'n_clicks'),
    Input('btn-register',      'n_clicks'),
    Input('btn-goto-login',    'n_clicks'),
    Input('btn-logout',        'n_clicks'),

    State('login-username', 'value'),
    State('login-password', 'value'),
    State('reg-username',   'value'),
    State('reg-email',      'value'),
    State('reg-password',   'value'),
    State('reg-password2',  'value'),
    State('session-store',  'data'),
    prevent_initial_call=True,
)
def handle_auth(ln, grn, rn, gln, lon,
                lu, lp, ru, re, rp, rp2, session):
    BG   = {'backgroundColor': C['light'], 'minHeight': '100vh'}
    HIDE = {'display': 'none'}
    SL   = {**BG, 'display': 'block'}
    SR   = {**BG, 'display': 'block'}
    SD   = {'display': 'block'}
    ES   = {'fontWeight': '600', 'marginBottom': '14px', 'minHeight': '22px',
            'textAlign': 'center', 'fontSize': '14px', 'color': C['danger']}
    OS   = {**ES, 'color': C['success']}

    t = callback_context.triggered[0]['prop_id'].split('.')[0]

    def nav_buttons(role='user'):
        btns = []
        for tid, label in TABS:
            if tid == 'tab-admin' and role != 'admin':
                continue
            btns.append(html.Button(
                label, id=f'nav-{tid}', n_clicks=0,
                style={'display': 'block', 'width': '100%',
                       'padding': '11px 14px', 'marginBottom': '3px',
                       'border': 'none', 'borderRadius': '6px',
                       'textAlign': 'left', 'cursor': 'pointer',
                       'fontSize': '13px', 'fontWeight': '600',
                       'backgroundColor': 'transparent', 'color': 'white',
                       'transition': 'background 0.15s'}))
        return btns

    if t == 'btn-goto-register':
        return HIDE, SR, HIDE, '', '', ES, '', session, '', '', []
    if t in ('btn-goto-login', 'btn-logout'):
        return SL, HIDE, HIDE, '', '', ES, '', None, '', '', []
    if t == 'btn-login':
        u = (lu or '').strip()
        p = (lp or '').strip()
        if not u or not p:
            return SL, HIDE, HIDE, 'Please enter username and password.', '', ES, '', None, u, '', []
        user, error = auth_db.authenticate(u, p)
        if user:
            return HIDE, HIDE, SD, '', '', ES, f'Welcome, {user["username"]}', user, '', '', nav_buttons(user['role'])
        return SL, HIDE, HIDE, error or 'Invalid credentials.', '', ES, '', None, u, '', []
    if t == 'btn-register':
        u  = (ru  or '').strip()
        e  = (re  or '').strip()
        p1 = (rp  or '').strip()
        p2 = (rp2 or '').strip()
        if not all([u, e, p1, p2]):
            return HIDE, SR, HIDE, '', 'All fields are required.', ES, '', None, '', '', []
        if p1 != p2:
            return HIDE, SR, HIDE, '', 'Passwords do not match.', ES, '', None, '', '', []
        if len(p1) < 8:
            return HIDE, SR, HIDE, '', 'Password must be at least 8 characters.', ES, '', None, '', '', []
        result = auth_db.create_user(u, e, p1)
        if result.get('success'):
            return HIDE, SR, HIDE, '', 'Account created! Awaiting admin approval.', OS, '', None, '', '', []
        return HIDE, SR, HIDE, '', result.get('error', 'Registration failed.'), ES, '', None, '', '', []
    return SL, HIDE, HIDE, '', '', ES, '', None, '', '', []


# ── CB 2: Content (tab + filters) ────────────────────────────────────────────
@app.callback(
    Output('dash-content', 'children'),
    Output('active-tab',   'data'),
    [Input(f'nav-{tid}', 'n_clicks') for tid, _ in TABS],
    Input('filter-state',      'value'),
    Input('filter-year',       'value'),
    Input('filter-const-name', 'value'),
    Input('filter-const-type', 'value'),
    Input('admin-refresh',     'data'),
    State('active-tab',    'data'),
    State('session-store', 'data'),
    prevent_initial_call=False,
)
def update_content(*args):
    nt       = len(TABS)
    f_state  = args[nt]
    f_year   = args[nt + 1]
    f_cname  = args[nt + 2]
    f_ctype  = args[nt + 3]
    active   = args[nt + 5] or 'tab-overview'
    session  = args[nt + 6]

    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'] != '.':
        prop = ctx.triggered[0]['prop_id'].split('.')[0]
        if prop.startswith('nav-'):
            active = prop.replace('nav-', '')

    if active == 'tab-admin':
        return build_admin_panel(session), active

    # For evolution tab use xlsx which has all 4 election cycles
    if active == 'tab-evolution':
        d_src = df_xlsx.copy()
        if f_state and 'State' in d_src.columns:
            d_src = d_src[d_src['State'].isin(f_state)]
        return build_constituency_evolution(d_src), active

    d = apply_filters(
        f_state or [],
        [int(y) for y in (f_year or [])],
        f_cname,
        f_ctype or [],
    )
    if len(d) == 0:
        return html.Div(html.H4('No data matches the selected filters.',
                                style={'color': '#999', 'textAlign': 'center',
                                       'marginTop': '80px'})), active

    BUILDERS = {
        'tab-overview':  build_overview,
        'tab-state':     build_state,
        'tab-party':     build_party,
        'tab-candidate': build_candidate,
        'tab-trends':    build_trends,
        'tab-turnout':   build_turnout,
        'tab-winloss':   build_winloss,
        'tab-financial': build_financial,
        'tab-criminal':  build_criminal,
        'tab-incumbent':  build_incumbent,
        'tab-predictors': build_win_predictors,
        'tab-evolution':  build_constituency_evolution,
        'tab-insights':   build_deep_insights,
    }
    return BUILDERS.get(active, build_overview)(d), active


# ── CB 3: Reset filters ───────────────────────────────────────────────────────
@app.callback(
    Output('filter-state',      'value'),
    Output('filter-year',       'value'),
    Output('filter-const-name', 'value'),
    Output('filter-const-type', 'value'),
    Input('btn-reset-filters',  'n_clicks'),
    prevent_initial_call=True,
)
def reset_filters(_):
    return None, None, None, None


# ── CB 4: Admin approve / reject ──────────────────────────────────────────────
@app.callback(
    Output('admin-refresh',    'data'),
    Output('admin-action-msg', 'children'),
    Output('admin-action-msg', 'style'),
    Input('btn-admin-approve', 'n_clicks'),
    Input('btn-admin-reject',  'n_clicks'),
    State('admin-user-select', 'value'),
    State('session-store',     'data'),
    State('admin-refresh',     'data'),
    prevent_initial_call=True,
)
def admin_action(ap, rj, uid, session, rc):
    OK  = {'marginTop': '12px', 'fontWeight': '700', 'textAlign': 'center',
           'fontSize': '14px', 'color': C['success']}
    ERR = {**OK, 'color': C['danger']}
    t   = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not uid:
        return rc, 'Please select a user first.', ERR
    if not session or session.get('role') != 'admin':
        return rc, 'Access denied.', ERR
    admin = session.get('username', 'admin')
    if t == 'btn-admin-approve':
        auth_db.approve_user(uid, admin)
        return (rc or 0) + 1, 'User approved — they can now log in!', OK
    if t == 'btn-admin-reject':
        auth_db.reject_user(uid, admin)
        return (rc or 0) + 1, 'User has been rejected.', ERR
    return rc, '', OK


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  ELECTION ANALYTICS DASHBOARD")
    print("  http://127.0.0.1:8050")
    print("  http://192.168.0.165:8050")
    print("  Login: admin / admin1432")
    print("=" * 60)
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)
