# OODEL Product Backlog

This backlog reflects the repository's current vertical slice. Update it when a story is demonstrated or its acceptance criteria change.

## Demo-ready

| Story | Status | Evidence |
| --- | --- | --- |
| Place an order as a guest | Done | Customer checkout creates an API-backed order. |
| Register, sign in, and resume a customer session | Done | Token authentication endpoints and frontend session restoration. |
| View and advance orders in the kitchen portal | Done | Staff queue, status transitions, and customer status refresh. |
| Add representative development data and verify relationships | Done | `seed_dev_data` plus automated order/item and email-association tests. |
| Demo the vertical slice | Ready to demo | Repeatable walkthrough documented in `README.md`. |

## Next priorities

| Priority | Story | Acceptance criteria |
| --- | --- | --- |
| P1 | Add continuous integration | Every pull request runs backend checks/tests and frontend build/lint automatically. |
| P1 | Link registered customers directly to orders | `Order` has an optional customer relationship, guest orders still work, and existing email lookup remains compatible. |
| P1 | Deliver ready-for-pickup notifications | A status change to ready sends an email once, records delivery outcome, and handles retryable failures. |
| P2 | Move the product catalog into the database | Staff can manage products/options without editing frontend and backend source files, and checkout prices remain server-controlled. |
| P2 | Add supported online payments | No card data reaches OODEL servers, payment status is verified server-side, and failed payments do not create paid orders. |
| P2 | Expand end-to-end coverage | Automated tests cover guest checkout, registered checkout, kitchen status updates, and customer tracking as one flow. |

## Known constraints

- Customer-to-order ownership is currently email-based rather than a database foreign key.
- Notification preferences are stored, but email delivery is not connected.
- Menu data is duplicated between the static customer page and backend catalog validation.
- Cash on pickup is the only supported payment method.
