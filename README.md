# envault

> Lightweight utility to encrypt and sync `.env` files across team members using GPG keys.

---

## Installation

```bash
pip install envault
```

Or install from source:

```bash
pip install git+https://github.com/yourorg/envault.git
```

---

## Usage

**Encrypt and share your `.env` file with a teammate:**

```bash
# Encrypt .env for a specific recipient using their GPG key
envault encrypt .env --recipient teammate@example.com

# Decrypt a received .env file
envault decrypt .env.gpg --output .env

# Sync encrypted .env to all team members listed in .envault.yml
envault sync
```

**Example `.envault.yml` config:**

```yaml
recipients:
  - alice@example.com
  - bob@example.com
source: .env
output: .env.gpg
```

**Import a teammate's GPG key:**

```bash
envault add-key --keyserver keys.openpgp.org --email alice@example.com
```

---

## Requirements

- Python 3.8+
- GPG installed and configured on your system

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Contributions welcome — open an issue or submit a pull request.*