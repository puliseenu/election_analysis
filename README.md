# Election Analysis Dashboard

A comprehensive, interactive analytics dashboard for analyzing 5-state election data with deep statistical insights, win prediction factors, and mobile responsiveness.

## Features

### Core Analytics (13 Tabs)
- **Overview**: KPI metrics, vote distribution, top candidates
- **State Analysis**: State-wise performance, party trends, turnout analysis
- **Party Analysis**: Party vote share, performance metrics, state comparison
- **Candidate Analysis**: Candidate performance, vote margins, constituency breakdown
- **Trends**: Historical trends, growth patterns, year-over-year analysis
- **Turnout**: Voter turnout analysis, demographic patterns
- **Win/Loss**: Winner vs loser comparison, winning factors analysis
- **Financial**: Campaign spending analysis, financial metrics
- **Criminal**: Candidate criminal history analysis
- **Incumbent**: Incumbent performance, advantage metrics
- **Win Predictors**: Binary parameters, age/education/wealth analysis, experience trends
- **Constituency Trends**: Multi-term tracking, repeat winners, party swing analysis
- **Deep Insights**: Winner DNA comparison, scatter plots, gender/terms distribution

### Mobile Responsive Design
- Hamburger menu for mobile navigation (< 768px)
- Responsive grid system (xs/sm/md/lg/xl breakpoints)
- Touch-optimized inputs (16px+ fonts, 48px+ touch targets)
- Auto-adapting layouts and charts
- Full functionality on all devices

### Authentication & Security
- User registration with email verification
- Admin approval workflow
- PBKDF2-SHA256 password hashing (100k iterations)
- Role-based access control
- SQLite database with audit logs

### Data Insights
- 31,365 election records across 5 Indian states
- 53+ data attributes per record
- Advanced statistical analysis
- 100+ interactive Plotly charts
- Global filters (State, Year, Constituency, Type)

## Tech Stack

- **Frontend**: Dash, Dash-Bootstrap-Components, Plotly
- **Backend**: Flask (built into Dash)
- **Database**: SQLite
- **Authentication**: PBKDF2-SHA256
- **Python Version**: 3.13.12+
- **Framework Version**: Dash 4.1.0+

## Quick Start

### Prerequisites
- Python 3.13+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/election_analysis.git
cd election_analysis
```

2. Create virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python start.py
```

5. Access the dashboard:
- **Local**: http://127.0.0.1:8050
- **Network**: http://192.168.x.x:8050 (replace x.x with your IP)
- **Public** (ngrok): https://verbose-unified-aloof.ngrok-free.dev

### Default Login
- **Username**: admin
- **Password**: admin1432

## Project Structure

```
election_analysis/
├── app.py                          # Main Dash application (1600+ lines)
├── start.py                        # Application launcher
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── src/
│   ├── auth.py                    # Authentication logic
│   └── utils.py                   # Utility functions
├── config/
│   └── settings.py                # Configuration settings
├── assets/
│   ├── style.css                  # Custom styling
│   └── logo.png                   # Dashboard logo
├── raw data/
│   └── election_data.csv          # 31,365 records dataset
├── utils/
│   ├── data_processor.py          # Data processing utilities
│   └── validators.py              # Data validators
└── docs/
    ├── MOBILE_RESPONSIVE_GUIDE.md
    ├── IMPLEMENTATION_COMPLETE.md
    └── RESPONSIVE_ARCHITECTURE_DIAGRAMS.md
```

## Key Analytics Functions

### Win Predictors Tab
Analyzes factors that influence electoral victories:
- Binary parameters (criminal cases, assets, etc.)
- Age, education, and professional background
- Wealth and financial metrics
- Years of political experience
- Party × State performance heatmap

### Constituency Trends Tab
Tracks multi-term election patterns:
- 4-term historical tracking
- Repeat winners identification
- Party swing analysis
- Voter roll growth trends
- Incumbent advantage metrics
- Vote margin trends

### Deep Insights Tab
Comparative analysis of winners vs losers:
- Winner DNA profile
- Parameter gap analysis
- Vote share vs demographic scatter plots
- Gender distribution analysis
- Political experience distribution
- KPI comparison cards

## Configuration

Edit `config/settings.py` to customize:
- Database path
- Server port (default: 8050)
- Number of data records to load
- Authentication settings
- Chart color schemes

## Database

### Authentication Database (auth.db)
- Users table (username, email, password_hash, approved, role)
- Audit log table (user_id, action, timestamp, details)

### Data Source
- CSV: `raw data/election_data.csv`
- Records: 31,365
- Columns: 53
- States: 5 (Andhra Pradesh, Telangana, Karnataka, Rajasthan, Madhya Pradesh)

## Mobile Responsiveness

The dashboard automatically adapts to all screen sizes:

| Breakpoint | Device | Layout |
|-----------|--------|--------|
| < 480px | Small phones | Single column, hamburger menu |
| 480-768px | Tablets | 2-column grid, hamburger menu |
| 768-992px | Tablets landscape | 3-column grid, visible sidebar |
| 992-1200px | Laptops | 4-column grid |
| > 1200px | Desktops | Full responsive grid |

## Public Access

### Using ngrok (Free)
1. Install ngrok: https://ngrok.com/download
2. Authenticate: `ngrok config add-authtoken YOUR_TOKEN`
3. Run: `ngrok http 8050`
4. Share the public URL

### Cloud Deployment
Recommended platforms:
- Render.com (free tier available)
- Railway.app
- AWS, Azure, GCP

## API Endpoints

The dashboard provides interactive Dash callbacks for:
- Global filtering across all tabs
- Dynamic chart updates
- User authentication
- Data export functionality

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

## Performance Notes

- Dashboard loads 31,365 records into memory on startup
- Plotly charts are cached for fast rendering
- Global filters update all tabs simultaneously
- Mobile hamburger menu optimizes for < 768px screens

## Troubleshooting

### Dashboard won't start
- Ensure Python 3.13+ is installed
- Check virtual environment is activated
- Verify all dependencies: `pip install -r requirements.txt`
- Check port 8050 isn't in use: `netstat -ano | find "8050"`

### Authentication issues
- Default credentials: admin/admin1432
- Check auth.db exists in project root
- Clear browser cookies and retry login

### Mobile menu not working
- Check viewport meta tag in browser dev tools
- Ensure JavaScript is enabled
- Clear browser cache and reload

### Data not loading
- Verify `raw data/election_data.csv` exists
- Check CSV file is not corrupted
- Ensure read permissions on CSV file

## License

This project is provided as-is for educational and research purposes.

## Contact & Support

For issues, questions, or contributions, please create an issue in the repository.

## Acknowledgments

- Election data sourced from public election commission records
- Dashboard built with Dash and Plotly
- Mobile responsiveness using Bootstrap grid system

---

**Version**: 1.0.0  
**Last Updated**: April 18, 2026  
**Status**: Production Ready ✓
