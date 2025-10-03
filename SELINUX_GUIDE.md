# SELinux Configuration Guide for Docker on Fedora Server

This guide provides comprehensive information about SELinux considerations when containerizing applications on Fedora Server, with specific focus on the Gelbooru Bot application.

## Understanding SELinux and Containers

SELinux (Security-Enhanced Linux) is a security architecture that provides mandatory access controls (MAC) for Linux systems. Fedora Server comes with SELinux enabled by default, providing enhanced security for containerized applications.

When running containers on SELinux-enabled systems, you have several options for handling security contexts:

## SELinux Labeling Options

### 1. Default Container Labeling (Recommended)
Containers run with the `container_t` type by default, which provides isolation between containers and from the host system.

```bash
# This is the default behavior - no special options needed
podman run -d -v ./data:/app/data:Z gelbooru-bot
```

### 2. Private Volume Labeling (:Z)
Use the `:Z` option when a volume is used exclusively by one container:

```yaml
# In docker-compose.yml
volumes:
  - ./data:/app/data:Z
```

This relabels the volume content for exclusive use by the container with a unique MCS (Multi-Category Security) label.

### 3. Shared Volume Labeling (:z)
Use the `:z` option when a volume is shared between multiple containers:

```yaml
# In docker-compose.yml
volumes:
  - ./shared_data:/app/data:z
```

This sets a shared SELinux label (`container_file_t:s0`) that allows multiple containers to access the volume.

### 4. Custom SELinux Policy
For more complex scenarios, use Udica to generate custom policies:

```bash
# Create container
podman create --name gelbooru-bot -v ./data:/app/data gelbooru-bot-image

# Generate policy
podman inspect gelbooru-bot | udica gelbooru_bot_policy

# Install policy
sudo semodule -i gelbooru_bot_policy.cil /usr/share/udica/templates/base_container.cil
```

### 5. Disable SELinux Separation (Not Recommended)
Only use when absolutely necessary:

```yaml
# In docker-compose.yml (NOT RECOMMENDED)
security_opt:
  - label=disable
```

## Fedora Server Specific Considerations

### Podman vs Docker
Fedora Server uses Podman as the default container engine, which has better SELinux integration than Docker:

```bash
# Using Podman (recommended on Fedora)
podman build -t gelbooru-bot .
podman run -d --name gelbooru-bot -v ./data:/app/data:Z gelbooru-bot

# Using Docker (requires additional SELinux configuration)
sudo dnf install docker
sudo systemctl start docker
sudo usermod -aG docker $USER
docker build -t gelbooru-bot .
docker run -d --name gelbooru-bot -v ./data:/app/data:Z gelbooru-bot
```

### Checking SELinux Status
Verify SELinux is enabled and in enforcing mode:

```bash
# Check SELinux status
sestatus

# Should show:
# SELinux status: enabled
# SELinuxfs mount: /selinux
# SELinux root directory: /etc/selinux
# Loaded policy name: targeted
# Current mode: enforcing
# Mode from config file: enforcing
```

### SELinux Troubleshooting
If you encounter SELinux issues:

```bash
# Check SELinux alerts
sudo ausearch -m avc -ts recent

# Temporarily set permissive mode for container_t (for debugging only)
sudo semanage permissive -a container_t

# Restore enforcing mode
sudo semanage permissive -d container_t

# Set proper file contexts
sudo restorecon -R -v /path/to/volume
```

## Implementation with Your Application

### Volume Mounting
For the Gelbooru Bot application, we recommend using the `:Z` flag for the data volume:

```yaml
volumes:
  - ./data:/app/data:Z
```

This ensures that:
1. The settings file is properly labeled for container access
2. Other containers cannot access this volume (enhanced security)
3. Host processes with matching UID cannot access the volume (isolation)

### Security Options
In your docker-compose.yml, we've set:

```yaml
security_opt:
  - label=type:container_t
```

This explicitly sets the container type, which is the default behavior but makes it clear in the configuration.

### File Contexts
The Dockerfile ensures proper file ownership:

```dockerfile
# Change ownership to non-root user
RUN chown -R 1000:1000 /app

# Switch to non-root user
USER 1000:1000
```

This prevents potential SELinux denials related to file access.

## Best Practices

1. **Always use volume labeling** (`:Z` or `:z`) when mounting host directories
2. **Run containers as non-root** users when possible
3. **Use Podman on Fedora Server** for better SELinux integration
4. **Don't disable SELinux** unless absolutely necessary
5. **Generate custom policies** with Udica for complex access requirements
6. **Regularly check SELinux logs** for denials during development

## Common SELinux Issues and Solutions

### Issue: Permission denied when accessing mounted volumes
**Solution**: Use `:Z` flag for private volumes or `:z` for shared volumes

### Issue: Container cannot bind to host ports
**Solution**: Check SELinux boolean settings:
```bash
getsebool container_connect_any
sudo setsebool container_connect_any on
```

### Issue: Container needs access to host network
**Solution**: Use custom SELinux policy or appropriate boolean settings

## Testing SELinux Configuration

1. Build your container:
```bash
podman build -t gelbooru-bot .
```

2. Run with volume mounting:
```bash
podman run -d --name gelbooru-bot -v ./data:/app/data:Z gelbooru-bot
```

3. Check for SELinux denials:
```bash
sudo ausearch -m avc -ts recent
```

4. Verify container is running properly:
```bash
podman logs gelbooru-bot
```

## References

- [Red Hat SELinux Container Labeling Guide](https://developers.redhat.com/articles/2025/04/11/my-advice-selinux-container-labeling)
- [Fedora Containerization Documentation](https://docs.fedoraproject.org/en-US/fedora-server/containerization/)
- [Udica Project](https://github.com/containers/udica)

---

With these SELinux considerations implemented, your containerized application will run securely on Fedora Server while maintaining proper isolation from both the host system and other containers.