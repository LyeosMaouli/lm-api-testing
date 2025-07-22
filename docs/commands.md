# 🛠️ Useful Commands Documentation

This document provides a comprehensive reference of all useful commands for developing, testing, and deploying the Brevo API Integration application.

## 📋 Table of Contents

- [Environment Setup](#environment-setup)
- [Backend Commands](#backend-commands)
- [Frontend Commands](#frontend-commands)
- [Development Workflow](#development-workflow)
- [Testing Commands](#testing-commands)
- [Code Quality Commands](#code-quality-commands)
- [Production Commands](#production-commands)
- [Debugging Commands](#debugging-commands)
- [Git Workflow Commands](#git-workflow-commands)
- [Docker Commands](#docker-commands)
- [Troubleshooting Commands](#troubleshooting-commands)

---

## 🔧 Environment Setup

### Initial Project Setup
```bash
# Clone repository
git clone <repository-url>
cd lm-api-testing

# Verify Python version
python --version  # Should be 3.8+

# Verify Node.js version
node --version    # Should be 16+
npm --version
```

### Backend Environment Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Verify virtual environment is active
which python  # Should point to venv/Scripts/python or venv/bin/python

# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Create environment file from template
copy .env.template .env  # Windows
cp .env.template .env    # macOS/Linux

# Edit .env file with your credentials
notepad .env             # Windows
nano .env               # Linux
vim .env                # macOS/Linux
```

### Frontend Environment Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
copy .env.template .env  # Windows
cp .env.template .env    # macOS/Linux

# Verify installation
npm list --depth=0
```

---

## 🐍 Backend Commands

### Development Server
```bash
# Start development server
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
python app.py

# Start with custom port
FLASK_PORT=5001 python app.py

# Start with debug mode disabled
FLASK_DEBUG=false python app.py

# Start with specific configuration
FLASK_ENV=production python app.py
```

### Production Server
```bash
# Start with Gunicorn (recommended for production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Start with custom workers and binding
gunicorn -w 8 -b 0.0.0.0:8000 app:app

# Start with logging
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app

# Start as daemon
gunicorn -w 4 -b 0.0.0.0:5000 -D app:app

# Kill gunicorn processes
pkill -f gunicorn
```

### Dependency Management
```bash
# Install new package
pip install package-name

# Install with version
pip install package-name==1.2.3

# Update requirements file
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt

# Update all packages
pip install --upgrade -r requirements.txt

# Show installed packages
pip list

# Show package information
pip show package-name
```

---

## ⚛️ Frontend Commands

### Development Server
```bash
# Start development server
cd frontend
npm start

# Start with custom port
PORT=3001 npm start

# Start with HTTPS
HTTPS=true npm start

# Start with custom host
HOST=0.0.0.0 npm start
```

### Build Commands
```bash
# Create production build
npm run build

# Build with custom output directory
BUILD_PATH=dist npm run build

# Analyze bundle size
npm run build -- --analyze

# Serve production build locally
npx serve -s build -l 3000
```

### Dependency Management
```bash
# Install new package
npm install package-name

# Install development dependency
npm install --save-dev package-name

# Install specific version
npm install package-name@1.2.3

# Update dependencies
npm update

# Audit dependencies for vulnerabilities
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Show outdated packages
npm outdated

# Remove package
npm uninstall package-name

# Clean install (remove node_modules and reinstall)
rm -rf node_modules package-lock.json
npm install
```

---

## 🔄 Development Workflow

### Daily Development Commands
```bash
# Start both services (run in separate terminals)
# Terminal 1 - Backend
cd backend && venv\Scripts\activate && python app.py

# Terminal 2 - Frontend
cd frontend && npm start

# Check health of both services
curl http://127.0.0.1:5000/     # Backend health check
curl http://localhost:3000      # Frontend (should redirect or serve)
```

### Environment Management
```bash
# Check environment variables
# Backend
cd backend && venv\Scripts\activate
python -c "import os; print('BREVO_API_KEY:', bool(os.getenv('BREVO_API_KEY')))"

# Frontend
cd frontend
echo $REACT_APP_API_BASE_URL
```

### Hot Reload and Live Development
```bash
# Backend with auto-reload (development only)
cd backend
venv\Scripts\activate
python app.py  # Flask debug mode enables auto-reload

# Frontend (automatically enabled)
npm start  # Hot reload is automatic

# Watch for backend file changes (alternative)
pip install watchdog
watchmedo auto-restart --patterns="*.py" --recursive -- python app.py
```

---

## 🧪 Testing Commands

### Backend Testing
```bash
cd backend
venv\Scripts\activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py

# Run specific test function
pytest tests/test_app.py::TestHealthCheck::test_health_check_success

# Run tests with coverage
pytest --cov

# Run tests with detailed coverage report
pytest --cov --cov-report=html

# Run tests with coverage and exclude files
pytest --cov --cov-report=html --cov-config=pyproject.toml

# Run tests in parallel
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Run tests matching pattern
pytest -k "email"

# Run tests with custom markers
pytest -m "unit"
pytest -m "integration"

# Generate XML report for CI
pytest --junitxml=test-results.xml

# Watch for file changes and re-run tests
pytest-watch
```

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run tests in CI mode (non-interactive)
npm test -- --watchAll=false

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- src/components/App.test.js

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Update snapshots
npm test -- --updateSnapshot

# Run tests in debug mode
npm test -- --debug

# Run tests with custom reporter
npm test -- --reporters=default --reporters=jest-junit
```

### End-to-End Testing (if implemented)
```bash
# Install Cypress (example)
npm install --save-dev cypress

# Run Cypress tests
npx cypress run

# Open Cypress interactive mode
npx cypress open
```

---

## 📊 Code Quality Commands

### Backend Code Quality
```bash
cd backend
venv\Scripts\activate

# Format code with Black
black .

# Check formatting without making changes
black --check .

# Format specific files
black app.py config.py

# Lint with flake8
flake8 .

# Lint specific files
flake8 app.py

# Sort imports with isort
isort .

# Check import sorting
isort --check-only .

# Type checking with mypy
mypy .

# Type check specific files
mypy app.py

# All quality checks in sequence
black . && isort . && flake8 . && mypy .

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

### Frontend Code Quality
```bash
cd frontend

# Lint with ESLint
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Lint specific files
npx eslint src/App.js

# Format with Prettier
npm run format

# Check formatting without making changes
npm run format:check

# Format specific files
npx prettier --write src/App.js

# All quality checks
npm run lint && npm run format:check

# Type checking (if TypeScript is added)
npx tsc --noEmit
```

### Combined Quality Checks
```bash
# Backend and Frontend in parallel
# Run this from project root
(cd backend && venv\Scripts\activate && black . && flake8 . && pytest) & \
(cd frontend && npm run lint && npm run format:check && npm test -- --watchAll=false)
```

---

## 🚀 Production Commands

### Build for Production
```bash
# Backend - no build step needed, but install production dependencies
cd backend
venv\Scripts\activate
pip install -r requirements.txt --no-dev

# Frontend production build
cd frontend
npm run build

# Verify build output
ls -la build/
du -sh build/
```

### Production Server Commands
```bash
# Start production backend
cd backend
venv\Scripts\activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Start with logging and monitoring
gunicorn -w 4 -b 0.0.0.0:5000 \
  --access-logfile /var/log/brevo-api/access.log \
  --error-logfile /var/log/brevo-api/error.log \
  --pid /var/run/brevo-api.pid \
  app:app

# Start with systemd (create service file first)
sudo systemctl start brevo-api
sudo systemctl enable brevo-api
sudo systemctl status brevo-api

# Serve frontend with nginx (example config needed)
sudo nginx -t  # Test configuration
sudo systemctl reload nginx

# Serve frontend with simple HTTP server (development/testing)
cd frontend/build
python -m http.server 3000
```

### Environment Variables for Production
```bash
# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=false
export BREVO_API_KEY=your_production_key
export BREVO_SENDER_EMAIL=noreply@yourdomain.com

# Or use .env file
cd backend
echo "FLASK_ENV=production" > .env.production
echo "FLASK_DEBUG=false" >> .env.production
echo "BREVO_API_KEY=your_production_key" >> .env.production
```

---

## 🐛 Debugging Commands

### Backend Debugging
```bash
cd backend
venv\Scripts\activate

# Run with Python debugger
python -m pdb app.py

# Debug specific test
python -m pdb -m pytest tests/test_app.py

# Check Flask configuration
python -c "from app import app; print(app.config)"

# Test API endpoints manually
curl -X GET http://127.0.0.1:5000/
curl -X GET http://127.0.0.1:5000/api/account
curl -X POST http://127.0.0.1:5000/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test","content":"<p>Hello</p>"}'

# Check logs
tail -f logs/app.log  # If logging to file
```

### Frontend Debugging
```bash
cd frontend

# Start with debug information
DEBUG=true npm start

# Check build output
npm run build && ls -la build/

# Analyze bundle size
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js

# Debug service worker (if enabled)
npx serve -s build -l 3000
# Open DevTools -> Application -> Service Workers
```

### Network Debugging
```bash
# Test backend connectivity
curl -I http://127.0.0.1:5000/
nc -zv 127.0.0.1 5000

# Test CORS
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://127.0.0.1:5000/api/account

# Monitor HTTP traffic
# Install httpie
pip install httpie
http GET :5000/api/account

# Monitor with tcpdump (Linux/macOS)
sudo tcpdump -i lo port 5000
```

---

## 📝 Git Workflow Commands

### Daily Git Workflow
```bash
# Check status
git status

# Add changes
git add .                    # Add all changes
git add backend/app.py      # Add specific file
git add backend/            # Add directory

# Commit changes
git commit -m "feat: add email validation to backend"
git commit -m "fix: resolve CORS issue in production"
git commit -m "docs: update API documentation"

# Push changes
git push origin main

# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/custom-events
git push -u origin feature/custom-events
```

### Code Quality Pre-commit
```bash
# Create pre-commit script
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Run backend quality checks
cd backend && source venv/bin/activate && black --check . && flake8 . && pytest --tb=short
# Run frontend quality checks  
cd ../frontend && npm run lint && npm run format:check && npm test -- --watchAll=false
EOF

chmod +x .git/hooks/pre-commit

# Or use pre-commit framework
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Git Aliases (add to ~/.gitconfig)
```bash
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    df = diff
    lg = log --oneline --graph --all
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk
```

---

## 🐳 Docker Commands

### Docker Setup (Optional Enhancement)
```bash
# Create Dockerfile for backend
cat > backend/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
EOF

# Create Dockerfile for frontend
cat > frontend/Dockerfile << 'EOF'
FROM node:16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
EOF

# Build Docker images
docker build -t brevo-api-backend ./backend
docker build -t brevo-api-frontend ./frontend

# Run containers
docker run -d -p 5000:5000 --env-file backend/.env brevo-api-backend
docker run -d -p 3000:80 brevo-api-frontend

# Docker Compose setup
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    env_file:
      - ./backend/.env
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
EOF

# Run with Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## 🔧 Troubleshooting Commands

### Backend Troubleshooting
```bash
# Check Python environment
which python
python --version
pip --version

# Verify virtual environment
echo $VIRTUAL_ENV

# Check installed packages
pip list
pip show flask

# Test imports
python -c "import flask; print(flask.__version__)"
python -c "from app import app; print('App created successfully')"

# Check environment variables
python -c "import os; print('API Key configured:', bool(os.getenv('BREVO_API_KEY')))"

# Test database connections (if applicable)
python -c "from app import db; print('Database connection OK')"

# Check file permissions
ls -la backend/
ls -la backend/.env

# Monitor logs
tail -f /var/log/brevo-api/app.log
journalctl -u brevo-api -f  # If using systemd
```

### Frontend Troubleshooting
```bash
# Check Node.js environment
node --version
npm --version
which node

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for conflicting ports
netstat -tulpn | grep :3000
lsof -i :3000  # macOS

# Build with verbose output
npm run build -- --verbose

# Check bundle size issues
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

### System Troubleshooting
```bash
# Check system resources
top
htop
df -h        # Disk usage
free -h      # Memory usage

# Check network connectivity
ping google.com
curl -I https://api.brevo.com

# Check firewall (Linux)
sudo ufw status
sudo iptables -L

# Check running processes
ps aux | grep python
ps aux | grep node

# Kill stuck processes
pkill -f "python app.py"
pkill -f "node.*react-scripts"

# Check log files
tail -f /var/log/syslog
tail -f /var/log/nginx/error.log
```

### Performance Monitoring
```bash
# Monitor API performance
curl -w "@curl-format.txt" -o /dev/null -s http://127.0.0.1:5000/api/account

# Create curl-format.txt
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF

# Load testing with ab (Apache Bench)
ab -n 100 -c 10 http://127.0.0.1:5000/

# Memory profiling
pip install memory_profiler
python -m memory_profiler app.py
```

---

## 📚 Quick Reference

### Most Common Commands
```bash
# Daily development startup
cd backend && venv\Scripts\activate && python app.py    # Terminal 1
cd frontend && npm start                                  # Terminal 2

# Run all tests
cd backend && pytest --cov                               # Backend tests
cd frontend && npm test -- --watchAll=false             # Frontend tests

# Code quality check
cd backend && black . && flake8 . && mypy .            # Backend quality
cd frontend && npm run lint && npm run format:check     # Frontend quality

# Production build
cd backend && pip install -r requirements.txt           # Backend ready
cd frontend && npm run build                            # Frontend build

# Health checks
curl http://127.0.0.1:5000/                            # Backend health
curl http://localhost:3000                             # Frontend served
```

### Environment Variables Quick Reference
```bash
# Backend (.env)
BREVO_API_KEY=your_api_key
BREVO_SENDER_EMAIL=sender@domain.com
FLASK_ENV=development
FLASK_DEBUG=true

# Frontend (.env)
REACT_APP_API_BASE_URL=http://127.0.0.1:5000
REACT_APP_API_TIMEOUT=10000
REACT_APP_ENABLE_DEBUG_MODE=true
```

### Port Reference
- Backend Development: `http://127.0.0.1:5000`
- Frontend Development: `http://localhost:3000`
- Frontend Production Build: `http://localhost:3000` (with serve)

---

*This command reference is comprehensive but can be customized based on your specific development needs and deployment environment.*