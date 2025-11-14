# 🚀 Complete Setup Guide

This guide will walk you through setting up Adhikar.ai from scratch.

## Step 1: Prerequisites Check

Ensure you have:
- ✅ Python 3.8 or higher installed
- ✅ Git installed
- ✅ Internet connection

Check Python version:
```bash
python --version
# or
python3 --version
```

## Step 2: Clone Repository

```bash
git clone https://github.com/neminharia/Adhikar.ai.git
cd SGP_FB
```

## Step 3: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- Streamlit (web framework)
- PyMongo (MongoDB driver)
- Transformers (LegalBERT)
- Torch (PyTorch)
- Google Generative AI
- PyMuPDF (PDF processing)
- Tesseract OCR bindings
- And other dependencies

## Step 5: MongoDB Atlas Setup

### 5.1 Create Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Click "Try Free"
3. Sign up with email or Google account

### 5.2 Create Cluster
1. Choose "Build a Database" → Free tier (M0)
2. Select cloud provider and region (closest to you)
3. Click "Create"
4. Wait 3-5 minutes for cluster creation

### 5.3 Create Database User
1. Go to "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Enter username and generate secure password
5. **Save the password** - you'll need it!
6. Set user privileges to "Atlas admin" (for development)
7. Click "Add User"

### 5.4 Whitelist IP Address
1. Go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

### 5.5 Get Connection String
1. Go to "Database" → "Connect"
2. Choose "Connect your application"
3. Select "Python" and version "3.6 or later"
4. Copy the connection string
5. Replace `<password>` with your database user password
6. Replace `<dbname>` with `court_chat_db` (or your preferred name)

Example:
```
mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/court_chat_db?retryWrites=true&w=majority
```

## Step 6: Google Gemini API Setup

### 6.1 Get API Key
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the API key

### 6.2 (Optional) Set Usage Limits
1. Go to Google Cloud Console
2. Set up billing (free tier available)
3. Set usage quotas to prevent unexpected charges

## Step 7: Configure Application

### 7.1 Create Secrets Directory
```bash
mkdir .streamlit
```

### 7.2 Create Secrets File
Copy the example file:
```bash
# Windows
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# Linux/Mac
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### 7.3 Edit Secrets File
Open `.streamlit/secrets.toml` and fill in:

```toml
[mongo]
uri = "mongodb+srv://youruser:yourpassword@cluster0.xxxxx.mongodb.net/court_chat_db?retryWrites=true&w=majority"

[gemini]
api_key = "your_actual_gemini_api_key_here"

[ocr]
# Windows only - path to Tesseract installation
tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
```

**⚠️ Important**: Never commit `secrets.toml` to git!

## Step 8: Install Tesseract OCR (Optional but Recommended)

### Windows:
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer
3. Note installation path (usually `C:\Program Files\Tesseract-OCR`)
4. Add to `secrets.toml` as shown above

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-hin tesseract-ocr-guj  # For Hindi/Gujarati
```

### Mac:
```bash
brew install tesseract
brew install tesseract-lang
```

## Step 9: Add LegalBERT Model

The model files are too large for GitHub. You need to:

1. **If you have a trained model:**
   - Place model files in `archive_new/legalbert_supreme/`
   - Required files:
     - `config.json`
     - `model.safetensors` or `pytorch_model.bin`
     - `tokenizer.json`
     - `tokenizer_config.json`
     - `vocab.txt`
     - `special_tokens_map.json`

2. **If you need to train a model:**
   - Use `model_trainer.py` (if available)
   - Or train using Hugging Face Transformers
   - See model training documentation

3. **Verify model structure:**
   ```bash
   ls archive_new/legalbert_supreme/
   ```

## Step 10: Run the Application

```bash
streamlit run archive_new/app.py
```

The app will:
1. Start the Streamlit server
2. Open automatically in your browser at `http://localhost:8501`
3. Show login/register page

## Step 11: Create Your First Account

1. Click "📝 Register" tab
2. Enter:
   - Username
   - Email
   - Password
   - Confirm Password
3. Click "Register"
4. You'll see success message
5. Go to "🔑 Login" tab
6. Login with your credentials

## Step 12: Verify Everything Works

### Test Case Prediction:
1. Select "🏛️ Case Outcome Prediction"
2. Type a case summary
3. Check if prediction appears

### Test Document Upload:
1. Select "🏛️ Case Outcome Prediction"
2. Upload a PDF file
3. Type "predict the case outcome and explain"
4. Verify prediction works

### Test Legal Aid:
1. Select "💬 General Legal Aid"
2. Ask a legal question
3. Verify response appears

## Troubleshooting

### "MongoDB connection failed"
- ✅ Check connection string in `secrets.toml`
- ✅ Verify password doesn't have special characters (URL encode if needed)
- ✅ Check IP whitelist in MongoDB Atlas
- ✅ Ensure cluster is running

### "Model not loaded"
- ✅ Check if `archive_new/legalbert_supreme/` exists
- ✅ Verify all model files are present
- ✅ Check file permissions

### "Gemini API error"
- ✅ Verify API key is correct
- ✅ Check internet connection
- ✅ Verify API key has proper permissions

### "OCR not working"
- ✅ Install Tesseract OCR
- ✅ Set correct path in `secrets.toml` (Windows)
- ✅ For Linux/Mac, ensure Tesseract is in PATH

### "Port already in use"
```bash
# Find process using port 8501
# Windows
netstat -ano | findstr :8501

# Linux/Mac
lsof -i :8501

# Kill process or use different port
streamlit run archive_new/app.py --server.port 8502
```

## Next Steps

- ✅ Read the main README.md for feature details
- ✅ Check MULTILINGUAL_IMPLEMENTATION.md for language features
- ✅ Review TESTING_GUIDE.md for testing procedures
- ✅ Customize the application for your needs

## Getting Help

- 📖 Check documentation files
- 🐛 Open an issue on GitHub
- 💬 Check existing GitHub issues

---

**Happy Coding! 🎉**

