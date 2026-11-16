# OODEL API Reference

Base URL: `VITE_API_HOST` in production, `http://127.0.0.1:8000` locally. All bodies are JSON.

## Authentication

| Who | Header |
| --- | --- |
| Guest | none |
| Customer | `Authorization: Token <token>` (from `/api/auth/login/` or `/register/`) |
| Staff (baker) | `Authorization: Basic <base64(username:password)>` |

## Errors (same shape for every endpoint)

```json
{ "detail": "Human-readable message to show the user", "errors": { "email": ["Enter a valid email address."] } }
```

- `detail` is always a string. Show it directly.
- `errors` maps field name to a list of messages. It is `{}` when the error is not about a field.
- For order items, `errors.items` is a list with one entry per item (empty `{}` for valid ones).

| Status | Meaning |
| --- | --- |
| 400 | Validation failed (see `errors`) |
| 401 | Missing or bad credentials |
| 403 | Signed in but not allowed (e.g. customer calling a staff endpoint) |
| 404 | Order not found (or email does not match) |

## Order endpoints (customers)

### `POST /api/orders/` — place an order (guest or customer) → `201`

Request:
```json
{
  "name": "Ada Baker",
  "email": "ada@example.com",
  "phone": "(818) 555-0100",
  "pickup_at": "2026-12-01T17:30:00-08:00",
  "payment": "cash",
  "items": [
    { "product_id": "strawberry", "detail": "Medium · Strawberry", "quantity": 2, "note": "Happy birthday" }
  ]
}
```
Rules: `name`, `email`, `pickup_at`, `payment` (`"cash"` only), and `items` (at least 1) are required. `phone` and `note` are optional. `pickup_at` must be in the future. `quantity` is 1–20. `product_id` and the size/box option in `detail` (the text before ` · `) must exist in the menu. **Prices are set by the server**; any price sent is ignored. If the customer is signed in, their account email is used.

Response: an [Order](#order-object).

### `GET /api/orders/<id>/?email=<email>` — look up an order → `200`
`email` is required and must match the order (case-insensitive). Returns an [Order](#order-object). A wrong email gives `404`.

### `PATCH /api/orders/<id>/notification/` — set notification email (customer token) → `200`
Request: `{ "notification_email": "notify@example.com" }` (use `""` to turn off).
Response: `{ "notification_email": "notify@example.com" }` (or `null` when off).
Only the customer whose account email matches the order can do this.

## Staff endpoints (baker login required)

| Method and path | Purpose | Success |
| --- | --- | --- |
| `POST /api/staff/login/` | Check staff credentials | `200` `{ "username": "baker" }` |
| `GET /api/staff/orders/` | Orders not yet picked up | `200` list of [Staff orders](#staff-order-object) |
| `GET /api/staff/orders/<id>/` | One order | `200` [Staff order](#staff-order-object) |
| `PATCH /api/staff/orders/<id>/status/` | Advance to the next status | `200` [Staff order](#staff-order-object) |
| `DELETE /api/staff/orders/<id>/` | Delete an order | `204` no body |

Status request: `{ "status": "baking" }`. Statuses move strictly in order: `placed` → `baking` → `ready` → `done`. Skipping a step, repeating one, or changing a finished order returns `400` with `errors.status`.

## Response objects

### Order object
```json
{
  "id": "CK-123456", "email": "ada@example.com", "name": "Ada Baker", "phone": "(818) 555-0100",
  "pay": "cash", "stage": 0, "status": "placed",
  "placedAt": "9:15 AM", "pickup": "Dec 1 · 5:30 PM", "notify": null,
  "items": [{ "id": "strawberry", "name": "Strawberry Cake", "detail": "Medium · Strawberry", "qty": 2, "unit": 24.0, "note": "Happy birthday" }],
  "totals": { "sub": 48.0, "tax": 4.56, "total": 52.56 }
}
```

### Staff order object
```json
{
  "id": "CK-123456", "customer": "Ada Baker", "phone": "(818) 555-0100", "email": "ada@example.com",
  "status": "baking", "placedAt": "9:15 AM", "pickup": "Dec 1 · 5:30 PM",
  "startedAt": "10:02 AM", "readyAt": "11:10 AM",
  "items": [{ "qty": 2, "name": "Strawberry Cake", "detail": "Medium · Strawberry" }],
  "note": "Happy birthday", "total": 52.56, "pay": "Cash on pickup"
}
```
`startedAt` and `readyAt` appear only once those steps have happened.

## Where the code lives

- `orders/data.py` — all database reads and writes for orders
- `orders/serializers.py` — request validation and server-side pricing
- `orders/views.py` — the endpoints above
- `config/exceptions.py` — builds the shared error shape
