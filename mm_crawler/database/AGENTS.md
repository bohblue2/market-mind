# DATABASE KNOWLEDGE BASE

## OVERVIEW
SQLAlchemy ORM and session layer for crawler persistence.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add or alter table schema | `models.py` | Update ORM model class first |
| Change engine/session creation | `session.py` | Uses `settings.SQLALCHEMY_DATABASE_URL` |
| Change declarative base | `base.py` | Shared Base for all ORM models |
| Add migration for model changes | `../alembic/versions/` | Keep Alembic revision in sync with ORM |

## CONVENTIONS
- Table classes follow `Naver*Orm` naming and explicit `__tablename__`.
- Timestamps generally use timezone-aware `DateTime(timezone=True)` with `func.now()` defaults.
- Relationships are explicit with `cascade='all, delete-orphan'` where child records are owned.

## ANTI-PATTERNS
- Do not import `session.py` in code paths that must avoid side effects; `init_db()` runs at import.
- Do not change enum members in `NaverArticleCategoryEnum` without migration impact review (stored enum values in DB).
- Do not mix incompatible timezone naive/aware datetimes for persisted fields.
- Do not modify `models.py` without creating an Alembic revision; schema drift breaks runtime and migration parity.

## NOTES
- `alembic/env.py` sources DB URL from `ALEMBIC_DB_URL`, while runtime session uses `config.py` composed DSN.
- Initial schema exists in `../alembic/versions/2c9c354b4c6b_init.py`; use it as baseline when comparing drift.
