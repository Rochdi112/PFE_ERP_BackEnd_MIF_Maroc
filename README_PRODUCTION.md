# ERP MIF Maroc - Production Deployment

This document provides instructions for deploying the ERP MIF Maroc application in production.

## Architecture

The production setup consists of:
- **Frontend**: React/Vite application served by Nginx
- **Backend**: FastAPI application with PostgreSQL database
- **Nginx**: Reverse proxy handling routing between frontend and backend
- **Redis**: Caching layer
- **PostgreSQL**: Primary database
- **Prometheus/Grafana**: Monitoring (optional)

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 80, 443, 5432, 6379, 9090, 3000 available

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Database
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST_PORT=5432

# Security
SECRET_KEY=your_very_secure_secret_key_here
FILES_ENC_KEY=your_32_char_fernet_key_here

# Email (optional)
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_email_password
EMAILS_FROM_EMAIL=noreply@yourdomain.com

# Monitoring (optional)
GRAFANA_PASSWORD=your_grafana_admin_password
```

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

1. **Windows**: Run `deploy-prod.bat`
2. **Linux/Mac**: Run `chmod +x deploy-prod.sh && ./deploy-prod.sh`

### Option 2: Manual Deployment

1. **Build Frontend**:
   ```bash
   cd ../VITE-FRONTEND-ERP-MIF-MAROC
   npm ci
   npm run build
   cd ../PFE_ERP_BackEnd_MIF_Maroc
   ```

2. **Start Services**:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Check Status**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

## Access URLs

After successful deployment:
- **Application**: http://localhost
- **API**: http://localhost/api/v1/
- **API Documentation**: http://localhost/docs
- **Health Check**: http://localhost/health
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## SSL Configuration (Optional)

To enable HTTPS:

1. Place your SSL certificate and key in `nginx/ssl/`
2. Uncomment the HTTPS server block in `nginx/nginx.conf`
3. Update the server_name directive
4. Restart the nginx service

## Monitoring

The setup includes Prometheus and Grafana for monitoring:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (default login: admin/admin)

## Troubleshooting

### Check Service Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs db
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Rebuild and Restart
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d
```

### Database Issues
If the database fails to start, check:
1. PostgreSQL port is not in use
2. Sufficient disk space
3. Correct permissions on data volume

### Frontend Issues
If the frontend doesn't load:
1. Check that the build completed successfully
2. Verify nginx configuration
3. Check browser console for errors

## Backup and Recovery

### Database Backup
```bash
# Create backup
docker exec -t erp_db pg_dump -U erp_user -d erp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker exec -i erp_db psql -U erp_user -d erp_db < backup_file.sql
```

### File Uploads
Uploads are stored in the `uploads_data` Docker volume. To backup:
```bash
docker run --rm -v erp_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz -C /data .
```

## Performance Optimization

1. **Database**: Ensure proper indexing on frequently queried columns
2. **Redis**: Configure appropriate cache TTL values
3. **Nginx**: Adjust worker processes based on server resources
4. **Frontend**: Enable service worker for caching static assets

## Security Considerations

1. Change default passwords
2. Use strong SECRET_KEY and FILES_ENC_KEY
3. Configure firewall rules
4. Keep Docker images updated
5. Monitor logs for suspicious activity
6. Use HTTPS in production
7. Implement rate limiting (already configured)

## Support

For issues or questions:
1. Check the logs using the commands above
2. Verify environment variables are set correctly
3. Ensure all prerequisites are met
4. Check Docker and Docker Compose versions
