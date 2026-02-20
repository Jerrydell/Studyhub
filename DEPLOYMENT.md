# 🚀 Production Deployment Guide

## 📋 Pre-Deployment Checklist

### Security
- [ ] Set strong `SECRET_KEY` in production
- [ ] Set `FLASK_ENV=production`
- [ ] Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure CORS if needed
- [ ] Set up rate limiting
- [ ] Configure database backups

### Performance
- [ ] Enable Gunicorn with multiple workers
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure caching
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Enable gzip compression
- [ ] Minify static files

### Monitoring
- [ ] Set up error logging
- [ ] Configure health checks
- [ ] Enable performance monitoring
- [ ] Set up uptime monitoring
- [ ] Configure alerts

---

## 🔧 Environment Setup

### 1. Generate Strong Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Create Production .env

```bash
# .env.production
FLASK_ENV=production
SECRET_KEY=your-generated-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/studyhub
```

### 3. Install Production Dependencies

```bash
pip install gunicorn psycopg2-binary
```

---

## 🗄️ Database Migration (SQLite → PostgreSQL)

### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### Create Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE studyhub;
CREATE USER studyhub_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE studyhub TO studyhub_user;
\q
```

### Update Configuration

```python
# config.py - Production
DATABASE_URL = 'postgresql://studyhub_user:your-password@localhost/studyhub'
```

### Run Migration

```bash
# Export data from SQLite (if needed)
# Then create tables in PostgreSQL
python migrate_db.py
```

---

## 🌐 Deployment Options

## Option 1: Render.com (Recommended - Free Tier Available)

### Steps:

1. **Prepare Repository**
```bash
# Create requirements.txt with all dependencies
pip freeze > requirements.txt

# Create Procfile
echo "web: gunicorn run:app" > Procfile

# Commit to Git
git init
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Deploy on Render**
- Go to https://render.com
- Connect your GitHub repository
- Choose "Web Service"
- Set build command: `pip install -r requirements.txt`
- Set start command: `gunicorn run:app`
- Add environment variables:
  ```
  FLASK_ENV=production
  SECRET_KEY=your-secret-key
  DATABASE_URL=your-postgres-url
  ```
- Click "Create Web Service"

3. **Add PostgreSQL**
- Create new PostgreSQL database on Render
- Copy the Internal Database URL
- Add to environment variables

---

## Option 2: Railway.app

### Steps:

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Initialize Project**
```bash
railway login
railway init
```

3. **Add PostgreSQL**
```bash
railway add
# Select PostgreSQL
```

4. **Deploy**
```bash
railway up
```

5. **Set Environment Variables**
```bash
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=your-secret-key
```

---

## Option 3: Heroku

### Steps:

1. **Install Heroku CLI**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Create Heroku App**
```bash
heroku login
heroku create studyhub-app
```

3. **Add PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
```

4. **Configure Environment**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
```

5. **Deploy**
```bash
git push heroku main
heroku run python migrate_db.py
heroku open
```

---

## Option 4: VPS (DigitalOcean, Linode, etc.)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx postgresql -y

# Create user
sudo adduser studyhub
sudo usermod -aG sudo studyhub
su - studyhub
```

### 2. Application Setup

```bash
# Clone repository
git clone your-repo-url
cd studyhub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3. Configure Gunicorn

Create `/etc/systemd/system/studyhub.service`:

```ini
[Unit]
Description=StudyHub Gunicorn Service
After=network.target

[Service]
User=studyhub
Group=www-data
WorkingDirectory=/home/studyhub/studyhub
Environment="PATH=/home/studyhub/studyhub/venv/bin"
EnvironmentFile=/home/studyhub/studyhub/.env
ExecStart=/home/studyhub/studyhub/venv/bin/gunicorn --workers 3 --bind unix:studyhub.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
```

### 4. Configure Nginx

Create `/etc/nginx/sites-available/studyhub`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/studyhub/studyhub/studyhub.sock;
    }

    location /static {
        alias /home/studyhub/studyhub/app/static;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/studyhub /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Start Services

```bash
sudo systemctl start studyhub
sudo systemctl enable studyhub
sudo systemctl status studyhub
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Performance Optimization

### 1. Gunicorn Configuration

```python
# gunicorn_config.py
workers = 4  # (2 x CPU cores) + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
```

Run with:
```bash
gunicorn -c gunicorn_config.py run:app
```

### 2. Database Connection Pooling

```python
# config.py
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_MAX_OVERFLOW = 20
```

### 3. Add Database Indexes

```python
# In migration or models
CREATE INDEX idx_subject_user ON subjects(user_id);
CREATE INDEX idx_note_subject ON notes(subject_id);
CREATE INDEX idx_note_updated ON notes(updated_at);
```

### 4. Nginx Caching

```nginx
location /static {
    alias /path/to/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 📈 Monitoring & Logging

### 1. Application Logging

```python
# In create_app()
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/studyhub.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('StudyHub startup')
```

### 2. Error Tracking (Optional)

**Sentry:**
```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 3. Health Check Endpoint

```python
# In routes.py
@main_bp.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

---

## 🔒 Security Hardening

### 1. Rate Limiting

```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

### 2. Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 3. Database Backups

```bash
# Automated PostgreSQL backup
0 2 * * * pg_dump studyhub > /backups/studyhub_$(date +\%Y\%m\%d).sql
```

---

## 📱 Domain & DNS Setup

### 1. Purchase Domain
- Namecheap
- Google Domains
- Cloudflare

### 2. Configure DNS

**A Record:**
```
Type: A
Name: @
Value: your-server-ip
TTL: 3600
```

**CNAME Record (www):**
```
Type: CNAME
Name: www
Value: your-domain.com
TTL: 3600
```

---

## ✅ Post-Deployment Testing

```bash
# Test application
curl https://your-domain.com/health

# Test SSL
curl -I https://your-domain.com

# Load test (optional)
ab -n 1000 -c 100 https://your-domain.com/

# Security scan
nmap your-domain.com
```

---

## 📊 Monitoring Services

### Free Options:
- **UptimeRobot**: Uptime monitoring
- **Pingdom**: Website monitoring
- **Google Analytics**: Usage analytics
- **Sentry**: Error tracking

---

## 🚨 Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo journalctl -u studyhub -n 50

# Check Gunicorn
ps aux | grep gunicorn

# Test manually
gunicorn --bind 0.0.0.0:8000 run:app
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U studyhub_user -d studyhub -h localhost

# Check connection string
echo $DATABASE_URL
```

### Static Files Not Loading
```bash
# Collect static files
python -c "from app import create_app; app = create_app(); print(app.static_folder)"

# Check Nginx config
sudo nginx -t
```

---

## 📝 Maintenance

### Regular Tasks:
- **Daily**: Check logs for errors
- **Weekly**: Review analytics
- **Monthly**: Update dependencies
- **Quarterly**: Security audit

### Update Application:
```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart studyhub
```

---

## 🎉 Launch Checklist

- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Database migrated
- [ ] Environment variables set
- [ ] Application running
- [ ] Nginx configured
- [ ] Backups scheduled
- [ ] Monitoring enabled
- [ ] Error tracking setup
- [ ] Load testing completed
- [ ] Security scan passed

---

**Congratulations! StudyHub is production-ready!** 🚀

For support: Check logs, review documentation, or consult Flask community.
