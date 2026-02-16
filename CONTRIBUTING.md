Contributing
============

How to run locally
-------------------

Backend
~~~~~~~

1. Create and activate virtual environment:

```bash
python3 -m venv backend/backendenv
source backend/backendenv/bin/activate
pip install -r backend/requirements.txt
```

2. Configure environment variables in `backend/.env` (copy from `.env.example` if present).

3. Run the backend:

```bash
cd backend
source backendenv/bin/activate
uvicorn app:app --reload
```

Frontend
~~~~~~~~

1. Install dependencies and run dev server:

```bash
cd frontend
npm install
npm run dev
```

Testing
-------

- Frontend tests (Vitest) live in `frontend/test`.
- Add backend tests in `backend/tests` and run with `pytest`.

Code reviews
------------

- Ensure formatting (`black` / `prettier`) and linting (`flake8` / `eslint`) pass before merging.
