# Complete Guide to Containerizing Applications on Fedora Server with SELinux

This comprehensive guide provides step-by-step instructions for containerizing applications on Fedora Server while properly handling SELinux security contexts. The guide covers Docker and Podman approaches, SELinux considerations, and Git repository management.

## 1. Understanding the Environment

Fedora Server comes with SELinux enabled by default in enforcing mode. This provides enhanced security for containerized applications but requires proper handling of file contexts and volume mounts.

### Key Components:
- **SELinux**: Security-Enhanced Linux providing mandatory access controls
- **Podman**: Default container engine on Fedora (rootless containers)
- **Docker**: Alternative container engine (requires daemon with root privileges)
- **Cockpit**: Web-based interface for system administration

## 2. Containerization Process

### A. Creating the Dockerfile

We've created a multi-stage Dockerfile that:
- Uses Python 3.11 slim base image
- Implements security best practices (non-root user)
- Separates build dependencies from runtime
- Properly handles file ownership for SELinux compatibility

```dockerfile
# Multi-stage build for security and size optimization
FROM python:3.11-slim as builder
# Build stage with dependencies

FROM python:3.11-slim
# Runtime stage with minimal footprint
```

### B. Docker Compose Configuration

The `docker-compose.yml` file includes SELinux-specific volume labeling:

```yaml
volumes:
  # Private volume labeling for exclusive container access
  - ./data:/app/data:Z
  
security_opt:
  # Explicit container type (default behavior but clear in config)
  - label=type:container_t
```

### C. Deployment Script

The `deploy.sh` script automates the entire process:
1. Checks for SELinux status
2. Verifies container engine availability
3. Creates data directory with proper contexts
4. Builds the container image
5. Manages existing containers
6. Runs with proper SELinux volume labeling

## 3. SELinux Considerations

### Volume Mounting Options:

1. **`:Z` (Private Labeling)** - For volumes used by a single container
   ```bash
   podman run -v ./data:/app/data:Z gelbooru-bot
   ```

2. **`:z` (Shared Labeling)** - For volumes shared between containers
   ```bash
   podman run -v ./shared:/app/shared:z gelbooru-bot
   ```

3. **Custom Policies** - Using Udica for complex requirements
   ```bash
   podman inspect gelbooru-bot | udica gelbooru_bot_policy
   sudo semodule -i gelbooru_bot_policy.cil
   ```

### Security Best Practices:

- Run containers as non-root users
- Use SELinux volume labeling (`:Z` or `:z`)
- Generate custom policies with Udica when needed
- Never disable SELinux unless absolutely necessary
- Regularly check SELinux logs for denials

## 4. Git Repository Management

### Files to Commit:
- All source code files
- Documentation files
- Containerization configuration files
- `.env.example` template (without real credentials)
- `.dockerignore` for optimized builds

### Files to Exclude:
- `.env` with real credentials
- `user_settings.json` with user data
- Data directories
- Logs and temporary files

### Repository Structure:
```
gelbooru-bot/
├── Core Implementation
│   ├── gelbooru_api.py
│   └── telegram_bot.py
├── Documentation
│   ├── README.md
│   ├── SELINUX_GUIDE.md
│   └── GIT_DEPLOYMENT.md
├── Containerization
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── deploy.sh
│   └── .dockerignore
├── Configuration
│   ├── requirements.txt
│   └── .env.example
└── Examples & Tests
    ├── example_usage.py
    ├── test_api.py
    └── demo.py
```

## 5. Deployment Workflow

### On Fedora Server with Cockpit:

1. **Prepare Environment**:
   ```bash
   # Ensure SELinux is enabled
   sestatus
   
   # Install container engine if needed
   sudo dnf install podman
   ```

2. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

3. **Configure Application**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Deploy Application**:
   ```bash
   # Using deployment script
   ./deploy.sh
   
   # Or manual deployment
   podman build -t gelbooru-bot .
   podman run -d --name gelbooru-bot -v ./data:/app/data:Z gelbooru-bot
   ```

5. **Monitor with Cockpit**:
   - Access Cockpit at `https://your-server-ip:9090`
   - Navigate to Containers section
   - View logs, resource usage, and container status

## 6. Troubleshooting SELinux Issues

### Common Issues and Solutions:

1. **Permission denied on volume mounts**:
   - Solution: Use `:Z` for private volumes or `:z` for shared volumes

2. **Container cannot write to mounted volumes**:
   - Check: `ls -Z ./data` to verify contexts
   - Fix: `sudo chcon -Rt container_file_t ./data`

3. **Container cannot bind to host ports**:
   - Check boolean: `getsebool container_connect_any`
   - Enable if needed: `sudo setsebool container_connect_any on`

4. **Container needs special host access**:
   - Solution: Use Udica to generate custom policies

### Checking SELinux Status:
```bash
# View SELinux status
sestatus

# Check for recent denials
sudo ausearch -m avc -ts recent

# Set permissive mode for debugging (temporary)
sudo semanage permissive -a container_t
```

## 7. Testing Containerization

### Build and Run Tests:
1. Build container image:
   ```bash
   podman build -t gelbooru-bot .
   ```

2. Verify image creation:
   ```bash
   podman images | grep gelbooru-bot
   ```

3. Run container:
   ```bash
   podman run -d --name gelbooru-bot -v ./data:/app/data:Z gelbooru-bot
   ```

4. Check container status:
   ```bash
   podman ps --filter "name=gelbooru-bot"
   ```

5. View logs:
   ```bash
   podman logs gelbooru-bot
   ```

## 8. Production Considerations

### Security Hardening:
- Run containers as non-root users
- Use read-only root filesystem when possible
- Implement proper network policies
- Regularly update base images and dependencies

### Monitoring:
- Use Cockpit's container monitoring features
- Set up log aggregation
- Monitor resource usage
- Implement health checks

### Backup Strategy:
- Regularly backup the `./data` directory
- Version control all configuration files
- Document recovery procedures

### Scaling Options:
- Use container orchestration (Kubernetes, OpenShift)
- Implement load balancing
- Use container registries for image distribution

## 9. Best Practices Summary

1. **SELinux Integration**:
   - Always use volume labeling (`:Z` or `:z`)
   - Prefer Podman over Docker on Fedora
   - Generate custom policies with Udica for complex access

2. **Container Security**:
   - Run as non-root user
   - Use multi-stage builds
   - Minimize attack surface with .dockerignore

3. **Git Management**:
   - Commit all necessary files
   - Exclude sensitive information
   - Use semantic versioning
   - Document SELinux requirements

4. **Deployment Automation**:
   - Use deployment scripts
   - Implement CI/CD pipelines
   - Test in development environments first

## 10. References and Resources

- [Fedora Containerization Documentation](https://docs.fedoraproject.org/en-US/fedora-server/containerization/)
- [Red Hat SELinux Container Labeling Guide](https://developers.redhat.com/articles/2025/04/11/my-advice-selinux-container-labeling)
- [Udica Project for Custom SELinux Policies](https://github.com/containers/udica)
- [Cockpit Project Documentation](https://cockpit-project.org/)

---

With this comprehensive guide, you can successfully containerize applications on Fedora Server while properly handling SELinux security contexts. The provided Dockerfile, docker-compose.yml, and deployment script ensure a secure and reproducible deployment process.