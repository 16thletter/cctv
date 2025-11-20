# Environment Variables Setup

## Overview

This project uses environment variables to securely store sensitive configuration like RTSP camera URLs with credentials. This prevents accidentally committing passwords to version control.

## Quick Setup

### 1. Install python-dotenv

```bash
pip install python-dotenv
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Create your .env file

Copy the example file:

```bash
cp .env.example .env
```

### 3. Edit .env with your actual RTSP URL

```bash
nano .env  # or use your preferred editor
```

Add your actual RTSP URL:

```env
RTSP_URL=rtsp://admin:YOUR_PASSWORD@60.254.111.210:555/stream1
```

### 4. Run the application

The application will automatically load the RTSP URL from the `.env` file:

```bash
python main.py
```

## How It Works

1. **`.env` file** - Contains your actual credentials (NOT committed to git)
2. **`.env.example`** - Template file (safe to commit)
3. **`.gitignore`** - Already configured to ignore `.env` files
4. **`src/utils.py`** - Loads environment variables and overrides config

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RTSP_URL` | Full RTSP camera URL with credentials | `rtsp://user:pass@ip:port/stream` |

## Security Best Practices

✅ **DO:**
- Keep `.env` file local only (already in `.gitignore`)
- Use `.env.example` as a template for others
- Share credentials through secure channels (not git)
- Use strong passwords for camera access

❌ **DON'T:**
- Commit `.env` file to git
- Put credentials in `config.yaml`
- Share `.env` file in public channels
- Use default camera passwords

## Troubleshooting

### Environment variable not loading

Make sure:
1. `.env` file exists in project root
2. `python-dotenv` is installed
3. Variable name is exactly `RTSP_URL`
4. No spaces around the `=` sign

### Still using config.yaml source

The environment variable takes precedence. If `RTSP_URL` is set in `.env`, it will override the `source` in `config.yaml`.

To verify:
```python
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv('RTSP_URL'))
```

## Alternative: Command Line Override

You can also override the source via command line:

```bash
python main.py --source "rtsp://admin:password@192.168.1.100:555/stream1"
```

But this is less secure as the password may be visible in process lists.

## For Production/Deployment

For production environments, set environment variables directly in your system:

**Linux/Mac:**
```bash
export RTSP_URL="rtsp://admin:password@ip:port/stream"
python main.py
```

**Windows:**
```cmd
set RTSP_URL=rtsp://admin:password@ip:port/stream
python main.py
```

**Docker:**
```yaml
environment:
  - RTSP_URL=rtsp://admin:password@ip:port/stream
```

**Systemd Service:**
```ini
[Service]
Environment="RTSP_URL=rtsp://admin:password@ip:port/stream"
```

