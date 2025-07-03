# Deployment Guide - Advanced Esports Tournament Bot

## Overview

This guide covers multiple deployment strategies for the Advanced Esports Tournament Bot, from simple local deployment to enterprise-scale production environments supporting 10K+ users.

## Prerequisites

- Python 3.8+
- Telegram Bot Token (obtain from @BotFather)
- Admin usernames for management
- Docker (for containerized deployment)

## Deployment Options

### 1. Local Development Deployment

```bash
# Clone the repository
git clone <repository-url>
cd esports-tournament-bot

# Set up environment
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMINS

# Install dependencies
pip install python-telegram-bot python-dotenv pytest

# Run the bot
python main.py
```

### 2. Docker Deployment (Recommended)

#### Single Container
```bash
# Build the image
docker build -t esports-bot .

# Run the container
docker run -d \
  --name esports-tournament-bot \
  --restart unless-stopped \
  -e BOT_TOKEN=your_bot_token_here \
  -e ADMINS=admin1,admin2 \
  -v $(pwd)/data:/app/data \
  esports-bot
```

#### Docker Compose (Production Ready)
```bash
# Set up environment
cp .env.example .env
# Configure your .env file

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f esports-bot

# Stop services
docker-compose down
```

### 3. Production Deployment with Scaling

#### Architecture for 10K+ Users

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - bot-1
      - bot-2

  # Bot Instances (Horizontal Scaling)
  bot-1:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://botuser:${POSTGRES_PASSWORD}@postgres:5432/esports_bot
    depends_on:
      - redis
      - postgres

  bot-2:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://botuser:${POSTGRES_PASSWORD}@postgres:5432/esports_bot
    depends_on:
      - redis
      - postgres

  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: esports_bot
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Cache Layer
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

volumes:
  postgres_data:
  redis_data:
```

## Environment Configuration

### Required Environment Variables

```bash
# .env file
BOT_TOKEN=your_telegram_bot_token_here
ADMINS=admin1,admin2,admin3

# Optional Settings
MAX_TEAM_NAME_LENGTH=50
MIN_RATING=0
MAX_RATING=100
CLEANUP_INTERVAL_HOURS=24
UNCONFIRMED_DATA_EXPIRY_HOURS=24
LOG_LEVEL=INFO
DEFAULT_LANGUAGE=en
```

### Production Environment Variables

```bash
# Database Configuration (for high-scale deployments)
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379

# Security
SECRET_KEY=your_secret_key_here
WEBHOOK_SECRET=your_webhook_secret

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=30
MAX_REGISTRATIONS_PER_USER=2
```

## Scaling Strategies

### 1. Vertical Scaling (Single Instance)
- **Capacity**: Up to 1,000 concurrent users
- **Memory**: 512MB - 2GB RAM
- **CPU**: 1-2 cores
- **Storage**: SSD for JSON persistence

### 2. Horizontal Scaling (Multi-Instance)
- **Capacity**: 10,000+ concurrent users
- **Components**:
  - Multiple bot instances behind load balancer
  - Shared PostgreSQL database
  - Redis for session management
  - Message queue for async processing

### 3. Microservices Architecture
- **NLP Service**: Dedicated natural language processing
- **Registration Service**: User registration handling
- **Admin Service**: Administrative functions
- **Notification Service**: User notifications
- **Analytics Service**: Statistics and reporting

## Database Migration for Scale

### From JSON to PostgreSQL

```sql
-- Database schema for production
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('vsa', 'h2h')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id BIGINT PRIMARY KEY, -- Telegram user ID
    username VARCHAR(32) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    tournament_id INTEGER REFERENCES tournaments(id),
    team_name VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating >= 0 AND rating <= 100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    created_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    UNIQUE(user_id, tournament_id)
);

CREATE INDEX idx_registrations_status ON registrations(status);
CREATE INDEX idx_registrations_tournament ON registrations(tournament_id);
```

## Monitoring and Logging

### Application Metrics
```python
# metrics.py - Add to bot for production monitoring
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
registrations_total = Counter('registrations_total', 'Total registrations', ['tournament_type'])
command_processing_time = Histogram('command_processing_seconds', 'Time spent processing commands')
active_users = Gauge('active_users_total', 'Number of active users')

# In your handlers
registrations_total.labels(tournament_type='vsa').inc()
```

### Log Configuration
```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_production_logging():
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/bot.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.WARNING)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
```

## Security Best Practices

### 1. Container Security
```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' botuser
USER botuser

# Minimal base image
FROM python:3.11-slim

# Security scanning
RUN pip install safety
RUN safety check
```

### 2. Network Security
```yaml
# docker-compose security
services:
  bot:
    networks:
      - bot-network
    # No exposed ports for polling mode

networks:
  bot-network:
    driver: bridge
    internal: true  # No external access
```

### 3. Environment Security
```bash
# Use Docker secrets
echo "your_bot_token" | docker secret create bot_token -
echo "your_db_password" | docker secret create db_password -
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Indexes for common queries
CREATE INDEX CONCURRENTLY idx_registrations_user_tournament 
ON registrations(user_id, tournament_id);

CREATE INDEX CONCURRENTLY idx_registrations_created_at 
ON registrations(created_at DESC);

-- Partitioning for large datasets
CREATE TABLE registrations_2024 PARTITION OF registrations
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 2. Caching Strategy
```python
# redis_cache.py
import redis
import json
from typing import Optional, Dict, Any

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        data = self.redis.get(f"user:{user_id}")
        return json.loads(data) if data else None
    
    async def set_user_data(self, user_id: int, data: Dict[str, Any], ttl: int = 3600):
        self.redis.setex(
            f"user:{user_id}", 
            ttl, 
            json.dumps(data)
        )
```

## Health Checks and Monitoring

### Application Health Check
```python
# health.py
from telegram.ext import Application

async def health_check(application: Application) -> Dict[str, Any]:
    """Comprehensive health check"""
    try:
        # Test bot connection
        bot_info = await application.bot.get_me()
        
        # Test database connection
        # db_status = await test_database_connection()
        
        # Test external services
        # redis_status = await test_redis_connection()
        
        return {
            "status": "healthy",
            "bot": {"username": bot_info.username, "id": bot_info.id},
            "timestamp": datetime.now().isoformat(),
            # "database": db_status,
            # "cache": redis_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

## Backup and Recovery

### 1. Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump -h postgres -U botuser esports_bot > "$BACKUP_DIR/postgres_$DATE.sql"

# Redis backup
redis-cli --rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

### 2. Automated Backup
```yaml
# Add to docker-compose.yml
backup:
  image: postgres:15
  volumes:
    - ./backups:/backups
    - ./backup.sh:/backup.sh
  environment:
    - PGPASSWORD=${POSTGRES_PASSWORD}
  command: ["/bin/bash", "-c", "chmod +x /backup.sh && /backup.sh"]
  depends_on:
    - postgres
    - redis
  # Run daily at 2 AM
  deploy:
    replicas: 0
```

## Troubleshooting

### Common Issues

1. **Bot Not Responding**
   ```bash
   # Check logs
   docker-compose logs esports-bot
   
   # Verify token
   curl "https://api.telegram.org/bot$BOT_TOKEN/getMe"
   ```

2. **High Memory Usage**
   ```bash
   # Monitor container stats
   docker stats esports-tournament-bot
   
   # Check for memory leaks
   docker exec -it esports-tournament-bot python -c "
   import psutil
   print(f'Memory: {psutil.virtual_memory().percent}%')
   "
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker exec -it postgres psql -U botuser -d esports_bot -c "SELECT 1;"
   ```

### Performance Monitoring

```bash
# Monitor key metrics
docker exec -it esports-tournament-bot python -c "
import psutil
import json

metrics = {
    'cpu_percent': psutil.cpu_percent(),
    'memory_percent': psutil.virtual_memory().percent,
    'disk_usage': psutil.disk_usage('/').percent
}

print(json.dumps(metrics, indent=2))
"
```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring dashboards set up
- [ ] Log rotation configured
- [ ] Rate limiting enabled
- [ ] Security scanning completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Health checks implemented

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review error logs
   - Check backup integrity
   - Monitor resource usage

2. **Monthly**:
   - Update dependencies
   - Security scan
   - Performance optimization review

3. **Quarterly**:
   - Disaster recovery testing
   - Capacity planning review
   - Security audit

### Scaling Triggers

- **Scale Up**: CPU > 80% for 5 minutes
- **Scale Out**: Response time > 2 seconds
- **Database Scale**: Connection pool exhaustion
- **Cache Scale**: Hit ratio < 90%

This deployment guide provides a comprehensive foundation for running the Advanced Esports Tournament Bot in any environment, from development to enterprise production scale.