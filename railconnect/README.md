# RailConnect — Railway Booking Backend

RailConnect is a REST API backend for user authentication, train search, seat availability, ticket booking, PNR lookup, booking cancellation, and admin train management.

## Features
- User signup and login with hashed passwords
- JWT access tokens and protected endpoints
- Admin-only train creation
- Train search by source and destination
- Seat availability lookup
- Ticket booking with a generated PNR
- Booking history, PNR lookup, cancellation, and seat restoration
- Forgot-password development simulation with expiring, single-use reset tokens
- Pytest API tests

## Tech stack
Python, FastAPI, SQLModel, SQLite by default, PyJWT, pwdlib, HTTPX, Pytest.

## Setup
1. Create and activate a virtual environment, or use your existing `uv` environment.
2. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
   With uv:
   ```bash
   uv pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set a strong `JWT_SECRET_KEY`.
4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Open `http://127.0.0.1:8000/docs`.

## Admin account
For local demo purposes, the email configured in `ADMIN_EMAIL` receives the admin role at signup. Register that email through `/auth/signup`, then log in. Do not use this simplified approach for a production deployment; use a secure admin provisioning process.

## Important endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/signup` | Register |
| POST | `/auth/login` | Get JWT |
| GET | `/auth/me` | Current user |
| POST | `/auth/logout` | Client-side token discard explanation |
| POST | `/auth/forgot-password` | Generate development reset token |
| POST | `/auth/reset-password` | Reset password once before expiry |
| POST | `/admin/trains` | Admin adds a train |
| GET | `/trains?source=Delhi&destination=Jaipur` | Search trains |
| GET | `/trains/{train_id}/seats` | Check seats |
| POST | `/bookings` | Book seats |
| GET | `/bookings` | View current user's bookings |
| GET | `/bookings/{pnr}` | View a booking |
| POST | `/bookings/{pnr}/cancel` | Cancel a booking |

## Run tests
```bash
pytest -q
```

## Screenshot checklist
Capture real responses from Swagger `/docs` or another API client:
1. Signup and login
2. Failed login or unauthorized access
3. Forgot-password and reset-password
4. Admin adding a train
5. Train search and seat availability
6. Booking response with PNR
7. Viewing and cancelling a booking
8. Successful `pytest -q` output

## Logout and token handling
This starter uses stateless JWT access tokens. Logout asks the client to discard the token; a copied token can still work until its expiry. Server-side token revocation is not implemented in this starter.

## Security notes
- Never commit `.env`, credentials, or production secrets.
- The forgot-password route returns the reset token only as a development simulation. A real deployment should email the token instead.
- Change the development JWT secret before sharing or deploying the project.
- This is an educational project, not a production railway reservation system. Production booking requires transaction/locking safeguards for simultaneous seat requests.
