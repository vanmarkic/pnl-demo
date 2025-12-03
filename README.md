# PnL Demo - Monorepo

This is a monorepo containing a React frontend and FastAPI backend application.

## Project Structure

```
pnl-demo/
├── frontend/          # React application (Vite)
├── backend/           # FastAPI application
└── README.md          # This file
```

## Prerequisites

- Node.js (v18 or higher)
- Python 3.12+
- npm or yarn

## Quick Start

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

### Frontend
- Built with React and Vite
- Hot module replacement for fast development
- See [frontend/README.md](frontend/README.md) for more details

### Backend
- Built with FastAPI
- Auto-reloading development server
- Interactive API documentation
- See [backend/README.md](backend/README.md) for more details

## Running Both Services

You'll need two terminal windows:

Terminal 1 (Frontend):
```bash
cd frontend && npm run dev
```

Terminal 2 (Backend):
```bash
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000
```