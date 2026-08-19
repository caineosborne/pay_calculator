# Pay Checker MVP

## Local testing accounts

The calculator, built-in rulesets, customization editor, and rule validation
remain public. A named local testing account is required only to save, load,
rename, delete, or calculate with a private custom ruleset.

Account administration is intentionally available only through local scripts;
there is no user-listing or account-management API.

```bash
backend/.venv/bin/python backend/scripts/manage_users.py add caine --display-name Caine
backend/.venv/bin/python backend/scripts/manage_users.py add simon --display-name Simon
backend/.venv/bin/python backend/scripts/manage_users.py list
backend/.venv/bin/python backend/scripts/manage_users.py deactivate simon
backend/.venv/bin/python backend/scripts/manage_users.py reactivate simon
```

Configure or rotate the generic testing password with an interactive hidden
prompt. The plaintext password is never printed or stored; only its Argon2id
hash is saved in PostgreSQL. Changing it revokes all existing sessions.

```bash
backend/.venv/bin/python backend/scripts/manage_auth.py set-password
```

Legacy custom rules without an owner can be removed explicitly:

```bash
backend/.venv/bin/python backend/scripts/manage_users.py delete-unowned-rules
```

These accounts are only for controlled testing. Full authentication, account
recovery, and individual credentials are not yet live. Do not use sensitive or
production data.

## Local development

Start PostgreSQL and apply all bundled migrations:

```bash
docker compose up -d postgres
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/initialize_rule_configuration_store.py
```

Start the backend from `backend/` and the frontend from `frontend/`:

```bash
cd backend
.venv/bin/uvicorn main:app --reload
```

```bash
cd frontend
npm run dev
```
