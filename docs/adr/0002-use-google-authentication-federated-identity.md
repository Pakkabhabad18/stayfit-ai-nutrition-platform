# ADR 0002: Use Federated Identity Pattern (Google Auth)

## Status
Accepted

## Context
User onboarding is a critical funnel for health tracking applications. Requiring users to fill out long registration forms and manage passwords introduces friction that can reduce sign-up conversion rates. Furthermore, storing and securing user passwords manually places the burden of security, hashing logic, and credential management on our application, increasing the risk profile.

## Decision
We decided to implement the **Federated Identity Pattern** using Google OAuth2. 

We integrated `@react-oauth/google` on the frontend and the `google.oauth2.id_token` library on the backend. 
When a user logs in via Google, an encrypted JWT `credential` is provided directly to the React application. The React app then forwards this token payload to our backend (`/api/auth/google`), which cryptographically verifies it securely via `id_token.verify_oauth2_token()` utilizing our `GOOGLE_CLIENT_ID`.

If the user does not exist in our database, we automatically register a new `User` record utilizing their Google email, assigning a random cryptographic string to the `password_hash` column to safely satisfy database schema constraints.

Ultimately, the backend then generates and issues a distinct system-internal JWT access token (`flask_jwt_extended`), completely decoupling the internal app session lifecycle from Google's short-lived authentication token.

## Consequences
### Positive
- **Zero-Trust Security:** We offload password security, hashing logic, and credential management to an enterprise provider (Google). We do not store sensitive passwords in our PostgreSQL database.
- **Reduced Friction:** Users can jump straight into the health tracking funnel with one click, maximizing sign-up conversion and improving the user experience.
- **Standardized Identity:** Provides a solid, battle-tested foundation for user identification.

### Negative
- **Third-Party Dependency:** We are reliant on Google's OAuth infrastructure. If Google Auth goes down or changes its API, our authentication flow handles could be impacted.
- **Integration Complexity:** Requires setting up Google Cloud Console credentials, maintaining client IDs across environments, and ensuring secure token forwarding between the frontend and backend.
