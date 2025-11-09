# ⚖️ Adhikar.ai - Legal AI Assistant

A comprehensive legal AI assistant application for predicting Supreme Court case outcomes and providing general legal aid information. Built with Streamlit, LegalBERT, and Google Gemini AI.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

### 🏛️ Case Outcome Prediction
- **LegalBERT Model**: Fine-tuned model for Supreme Court of India case prediction
- **Document Upload**: Upload PDF/Image files containing case details
- **Text Extraction**: Automatic OCR and text extraction from documents
- **Smart Prediction**: Predicts "Appeal Dismissed" or "Appeal Allowed" with confidence scores
- **Detailed Explanations**: AI-powered legal reasoning using Google Gemini

### 💬 General Legal Aid
- **Indian Law Information**: Comprehensive information about Indian legal system
- **Step-by-step Guidance**: Actionable steps for legal issues
- **Legal References**: Relevant Indian laws and statutes
- **Contact Information**: Authorities and organizations to contact

### 🔐 Security & User Management
- **User Authentication**: Secure login/registration with bcrypt password hashing
- **Session Management**: Persistent chat sessions across page refreshes
- **Data Security**: SHA-256 message hashing for integrity verification
- **User-specific Data**: Isolated data per user account

### 🌐 Multilingual Support
- **English**: Full support
- **Hindi (हिंदी)**: Complete UI and response translation
- **Gujarati (ગુજરાતી)**: Complete UI and response translation
- **Font Support**: Optimized fonts for Devanagari and Gujarati scripts

### 📊 Additional Features
- **Chat History**: Persistent conversation history in MongoDB
- **Real-time Streaming**: Live response streaming for better UX
- **Document Processing**: OCR support for scanned documents
- **Session Management**: Load and manage previous chat sessions

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (free tier works)
- Google Gemini API key (optional but recommended)
- Tesseract OCR (optional, for better image OCR support)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/SGP_FB.git
cd SGP_FB
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.streamlit` folder in the project root and add a `secrets.toml` file:

```bash
mkdir .streamlit
```

Create `.streamlit/secrets.toml`:

```toml
[mongo]
uri = "your_mongodb_atlas_connection_string"

[gemini]
api_key = "your_gemini_api_key"

[ocr]
tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"  # Windows only, optional
```

**OR** set environment variables:

```bash
# Windows (PowerShell)
$env:MONGODB_URI="your_mongodb_atlas_connection_string"
$env:GEMINI_API_KEY="your_gemini_api_key"

# Linux/Mac
export MONGODB_URI="your_mongodb_atlas_connection_string"
export GEMINI_API_KEY="your_gemini_api_key"
```

### 5. Set Up LegalBERT Model

Place your fine-tuned LegalBERT model files in:
```
archive_new/legalbert_supreme/
```

Required files:
- `config.json`
- `model.safetensors` or `pytorch_model.bin`
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.txt`
- `special_tokens_map.json`

> **Note**: Model files are excluded from git due to size. You'll need to add your trained model separately.

### 6. Run the Application

```bash
streamlit run archive_new/app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Detailed Setup Instructions

### MongoDB Atlas Setup

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for a free account

2. **Create a Cluster**
   - Create a new cluster (free tier M0 works)
   - Wait for cluster to be created

3. **Create Database User**
   - Go to Database Access
   - Add new database user
   - Save username and password

4. **Whitelist IP Address**
   - Go to Network Access
   - Add IP address (0.0.0.0/0 for development)

5. **Get Connection String**
   - Go to Clusters → Connect → Connect your application
   - Copy the connection string
   - Replace `<password>` with your database user password

### Google Gemini API Setup

1. **Get API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with Google account
   - Create new API key
   - Copy the API key

2. **Add to Configuration**
   - Add to `.streamlit/secrets.toml` or set as environment variable

### Tesseract OCR Setup (Optional)

For better OCR support on scanned documents:

**Windows:**
1. Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and note the installation path
3. Add path to `secrets.toml` or environment variable

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-hin tesseract-ocr-guj  # For Hindi/Gujarati
```

**Mac:**
```bash
brew install tesseract
brew install tesseract-lang  # For additional languages
```

## 🏗️ Project Structure

```
SGP_FB/
├── archive_new/
│   ├── app.py                    # Main Streamlit application
│   └── legalbert_supreme/        # LegalBERT model directory (not in git)
├── .streamlit/
│   └── secrets.toml              # Configuration secrets (not in git)
├── venv/                         # Virtual environment (not in git)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── .gitignore                    # Git ignore rules
└── MULTILINGUAL_IMPLEMENTATION.md # Multilingual feature docs
```

## 🔧 Configuration

### Database Collections

The app uses the following MongoDB collections:
- `chat_messages`: Stores chat history and messages
- `users`: Stores user accounts and authentication data
- `documents`: Stores document metadata (if using vector search)
- `doc_chunks`: Stores document chunks with embeddings (if using vector search)

### Model Configuration

Edit `MODEL_DIR` in `app.py` to change model location:
```python
MODEL_DIR = "archive_new/legalbert_supreme"
```

## 🎯 Usage

### Case Outcome Prediction

1. Select "🏛️ Case Outcome Prediction" mode
2. (Optional) Upload a PDF/Image document containing case details
3. Type your case details or query (e.g., "predict the case outcome and explain")
4. View the prediction and detailed legal explanation

### General Legal Aid

1. Select "💬 General Legal Aid" mode
2. Type your legal question
3. Get comprehensive information about Indian laws and procedures

## 🛠️ Development

### Running in Development Mode

```bash
streamlit run archive_new/app.py --server.headless true
```

### Adding New Languages

1. Add language to `SUPPORTED_LANGUAGES` in `app.py`
2. Add translations to `UI_TRANSLATIONS`
3. Update language selector

### Customizing Models

To use a different model:
1. Update `MODEL_DIR` path
2. Ensure model format matches expected structure
3. Update class labels in `predict_outcome()` function

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Recommended |
| `TESSERACT_CMD` | Path to Tesseract executable | Optional |

## 🐛 Troubleshooting

### Model Not Loading
- Check if model directory exists at `archive_new/legalbert_supreme/`
- Verify all required model files are present
- Check file permissions

### MongoDB Connection Failed
- Verify connection string is correct
- Check IP whitelist in MongoDB Atlas
- Ensure database user has proper permissions

### Gemini API Errors
- Verify API key is correct
- Check API quota/limits
- Ensure internet connection

### OCR Not Working
- Install Tesseract OCR
- Set correct path in `TESSERACT_CMD`
- For multilingual OCR, install language packs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👥 Authors

- Your Name - [Your GitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- LegalBERT model based on Hugging Face Transformers
- Google Gemini AI for legal explanations
- Streamlit for the web framework
- MongoDB Atlas for database hosting

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**⚠️ Disclaimer**: This application is for informational purposes only and does not constitute legal advice. Always consult with a qualified lawyer for legal matters.
