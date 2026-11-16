# Credits

This project is a fork and derivative of open-source work by the following authors.
All original copyright notices and license files are preserved.

---

## Spine (forked)

| Project | Author | License | URL |
|---|---|---|---|
| **fdroid-store** | Dim145 | MIT | https://github.com/Dim145/fdroid-store |

The backend architecture, APK upload pipeline, authentication system, audit log,
rate limiting, storage abstraction, ClamAV integration, and F-Droid index builder
are derived from this project. The Next.js frontend has been removed.

**AmaApp-added features** (not present in spine):
- `ListingType` enum (`APK` / `WEB_APP`) and `WebAppListing` model
- Developer profile fields (`bio`, `links`, `avatar_url`) and `/u/{username}` route
- Web-app URL moderation service (scheme allow-list, SSRF guard, admin review queue)
- `Report` model with rate-limited reporting endpoints and admin queue
- `Rating` and `Comment` models (1–5 stars, threaded, soft-delete)
- Full-text search endpoint (`GET /api/v1/listings/search`) with pg_trgm indexes
- VirusTotal hash lookup service with graceful fallback when no API key is set
- ClamAV enabled by default (removed optional `profiles: ["clamav"]` from compose)

---

## Reference projects (ideas read, not forked)

| Project | Author | License | What we looked at |
|---|---|---|---|
| **selfdroid-web-app** | vitlabuda | MIT | APK upload form and download flow simplicity |
| **open-app-kit** | t3xydev | (see repo) | Stable shareable URL per listing (`/apps/{bundle-id}`) and webhook auth pattern |
| **gmch1/store** | gmch1 | MIT | Signed F-Droid repository builder — compared with spine's index code |
| **f-server** | EdwardJXLi | (see repo) | Multi-project ownership and collaborator model |
| **fdroidserver** | F-Droid contributors | AGPL-3.0 | APK metadata parsing and signature verification reference |

No code blocks were directly copied from these projects. Each idea was re-implemented
from scratch in the spine's Python/FastAPI/SQLAlchemy style. Licenses were checked
before reading; nothing from AGPL-licensed fdroidserver was incorporated into the
codebase.

---

## Runtime dependencies

Runtime and build dependencies carry their own licenses; see
`backend/requirements.txt` and the `pyproject.toml` for the full list.
Key ones: FastAPI (MIT), SQLAlchemy (MIT), Alembic (MIT), PostgreSQL (PostgreSQL License),
Redis (BSD-3-Clause), androguard (Apache-2.0), Authlib (BSD-3-Clause),
pwdlib (MIT), PyJWT (MIT).
