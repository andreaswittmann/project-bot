# Docker Setup for Project Bot

This Docker setup provides a simple, single-container solution that runs both your Python backend and Vue.js frontend with proper data persistence and multi-architecture support.

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
# Navigate to the docker directory
cd docker

# Create environment file with your API keys
cp .env.template .env
# Edit .env with your actual API keys

# Ensure your config.yaml is properly configured (in project root)
cp ../config_template.yaml ../config.yaml
# Edit ../config.yaml as needed
```

### 2. Build and Run
```bash
# Navigate to docker directory
cd docker

# Build the Docker image
docker compose build

# Start the application
docker compose up -d

# View logs
docker compose logs -f

# Stop the application
docker compose down
```

### 3. Access Application
- **Web Interface**: http://localhost:8002
- **API**: http://localhost:8002/api/v1/
- **Health Check**: http://localhost:8002/api/v1/health

## 📁 Project Structure

```
project-bot/
├── docker/                # Docker configuration directory
│   ├── Dockerfile         # Multi-stage build configuration
│   ├── docker-compose.yml # Container orchestration
│   ├── .env.template      # API keys template
│   ├── .dockerignore      # Build optimization
│   ├── DOCKER_README.md   # Docker documentation
│   └── docker-setup.sh    # Setup script
├── data/                  # Mounted from host (CV, config data)
├── projects/              # Mounted from host (scraped projects)
├── logs/                  # Mounted from host (application logs)
└── config.yaml            # Mounted from host (configuration)
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: If you use multiple Anthropic keys
ANTHROPIC_API_KEY2=your_second_anthropic_key_here
```

### Config File (config.yaml)
Your existing `config.yaml` is mounted into the container. Make sure to use environment variable references:

```yaml
llm:
  provider: OpenAI
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}

application_generator:
  llm:
    provider: "Anthropic"
    model: "claude-sonnet-4-20250514"
    api_key: ${ANTHROPIC_API_KEY2}
```

## 🏗️ Architecture

### Single Container Design
- **Frontend**: Vue.js application built and served by Flask
- **Backend**: Flask API server with all Python dependencies
- **Data**: All persistent data mounted from host filesystem
- **Multi-Architecture**: Works on Intel Mac and Apple Silicon

### Data Persistence
All important data is mounted to the host:
- `./data` → CV files, quick filters, schedules
- `./projects` → All scraped project files
- `./logs` → Application logs
- `./config.yaml` → Configuration file

## 🛠️ Development Commands

### Build Commands
```bash
# Build for current platform only
docker compose build

# Build for multiple architectures (Intel + Apple Silicon)
docker buildx build --platform linux/amd64,linux/arm64 -t project-bot .

# Rebuild without cache
docker compose build --no-cache
```

### Runtime Commands
```bash
# Start in background
docker compose up -d

# Start with logs
docker compose up

# View logs
docker compose logs -f

# Stop application
docker compose down

# Restart application
docker compose restart

# View running containers
docker compose ps
```

### Debugging Commands
```bash
# Enter running container
docker compose exec project-bot bash

# View container logs
docker compose logs project-bot

# Check container health
docker compose ps
curl http://localhost:8002/api/v1/health
```

## 🔒 Security Considerations

### API Keys
- API keys are provided via environment variables (not baked into image)
- `.env` file is excluded from version control
- Never commit actual API keys to repository

### Data Persistence
- All sensitive data remains on host filesystem
- Container can be destroyed and rebuilt without data loss
- Back up `./data`, `./projects`, and `./config.yaml` regularly

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)
```bash
docker compose up -d
```

### Option 2: Pure Docker
```bash
docker build -t project-bot .
docker run -d -p 8002:8002 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  project-bot
```

### Option 3: Docker with .env file
```bash
docker run --env-file .env -d -p 8002:8002 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.yaml:/app/config.yaml \
  project-bot
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Backup Data
```bash
# Create backup of persistent data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ projects/ config.yaml

# Restore from backup
tar -xzf backup-20241201.tar.gz
```

### Clean Up
```bash
# Remove stopped containers
docker compose down

# Remove images
docker image rm project-bot

# Clean up unused resources
docker system prune
```

## 🐛 Troubleshooting

### Common Issues

**Port 8002 already in use**
```bash
# Find what's using the port
lsof -i :8002
# Or change the port in docker-compose.yml
```

**Permission issues with mounted volumes**
```bash
# Ensure proper permissions on host directories
chmod -R 755 data/ projects/ logs/
```

**Container won't start**
```bash
# Check logs for errors
docker compose logs project-bot

# Verify environment variables
docker compose exec project-bot env | grep API_KEY
```

**Frontend not loading**
```bash
# Check if frontend was built correctly
docker compose exec project-bot ls -la frontend/dist/

# Rebuild frontend
docker compose exec project-bot npm run build
```

### Health Checks
```bash
# Manual health check
curl http://localhost:8002/api/v1/health

# Check container health
docker compose ps
```

## 📊 Monitoring

### Logs
```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f project-bot

# Follow logs with timestamps
docker compose logs -f -t
```

### Resource Usage
```bash
# View container resource usage
docker stats

# View disk usage
docker system df
```

## 🎯 Performance Optimization

### Build Optimization
- Multi-stage build reduces final image size
- `.dockerignore` excludes unnecessary files
- Dependencies cached in layers

### Runtime Optimization
- Health checks ensure container reliability
- Restart policies handle failures automatically
- Resource limits prevent runaway processes

## 📝 Notes

- The container includes health checks and will restart automatically if it fails
- All data persists on the host filesystem and survives container updates
- The application is accessible at http://localhost:8002
- API keys are never stored in the container image
- Multi-architecture support works on both Intel and Apple Silicon Macs

## 🤝 Support

For issues with the Docker setup:
1. Check the logs: `docker compose logs -f`
2. Verify your `.env` file has the correct API keys
3. Ensure your `config.yaml` is properly configured
4. Check that all required directories exist on the host