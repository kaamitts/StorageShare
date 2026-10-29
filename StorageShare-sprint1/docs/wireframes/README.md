> Исходные макеты. В интегрированной версии занятый email возвращает HTTP 400 (не 409). Актуальный контракт: ../api-auth.md.

# Wireframes — Login & Registration (IPM-3)

Author: Birzhan Orynbasar (UX / Frontend) · Date: 12 October 2026
Fidelity: low (boxes and labels, no colours, no final design)
Tool: Figma · Source file: https://www.figma.com/design/VttPEanGfiBOfJBrSflL8r/StorageShare-%E2%80%94-Wireframes?node-id=0-1&t=86ZfqyMzClhvXfAm-1

Covers the **Must** feature "User registration & login (traveller & partner)" from the
TSIS 1+2 Features List. The field names match `users` in [`docs/db-schema.md`](../db-schema.md).

## Frames

| # | Frame in Figma | File | What it shows |
| --- | --- | --- | --- |
| 1 | `Login` | `01-login.png` | email, password, "Log in" button, link to registration |
| 2 | `Login — wrong password` | `02-login-wrong-password.png` | API returned 401 |
| 3 | `Login — empty fields` | `03-login-empty-fields.png` | client-side validation, no request sent |
| 4 | `Register` | `04-register.png` | full name, email, password, role, "Register" button |
| 5 | `Register — email already taken` | `05-register-email-taken.png` | API returned 409 (`users.email` is unique) |
| 6 | `Register — empty fields` | `06-register-empty-fields.png` | client-side validation, no request sent |

## Fields and where they go in the database

| Form field | Column in `users` | Required |
| --- | --- | --- |
| Full name | `full_name` varchar(120) | yes |
| Email | `email` varchar(254), unique — this is the login | yes |
| Password | hashed by the backend into `password_hash` | yes, min. 8 characters |
| I am a: Traveller / Partner | `role` — `traveler` \| `partner` | yes, no default |

`phone` is nullable in the schema and is **not** on the registration form — the user fills
it in later in the profile. To be confirmed with Dastan at the review.

## Rules the screens follow

- **One error message for a wrong login.** "Wrong email or password" is shown both for a
  wrong password and for an email that does not exist. Two different messages would tell
  an attacker which emails are registered.
- **Empty fields are caught in the browser.** No request is sent; the focus jumps to the
  first invalid field. The backend validates the same rules again.
- **Nothing the user typed is lost on an error** — except the password, which is cleared.
- **No default role.** The user has to choose, so nobody registers as a partner by accident.
- **The button is disabled while the request is running**, so an account cannot be created
  twice by double-clicking.

## After login

- `role = traveler` → the search page
- `role = partner` → the partner dashboard

## AI Disclosure

AI (Claude) was used to generate the first skeleton of the frames and to phrase this
document in English. The screens, the fields, the states and the rules above were decided
by the team and reworked in Figma by the author.
