# ⚡ Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
python --version  # Should be 3.8+
```

## 1. Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/SGP_FB.git
cd SGP_FB

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure Secrets (1 minute)

```bash
# Create secrets directory
mkdir .streamlit

# Copy example file
# Windows:
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# Linux/Mac:
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:
```toml
[mongo]
uri = "your_mongodb_connection_string"

[gemini]
api_key = "your_gemini_api_key"
```

## 3. Add Model Files (1 minute)

Place your LegalBERT model in:
```
archive_new/legalbert_supreme/
```

Required files: `config.json`, `model.safetensors`, `tokenizer.json`, etc.

## 4. Run! (1 minute)

```bash
streamlit run archive_new/app.py
```

Open browser at `http://localhost:8501` 🎉

## Need Help?

- 📖 Full setup: See [SETUP.md](SETUP.md)
- 🐛 Issues: Check [README.md](README.md) troubleshooting section
- 💬 Questions: Open a GitHub issue

---

**That's it! You're ready to go!** 🚀

