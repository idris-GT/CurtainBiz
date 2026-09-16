# CurtainBiz

**CurtainBiz** is a business operations platform designed to bring day-to-day business workflows and machine-learning-based decision support into one application.

The project was built as a final-year software project with a focus on connecting a modern frontend, API backend, relational database, authentication, business workflows, analytics, and ML intelligence into a single system.

## What it covers

- Customer management
- Product and material management
- Inventory and stock transactions
- Quotations and quotation items
- Orders and order items
- Production and production tasks
- Deliveries
- Payments
- Notifications and activity logs
- Role-based access control
- Business Intelligence and analytics
- Machine-learning-based sales forecasting and operational intelligence

## Intelligence layer

CurtainBiz includes machine-learning decision-support features built around historical business data. The intelligence modules provide forecasting, department-level operational signals, risk indicators, and recommendations for business decision-making.

The project includes intelligence across areas such as:

- Sales and demand
- Inventory
- Production
- Delivery
- Accounts
- Executive/business-level insights

## Architecture

```text
React + Vite frontend
        |
        | HTTP / JSON
        v
FastAPI backend
        |
        +---- Authentication / RBAC
        |
        +---- Business APIs
        |
        +---- ML / Analytics services
        |
        v
PostgreSQL (Supabase)
```

## Tech stack

**Frontend**
- React
- Vite
- React Router
- Axios

**Backend**
- Python
- FastAPI
- Uvicorn
- Pydantic

**Database & authentication**
- PostgreSQL
- Supabase
- JWT-based authentication
- Role and permission based access control

**Machine Learning / analytics**
- NumPy
- Pandas
- Scikit-learn

**Deployment**
- Backend deployed on Render

## Repository structure

```text
CurtainBiz/
├── .github/
├── PowerBI/
├── business-operations-platform/
│   └── backend/
└── frontend/
```

## Running locally

### 1. Backend

Open a terminal in:

```text
business-operations-platform/backend
```

Create and activate a virtual environment, install the dependencies, configure the environment variables, then run:

```bash
uvicorn app.server:app --reload
```

The development API is available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available in development at:

```text
http://127.0.0.1:8000/docs
```

### 2. Frontend

Open another terminal in:

```text
frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The Vite development server normally runs at:

```text
http://localhost:5173
```

## Environment variables

Create a local `.env` file in the backend directory. Never commit real credentials or database connection strings.

See `business-operations-platform/backend/.env.example` for the required variable names.

## Production API

The frontend API client is configured to use the deployed backend API:

```text
https://curtainbiz-9yod.onrender.com
```

## Security notes

- Secrets and environment files are excluded through `.gitignore`.
- Authentication uses JWT validation against Supabase's authentication JWKS endpoint.
- API access can be protected through user roles and permissions.
- Production configuration disables the FastAPI documentation endpoints when `APP_ENV=production`.

## Project status

CurtainBiz is a portfolio-ready full-stack project demonstrating frontend development, REST API design, relational database integration, authentication and authorization, business workflow implementation, machine-learning integration, analytics, and deployment.

## Author

**Mohammed Mohideen Idris**

B.Tech — Artificial Intelligence & Data Science

GitHub: `idris-GT`
