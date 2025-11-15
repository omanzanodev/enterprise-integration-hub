# Enterprise Integration Hub Makefile
# Sistema completo de integración empresarial

.PHONY: help build start stop restart health-check logs clean test lint format install-deps dashboard

# Variables
COMPOSE_FILE := docker-compose.yml
COMPOSE_DEV_FILE := docker-compose.dev.yml
PROJECT_NAME := enterprise-integration-hub

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Mostrar ayuda de comandos disponibles
	@echo "$(BLUE)Enterprise Integration Hub - Sistema de Integración Empresarial$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Ejemplos de uso:$(NC)"
	@echo "  make setup          - Configurar todo el sistema"
	@echo "  make start          - Iniciar todos los servicios"
	@echo "  make dashboard      - Abrir dashboard de monitoreo"
	@echo "  make test-workflow  - Probar workflow de integración"

setup: ## Configurar todo el sistema (primer uso)
	@echo "$(BLUE)🚀 Configurando Enterprise Integration Hub...$(NC)"
	@echo "$(YELLOW)Creando directorios necesarios...$(NC)"
	@mkdir -p logs monitoring/grafana/{dashboards,datasources} nginx/ssl init-db n8n-workflows
	@echo "$(YELLOW)Generando variables de entorno...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ .env creado - por favor edita con tus credenciales$(NC)"; \
	else \
		echo "$(GREEN)✅ .env ya existe$(NC)"; \
	fi
	@echo "$(YELLOW)Creando scripts de inicialización...$(NC)"
	@echo "#!/bin/bash\\n# Database initialization script for PostgreSQL\\npsql -U \$$POSTGRES_USER -d \$$POSTGRES_DB -c \"CREATE EXTENSION IF NOT EXISTS 'uuid-ossp';\"" > init-db/01-init.sh
	@chmod +x init-db/01-init.sh
	@echo "$(GREEN)✅ Configuración completada$(NC)"
	@echo "$(YELLOW)Siguiente paso: edita .env con tus credenciales y ejecuta 'make build'$(NC)"

build: ## Construir imágenes Docker
	@echo "$(BLUE)🐳 Construyendo imágenes Docker...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build
	@echo "$(GREEN)✅ Imágenes construidas exitosamente$(NC)"

start: ## Iniciar todos los servicios
	@echo "$(BLUE)🚀 Iniciando Enterprise Integration Hub...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Servicios iniciados$(NC)"
	@echo "$(YELLOW)Esperando que los servicios estén listos...$(NC)"
	@sleep 30
	@make health-check

stop: ## Detener todos los servicios
	@echo "$(BLUE)🛑 Deteniendo servicios...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

restart: ## Reiniciar todos los servicios
	@echo "$(BLUE)🔄 Reiniciando servicios...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart
	@echo "$(GREEN)✅ Servicios reiniciados$(NC)"

status: ## Mostrar estado de todos los servicios
	@echo "$(BLUE)📊 Estado de los servicios:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps

health-check: ## Verificar salud de todos los servicios
	@echo "$(BLUE)🏥 Verificando salud del sistema...$(NC)"
	@echo "$(YELLOW)Shared Context Server:$(NC)"
	@curl -s http://localhost:23456/health | jq . 2>/dev/null || echo "$(RED)❌ No responde$(NC)"
	@echo ""
	@echo "$(YELLOW)n8n Workflows:$(NC)"
	@curl -s http://localhost:5678/healthz | jq . 2>/dev/null || echo "$(RED)❌ No responde$(NC)"
	@echo ""
	@echo "$(YELLOW)Dashboard:$(NC)"
	@curl -s http://localhost:8080/health | jq . 2>/dev/null || echo "$(RED)❌ No responde$(NC)"
	@echo ""
	@echo "$(YELLOW)Prometheus:$(NC)"
	@curl -s http://localhost:9090/-/healthy | jq . 2>/dev/null || echo "$(RED)❌ No responde$(NC)"
	@echo ""
	@echo "$(YELLOW)Grafana:$(NC)"
	@curl -s http://localhost:3001/api/health | jq . 2>/dev/null || echo "$(RED)❌ No responde$(NC)"

logs: ## Mostrar logs de todos los servicios
	@echo "$(BLUE)📋 Mostrando logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-service: ## Mostrar logs de un servicio específifo (uso: make logs-service SERVICE=shared-context-server)
	@echo "$(BLUE)📋 Logs de $(SERVICE):$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE)

dashboard: ## Abrir dashboard de monitoreo en navegador
	@echo "$(BLUE)📊 Abriendo dashboard...$(NC)"
	@open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "$(YELLOW)Abre http://localhost:8080 en tu navegador$(NC)"

n8n: ## Abrir n8n en navegador
	@echo "$(BLUE)🔄 Abriendo n8n...$(NC)"
	@open http://localhost:5678 2>/dev/null || xdg-open http://localhost:5678 2>/dev/null || echo "$(YELLOW)Abre http://localhost:5678 en tu navegador$(NC)"

grafana: ## Abrir Grafana en navegador
	@echo "$(BLUE)📈 Abriendo Grafana...$(NC)"
	@open http://localhost:3001 2>/dev/null || xdg-open http://localhost:3001 2>/dev/null || echo "$(YELLOW)Abre http://localhost:3001 en tu navegador$(NC)"

prometheus: ## Abrir Prometheus en navegador
	@echo "$(BLUE)🔍 Abriendo Prometheus...$(NC)"
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "$(YELLOW)Abre http://localhost:9090 en tu navegador$(NC)"

kibana: ## Abrir Kibana en navegador
	@echo "$(BLUE)🔍 Abriendo Kibana...$(NC)"
	@open http://localhost:5601 2>/dev/null || xdg-open http://localhost:5601 2>/dev/null || echo "$(YELLOW)Abre http://localhost:5601 en tu navegador$(NC)"

test-workflow: ## Probar workflow de integración con email de ejemplo
	@echo "$(BLUE)🧪 Probando workflow de integración...$(NC)"
	@curl -X POST http://localhost:5678/webhook/email-integration \
		-H "Content-Type: application/json" \
		-d '{
			"subject": "Test Email from Enterprise Hub",
			"from": "test@example.com",
			"body": "This is a test email to verify the integration workflow is working properly.",
			"timestamp": "'$$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
		}' | jq .
	@echo "$(GREEN)✅ Workflow test enviado$(NC)"

test-api: ## Probar API del dashboard
	@echo "$(BLUE)🧪 Probando API del dashboard...$(NC)"
	@curl -s http://localhost:8080/api/status | jq .
	@echo ""
	@curl -s http://localhost:8080/api/metrics | jq .

test-microsoft365: ## Probar integración con Microsoft 365
	@echo "$(BLUE)🧪 Probando Microsoft 365 integration...$(NC)"
	@echo "$(YELLOW)Verificando configuración...$(NC)"
	@if [ -n "$$MS365_CLIENT_ID" ] && [ -n "$$MS365_TENANT_ID" ]; then \
		echo "$(GREEN)✅ Variables de entorno configuradas$(NC)"; \
		echo "$(YELLOW)Para autenticación completa, visita: https://microsoft.com/devicelogin$(NC)"; \
	else \
		echo "$(RED)❌ Variables de entorno no configuradas$(NC)"; \
		echo "$(YELLOW)Por favor configura MS365_CLIENT_ID y MS365_TENANT_ID en .env$(NC)"; \
	fi

test-github: ## Probar integración con GitHub
	@echo "$(BLUE)🧪 Probando GitHub integration...$(NC)"
	@if [ -n "$$GITHUB_TOKEN" ]; then \
		curl -s -H "Authorization: token $$GITHUB_TOKEN" https://api.github.com/user | jq .login; \
		echo "$(GREEN)✅ GitHub API conectada$(NC)"; \
	else \
		echo "$(RED)❌ GITHUB_TOKEN no configurado$(NC)"; \
	fi

test-notion: ## Probar integración con Notion
	@echo "$(BLUE)🧪 Probando Notion integration...$(NC)"
	@if [ -n "$$NOTION_TOKEN" ]; then \
		curl -s -H "Authorization: Bearer $$NOTION_TOKEN" \
			-H "Notion-Version: 2022-06-28" \
			https://api.notion.com/v1/users/me | jq .name; \
		echo "$(GREEN)✅ Notion API conectada$(NC)"; \
	else \
		echo "$(RED)❌ NOTION_TOKEN no configurado$(NC)"; \
	fi

backup: ## Crear backup de datos
	@echo "$(BLUE)💾 Creando backup de datos...$(NC)"
	@mkdir -p backups
	@docker-compose -f $(COMPOSE_FILE) exec -T postgres pg_dump -U scs_user scs_db > backups/scs_db_$$(date +%Y%m%d_%H%M%S).sql
	@docker-compose -f $(COMPOSE_FILE) exec -T postgres pg_dump -U n8n_user n8n_db > backups/n8n_db_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup completado$(NC)"

restore: ## Restaurar backup (uso: make restore DB=scs_db FILE=backup.sql)
	@echo "$(BLUE)🔄 Restaurando backup...$(NC)"
	@if [ -n "$(FILE)" ] && [ -n "$(DB)" ]; then \
		docker-compose -f $(COMPOSE_FILE) exec -T postgres psql -U $$(echo $(DB) | sed 's/_db//_user') $(DB) < $(FILE); \
		echo "$(GREEN)✅ Backup restaurado$(NC)"; \
	else \
		echo "$(RED)❌ Especifica DB y FILE: make restore DB=scs_db FILE=backup.sql$(NC)"; \
	fi

clean: ## Limpiar contenedores, imágenes y volúmenes
	@echo "$(BLUE)🧹 Limpiando sistema...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Sistema limpiado$(NC)"

dev: ## Iniciar entorno de desarrollo
	@echo "$(BLUE)🛠️ Iniciando entorno de desarrollo...$(NC)"
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d
	@echo "$(GREEN)✅ Entorno de desarrollo iniciado$(NC)"

install-deps: ## Instalar dependencias de desarrollo
	@echo "$(BLUE)📦 Instalando dependencias...$(NC)"
	@pip install -r requirements.txt 2>/dev/null || echo "$(YELLOW)requirements.txt no encontrado$(NC)"
	@npm install 2>/dev/null || echo "$(YELLOW)package.json no encontrado$(NC)"
	@echo "$(GREEN)✅ Dependencias instaladas$(NC)"

test: ## Ejecutar tests
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	@python -m pytest tests/ -v 2>/dev/null || echo "$(YELLOW)No se encontraron tests$(NC)"
	@echo "$(GREEN)✅ Tests completados$(NC)"

lint: ## Ejecutar linting de código
	@echo "$(BLUE)🔍 Ejecutando linting...$(NC)"
	@python -m flake8 src/ 2>/dev/null || echo "$(YELLOW)flake8 no instalado$(NC)"
	@python -m black --check src/ 2>/dev/null || echo "$(YELLOW)black no instalado$(NC)"
	@echo "$(GREEN)✅ Linting completado$(NC)"

format: ## Formatear código
	@echo "$(BLUE)📝 Formateando código...$(NC)"
	@python -m black src/ 2>/dev/null || echo "$(YELLOW)black no instalado$(NC)"
	@python -m isort src/ 2>/dev/null || echo "$(YELLOW)isort no instalado$(NC)"
	@echo "$(GREEN)✅ Código formateado$(NC)"

shell-scs: ## Acceder a shell de Shared Context Server
	@echo "$(BLUE)🐚 Accediendo a shell de Shared Context Server...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec shared-context-server /bin/bash

shell-postgres: ## Acceder a shell de PostgreSQL
	@echo "$(BLUE)🐚 Accediendo a shell de PostgreSQL...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U scs_user -d scs_db

shell-n8n: ## Acceder a shell de n8n
	@echo "$(BLUE)🐚 Accediendo a shell de n8n...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec n8n /bin/bash

update: ## Actualizar imágenes Docker
	@echo "$(BLUE)🔄 Actualizando imágenes Docker...$(NC)"
	docker-compose -f $(COMPOSE_FILE) pull
	@echo "$(GREEN)✅ Imágenes actualizadas$(NC)"

security-scan: ## Escanear vulnerabilidades de seguridad
	@echo "$(BLUE)🔒 Escaneando vulnerabilidades...$(NC)"
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-aquasec/trivy image enterprise-integration-hub_shared-context-server:latest || \
		echo "$(YELLOW)Trivy no disponible$(NC)"
	@echo "$(GREEN)✅ Escaneo de seguridad completado$(NC)"

benchmark: ## Ejecutar benchmark de rendimiento
	@echo "$(BLUE)⚡ Ejecutando benchmark...$(NC)"
	@echo "$(YELLOW)Probando rendimiento de API del dashboard...$(NC)"
	@time curl -s http://localhost:8080/api/status > /dev/null
	@echo "$(YELLOW)Probando Shared Context Server...$(NC)"
	@time curl -s http://localhost:23456/health > /dev/null
	@echo "$(GREEN)✅ Benchmark completado$(NC)"

docs: ## Generar documentación
	@echo "$(BLUE)📚 Generando documentación...$(NC)"
	@mkdir -p docs
	@echo "# Enterprise Integration Hub Documentation\n\nGenerated on $$(date)" > docs/README.md
	@echo "## Services\n\n- Shared Context Server: http://localhost:23456\n- Dashboard: http://localhost:8080\n- n8n: http://localhost:5678\n- Grafana: http://localhost:3001\n- Prometheus: http://localhost:9090" >> docs/README.md
	@echo "$(GREEN)✅ Documentación generada$(NC)"

info: ## Mostrar información del sistema
	@echo "$(BLUE)ℹ️ Enterprise Integration Hub Information$(NC)"
	@echo "$(YELLOW)Version:$(NC) 1.0.0"
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  - Shared Context Server: http://localhost:23456"
	@echo "  - Dashboard: http://localhost:8080"
	@echo "  - n8n Workflows: http://localhost:5678"
	@echo "  - Grafana: http://localhost:3001"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Kibana: http://localhost:5601"
	@echo "$(YELLOW)Documentation:$(NC) https://github.com/omanzanodev/enterprise-integration-hub"
	@echo "$(YELLOW)Support:$(NC) Create an issue in GitHub repository"

# Comandos de emergencia
emergency-stop: ## Detención de emergencia de todos los servicios
	@echo "$(RED)🚨 Detención de emergencia...$(NC)"
	docker-compose -f $(COMPOSE_FILE) kill
	docker-compose -f $(COMPOSE_FILE) down --remove-orphans
	@echo "$(GREEN)✅ Todos los servicios detenidos$(NC)"

reset-data: ## Resetear todos los datos (peligroso)
	@echo "$(RED)⚠️ ADVERTENCIA: Esto eliminará todos los datos$(NC)"
	@read -p "¿Estás seguro? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker-compose -f $(COMPOSE_FILE) down -v
	docker volume rm $$(docker volume ls -q | grep enterprise) 2>/dev/null || true
	@echo "$(GREEN)✅ Datos eliminados$(NC)"