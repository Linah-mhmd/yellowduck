# Yellow Duck — React + Flask

A smart investment platform connecting founders and investors, with AI-powered funding and cash flow analysis.

## Project Structure

```
yellowduck/
├── app.py              # Flask API Backend
├── api_routes.py       # REST API endpoints
├── frontend/           # React SPA (Vite)
│   ├── src/
│   │   ├── components/ # Layout, ProtectedRoute
│   │   ├── context/    # AuthContext
│   │   ├── pages/      # 15 React pages
│   │   ├── services/   # API client (axios)
│   │   └── styles/     # CSS
│   └── package.json
├── ai_funding_optimizer.py
├── cash_flow.py
├── recommendations.py
└── requirements.txt
```

## Requirements

- Python 3.10+
- Node.js 18+
- MongoDB (localhost:27017)

## Setup

```bash
cd yellowduck
copy .env.example .env   # edit SECRET_KEY and MONGO_URI
pip install -r requirements.txt
```

## Development

### 1. Backend (Flask API)

```bash
cd yellowduck
pip install -r requirements.txt
python app.py
```

Runs at: `http://localhost:5001`

### 2. Frontend (React)

```bash
cd yellowduck/frontend
npm install
npm run dev
```

Runs at: `http://localhost:3000` (with automatic API proxy)

## Production

```bash
cd yellowduck/frontend
npm install
npm run build

cd ..
python app.py
```

Flask automatically serves the React build from `frontend/dist`.

## Pages (React)

| Route | Description |
|-------|-------------|
| `/` | Home page + AI recommendations |
| `/login` | Sign in |
| `/signup` | Create account |
| `/poll` | Matching questionnaire |
| `/projects` | Project list |
| `/projects/:id` | Project details + invest |
| `/create-project` | Create project (Founder) |
| `/control-projects` | Manage projects |
| `/funding-optimizer` | AI funding analyzer |
| `/cash-flow` | Cash flow analysis |
| `/portfolio` | View profile |
| `/portfolio/form` | Create / edit portfolio |
| `/notifications` | Notifications |
| `/investment/:id` | Investment request details |

## API Endpoints

All endpoints are under `/api/`:

- `GET/POST /api/auth/*` — Authentication
- `GET /api/home` — Recommendations
- `GET/POST /api/projects` — Projects
- `POST /api/funding-optimizer` — Funding analysis
- `POST /api/cash-flow` — Cash flow analysis
- `GET/POST /api/portfolio/*` — Portfolio
- `GET /api/notifications` — Notifications

## Docker

```bash
docker-compose up --build
```

## Tests

```bash
py -m pytest tests/ -v
```

## Improvements

- **Password hashing** (scrypt) with automatic upgrade for legacy accounts
- **User permissions** — each founder can only edit their own projects
- **Project deletion** — API + UI in Control Projects
- **Portfolio upsert** — no duplicates, automatic data loading
- **Search** — search projects from Home and Projects
- **Real statistics** — from MongoDB instead of placeholder numbers
- **404 + ErrorBoundary** — React error handling
- **Docker + .env** — ready for deployment
- **pytest** — 6 API tests
- **React SPA** instead of Jinja templates — faster experience without full page reloads
- **React Router** — smooth navigation between pages
- **AuthContext** — centralized user state management
- **Axios API layer** — organized requests with error handling
- **Protected Routes** — page access by role (Founder / Investor)
- **Chart.js via react-chartjs-2** — interactive charts
- **Flask REST API** — separated frontend and backend
- **CORS + Session cookies** — authentication security
