# Dashboard Partners - Guia de Despliegue en Produccion

## Resumen de Arquitectura

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    PRODUCCION                           │
                    │                                                         │
   Internet         │   ┌─────────────┐      ┌──────────────────────────┐    │
       │            │   │   Nginx     │      │     Docker Compose       │    │
       │            │   │  (Reverse   │      │                          │    │
       ▼            │   │   Proxy)    │      │  ┌────────────────────┐  │    │
  ┌─────────┐       │   │             │      │  │ Frontend (React)   │  │    │
  │  CDN    │───────┼──▶│  :443 SSL   │─────▶│  │ Puerto: 5173       │  │    │
  │Cloudflare│      │   │             │      │  └────────────────────┘  │    │
  └─────────┘       │   │             │      │                          │    │
                    │   │             │      │  ┌────────────────────┐  │    │
                    │   │             │─────▶│  │ Backend (FastAPI)  │  │    │
                    │   │             │      │  │ Puerto: 8000       │  │    │
                    │   └─────────────┘      │  └────────────────────┘  │    │
                    │                        │                          │    │
                    │   ┌─────────────┐      │  ┌────────────────────┐  │    │
                    │   │  MongoDB    │◀────▶│  │                    │  │    │
                    │   │  :27017     │      │  └────────────────────┘  │    │
                    │   └─────────────┘      └──────────────────────────┘    │
                    │                                                         │
                    └─────────────────────────────────────────────────────────┘
```

---

## Indice

1. [Prerequisitos](#1-prerequisitos)
2. [Configuracion del Servidor](#2-configuracion-del-servidor)
3. [Variables de Entorno](#3-variables-de-entorno)
4. [Despliegue con Docker](#4-despliegue-con-docker)
5. [Configuracion de Nginx](#5-configuracion-de-nginx)
6. [Certificados SSL](#6-certificados-ssl)
7. [Configuracion de Google OAuth](#7-configuracion-de-google-oauth)
8. [MongoDB en Produccion](#8-mongodb-en-produccion)
9. [Monitoreo y Logs](#9-monitoreo-y-logs)
10. [Checklist de Seguridad](#10-checklist-de-seguridad)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisitos

### Servidor
- Ubuntu 22.04 LTS o superior
- Minimo 2 CPU, 4GB RAM
- 50GB SSD

### Software Requerido
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Instalar Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Verificar instalaciones
docker --version
docker-compose --version
nginx -v
```

---

## 2. Configuracion del Servidor

### 2.1 Crear Usuario de Aplicacion
```bash
# Crear usuario sin shell interactivo
sudo useradd -r -s /bin/false dashboard

# Crear directorios
sudo mkdir -p /opt/dashboard-partners
sudo chown dashboard:dashboard /opt/dashboard-partners
```

### 2.2 Configurar Firewall
```bash
# UFW Firewall
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

### 2.3 Clonar Repositorio
```bash
cd /opt/dashboard-partners
git clone https://github.com/ludapartners/Dashboard_partners.git .
```

---

## 3. Variables de Entorno

### 3.1 Generar Secretos Seguros
```bash
# Generar JWT Secret (64 caracteres hex)
openssl rand -hex 32

# Ejemplo de salida:
# a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### 3.2 Backend (.env)
Crear archivo `/opt/dashboard-partners/backend/.env`:

```bash
# =============================================================================
# PRODUCCION - Dashboard Partners Backend
# =============================================================================

# MongoDB Connection
# IMPORTANTE: Usar credenciales seguras, NO las de desarrollo
MONGODB_URL=mongodb://dashboard_user:CONTRASEÑA_SEGURA_AQUI@mongodb:27017/LudaFarma-PRO?authSource=admin
DATABASE_NAME=LudaFarma-PRO

# JWT Configuration
# IMPORTANTE: Generar con: openssl rand -hex 32
JWT_SECRET_KEY=GENERAR_NUEVO_SECRET_CON_OPENSSL
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Google OAuth Configuration
# IMPORTANTE: Obtener de Google Cloud Console para produccion
GOOGLE_CLIENT_ID=TU_GOOGLE_CLIENT_ID_PRODUCCION
GOOGLE_CLIENT_SECRET=TU_GOOGLE_CLIENT_SECRET_PRODUCCION

# Email Domain Restriction
ALLOWED_EMAIL_DOMAIN=ludapartners.com

# CORS Configuration
CORS_ORIGINS_RAW=https://dashboard.ludapartners.com

# Environment
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### 3.3 Frontend (.env)
Crear archivo `/opt/dashboard-partners/frontend/.env`:

```bash
# =============================================================================
# PRODUCCION - Dashboard Partners Frontend
# =============================================================================

# Google OAuth (Client ID es publico, OK exponerlo)
VITE_GOOGLE_CLIENT_ID=TU_GOOGLE_CLIENT_ID_PRODUCCION

# API URL (debe apuntar al dominio de produccion)
VITE_API_URL=https://dashboard.ludapartners.com/api
```

### 3.4 Permisos de Archivos .env
```bash
# Solo el propietario puede leer
chmod 600 /opt/dashboard-partners/backend/.env
chmod 600 /opt/dashboard-partners/frontend/.env
```

---

## 4. Despliegue con Docker

### 4.1 Crear docker-compose.yml
Crear archivo `/opt/dashboard-partners/docker-compose.yml`:

```yaml
version: '3.8'

services:
  # ==========================================================================
  # Frontend - React/Vite
  # ==========================================================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: dashboard-frontend
    restart: unless-stopped
    ports:
      - "5173:80"
    environment:
      - NODE_ENV=production
    networks:
      - dashboard-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==========================================================================
  # Backend - FastAPI
  # ==========================================================================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: dashboard-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    networks:
      - dashboard-network
    depends_on:
      - mongodb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ==========================================================================
  # MongoDB (opcional si usas MongoDB externo)
  # ==========================================================================
  mongodb:
    image: mongo:6.0
    container_name: dashboard-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./mongodb/init:/docker-entrypoint-initdb.d
    networks:
      - dashboard-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  dashboard-network:
    driver: bridge

volumes:
  mongodb_data:
```

### 4.2 Dockerfile para Frontend
Crear archivo `/opt/dashboard-partners/frontend/Dockerfile.prod`:

```dockerfile
# =============================================================================
# Stage 1: Build
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar codigo fuente
COPY . .

# Build de produccion
RUN npm run build

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM nginx:alpine

# Copiar configuracion de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar build de produccion
COPY --from=builder /app/dist /usr/share/nginx/html

# Exponer puerto
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 Dockerfile para Backend
Crear archivo `/opt/dashboard-partners/backend/Dockerfile.prod`:

```dockerfile
# =============================================================================
# Stage 1: Build
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root
RUN useradd -r -s /bin/false appuser

# Copiar dependencias instaladas
COPY --from=builder /root/.local /home/appuser/.local

# Copiar codigo fuente
COPY . .

# Cambiar propietario
RUN chown -R appuser:appuser /app

# Usar usuario no-root
USER appuser

# Agregar local bin al PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 4.4 Nginx Config para Frontend Container
Crear archivo `/opt/dashboard-partners/frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # No cache for HTML
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }
}
```

### 4.5 Comandos de Despliegue
```bash
# Construir imagenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado
docker-compose ps

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down
```

---

## 5. Configuracion de Nginx

### 5.1 Crear Configuracion del Sitio
Crear archivo `/etc/nginx/sites-available/dashboard.ludapartners.com`:

```nginx
# =============================================================================
# Dashboard Partners - Nginx Configuration
# =============================================================================

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# Upstream servers
upstream frontend {
    server 127.0.0.1:5173;
}

upstream backend {
    server 127.0.0.1:8000;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name dashboard.ludapartners.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name dashboard.ludapartners.com;

    # SSL Certificates (Certbot will update these)
    ssl_certificate /etc/letsencrypt/live/dashboard.ludapartners.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.ludapartners.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com https://apis.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://accounts.google.com https://www.googleapis.com; frame-ancestors 'none';" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), usb=()" always;

    # Logging
    access_log /var/log/nginx/dashboard.access.log;
    error_log /var/log/nginx/dashboard.error.log;

    # API Backend
    location /api/ {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
        proxy_connect_timeout 90;
    }

    # Login endpoint - stricter rate limiting
    location /api/auth/google {
        limit_req zone=login_limit burst=5 nodelay;

        proxy_pass http://backend/auth/google;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend (React SPA)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Block common attack vectors
    location ~ /\. {
        deny all;
    }

    location ~* /(wp-admin|wp-login|xmlrpc\.php|\.git|\.env) {
        deny all;
        return 404;
    }
}
```

### 5.2 Activar Configuracion
```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/dashboard.ludapartners.com /etc/nginx/sites-enabled/

# Verificar configuracion
sudo nginx -t

# Recargar nginx
sudo systemctl reload nginx
```

---

## 6. Certificados SSL

### 6.1 Obtener Certificado con Certbot
```bash
# Obtener certificado (antes de activar config SSL)
sudo certbot --nginx -d dashboard.ludapartners.com

# Verificar renovacion automatica
sudo certbot renew --dry-run

# La renovacion automatica se configura en:
# /etc/cron.d/certbot
```

### 6.2 Renovacion Automatica
```bash
# Crear script de renovacion
sudo nano /etc/cron.d/certbot-renew

# Contenido:
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 7. Configuracion de Google OAuth

### 7.1 Crear Proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear nuevo proyecto: "Dashboard Partners Production"
3. Habilitar "Google+ API" y "People API"

### 7.2 Configurar OAuth Consent Screen

1. Navegar a "APIs & Services" > "OAuth consent screen"
2. Seleccionar "Internal" (solo usuarios de @ludapartners.com)
3. Completar informacion:
   - App name: Dashboard Partners
   - User support email: soporte@ludapartners.com
   - Developer contact: dev@ludapartners.com

### 7.3 Crear Credenciales OAuth

1. Navegar a "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Web application"
4. Name: "Dashboard Partners Production"
5. Authorized JavaScript origins:
   ```
   https://dashboard.ludapartners.com
   ```
6. Authorized redirect URIs:
   ```
   https://dashboard.ludapartners.com
   https://dashboard.ludapartners.com/api/auth/google/callback
   ```
7. Copiar Client ID y Client Secret

### 7.4 Actualizar .env con Nuevas Credenciales
```bash
# Backend .env
GOOGLE_CLIENT_ID=NUEVO_CLIENT_ID_PRODUCCION
GOOGLE_CLIENT_SECRET=NUEVO_CLIENT_SECRET_PRODUCCION

# Frontend .env
VITE_GOOGLE_CLIENT_ID=NUEVO_CLIENT_ID_PRODUCCION
```

---

## 8. MongoDB en Produccion

### 8.1 Opcion A: MongoDB en Docker (mismo servidor)
Ya incluido en docker-compose.yml

### 8.2 Opcion B: MongoDB Atlas (recomendado)

1. Crear cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear cluster M10 o superior para produccion
3. Configurar Network Access:
   - Whitelist IP del servidor de produccion
4. Crear Database User:
   - Username: dashboard_prod
   - Password: (generar contraseña segura)
   - Rol: readWrite en database LudaFarma-PRO
5. Obtener connection string:
   ```
   mongodb+srv://dashboard_prod:PASSWORD@cluster.mongodb.net/LudaFarma-PRO?retryWrites=true&w=majority
   ```

### 8.3 Backup de MongoDB
```bash
# Crear script de backup
cat > /opt/dashboard-partners/scripts/backup-mongodb.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/mongodb"
mkdir -p $BACKUP_DIR

# Backup
docker exec dashboard-mongodb mongodump \
  --out /tmp/backup_$DATE \
  --gzip

# Copiar backup fuera del container
docker cp dashboard-mongodb:/tmp/backup_$DATE $BACKUP_DIR/

# Limpiar backups antiguos (mantener ultimos 7 dias)
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completado: $BACKUP_DIR/backup_$DATE"
EOF

chmod +x /opt/dashboard-partners/scripts/backup-mongodb.sh

# Programar backup diario
echo "0 2 * * * root /opt/dashboard-partners/scripts/backup-mongodb.sh" | sudo tee /etc/cron.d/mongodb-backup
```

---

## 9. Monitoreo y Logs

### 9.1 Configurar Logging Centralizado
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs especificos
docker-compose logs -f backend
docker-compose logs -f frontend

# Logs de Nginx
sudo tail -f /var/log/nginx/dashboard.access.log
sudo tail -f /var/log/nginx/dashboard.error.log
```

### 9.2 Health Checks
```bash
# Verificar servicios
curl -s https://dashboard.ludapartners.com/health
curl -s https://dashboard.ludapartners.com/api/health

# Script de monitoreo
cat > /opt/dashboard-partners/scripts/health-check.sh << 'EOF'
#!/bin/bash
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" https://dashboard.ludapartners.com/)
BACKEND=$(curl -s -o /dev/null -w "%{http_code}" https://dashboard.ludapartners.com/api/health)

if [ "$FRONTEND" != "200" ] || [ "$BACKEND" != "200" ]; then
    echo "ALERT: Service down! Frontend: $FRONTEND, Backend: $BACKEND"
    # Enviar notificacion (email, Slack, etc.)
fi
EOF

chmod +x /opt/dashboard-partners/scripts/health-check.sh

# Ejecutar cada 5 minutos
echo "*/5 * * * * root /opt/dashboard-partners/scripts/health-check.sh" | sudo tee /etc/cron.d/health-check
```

### 9.3 Metricas con Prometheus (opcional)
```yaml
# Agregar a docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - dashboard-network
```

---

## 10. Checklist de Seguridad

### Antes del Despliegue

- [ ] **Credenciales rotadas**: Generar nuevos secretos para produccion
  - [ ] JWT_SECRET_KEY (nuevo con `openssl rand -hex 32`)
  - [ ] GOOGLE_CLIENT_SECRET (nuevo en Google Cloud Console)
  - [ ] Contraseña MongoDB (nueva, minimo 32 caracteres)

- [ ] **Archivos .env**:
  - [ ] No versionados en Git (verificar .gitignore)
  - [ ] Permisos 600 (solo propietario puede leer)
  - [ ] Sin valores de desarrollo

- [ ] **SSL/TLS**:
  - [ ] Certificados instalados
  - [ ] HTTP redirige a HTTPS
  - [ ] TLS 1.2+ solamente

- [ ] **Headers de seguridad**:
  - [ ] HSTS habilitado
  - [ ] CSP configurado
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff

- [ ] **Rate limiting**:
  - [ ] Configurado en Nginx
  - [ ] Login endpoint con limite estricto

- [ ] **Firewall**:
  - [ ] Solo puertos 22, 80, 443 abiertos
  - [ ] MongoDB no expuesto a internet

### Despues del Despliegue

- [ ] **Verificar acceso**:
  - [ ] Login con Google funciona
  - [ ] Solo emails @ludapartners.com permitidos
  - [ ] Tokens JWT validos

- [ ] **Monitoreo**:
  - [ ] Health checks funcionando
  - [ ] Logs accesibles
  - [ ] Alertas configuradas

- [ ] **Backup**:
  - [ ] Backup automatico configurado
  - [ ] Restauracion probada

---

## 11. Troubleshooting

### Error: "Google OAuth not configured"
```bash
# Verificar variables de entorno
docker exec dashboard-backend env | grep GOOGLE

# Verificar que .env esta siendo leido
docker exec dashboard-backend cat /app/.env
```

### Error: "Connection refused" a MongoDB
```bash
# Verificar que MongoDB esta corriendo
docker-compose ps mongodb

# Ver logs de MongoDB
docker-compose logs mongodb

# Verificar conectividad
docker exec dashboard-backend python -c "from pymongo import MongoClient; print(MongoClient('mongodb://...'))"
```

### Error: 502 Bad Gateway
```bash
# Verificar que backend esta corriendo
curl http://localhost:8000/health

# Ver logs de backend
docker-compose logs backend

# Reiniciar backend
docker-compose restart backend
```

### Error: SSL Certificate issues
```bash
# Verificar certificados
sudo certbot certificates

# Renovar manualmente
sudo certbot renew --force-renewal

# Verificar permisos
sudo ls -la /etc/letsencrypt/live/dashboard.ludapartners.com/
```

### Limpiar y Reconstruir
```bash
# Parar todo
docker-compose down

# Limpiar imagenes
docker system prune -a

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

---

## Comandos Utiles

```bash
# Estado de servicios
docker-compose ps

# Logs en tiempo real
docker-compose logs -f --tail=100

# Reiniciar un servicio
docker-compose restart backend

# Entrar a un container
docker exec -it dashboard-backend /bin/bash

# Ver uso de recursos
docker stats

# Actualizar codigo
git pull
docker-compose build
docker-compose up -d

# Backup rapido de MongoDB
docker exec dashboard-mongodb mongodump --out /backup --gzip
docker cp dashboard-mongodb:/backup ./mongodb-backup-$(date +%Y%m%d)
```

---

## Contactos de Soporte

- **DevOps**: devops@ludapartners.com
- **Desarrollo**: dev@ludapartners.com
- **Seguridad**: security@ludapartners.com

---

*Ultima actualizacion: Enero 2026*
*Version: 2.0.0*
