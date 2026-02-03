# AutoGenChecker Web UI - Deployment Guide

## Overview

This guide provides instructions for deploying the AutoGenChecker Web UI in different environments.

## Local Development Deployment

### Quick Start

**Windows:**
```powershell
.\start_all.ps1
```

**Linux/Mac:**
```bash
# Start backend
python start_backend.py &

# Start frontend
cd frontend && npm run dev
```

### Manual Setup

1. **Backend:**
```bash
cd web_ui/backend
pip install -r requirements.txt
python app.py
```

Backend runs on: http://localhost:8000

2. **Frontend:**
```bash
cd web_ui/frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## Production Deployment

### Option 1: Docker Deployment (Recommended)

#### Create Dockerfile for Backend

```dockerfile
# web_ui/backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Create Dockerfile for Frontend

```dockerfile
# web_ui/frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

```yaml
# web_ui/docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - JEDAI_API_KEY=${JEDAI_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

#### Deploy with Docker

```bash
# Set environment variables
export JEDAI_API_KEY=your_api_key

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Native Deployment

#### Backend (Production)

1. **Install Production Server:**
```bash
pip install gunicorn
```

2. **Create systemd service (Linux):**

```ini
# /etc/systemd/system/autogenchecker-backend.service
[Unit]
Description=AutoGenChecker Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/autogenchecker/web_ui/backend
Environment="PATH=/opt/autogenchecker/venv/bin"
ExecStart=/opt/autogenchecker/venv/bin/gunicorn app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Start service:**
```bash
sudo systemctl enable autogenchecker-backend
sudo systemctl start autogenchecker-backend
```

#### Frontend (Production)

1. **Build static files:**
```bash
cd web_ui/frontend
npm run build
```

2. **Configure Nginx:**

```nginx
# /etc/nginx/sites-available/autogenchecker
server {
    listen 80;
    server_name autogenchecker.example.com;

    # Frontend
    location / {
        root /opt/autogenchecker/web_ui/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # SSE endpoint (special handling)
    location /api/generation/stream/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }
}
```

3. **Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/autogenchecker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 3: Cloud Deployment

#### AWS (EC2 + S3)

1. **Backend on EC2:**
   - Launch EC2 instance (t3.medium recommended)
   - Install Python 3.9+
   - Configure security group (port 8000)
   - Deploy using systemd service

2. **Frontend on S3 + CloudFront:**
   - Build static files
   - Upload to S3 bucket
   - Configure CloudFront distribution
   - Set up custom domain

#### Azure (App Service)

```bash
# Backend
az webapp up --name autogenchecker-api --runtime "PYTHON:3.9"

# Frontend
az staticwebapp create \
  --name autogenchecker-ui \
  --resource-group autogenchecker-rg \
  --app-location "./web_ui/frontend" \
  --output-location "dist"
```

#### Google Cloud Platform (Cloud Run)

```bash
# Backend
gcloud run deploy autogenchecker-api \
  --source ./web_ui/backend \
  --platform managed \
  --region us-central1

# Frontend (Cloud Storage + CDN)
gsutil -m cp -r dist/* gs://autogenchecker-ui/
```

## Environment Configuration

### Backend Environment Variables

```bash
# .env file
JEDAI_API_KEY=your_api_key
DATABASE_URL=sqlite:///./autogenchecker.db
CORS_ORIGINS=http://localhost:5173,https://autogenchecker.example.com
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```javascript
// .env.production
VITE_API_BASE_URL=https://api.autogenchecker.example.com
VITE_SSE_ENABLED=true
```

## Security Considerations

1. **HTTPS:** Always use HTTPS in production
   - Use Let's Encrypt for free SSL certificates
   - Configure automatic renewal

2. **Authentication:** Add authentication layer
   - API keys for backend
   - JWT tokens for session management

3. **CORS:** Configure CORS properly
   - Whitelist specific origins
   - Don't use wildcard (*) in production

4. **Rate Limiting:** Implement rate limiting
   - Prevent abuse of LLM API
   - Use Redis for distributed rate limiting

5. **Secrets Management:**
   - Use environment variables
   - Never commit secrets to git
   - Use vault services (AWS Secrets Manager, etc.)

## Monitoring & Logging

### Application Logging

```python
# Configure structured logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/autogenchecker/app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

```python
# Add health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Monitoring Tools

- **Application Monitoring:** New Relic, DataDog
- **Log Aggregation:** ELK Stack, Splunk
- **Uptime Monitoring:** UptimeRobot, Pingdom

## Backup & Recovery

1. **Database Backup:**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
sqlite3 autogenchecker.db ".backup /backups/autogenchecker_$DATE.db"
```

2. **Code Backup:**
   - Use Git for version control
   - Tag releases
   - Maintain separate production branch

3. **Data Backup:**
   - Backup history data regularly
   - Store generated files in persistent storage
   - Use cloud storage for redundancy

## Scaling Strategies

1. **Horizontal Scaling:**
   - Use load balancer (Nginx, HAProxy)
   - Multiple backend instances
   - Shared database/cache

2. **Vertical Scaling:**
   - Increase instance size
   - More CPU for LLM requests
   - More memory for caching

3. **Caching:**
   - Redis for session cache
   - CDN for static assets
   - Application-level caching

## Troubleshooting

### Backend Issues

```bash
# Check service status
sudo systemctl status autogenchecker-backend

# View logs
sudo journalctl -u autogenchecker-backend -f

# Test API directly
curl http://localhost:8000/health
```

### Frontend Issues

```bash
# Check build
npm run build

# Check Nginx config
sudo nginx -t

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Common Issues

1. **CORS Errors:** Check CORS configuration in backend
2. **SSE Not Working:** Check proxy timeouts
3. **Slow Performance:** Check LLM API rate limits
4. **Database Errors:** Check file permissions

## Maintenance

1. **Regular Updates:**
   - Update dependencies monthly
   - Security patches immediately
   - Test updates in staging first

2. **Database Maintenance:**
   - Vacuum SQLite database
   - Clean old history entries
   - Index optimization

3. **Log Rotation:**
   - Configure logrotate
   - Keep 30 days of logs
   - Compress old logs

## Rollback Procedure

```bash
# Stop services
docker-compose down

# Restore previous version
git checkout v1.0.0

# Rebuild and restart
docker-compose up -d --build

# Verify
curl http://localhost:8000/health
```

## Support & Contact

For deployment issues:
- Check documentation: /web_ui/README.md
- Review logs: /var/log/autogenchecker/
- Contact: [Support Email]
