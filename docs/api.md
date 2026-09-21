# REST API

Base URL defaults to `http://127.0.0.1:5000`.

## POST /api/tickets
Purpose: create a ticket without running ML/LLM.
Request:
```json
{"customer_id":"CUST-100","message":"My card payment was declined."}
```
Response `201`:
```json
{"ticket_id":1,"status":"Open"}
```
Errors: `400` validation, `500` server failure.

## GET /api/tickets/<ticket_id>
Returns ticket, predictions, AI interactions, and feedback.
`200` success, `404` missing ticket.

## POST /api/predict
Request:
```json
{"ticket_id":1}
```
or include `"message"` to override inference text for the request.
Returns category, priority, model version, and human-review flag.
`400` validation, `404` missing ticket, `503` missing models.

## POST /api/generate-response
Request:
```json
{"ticket_id":1}
```
Returns generated response and prompt version.
`200`, `404`, or `500`.

## POST /api/process-ticket
Request:
```json
{"customer_id":"CUST-100","message":"I suspect an unauthorized payment."}
```
Response `201`:
```json
{
  "ticket_id": 2,
  "prediction": {
    "category": "Payment",
    "priority": "Critical",
    "human_review_required": true,
    "model_version": "tfidf-logreg-v1"
  },
  "ai_response": "Thanks for contacting support...",
  "prompt_version": "v1.0"
}
```

## POST /api/feedback
Request:
```json
{"ticket_id":2,"rating":5,"comments":"Clear response"}
```
Returns `201` with `{"status":"stored"}`.

## GET /api/analytics
Returns aggregate ticket, category, priority, AI interaction, and feedback metrics.

All endpoints use JSON, parameterized database access, bounded inputs, and safe error messages.


## Authentication endpoints

### POST /api/auth/register
Creates a customer account. Passwords must be at least 10 characters.
```json
{"name":"Alice","email":"alice@example.com","password":"long-secure-password"}
```
`201` creates the account; `409` is returned for an existing email.

### POST /api/auth/login
```json
{"email":"alice@example.com","password":"long-secure-password"}
```
Returns an expiring bearer token. Protected endpoints require `Authorization: Bearer <token>`.

## GET /api/review-queue
Admin-only. Returns unresolved tickets with `human_review_required=1`, ordered Critical → High → Medium → Low.

All customer ticket reads/writes are authorized against the authenticated user's `user_id`.
