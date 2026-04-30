# envault

> Secure environment variable manager that syncs encrypted `.env` files across team members via a shared backend.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Initialize a new vault in your project:**

```bash
envault init
```

**Push your local `.env` to the shared backend:**

```bash
envault push
```

**Pull the latest secrets to your local `.env`:**

```bash
envault pull
```

**Add or update a single secret:**

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

**List all stored keys (values are hidden by default):**

```bash
envault list
```

All secrets are encrypted client-side before being sent to the backend. Your plaintext values never leave your machine unencrypted.

---

## Configuration

On first run, `envault init` creates a `.envault.toml` config file in your project root where you can specify the backend URL and encryption settings. Add `.envault.toml` to version control and keep your `.env` in `.gitignore`.

---

## License

MIT © [envault contributors](LICENSE)