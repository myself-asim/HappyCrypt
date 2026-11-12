# HappyCrypt

**Your Passwords. Your Privacy. Your Control.**

HappyCrypt is a fully local-first, offline password manager built with Python (FastAPI) and vanilla HTML, CSS, and JavaScript. All encryption, storage, and processing happen on your machine. No cloud, no telemetry, no external network dependencies.

## Features

- **Local-First & Offline** - Runs entirely on `127.0.0.1`, no internet connection required
- **Strong Encryption** - AES-256-GCM authenticated encryption with unique nonces per operation
- **Secure Key Derivation** - Argon2id with configurable parameters
- **Master Password Protection** - Never stored or recoverable; keys kept in memory only while unlocked
- **Password Vault** - Add, view, search, sort, update, delete credentials with encrypted storage
- **Password Generator** - Cryptographically secure (`secrets` module), customizable options
- **Password Strength Analyzer** - Local analysis with actionable feedback
- **Security Dashboard** - Detect weak, reused, and potentially outdated passwords
- **Secure Backup & Restore** - Encrypted JSON backups with integrity verification (never plaintext)
- **Auto-Lock** - Configurable inactivity timeout
- **Clipboard Protection** - Optional automatic clearing
- **Dark/Light Themes** - Modern, premium UI
- **Tamper Detection** - Authenticated encryption detects data tampering

## Technology Stack

- **Backend:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy, Pydantic
- **Security:** cryptography (AES-256-GCM), argon2-cffi (Argon2id), secrets
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Database:** SQLite (local file only)

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
Or use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Usage

Launch HappyCrypt:
```bash
python run.py
```

The application will start the local backend at `http://127.0.0.1:8000` and automatically open it in your default browser.

### First Time Setup
1. Create a master password (minimum 8 characters). **This cannot be recovered if lost.**
2. Start adding your credentials to the encrypted vault

### Daily Use
- **Dashboard** - Overview of vault security health
- **Password Vault** - Manage all credentials (search, copy, view, edit, delete)
- **Password Generator** - Create strong passwords with custom rules
- **Security Center** - Identify weak/reused/outdated passwords
- **Settings** - Theme, auto-lock, clipboard timeout, change master password, backup/restore

## Security Notes

- **Local Only**: All data stays on your computer. No network transmission of credentials.
- **Encryption**: Sensitive fields encrypted with AES-256-GCM before database storage.
- **Key Management**: Encryption keys derived from master password with Argon2id, never persisted.
- **Authentication**: Master password verified via encrypted verifier; incorrect attempts don't leak info.
- **Session Security**: HttpOnly cookies, localhost-only origins, session locking.
- **Backups**: Exported as encrypted JSON with SHA-256 integrity checks. Never contain plaintext.
- **Password Generator**: Uses Python's `secrets` module (cryptographically secure).
- **No Telemetry**: No analytics, tracking, or external API calls.

## Database Location

- Database: `data/happycrypt.db`
- Backups: `backups/`

All paths are local to the application directory.

## Testing

Run automated tests:
```bash
pip install -r requirements.txt
pytest -q
```

Tests cover: encryption/decryption, tamper detection, authentication flows, vault CRUD, plaintext inspection (ensures no sensitive data stored unencrypted), backup export/import/integrity, password generator/analyzer, and unauthorized access protection.

## Project Structure

```
HappyCrypt/
├── backend/          # FastAPI backend (API, security, services)
├── frontend/         # Web UI (HTML, CSS, JS)
├── data/             # Local SQLite database (created on first run)
├── backups/          # Local backup storage
├── tests/            # Automated test suite
├── requirements.txt  # Dependencies
├── run.py            # Application launcher
└── README.md         # Documentation
```

## Development Checklist

- [x] Phase 1: Architecture and project setup
- [x] Phase 2: Database design and encryption engine
- [x] Phase 3: Master password authentication
- [x] Phase 4: Password vault and CRUD operations
- [x] Phase 5: Password generator and analyzer
- [x] Phase 6: Frontend design and implementation
- [x] Phase 7: Backend/frontend integration
- [x] Phase 8: Backup and restore
- [x] Phase 9: Security testing and debugging
- [x] Phase 10: Final packaging and documentation

## Limitations

- This is a local desktop application, not designed for multi-user or cloud sync
- Master password cannot be recovered - store it safely
- Clipboard clearing depends on OS/browser clipboard permissions
- Browser may have limitations on clipboard APIs in some contexts

**HappyCrypt - Your passwords, your privacy, your control.**
