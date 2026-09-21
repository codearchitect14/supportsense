# Manual QA Checklist

This checklist covers the full user journey through SupportSense end to end. Run
it against a local environment before a release, and against a staging or
production deployment after every deploy.

Prerequisites: the backend, frontend, PostgreSQL, and Redis are running, both
datasets are loaded, and at least one LLM provider API key is configured (see
the root `README.md` for setup instructions).

## 1. Public marketing site

- [ ] Visit the site root and confirm the homepage loads with no console errors.
- [ ] Confirm the navigation links (features, pricing, contact, or equivalent
      sections present on the page) scroll to or navigate to the correct section.
- [ ] Confirm the page is legible and usable at a mobile viewport width.
- [ ] Confirm links to the login and signup pages work.

## 2. Account creation and authentication

- [ ] Sign up with a new email address and a valid password; confirm the account
      is created and the user is redirected into the authenticated app.
- [ ] Attempt to sign up again with the same email; confirm a clear duplicate
      account error is shown.
- [ ] Attempt to sign up with a weak password; confirm a clear validation error
      is shown and no account is created.
- [ ] Log out, then log back in with the same credentials; confirm access is
      restored.
- [ ] Attempt to log in with an incorrect password; confirm a clear error is
      shown and no session is created.
- [ ] Refresh the page while logged in; confirm the session persists rather than
      redirecting to the login page.

## 3. Chat conversation

- [ ] Open the chat page and send a question that matches the support
      knowledge base closely (for example, a question about refunds); confirm a
      direct, fast answer is returned with a knowledge base provider indicator.
- [ ] Send a question that is not covered by the knowledge base; confirm the
      assistant falls back to an LLM provider and the response identifies which
      provider answered.
- [ ] Send a message with only whitespace; confirm it is not submitted.
- [ ] Mark an assistant response as helpful, then as not helpful; confirm the
      feedback state is reflected in the UI and persists after a page refresh.
- [ ] Start a new conversation and confirm it appears separately from prior
      conversations in the conversation history.
- [ ] Log in as a viewer-role account and confirm chat access is denied with a
      clear message, since chat is restricted to agent and admin roles.

## 4. Voice conversation

- [ ] Open the voice page, grant microphone permission, and record a short
      question; confirm a live transcript appears and an assistant response is
      returned with synthesized audio playback.
- [ ] Confirm the recording button visibly changes state between idle,
      recording, and processing.
- [ ] Confirm a voice conversation appears in conversation history tagged as a
      voice channel conversation, distinct from chat conversations.
- [ ] Deny microphone permission and confirm a clear, actionable error message
      is shown instead of a silent failure.

## 5. Revenue and analytics dashboard

- [ ] Open the dashboard and confirm the overview, customers, operations, and
      support sections all load with data, not indefinite loading states.
- [ ] Apply a date range filter and confirm the charts and KPI tiles update to
      reflect the new range.
- [ ] Export a chart to CSV and confirm the downloaded file contains the
      expected columns and rows for the current filter selection.
- [ ] Confirm delivery and growth metrics fall within sane bounds (for example,
      average delivery time is a small number of days, not an implausibly large
      figure).
- [ ] Log in as a viewer-role account and confirm dashboard access is permitted
      but write actions, if any, are not available.

## 6. Administration

- [ ] Log in as an admin and confirm the user list is visible and other
      accounts' roles can be changed.
- [ ] Confirm an admin cannot change their own role through the same control.
- [ ] Log in as a non-admin and confirm the admin user management page is not
      reachable.

## 7. Logout and session handling

- [ ] Log out and confirm the user is returned to the marketing site or login
      page, and that authenticated pages are no longer reachable without
      logging in again.
- [ ] Confirm that after logging out, the browser back button does not expose
      any previously visible authenticated content.

## 8. Cross-cutting checks

- [ ] Confirm no browser console errors appear during the journey above.
- [ ] Confirm no sensitive values (API keys, tokens) are visible in the browser
      network tab in plaintext beyond what is required for the request itself.
- [ ] Confirm rate limiting is in effect: repeated rapid failed login attempts
      are eventually rejected with a clear rate limit message.
