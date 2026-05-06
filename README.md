# envault

> A lightweight utility to manage and encrypt per-project `.env` files with team-sharing support via GPG keys.

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

**Initialize envault in your project:**
```bash
envault init
```

**Encrypt your `.env` file for your team:**
```bash
envault lock --recipients alice@example.com bob@example.com
```

**Decrypt and load the `.env` file:**
```bash
envault unlock
```

**Run a command with the decrypted environment loaded:**
```bash
envault run -- python app.py
```

**Check which recipients can decrypt the current vault:**
```bash
envault recipients
```

Your encrypted `.env.vault` file can be safely committed to version control. The plaintext `.env` is never exposed to the repository.

---

## How It Works

1. `envault init` sets up a `.vault` config file in your project root.
2. `envault lock` encrypts your `.env` using the GPG public keys of specified recipients.
3. `envault unlock` decrypts `.env.vault` using your local GPG private key.
4. `envault recipients` lists the GPG key IDs that can decrypt the current `.env.vault`.
5. Team members only need their own GPG key to decrypt — no shared secrets required.

---

## Requirements

- Python 3.8+
- GPG (`gpg` must be available on your system PATH)

---

## License

MIT © 2024 — see [LICENSE](LICENSE) for details.
