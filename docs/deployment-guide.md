# 🚀 Deployment Guide

Complete guide for deploying the Brevo API Integration application to various environments.

## 📋 Table of Contents

- [Pre-deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Local Production Testing](#local-production-testing)
- [Server Deployment](#server-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Containerized Deployment](#containerized-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Rollback Procedures](#rollback-procedures)
- [Performance Optimization](#performance-optimization)

---

## ✅ Pre-deployment Checklist

### Code Quality Verification
```bash
# Backend checks
cd backend
venv\Scripts\activate
black --check .                    # Code formatting
flake8 .                          # Linting
mypy .                            # Type checking
pytest --cov                     # Tests with coverage

# Frontend checks
cd frontend
npm run lint                      # ESLint
npm run format:check              # Prettier
npm test -- --watchAll=false     # Tests
npm run build                     # Production build
```

### Security Verification
```bash
# Backend security audit
cd backend
pip audit                         # Check for vulnerable packages
bandit -r .                      # Security linting (install: pip install bandit)

# Frontend security audit
cd frontend
npm audit                         # Check for vulnerabilities
npm audit fix                     # Auto-fix issues
```

### Configuration Validation
```bash
# Verify environment files exist and are complete
ls backend/.env backend/.env.template
ls frontend/.env frontend/.env.template

# Check required environment variables
cd backend && python -c "
from config import config
errors = config.validate()
if errors:
    print('❌ Configuration errors:', errors)
    exit(1)
else:
    print('✅ Configuration valid')
"
```

---

## 🔧 Environment Configuration

### Production Backend Environment (.env)
```bash
# Brevo Configuration
BREVO_API_KEY=your_production_brevo_api_key
BREVO_SENDER_EMAIL=noreply@yourdomain.com
BREVO_SENDER_NAME=Your Company Name

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security (Optional)
SECRET_KEY=your-secret-key-here  # If sessions are used
```

### Production Frontend Environment (.env)
```bash
# API Configuration
REACT_APP_API_BASE_URL=https://api.yourdomain.com
REACT_APP_API_TIMEOUT=10000

# Feature Flags
REACT_APP_ENABLE_DEBUG_MODE=false
REACT_APP_CACHE_TTL=300000

# Build Configuration
GENERATE_SOURCEMAP=false          # For security
```

### Environment Security
```bash
# Set secure file permissions
chmod 600 backend/.env
chmod 600 frontend/.env

# Ensure .env files are in .gitignore
echo "backend/.env" >> .gitignore
echo "frontend/.env" >> .gitignore
echo ".env" >> .gitignore
```

---

## 🧪 Local Production Testing

### Backend Production Testing
```bash
cd backend

# Install production dependencies only
pip install --no-dev -r requirements.txt

# Test with Gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app

# Test endpoints
curl http://localhost:5000/                    # Health check
curl http://localhost:5000/api/account         # Account info

# Load testing (install: pip install locust)
locust -f tests/load_test.py --host=http://localhost:5000
```

### Frontend Production Testing
```bash
cd frontend

# Create production build
npm run build

# Test build locally
npx serve -s build -l 3000

# Test in browser
open http://localhost:3000

# Verify all functionality works
# Test all API operations through the UI
```

### End-to-End Testing
```bash
# Start both services in production mode
# Terminal 1: Backend
cd backend && gunicorn -w 2 -b 0.0.0.0:5000 app:app

# Terminal 2: Frontend
cd frontend && npx serve -s build -l 3000

# Terminal 3: Test complete workflow
curl http://localhost:5000/                    # Backend health
curl http://localhost:3000                     # Frontend served
# Test all API operations through frontend UI
```

---

## 🖥️ Server Deployment

### Ubuntu/Debian Server Setup

#### System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git

# Create application user
sudo useradd -m -s /bin/bash brevoapp
sudo usermod -aG www-data brevoapp

# Create application directory
sudo mkdir -p /opt/brevo-api
sudo chown brevoapp:brevoapp /opt/brevo-api
```

#### Application Deployment
```bash
# Switch to application user
sudo su - brevoapp

# Clone repository
git clone <your-repo-url> /opt/brevo-api
cd /opt/brevo-api

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create production environment file
cp .env.template .env
# Edit .env with production values

# Test backend
python app.py  # Should start without errors
curl http://localhost:5000/

# Frontend setup
cd ../frontend
npm install
npm run build

# Test frontend build
ls -la build/
```

#### Systemd Service Setup
```bash
# Create backend service file
sudo tee /etc/systemd/system/brevo-api-backend.service > /dev/null << 'EOF'
[Unit]
Description=Brevo API Backend
After=network.target

[Service]
Type=exec
User=brevoapp
Group=brevoapp
WorkingDirectory=/opt/brevo-api/backend
Environment=PATH=/opt/brevo-api/backend/venv/bin
ExecStart=/opt/brevo-api/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable brevo-api-backend
sudo systemctl start brevo-api-backend
sudo systemctl status brevo-api-backend
```

#### Nginx Configuration
```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/brevo-api > /dev/null << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend (React app)
    location / {
        root /opt/brevo-api/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    }

    # Health check endpoint
    location = / {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/brevo-api /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

#### SSL Setup with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS Elastic Beanstalk
```bash
# Install AWS CLI and EB CLI
pip install awscli awsebcli

# Configure AWS credentials
aws configure

# Initialize Elastic Beanstalk application
cd backend
eb init brevo-api-backend --platform python-3.8 --region us-east-1

# Create environment
eb create brevo-api-production

# Set environment variables
eb setenv BREVO_API_KEY=your_key BREVO_SENDER_EMAIL=sender@domain.com

# Deploy
eb deploy

# Check status
eb status
eb logs
```

#### Using AWS EC2 (Manual)
```bash
# Launch EC2 instance (Ubuntu 20.04 LTS)
# Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Follow Ubuntu server setup steps above
# Configure domain to point to EC2 public IP
```

### DigitalOcean Deployment

#### Using DigitalOcean Droplets
```bash
# Create droplet (Ubuntu 20.04, 2GB RAM minimum)
# Add SSH key for access

# Connect to droplet
ssh root@your-droplet-ip

# Follow Ubuntu server setup steps above
# Configure domain DNS to point to droplet IP
```

#### Using DigitalOcean App Platform
```yaml
# Create .do/app.yaml
name: brevo-api-integration
services:
- name: backend
  source_dir: backend
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: BREVO_API_KEY
    value: ${BREVO_API_KEY}
  - key: BREVO_SENDER_EMAIL
    value: ${BREVO_SENDER_EMAIL}
  - key: FLASK_ENV
    value: production
  - key: FLASK_DEBUG
    value: false
  http_port: 5000

- name: frontend
  source_dir: frontend
  github:
    repo: your-username/your-repo
    branch: main
  build_command: npm run build
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  - path: /api
    preserve_path_prefix: true
```

### Heroku Deployment

#### Backend Deployment
```bash
# Install Heroku CLI
# Create Procfile in backend directory
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT app:app" > backend/Procfile

# Create runtime.txt
echo "python-3.9.16" > backend/runtime.txt

# Initialize git and Heroku
cd backend
git init
heroku create brevo-api-backend

# Set environment variables
heroku config:set BREVO_API_KEY=your_key
heroku config:set BREVO_SENDER_EMAIL=sender@domain.com
heroku config:set FLASK_ENV=production

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Check logs
heroku logs --tail
```

#### Frontend Deployment (Netlify)
```bash
# Build settings for Netlify
# Build command: npm run build
# Publish directory: build

# Create _redirects file in public/
echo "/* /index.html 200" > frontend/public/_redirects

# Create netlify.toml
cat > frontend/netlify.toml << 'EOF'
[build]
  publish = "build"
  command = "npm run build"

[build.environment]
  REACT_APP_API_BASE_URL = "https://your-heroku-app.herokuapp.com"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
EOF
```

---

## 🐳 Containerized Deployment

### Docker Setup

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
# Multi-stage build
FROM node:16 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - BREVO_API_KEY=${BREVO_API_KEY}
      - BREVO_SENDER_EMAIL=${BREVO_SENDER_EMAIL}
      - FLASK_ENV=production
      - FLASK_DEBUG=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:5000
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

#### Kubernetes Deployment
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: brevo-api

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: brevo-api-config
  namespace: brevo-api
data:
  FLASK_ENV: "production"
  FLASK_DEBUG: "false"
  REACT_APP_API_BASE_URL: "https://api.yourdomain.com"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: brevo-api-secret
  namespace: brevo-api
type: Opaque
stringData:
  BREVO_API_KEY: "your_brevo_api_key"
  BREVO_SENDER_EMAIL: "sender@yourdomain.com"

---
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brevo-api-backend
  namespace: brevo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: brevo-api-backend
  template:
    metadata:
      labels:
        app: brevo-api-backend
    spec:
      containers:
      - name: backend
        image: your-registry/brevo-api-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: BREVO_API_KEY
          valueFrom:
            secretKeyRef:
              name: brevo-api-secret
              key: BREVO_API_KEY
        - name: BREVO_SENDER_EMAIL
          valueFrom:
            secretKeyRef:
              name: brevo-api-secret
              key: BREVO_SENDER_EMAIL
        envFrom:
        - configMapRef:
            name: brevo-api-config
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brevo-api-frontend
  namespace: brevo-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: brevo-api-frontend
  template:
    metadata:
      labels:
        app: brevo-api-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/brevo-api-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"

---
# k8s/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: brevo-api-backend-service
  namespace: brevo-api
spec:
  selector:
    app: brevo-api-backend
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: brevo-api-frontend-service
  namespace: brevo-api
spec:
  selector:
    app: brevo-api-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: brevo-api-ingress
  namespace: brevo-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: brevo-api-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: brevo-api-frontend-service
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: brevo-api-backend-service
            port:
              number: 5000
```

---

## 📊 Monitoring and Maintenance

### Application Monitoring
```bash
# Health check script
#!/bin/bash
# healthcheck.sh

BACKEND_URL="http://localhost:5000"
FRONTEND_URL="http://localhost:3000"

echo "Checking backend health..."
if curl -f -s $BACKEND_URL/ > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is unhealthy"
    exit 1
fi

echo "Checking frontend..."
if curl -f -s $FRONTEND_URL > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is inaccessible"
    exit 1
fi

echo "All services are healthy"
```

### Log Management
```bash
# Backend logs with systemd
sudo journalctl -u brevo-api-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs (if file logging is configured)
tail -f /opt/brevo-api/backend/logs/app.log

# Log rotation setup
sudo tee /etc/logrotate.d/brevo-api > /dev/null << 'EOF'
/opt/brevo-api/backend/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 brevoapp brevoapp
    postrotate
        systemctl reload brevo-api-backend
    endscript
}
EOF
```

### Performance Monitoring
```bash
# Server monitoring script
#!/bin/bash
# monitor.sh

echo "=== System Resources ==="
echo "CPU Usage:"
top -bn1 | grep load
echo "Memory Usage:"
free -h
echo "Disk Usage:"
df -h

echo "=== Application Status ==="
systemctl status brevo-api-backend --no-pager
systemctl status nginx --no-pager

echo "=== Network Connections ==="
ss -tuln | grep -E ':80|:443|:5000'

echo "=== Application Health ==="
curl -s http://localhost:5000/ | jq .
```

### Database Backup (if applicable)
```bash
# If using SQLite or PostgreSQL
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/brevo-api/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database (example for SQLite)
if [ -f "/opt/brevo-api/backend/app.db" ]; then
    cp /opt/brevo-api/backend/app.db $BACKUP_DIR/app_$DATE.db
    echo "Database backup created: $BACKUP_DIR/app_$DATE.db"
fi

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /opt/brevo-api/backend/.env \
    /opt/brevo-api/frontend/.env

echo "Configuration backup created: $BACKUP_DIR/config_$DATE.tar.gz"

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

---

## 🔄 Rollback Procedures

### Code Rollback
```bash
# Git-based rollback
cd /opt/brevo-api

# View recent commits
git log --oneline -10

# Rollback to previous commit
git checkout <previous-commit-hash>

# Rebuild and restart services
cd backend
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart brevo-api-backend
sudo systemctl restart nginx
```

### Service Rollback
```bash
# Stop current version
sudo systemctl stop brevo-api-backend

# Switch to backup version (if maintained)
sudo cp /opt/brevo-api/backup/app.py /opt/brevo-api/backend/app.py

# Restart service
sudo systemctl start brevo-api-backend
sudo systemctl status brevo-api-backend
```

### Database Rollback (if applicable)
```bash
# Stop application
sudo systemctl stop brevo-api-backend

# Restore database backup
cp /opt/brevo-api/backups/app_YYYYMMDD_HHMMSS.db /opt/brevo-api/backend/app.db

# Start application
sudo systemctl start brevo-api-backend
```

---

## ⚡ Performance Optimization

### Backend Optimization
```bash
# Gunicorn optimization
gunicorn -w $((2 * $(nproc) + 1)) \
         --max-requests 1000 \
         --max-requests-jitter 100 \
         --preload \
         -b 0.0.0.0:5000 \
         app:app

# Enable HTTP/2 in Nginx
# Add to nginx configuration:
# listen 443 ssl http2;
```

### Frontend Optimization
```bash
# Optimize build
npm run build

# Analyze bundle
npx webpack-bundle-analyzer build/static/js/*.js

# Enable gzip in Nginx
# Add to nginx configuration:
# gzip on;
# gzip_types text/plain text/css application/javascript application/json;
```

### Database Optimization (if applicable)
```bash
# SQLite optimization
sqlite3 app.db "PRAGMA optimize;"
sqlite3 app.db "VACUUM;"

# Add indexes for frequently queried columns
sqlite3 app.db "CREATE INDEX IF NOT EXISTS idx_email ON contacts(email);"
```

---

## 📝 Deployment Checklist

### Pre-deployment
- [ ] Code quality checks passed
- [ ] All tests passing
- [ ] Security audit completed
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database migrations applied (if applicable)
- [ ] Backup procedures tested

### Deployment
- [ ] Services deployed successfully
- [ ] Health checks passing
- [ ] All endpoints responding correctly
- [ ] Frontend routing working
- [ ] API integration functional
- [ ] SSL/TLS working correctly

### Post-deployment
- [ ] Monitoring configured
- [ ] Log rotation setup
- [ ] Backup schedules active
- [ ] Performance metrics baseline established
- [ ] Team notified of deployment
- [ ] Documentation updated

---

*This deployment guide covers various deployment scenarios and can be adapted based on your specific infrastructure requirements and constraints.*