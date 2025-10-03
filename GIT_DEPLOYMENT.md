# Git Repository Deployment Guide

This guide outlines how to properly commit and push your containerized application to a Git repository, ensuring all necessary files are included while maintaining security best practices.

## Files to Commit

### Core Application Files
- `gelbooru_api.py` - Main API wrapper implementation
- `telegram_bot.py` - Telegram bot implementation
- `example_usage.py` - Usage examples
- `test_api.py` - Test suite
- `demo.py` - Interactive demonstration

### Documentation Files
- `README.md` - Main project documentation
- `DEPLOYMENT.md` - Deployment instructions
- `ARCHITECTURE.md` - Architecture documentation
- `PROJECT_SUMMARY.md` - Project summary
- `QUICKSTART.md` - Quick start guide
- `FILES_OVERVIEW.md` - Files overview
- `INDEX.md` - Project index
- `SELINUX_GUIDE.md` - SELinux configuration guide

### Containerization Files
- `Dockerfile` - Container build instructions
- `docker-compose.yml` - Multi-container orchestration
- `deploy.sh` - Deployment script
- `.dockerignore` - Files to exclude from build context

### Configuration Files
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template (without actual values)

## Files to Exclude

### Security Considerations
Never commit actual credentials or sensitive information:
- `.env` - Contains real credentials
- `user_settings.json` - Contains user data

### Adding Files to .gitignore
Create or update `.gitignore` with these entries:

```gitignore
# Environment variables (contains secrets)
.env
user_settings.json

# Python cache and bytecode
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
.venv/
ENV/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
logs/
log/

# Data directory
data/

# Output directories
outputs/
```

## Git Workflow

### 1. Initialize Repository (if needed)
```bash
# If creating a new repository locally
git init
git remote add origin https://github.com/yourusername/your-repo.git
```

### 2. Add Files to Repository
```bash
# Add all files except those in .gitignore
git add .

# Or add specific files
git add gelbooru_api.py telegram_bot.py Dockerfile docker-compose.yml
git add README.md DEPLOYMENT.md ARCHITECTURE.md PROJECT_SUMMARY.md
git add requirements.txt .env.example .dockerignore
```

### 3. Commit Changes
```bash
# Make initial commit
git commit -m "Initial commit: Containerized Gelbooru Bot application with SELinux support"

# Or more descriptive commit message
git commit -m "Add containerization support for Fedora Server with SELinux
- Dockerfile with multi-stage build
- docker-compose.yml with SELinux volume labeling
- deploy.sh script for automated deployment
- SELINUX_GUIDE.md with Fedora-specific instructions
- Updated .dockerignore for optimized builds"
```

### 4. Push to Repository
```bash
# Push to main branch
git push origin main

# Or create and push to a new branch
git checkout -b containerization-feature
git push origin containerization-feature
```

## Repository Structure

After pushing, your repository will have this structure:

```
your-repo/
├── gelbooru_api.py
├── telegram_bot.py
├── example_usage.py
├── test_api.py
├── demo.py
├── README.md
├── DEPLOYMENT.md
├── ARCHITECTURE.md
├── PROJECT_SUMMARY.md
├── QUICKSTART.md
├── FILES_OVERVIEW.md
├── INDEX.md
├── SELINUX_GUIDE.md
├── Dockerfile
├── docker-compose.yml
├── deploy.sh
├── .dockerignore
├── requirements.txt
├── .env.example
├── .gitignore
└── .github/
    └── workflows/
        └── (optional CI/CD workflows)
```

## Creating a Release

To create a proper release of your containerized application:

### 1. Tag the Release
```bash
# Create annotated tag
git tag -a v1.0-containerized -m "Version 1.0 - Containerized Release with SELinux Support"

# Push tags
git push origin --tags
```

### 2. Create GitHub Release
```bash
# Create release using GitHub CLI
gh release create v1.0-containerized \
    --title "Version 1.0 - Containerized Release" \
    --notes "Containerized version of the Gelbooru Bot application with SELinux support for Fedora Server"
```

## CI/CD Considerations

### GitHub Actions Workflow Example
Create `.github/workflows/container-build.yml`:

```yaml
name: Build and Test Container

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Build container
      run: docker build -t gelbooru-bot .
      
    - name: Run tests
      run: |
        docker run --rm gelbooru-bot python -c "
          from gelbooru_api import GelbooruClient, Post, Tag, User;
          print('Import successful');
        "
```

## Best Practices

1. **Use Semantic Versioning** when tagging releases (v1.0.0, v1.1.0, etc.)
2. **Keep .env.example updated** with all required environment variables
3. **Document SELinux requirements** in your README
4. **Test deployment scripts** in a development environment first
5. **Use multi-stage Docker builds** to minimize image size
6. **Regularly update dependencies** in requirements.txt
7. **Include a comprehensive README** explaining the containerization approach

## Verification Steps

After pushing to your repository:

1. Clone to a fresh directory to verify:
```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
ls -la  # Verify all necessary files are present
```

2. Check that sensitive files are excluded:
```bash
# These should NOT be present in the repository
ls -la .env user_settings.json
```

3. Test the build process:
```bash
# Follow your deployment guide to ensure everything works
cp .env.example .env
# Edit .env with credentials
./deploy.sh
```

## Repository Management

### Branch Strategy
- `main` - Production-ready code
- `develop` - Development branch
- Feature branches - For specific features (e.g., `selinux-support`, `containerization`)

### Pull Requests
When working with teams:
1. Create feature branches for changes
2. Submit pull requests for code review
3. Ensure CI tests pass before merging
4. Delete feature branches after merging

This approach ensures your containerized application is properly versioned, documented, and can be easily deployed by others while maintaining security best practices.