# 📚 StudyHub - Student Productivity Platform

A professional, production-ready Flask web application for students to manage their studies, subjects, and notes.

## 🚀 Features

- ✅ Secure user authentication (registration & login)
- ✅ Dashboard with subject management
- ✅ Notes system with full CRUD operations
- ✅ Modern, mobile-responsive UI
- ✅ Professional folder structure with application factory pattern
- ✅ Database migrations support
- ✅ Production-ready configuration

## 🛠️ Tech Stack

- **Backend**: Flask 3.0
- **Database**: SQLAlchemy (SQLite for dev, PostgreSQL for production)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF with CSRF protection
- **Migrations**: Flask-Migrate
- **Frontend**: Bootstrap 5 / Tailwind CSS (to be implemented)

## 📁 Project Structure

```
studyhub/
│
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── routes.py            # URL routes (blueprints)
│   ├── forms.py             # WTForms definitions
│   ├── extensions.py        # Flask extensions
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
│
├── config.py                # Configuration classes
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
└── .gitignore              # Git ignore rules
```

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd studyhub
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
# Copy .env template and edit with your values
cp .env.example .env
```

### 5. Initialize database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Run the application
```bash
python run.py
```

Visit: `http://localhost:5000`

## 🔒 Security Features

- ✅ Password hashing with Werkzeug
- ✅ CSRF protection on all forms
- ✅ Secure session cookies
- ✅ Environment-based configuration
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ Login required decorators

## 🌐 Deployment

### Production Checklist
- [ ] Set strong `SECRET_KEY` in environment
- [ ] Use PostgreSQL database
- [ ] Set `FLASK_ENV=production`
- [ ] Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Use Gunicorn as WSGI server
- [ ] Configure reverse proxy (Nginx)

### Deploy to Render/Railway
```bash
# Ensure gunicorn is in requirements.txt
gunicorn run:app
```

## 👨‍💻 Development

### Database Migrations
```bash
# Create migration after model changes
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📝 License

MIT License - feel free to use for your projects

## 🤝 Contributing

Pull requests welcome! Please follow the existing code structure.

---

Built with ❤️ using Flask
