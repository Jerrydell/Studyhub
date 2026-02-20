# 🚀 StudyHub - Production Deployment Guide

## 📋 Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Database migrated
- [ ] SECRET_KEY set in environment
- [ ] DEBUG = False
- [ ] CSRF enabled
- [ ] HTTPS configured
- [ ] Database backups configured

---

## 🌐 Deployment Options

### Option 1: Render (Recommended for Beginners)

#### Step 1: Prepare Your Repository
```bash
# Ensure .gitignore includes
venv/
*.db
.env
__pycache__/
```

#### Step 2: Create `render.yaml`
```yaml
services:
  - type: web
    name: studyhub
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn run:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: studyhub_db
          property: connectionString

databases:
  - name: studyhub_db
    databaseName: studyhub
    user: studyhub
```

#### Step 3: Deploy
1. Push code to GitHub
2. Connect Render to your repository
3. Click "New > Web Service"
4. Select repository
5. Render auto-deploys!

---

### Option 2: Railway

#### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
railway login
```

#### Step 2: Initialize Project
```bash
railway init
railway add postgresql
```

#### Step 3: Set Environment Variables
```bash
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

#### Step 4: Deploy
```bash
railway up
```

---

### Option 3: Heroku

#### Step 1: Create `Procfile`
```
web: gunicorn run:app
```

#### Step 2: Create `runtime.txt`
```
python-3.12.3
```

#### Step 3: Deploy
```bash
heroku create studyhub-app
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python migrate_db.py
heroku open
```

---

### Option 4: DigitalOcean App Platform

#### Step 1: Create App Spec
```yaml
name: studyhub
services:
- name: web
  github:
    repo: your-username/studyhub
    branch: main
  build_command: pip install -r requirements.txt
  run_command: gunicorn run:app
  environment_slug: python
  envs:
  - key: FLASK_ENV
    value: production
  - key: SECRET_KEY
    type: SECRET
databases:
- name: db
  engine: PG
  version: "14"
```

---

### Option 5: VPS (Ubuntu Server)

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx supervisor postgresql -y
```

#### Step 2: Application Setup
```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/your-username/studyhub.git
cd studyhub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3: PostgreSQL Setup
```bash
sudo -u postgres psql

CREATE DATABASE studyhub;
CREATE USER studyhub WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE studyhub TO studyhub;
\q
```

#### Step 4: Environment Variables
```bash
# Create .env file
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql://studyhub:secure_password@localhost/studyhub
EOF
```

#### Step 5: Gunicorn Setup
```bash
# Test Gunicorn
gunicorn run:app --bind 0.0.0.0:8000
```

#### Step 6: Supervisor Configuration
```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/studyhub.conf
```

```ini
[program:studyhub]
directory=/var/www/studyhub
command=/var/www/studyhub/venv/bin/gunicorn run:app --workers 3 --bind unix:/var/www/studyhub/studyhub.sock
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/studyhub/err.log
stdout_logfile=/var/log/studyhub/out.log
```

```bash
# Create log directory
sudo mkdir -p /var/log/studyhub
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start studyhub
```

#### Step 7: Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/studyhub
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://unix:/var/www/studyhub/studyhub.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/studyhub/app/static;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/studyhub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 8: SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 🔒 Security Checklist

### Environment Variables
```bash
# Generate strong secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Security
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Strong database password
- [ ] Database user with limited privileges
- [ ] Regular automated backups

### Application Security
- [ ] `DEBUG = False`
- [ ] `SESSION_COOKIE_SECURE = True` (requires HTTPS)
- [ ] `CSRF_ENABLED = True`
- [ ] Strong `SECRET_KEY`
- [ ] Firewall configured
- [ ] Rate limiting enabled

### Updates
```bash
# Regular security updates
pip install --upgrade -r requirements.txt
```

---

## 📊 Monitoring

### Application Logs
```bash
# View logs (Supervisor)
sudo tail -f /var/log/studyhub/out.log
sudo tail -f /var/log/studyhub/err.log

# View logs (Nginx)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Monitoring
```bash
# PostgreSQL connections
SELECT * FROM pg_stat_activity;

# Database size
SELECT pg_size_pretty(pg_database_size('studyhub'));
```

---

## 💾 Backup Strategy

### Database Backups
```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/var/backups/studyhub"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump studyhub > $BACKUP_DIR/studyhub_$DATE.sql
gzip $BACKUP_DIR/studyhub_$DATE.sql
find $BACKUP_DIR -mtime +30 -delete  # Keep 30 days
```

### Automated Backups (Cron)
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /usr/local/bin/backup_studyhub.sh
```

---

## 🔄 Continuous Deployment

### GitHub Actions Example
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /var/www/studyhub
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python migrate_db.py
            sudo supervisorctl restart studyhub
```

---

## 📈 Performance Optimization

### Database Indexing
```sql
-- Already implemented in models, verify:
CREATE INDEX idx_subjects_user_id ON subjects(user_id);
CREATE INDEX idx_notes_subject_id ON notes(subject_id);
```

### Gunicorn Workers
```bash
# Calculate optimal workers: (2 × CPU cores) + 1
# For 2 cores: 5 workers
gunicorn run:app --workers 5 --bind 0.0.0.0:8000
```

### Caching (Optional)
```python
# Install Flask-Caching
pip install Flask-Caching

# In app/__init__.py
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U studyhub -d studyhub -h localhost
```

#### 2. Permission Errors
```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/studyhub
sudo chmod -R 755 /var/www/studyhub
```

#### 3. 502 Bad Gateway
```bash
# Check Gunicorn is running
sudo supervisorctl status studyhub

# Restart if needed
sudo supervisorctl restart studyhub
```

#### 4. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic  # If using Flask-Static

# Check Nginx config
sudo nginx -t
```

---

## 📞 Support Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Gunicorn Documentation**: https://gunicorn.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Nginx Documentation**: https://nginx.org/en/docs/

---

## ✅ Post-Deployment Checklist

- [ ] Application accessible via domain
- [ ] HTTPS working (green padlock)
- [ ] Database populated and working
- [ ] Can create account and login
- [ ] Can create subjects and notes
- [ ] Search functionality working
- [ ] All features tested
- [ ] Error pages working
- [ ] Logs being written
- [ ] Backups configured
- [ ] Monitoring in place

---

**Congratulations!** 🎉

Your StudyHub application is now live in production!

---

*Remember: Keep your dependencies updated and monitor your logs regularly* 🚀
