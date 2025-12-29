# 🛡️ AI Phishing Detector

**An intelligent system for detecting phishing messages and AI-generated threats in Gmail**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com)


## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Gmail API Setup](#gmail-api-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project implements an intelligent phishing detection system that:

1. **Scans Gmail inboxes** for potential phishing emails
2. **Analyzes links** using multi-factor heuristics
3. **Detects AI-generated content** using advanced algorithms
4. **Classifies threats** into three categories: Safe, Phishing, and AI-Generated Phishing

### Why This Matters

With the rise of AI tools like ChatGPT, phishing attacks have become more sophisticated. Traditional detection methods struggle to identify AI-generated phishing emails that appear legitimate. This system addresses this gap by combining traditional phishing detection with AI content analysis.

## ✨ Features

### 🔐 Multi-User Support
- User registration and authentication
- Personal dashboards for each user
- Individual Gmail connections
- Secure OAuth 2.0 authentication

### 📧 Email Scanning
- Automatic Gmail inbox scanning
- Link extraction and analysis
- Full email content examination
- Batch processing capabilities

### 🔍 Phishing Detection
- **URL Analysis**: Checks for suspicious TLDs, IP addresses, redirects
- **Domain Age**: Identifies newly created domains
- **HTTPS Verification**: Ensures secure connections
- **Brand Impersonation**: Detects fake domains mimicking legitimate brands
- **Risk Scoring**: Assigns risk levels (Low, Medium, High, Critical)

### 🤖 AI Content Detection
- **Perplexity Analysis**: Measures text predictability
- **Burstiness Scoring**: Analyzes sentence variation
- **Pattern Matching**: Identifies common AI phrases
- **Uniformity Checks**: Detects repetitive structures
- **Confidence Scoring**: Provides detection confidence levels

### 📊 Reporting & Analytics
- Real-time threat dashboards
- Detailed email analysis reports
- Historical scan tracking
- Statistical summaries

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│         (HTML/TailwindCSS + Django Templates)            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                  Django Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Auth System  │  │ Email Views  │  │  API Endpoints│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Detection Engine                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Gmail Client  │  │Link Analyzer │  │ AI Detector  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│         (SQLite/PostgreSQL Database)                     │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│         (Gmail API, WHOIS, ML Models)                    │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Gmail account for testing
- Google Cloud Platform account (for Gmail API)

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/S-cloud-tech/phishingDetector.git
cd phishingDetector
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up Django project**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. **Run the development server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 🔑 Gmail API Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project"
3. Name it "Phishing Detector"
4. Click "Create"

### Step 2: Enable Gmail API

1. Navigate to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on it and press "Enable"

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in required fields:
   - App name: "AI Phishing Detector"
   - User support email: your email
   - Developer contact: your email
4. Add scope: `https://www.googleapis.com/auth/gmail.readonly`
5. Add test users (your Gmail addresses)
6. Save and continue

### Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web"
4. Name it "Phishing Detector Client"
5. Download the JSON file
6. Rename it to `credentials.json`
7. Place it in the project root directory

### Important Notes

- The `credentials.json` file should be kept secure
- Add `credentials.json` and `token.pickle` to `.gitignore`
- Each user will get their own OAuth token

## 📖 Usage

### For First-Time Users

1. **Register an Account**
   - Visit the landing page
   - Click "Get Started Free"
   - Fill in registration form OR Click Connect with Google

2. **Connect Gmail**
   - After registration, you'll be redirected to Gmail connection
   - Click "Connect with Google"
   - Grant read-only permissions
   - You'll be redirected back to dashboard

3. **Scan Your Inbox**
   - Click "Start Scan" button
   - Wait for the scan to complete
   - View results on dashboard

4. **Review Emails**
   - Click on any email for detailed analysis
   - View phishing indicators
   - Check AI detection results
   - See link analysis

### For Returning Users

1. Login with username/password OR connect with gmail
2. Dashboard shows previous scan results
3. Click "Start Scan" for new scan
4. View profile to see statistics

## 📁 Project Structure

```
phishing-detector/
├── README.md
├── .gitignore
├── requirements.txt
├── credentials.json              # Gmail API (not in repo) get it after step 
├── manage.py
├── setup.sh                      # Quick setup script
│
├── core/            # Django project
│   ├── __init__.py
│   ├── settings.py              # Project settings
│   ├── urls.py                  # URL routing
│   └── wsgi.py
│
├── detector/                     # Main app
│    ├── models.py                # Database models
│    ├── views.py                 # Authentication\Dashboard views
│    ├── gmail_client.py          # Gmail integration
│    ├── link_analyzer.py         # Phishing detection
│    ├── ai_detector.py           # AI text detection
│    ├── urls.py                  # URL routing
│    │
│    └── templates/
│       ├── auth/
│       |    ├── register.html    # User registration
│       |    ├── login.html       # User login     
│       ├── detector/    
│       |    ├── dashboard.html   # Main dashboard
│       |    ├── connect_gmail.html
│       |    ├── email_list.html
│       |    └── email_detail.html
│       ├── profile/
│       |    ├── profile.html      # User profile
│       └── index.html
│
└── tests/
      ├── test_gmailclient.py
      └── test_messages.py
```

## 🛠️ Technology Stack

### Backend
- **Django 5.2** - Web framework
- **Python 3.13+** - Programming language
- **SQLite/PostgreSQL** - Database
- **Gmail API** - Email access
- **OAuth 2.0** - Authentication

### Frontend
- **HTML5** - Markup
- **TailwindCSS** - Styling
- **Font Awesome** - Icons
- **JavaScript** - Interactivity

### Detection Algorithms
- **Custom Heuristics** - Link analysis
- **NLP Techniques** - Text analysis
- **Machine Learning** - AI detection
- **WHOIS** - Domain information

## 🧪 Testing

### Test Scenarios

#### 1. Safe Email Test
```
From: notifications@google.com
Links: https://www.google.com
Expected: SAFE classification
```

#### 2. Phishing Email Test
```
From: security@paypal-verify.xyz
Links: http://192.168.1.1/login
Expected: HIGH/CRITICAL risk
```

#### 3. AI-Generated Phishing Test
```
Text contains: "It is important to note..."
Links: Suspicious URLs
Expected: AI-GENERATED PHISHING
```

### Running Tests

```bash
python manage.py test
```

### Manual Testing

1. Create test Gmail account
2. Send yourself test emails
3. Scan and verify detection
4. Check all three categories appear

## 📊 Detection Metrics

### Link Analysis Scoring

| Indicator | Score | Risk Level |
|-----------|-------|------------|
| IP Address | +25 | High |
| Suspicious TLD | +20 | Medium |
| No HTTPS | +15 | Medium |
| Multiple Redirects | +15 | Medium |
| New Domain (<30 days) | +25 | High |
| Long URL (>75 chars) | +10 | Low |

**Risk Levels:**
- 0-20: LOW
- 20-50: MEDIUM
- 50-75: HIGH
- 75+: CRITICAL

### AI Detection Confidence

| Score | Level | Meaning |
|-------|-------|---------|
| 0-0.3 | LOW | Likely Human |
| 0.3-0.6 | MEDIUM | Uncertain |
| 0.6-0.8 | HIGH | Likely AI |
| 0.8-1.0 | VERY HIGH | Almost Certainly AI |

## 🎓 Academic Use

This project was developed as a Masters thesis to demonstrate:

1. **Novel Approach**: Combining traditional phishing detection with AI content analysis
2. **Practical Implementation**: Working system with real Gmail integration
3. **Scalability**: Multi-user support and efficient processing
4. **Research Value**: Contributes to cybersecurity and AI detection fields

### Citing This Work

```
[Your Name]. (2024). AI Phishing Detection System: 
An Intelligent Approach to Identifying Phishing and AI-Generated Threats. 
[Your University]. Masters Thesis.
```

## 🤝 Contributing

This is an academic project, but contributions are welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open Pull Request

## 📝 License

This project is for academic and educational purposes only.

## 🙏 Acknowledgments

- Google Gmail API for email access
- Django framework for rapid development
- TailwindCSS for modern UI design
- Academic advisors and reviewers

## 📧 Contact

For questions or collaboration:
- Email: 
- GitHub: 
- LinkedIn: 

## 🔮 Future Enhancements

- [ ] Real-time monitoring with webhooks
- [ ] Mobile application (iOS/Android)
- [ ] Browser extension for real-time scanning
- [ ] Advanced ML models for detection
- [ ] Multi-language support
- [ ] Export reports (PDF/CSV)
- [ ] Collaborative threat intelligence
- [ ] Email client integration (Outlook, Yahoo)

---

**Built for cybersecurity research**
