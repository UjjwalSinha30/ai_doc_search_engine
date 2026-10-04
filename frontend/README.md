# Frontend

React + Vite frontend for the AI Knowledge Search Engine.

## Local Development

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Install dependencies and run Vite:

```powershell
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

In local mode, frontend API calls go directly to the FastAPI backend:

```text
http://localhost:8000/api/*
```

## Docker

In Docker, the frontend is built into static files and served by Nginx.

The browser opens:

```text
http://localhost
```

React calls relative API URLs:

```text
/api/chat
/api/upload
/api/documents
```

Nginx proxies those requests to the backend container:

```text
/api/* -> http://backend:8000/api/*
```

For Docker, `VITE_API_BASE_URL` should be empty:

```env
VITE_API_BASE_URL=
```

This keeps the frontend using the same host as the browser and lets Nginx route API requests internally.
