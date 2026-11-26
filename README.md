# Coderr Backend

REST API for **Coderr**, a freelancer platform where business users offer
services in three packages (basic, standard, premium) and customers order
and review them. Built with **Django** and the **Django REST Framework**.

The frontend is **not** part of this repository. It is provided by the
Developer Akademie: <https://github.com/Developer-Akademie-Backendkurs/project.Coderr>

## Tech stack

- Python 3.10+
- Django 5.2 LTS
- Django REST Framework (token authentication)
- django-filter (filtering of offers and reviews)
- django-cors-headers (the frontend runs on a different port)
- Pillow (profile pictures and offer images)
- SQLite (local development)

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/RaphaelNeuberger/Coderr-Backend.git
cd Coderr-Backend

# 2. Create and activate a virtual environment
python -m venv env
# Windows
env\Scripts\activate
# macOS / Linux
source env/bin/activate

# 3. Install the dependencies
pip install -r requirements.txt

# 4. Create the database
python manage.py migrate

# 5. Create the guest accounts used by the frontend guest login
python manage.py create_guest_users

# 6. Optional: create an admin account for the admin panel
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`, the admin panel at
`http://127.0.0.1:8000/admin/`.

### Connecting the frontend

1. Clone the frontend repository (see link above).
2. Open it in VS Code and start `index.html` with the **Live Server**
   extension (default: `http://127.0.0.1:5500`).
3. The frontend already points to `http://127.0.0.1:8000/api/`
   (`shared/scripts/config.js`).

### Guest accounts

`python manage.py create_guest_users` creates (or resets) the two accounts
that the frontend uses for its guest login:

| Type | Username | Password |
| --- | --- | --- |
| Customer | `andrey` | `asdasd` |
| Business | `kevin` | `asdasd24` |

These credentials are public demo accounts defined by the frontend. Do not
use them in production.

## Configuration

All settings have safe defaults for local development. For any other
environment set these environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | insecure development key | **Must** be set in production |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated host names |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:5500,http://localhost:5500` | Comma-separated frontend origins |

Uploaded files (profile pictures, offer images) are stored in `media/` and
served by Django while `DEBUG` is `True`.

## API overview

All endpoints start with `/api/`. Unless stated otherwise a token is required
(`Authorization: Token <token>`).

| Method | Endpoint | Description | Permission |
| --- | --- | --- | --- |
| POST | `registration/` | Register a customer or business user | public |
| POST | `login/` | Log in and receive a token | public |
| GET / PATCH | `profile/{user_id}/` | Read / update a profile | authenticated / owner |
| GET | `profiles/business/` | List all business profiles | authenticated |
| GET | `profiles/customer/` | List all customer profiles | authenticated |
| GET | `offers/` | Paginated offer list with filters | public |
| POST | `offers/` | Create an offer with three packages | business user |
| GET | `offers/{id}/` | Read a single offer | authenticated |
| PATCH / DELETE | `offers/{id}/` | Update / delete an offer | creator |
| GET | `offerdetails/{id}/` | Read a single offer package | authenticated |
| GET | `orders/` | Orders of the current user | authenticated |
| POST | `orders/` | Order an offer package | customer user |
| PATCH | `orders/{id}/` | Update the status of an order | business user of the order |
| GET | `order-count/{business_user_id}/` | Number of running orders | authenticated |
| GET | `completed-order-count/{business_user_id}/` | Number of completed orders | authenticated |
| GET | `reviews/` | List reviews (filter and ordering) | authenticated |
| POST | `reviews/` | Review a business user (once) | customer user |
| PATCH / DELETE | `reviews/{id}/` | Update / delete a review | author |
| GET | `base-info/` | Platform statistics | public |

### Offer list parameters

| Parameter | Description |
| --- | --- |
| `creator_id` | Only offers of this user |
| `min_price` | Lowest package price is at least this value |
| `max_delivery_time` | Fastest delivery time is at most this many days |
| `search` | Searches in title and description |
| `ordering` | `updated_at`, `-updated_at`, `min_price`, `-min_price` |
| `page`, `page_size` | Page number pagination (default page size: 6) |

### Special behaviour

- An offer must be created with exactly one `basic`, one `standard` and one
  `premium` package. When updating, every package is identified by its
  `offer_type`; its id stays the same.
- `revisions: -1` means unlimited revisions.
- An order copies the data of the ordered package, so later changes of the
  offer do not change existing orders.
- Every customer can review each business user only once.
- Empty profile text fields are returned as empty strings, never as `null`.

## Project structure

```text
core/            project settings and central URL routing
auth_app/        registration, login, guest user command
profile_app/     user profiles (customer / business)
offers_app/      offers and offer packages
orders_app/      orders and order counts
reviews_app/     reviews
base_info_app/   platform statistics
```

Every app contains an `api/` folder with `serializers.py`, `views.py`,
`urls.py` and (if needed) `permissions.py` and `filters.py`, and a `tests/`
folder.

## Tests and code quality

```bash
# Run all tests with coverage
coverage run manage.py test
coverage report

# Check PEP 8
flake8
```
