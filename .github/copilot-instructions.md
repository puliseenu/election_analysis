# Copilot Instructions – Election Analytics Dashboard

## Project Overview
A single-page Plotly Dash application analysing 31,365 Indian state-election records across 5 states (53+ columns). It includes authentication, 13 analytics tabs, and full mobile responsiveness.

## Architecture

```
app.py              ← Single-file Dash app (~1668 lines); all layout + callbacks live here
src/auth.py         ← AuthDB class: SQLite user management, PBKDF2-SHA256 hashing
raw data/
  election_data.csv ← Primary data source (always use CSV, not xlsx)
auth.db             ← Auto-created SQLite DB at startup (gitignored)
assets/             ← Static CSS/JS served automatically by Dash
```

- **`app.py`** is the monolith: data loading, layout, CSS-in-`index_string`, and all `@app.callback` definitions.
- `server = app.server` exposes the underlying Flask server for gunicorn/WSGI deployment.
- The `_archived/` folder contains superseded dashboard iterations—do not import from it.

## Data Loading Convention
Data is always loaded from `raw data/election_data.csv` at module level. Numeric coercion happens immediately after load:
```python
df[col] = pd.to_numeric(df[col], errors='coerce')
df['won'] = pd.to_numeric(df['won'], errors='coerce').fillna(0)
```
All analytics callbacks filter this global `df` DataFrame; never reload from disk inside a callback.

## Authentication Flow
1. `AuthDB('auth.db')` is instantiated at module start; creates DB + default admin on first run.
2. Default credentials: **admin / admin1432**
3. New users register → status `'pending'` → admin approves → status `'approved'`.
4. Roles: `'admin'` or `'user'`. Admin panel tab is only shown to admins.
5. Sessions are tracked via a hidden `dcc.Store` (`id='session-store'`) in the Dash layout.

## Key Patterns

### Callback structure
All callbacks use `callback_context` to determine which input triggered them. Global filter dropdowns (`state-filter`, `year-filter`, `constituency-filter`, `ctype-filter`) feed into every analytics tab callback.

### Mobile responsiveness
Custom CSS lives inside `app.index_string`. Breakpoints: `max-width: 768px` (mobile) and `max-width: 480px` (small mobile). The sidebar nav uses `.sidebar-nav` / `.sidebar-nav.show` toggled by a hamburger button callback.

### Adding a new analytics tab
1. Add a `dbc.NavLink` in the sidebar nav section.
2. Define the tab content function returning `html.Div(...)`.
3. Register a callback with `Output('tab-content', 'children')` that renders the new content when the tab is active.
4. Use the four global filter values as `Input` args.

## Developer Workflows

### Run locally
```powershell
.\.venv\Scripts\python.exe app.py
# Opens at http://127.0.0.1:8050
```

### Run via helper script
```powershell
py start.py
```

### Kill existing Python processes before restarting
```powershell
taskkill /F /IM python.exe /T 2>$null; Start-Sleep -Seconds 2; .\.venv\Scripts\python.exe app.py
```

### Production (Render / gunicorn)
```
web: gunicorn app:server
```
Port is read from `$PORT` env var (defaults to 8050).

### Install dependencies
```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

## External Dependencies
- **Dash 4.1+** with `suppress_callback_exceptions=True` (dynamic tab content)
- **dash-bootstrap-components** (BOOTSTRAP theme)
- **Plotly** for all charts (use `px.*` for quick charts, `go.*` for custom traces)
- **gunicorn** for production; not used locally
- **SQLite** – no separate DB server needed; `auth.db` is auto-created

## Important Constraints
- Python 3.13+ required (f-string features, type hints).
- On Windows, stdout is wrapped for UTF-8: do not remove the `sys.stdout` override at the top of `app.py`.
- CSV data path uses a raw string `r"raw data/election_data.csv"` because of the space in the folder name.
- Do not store sensitive state in Dash global variables between users—use `dcc.Store` per session.
