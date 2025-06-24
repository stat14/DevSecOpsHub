# Local Hosting Guide for Nexus Platform

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Node.js 20 or higher
- PostgreSQL 12+ (optional, defaults to SQLite)
- Redis (optional, for notifications)
- Git

### Hardware Requirements
- Minimum: 2GB RAM, 1 CPU core, 5GB disk space
- Recommended: 4GB RAM, 2 CPU cores, 10GB disk space

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd nexus-platform
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies (if needed)
```bash
npm install
```

### 4. Database Setup

#### Option A: SQLite (Default - Development)
No additional setup required. Database file will be created automatically.

#### Option B: PostgreSQL (Recommended for Production)
```bash
# Install PostgreSQL
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS (using Homebrew):
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE nexus_db;
CREATE USER nexus_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nexus_db TO nexus_user;
\q
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://nexus_user:your_password@localhost:5432/nexus_db
# Or for SQLite (default):
# DATABASE_URL=sqlite:///nexus.db

# Security Keys
SESSION_SECRET=your-super-secret-session-key-here
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=true
```

### 6. Redis Setup (Optional for Notifications)
```bash
# Ubuntu/Debian:
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS (using Homebrew):
brew install redis
brew services start redis

# Verify Redis is running:
redis-cli ping
# Should return: PONG
```

## Running the Application

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the application
python main.py

# Or using Flask directly:
flask run --host=0.0.0.0 --port=5000
```

### Production Mode
```bash
# Using Gunicorn (recommended for production)
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app

# Or with additional options:
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --timeout 120 \
         --keep-alive 2 \
         --max-requests 1000 \
         --max-requests-jitter 100 \
         main:app
```

## Default Admin Account

The application creates a default super admin account:
- **Email:** admin@nexus.local
- **Password:** admin123

**Important:** Change this password immediately after first login!

## Application Structure

```
nexus-platform/
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── models.py             # Database models
├── auth.py               # Authentication module
├── admin.py              # Admin panel
├── secure.py             # Security module
├── flow.py               # Development workflow
├── client.py             # Client portal
├── reports.py            # Report generation
├── analytics.py          # Advanced analytics
├── enhanced_reports.py   # Enhanced reporting
├── notifications.py      # Real-time notifications
├── rbac.py              # Role-based access control
├── ui_enhancements.py   # UI/UX enhancements
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
├── instance/            # Instance-specific files
└── requirements.txt     # Python dependencies
```

## Accessing the Application

1. **Web Interface:** http://localhost:5000
2. **Admin Dashboard:** http://localhost:5000/admin/dashboard
3. **Security Module:** http://localhost:5000/secure/dashboard
4. **Development Module:** http://localhost:5000/flow/dashboard
5. **Client Portal:** http://localhost:5000/client/dashboard
6. **Analytics:** http://localhost:5000/analytics/dashboard

## User Roles and Access

### Super Admin
- Full system access
- User management
- System configuration
- All module access

### Admin
- User management (limited)
- Project management
- All module access except system configuration

### Pentester
- Security module access
- Finding management
- Security report generation

### Developer
- Development module access
- Task management
- Kanban boards

### Client
- Read-only project access
- View assigned project status
- Download reports

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check database credentials
psql -U nexus_user -d nexus_db -h localhost
```

#### 2. Port Already in Use
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>
```

#### 3. Permission Errors
```bash
# Fix file permissions
chmod +x main.py
chown -R $USER:$USER .
```

#### 4. Python Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_finding_project_id ON finding(project_id);
CREATE INDEX idx_task_project_id ON task(project_id);
CREATE INDEX idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX idx_activity_log_timestamp ON activity_log(timestamp);
```

#### 2. Application Tuning
```bash
# Increase worker processes for production
gunicorn --workers $(nproc) --bind 0.0.0.0:5000 main:app

# Use a reverse proxy (nginx)
sudo apt-get install nginx
```

#### 3. Nginx Configuration (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/nexus-platform/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secrets for production
- Rotate secrets regularly

### 2. Database Security
- Use strong database passwords
- Limit database user permissions
- Enable SSL for database connections in production

### 3. Network Security
- Use HTTPS in production
- Configure firewall rules
- Consider VPN access for admin interfaces

### 4. Application Security
- Keep dependencies updated
- Enable CSRF protection
- Use secure session configurations
- Implement rate limiting

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump -U nexus_user -h localhost nexus_db > backup.sql

# SQLite backup
cp instance/nexus.db backup_nexus.db
```

### Application Backup
```bash
# Create complete backup
tar -czf nexus_backup_$(date +%Y%m%d).tar.gz \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=.git \
    .
```

### Recovery
```bash
# Restore PostgreSQL database
psql -U nexus_user -h localhost nexus_db < backup.sql

# Restore SQLite database
cp backup_nexus.db instance/nexus.db
```

## Monitoring and Logging

### Application Logs
```bash
# View application logs
tail -f logs/nexus.log

# Or if using systemd:
journalctl -u nexus -f
```

### System Monitoring
```bash
# Monitor system resources
htop

# Monitor application performance
ps aux | grep python
netstat -tlnp | grep :5000
```

## Updates and Maintenance

### Updating Dependencies
```bash
# Update Python packages
pip list --outdated
pip install --upgrade package_name

# Update all packages (be careful in production)
pip install --upgrade -r requirements.txt
```

### Database Migrations
```bash
# If using Flask-Migrate (recommended for production)
flask db init
flask db migrate -m "Description of changes"
flask db upgrade
```

## Support and Documentation

### Getting Help
1. Check the application logs first
2. Review this guide and troubleshooting section
3. Check the project documentation in `replit.md`
4. Contact system administrator

### Additional Resources
- Flask Documentation: https://flask.palletsprojects.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Gunicorn Documentation: https://gunicorn.org/
- Redis Documentation: https://redis.io/documentation

## Production Deployment Checklist

- [ ] Environment variables configured
- [ ] Strong secrets generated
- [ ] Database properly configured
- [ ] SSL/HTTPS enabled
- [ ] Reverse proxy configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Security hardening completed
- [ ] Performance testing done
- [ ] Default passwords changed
- [ ] Firewall rules configured
- [ ] Log rotation enabled