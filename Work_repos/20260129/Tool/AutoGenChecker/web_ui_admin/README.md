# AutoGenChecker Web UI

Modern React-based web interface for AutoGenChecker.

## Project Structure

```
web_ui/
├── backend/                # FastAPI backend
│   ├── app.py             # Main application
│   ├── api/               # API endpoints
│   ├── models/            # Data models
│   └── requirements.txt   # Python dependencies
│
└── frontend/              # React frontend
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/         # Page components
    │   ├── hooks/         # Custom hooks
    │   ├── store/         # Zustand state
    │   ├── api/           # API client
    │   └── styles/        # CSS styles
    ├── public/
    └── package.json
```

## Quick Start

### Backend

```bash
cd web_ui/backend
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:8000`

### Frontend

```bash
cd web_ui/frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## Features

- 📊 Dashboard - Project overview and statistics
- 🔧 Generator - Complete 9-step checker generation workflow
- 📚 History - View generation logs, code, README, and test results
- 📝 Templates - Template library and management
- ⚙️ Settings - Configuration management
- 📖 Documentation - Built-in documentation center

## Technology Stack

### Backend
- FastAPI 0.109+
- Uvicorn
- Python 3.9+

### Frontend
- React 18.3
- Vite 5.1
- TailwindCSS 3.4
- Zustand 4.5
- TanStack Query 5.0
- React Router 6.22
- Monaco Editor
- Axios

## Design Principles

- **Minimalist & Professional** - Clean interface with restrained color palette
- **Click-based Interaction** - No keyboard shortcuts required
- **Perfect Spacing** - Balanced 8px grid system
- **Responsive** - Works on desktop, tablet, and mobile
- **Team Collaboration** - Share URLs, track activity, version control
