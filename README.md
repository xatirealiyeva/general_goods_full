# Online Shopping System

A modular e-commerce backend (Django + DRF + PostgreSQL + Redis + JWT) with a
minimal React (Vite) frontend, fully containerized with Docker Compose.

## Quick start

```bash
cp .env.example .env    # already done for you; edit values if needed
docker-compose up --build
```

This starts:

| Service   | URL                              |
|-----------|-----------------------------------|
| Backend API | http://localhost:8000/api       |
| Django admin | http://localhost:8000/admin    |
| Frontend  | http://localhost:5173             |
| PostgreSQL | localhost:5432                   |
| Redis     | localhost:6379                    |

On first boot the backend automatically runs migrations and seeds demo data:

- **Admin**: `xatire777aliyeva@gmail.com` / `ChangeMe123!`
- **Seller**: `seller-demo@example.com` / `SellerPass123!`
- **Customer**: `customer-demo@example.com` / `CustomerPass123!`

⚠️ Change these passwords before any real deployment.

## Running the backend without Docker (SQLite, no Redis)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Without `POSTGRES_HOST`/`REDIS_URL` set, the app automatically falls back to
SQLite and Django's local-memory cache — the same codebase works in both
environments.

## Running the frontend without Docker

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if backend isn't on localhost:8000
npm run dev
```

## Project layout

```
backend/
  apps/
    shared/      # base models, permissions, pagination, exceptions
    users/       # custom User model (email login, roles)
    authx/       # JWT login/refresh, Redis-backed rate limiting
    customers/   # customer profiles
    sellers/     # seller profiles
    catalog/     # categories, products, variants, images, seller assignment
    inventory/   # stock adjustments, low-stock alerts
    cart/        # cart + cart items (Redis-cached)
    orders/      # checkout, order status machine
    payments/    # payment records (provider reference tokens only)
    shipments/   # shipment tracking
    reviews/     # ratings + moderation
  config/        # settings, urls, wsgi/asgi
  Dockerfile
  requirements.txt
frontend/
  src/
    api/         # axios client with JWT auto-refresh
    context/     # auth context
    pages/       # Login, Register, Products, Cart, Orders
    components/  # NavBar, RequireAuth
  Dockerfile
docker-compose.yml
.env.example
```

## Roles & permissions

- **Admin** — manages categories, products, users, orders, refunds, inventory.
- **Seller** — manages only their own products, views only their own orders,
  creates shipments only for orders containing their products.
- **Customer** — manages only their own cart/orders, browses products, leaves
  reviews for products they've purchased.

Enforced via `apps/shared/permissions.py` (role checks) plus per-view
ownership checks in each module's `views.py`/`services.py`.

## Order status flow

```
PENDING → CONFIRMED → SHIPPED → DELIVERED → REFUNDED
   ↓            ↓
CANCELLED   CANCELLED
```

Transitions are validated centrally in `apps/orders/models.py`
(`Order.ALLOWED_TRANSITIONS`) and applied via `OrderService.transition_status`.

## Key API endpoints

```
POST   /api/auth/login/                     JWT login (email + password)
POST   /api/auth/refresh/                   refresh access token
POST   /api/customers/register/             public customer signup
POST   /api/sellers/create/                 admin creates a seller

GET    /api/catalog/products/               list/search products (cached)
POST   /api/catalog/products/                create product (admin/seller)
POST   /api/catalog/products/{id}/variants/  add a variant

GET    /api/cart/                            view own cart
POST   /api/cart/items/                      add item to cart
POST   /api/orders/checkout/                 place order from cart
GET    /api/orders/mine/ | /seller/ | /admin/
PATCH  /api/orders/{id}/status/               admin transitions order status

POST   /api/payments/                         pay a PENDING order
POST   /api/payments/{id}/refund/             admin refund

POST   /api/shipments/                        seller creates shipment record
GET    /api/shipments/order/{order_id}/        track shipments for an order

POST   /api/reviews/                          submit review (verified purchase only)
PATCH  /api/reviews/{id}/moderate/             admin moderation
```

## Security notes

- Passwords hashed with BCrypt (`PASSWORD_HASHERS` in `config/settings.py`).
- JWT auth via `djangorestframework-simplejwt`.
- No raw card data is ever stored — `payments.Payment.provider_reference` is
  an opaque gateway token only (see `apps/payments/models.py`).
- Redis is used for product-list caching, cart cache invalidation, and
  login rate limiting (`apps/authx/throttles.py`).
