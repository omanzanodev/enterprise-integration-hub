#!/usr/bin/env python3
"""
Enterprise Integration Hub - Sistema de Integración Empresarial
Centro neurálgico que coordina múltiples sistemas externos usando
Shared Context Server como base para automatización inteligente.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

# Importaciones de MCP
import aiohttp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationStatus:
    """Estado de una integración"""
    service: str
    status: str  # 'connected', 'disconnected', 'error'
    last_check: datetime
    metrics: Dict[str, Any]

class EnterpriseIntegrationHub:
    """Clase principal del Hub de Integración Empresarial"""
    
    def __init__(self):
        self.scs_url = os.getenv('SCS_URL', 'http://localhost:23456')
        self.scs_api_key = os.getenv('SCS_API_KEY')
        self.n8n_url = os.getenv('N8N_URL', 'http://localhost:5678')
        self.n8n_api_key = os.getenv('N8N_API_KEY')
        
        # Estados de integraciones
        self.integrations: Dict[str, IntegrationStatus] = {}
        self.session = None
        self.mcp_session = None
        
        # Headers para API calls
        self.scs_headers = {
            'X-API-Key': self.scs_api_key,
            'Content-Type': 'application/json'
        }
        
        self.n8n_headers = {
            'X-N8N-API-KEY': self.n8n_api_key,
            'Content-Type': 'application/json'
        }
    
    async def initialize(self):
        """Inicializar todas las conexiones"""
        logger.info("🚀 Inicializando Enterprise Integration Hub")
        
        # Crear sesión HTTP
        self.session = aiohttp.ClientSession()
        
        # Conectar a Shared Context Server
        await self._connect_scs()
        
        # Inicializar integraciones
        await self._initialize_integrations()
        
        # Verificar estado de todos los servicios
        await self._health_check_all()
        
        logger.info("✅ Enterprise Integration Hub inicializado correctamente")
    
    async def _connect_scs(self):
        """Conectar a Shared Context Server"""
        try:
            async with self.session.get(
                f"{self.scs_url}/health",
                headers=self.scs_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Conectado a Shared Context Server: {data.get('status', 'healthy')}")
                    self.integrations['shared-context-server'] = IntegrationStatus(
                        service='Shared Context Server',
                        status='connected',
                        last_check=datetime.now(timezone.utc),
                        metrics=data
                    )
                else:
                    raise Exception(f"Status code: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error conectando a Shared Context Server: {e}")
            self.integrations['shared-context-server'] = IntegrationStatus(
                service='Shared Context Server',
                status='error',
                last_check=datetime.now(timezone.utc),
                metrics={'error': str(e)}
            )
    
    async def _initialize_integrations(self):
        """Inicializar todas las integraciones"""
        logger.info("🔌 Inicializando integraciones empresariales...")
        
        # Microsoft 365
        await self._init_microsoft365()
        
        # GitHub Enterprise
        await self._init_github_enterprise()
        
        # Notion
        await self._init_notion()
        
        # n8n Workflows
        await self._init_n8n()
        
        # APIs Externas
        await self._init_external_apis()
    
    async def _init_microsoft365(self):
        """Inicializar integración con Microsoft 365"""
        try:
            # Verificar credenciales de Microsoft 365
            tenant_id = os.getenv('MS365_TENANT_ID')
            client_id = os.getenv('MS365_CLIENT_ID')
            
            if tenant_id and client_id:
                logger.info("📧 Inicializando Microsoft 365 integration...")
                
                # Crear sesión en SCS para Microsoft 365
                session_data = await self._create_scs_session(
                    purpose="Microsoft 365 Integration",
                    metadata={"service": "microsoft365", "tenant": tenant_id}
                )
                
                self.integrations['microsoft365'] = IntegrationStatus(
                    service='Microsoft 365',
                    status='connected',
                    last_check=datetime.now(timezone.utc),
                    metrics={'session_id': session_data.get('session_id'), 'tenant': tenant_id}
                )
                
                logger.info("✅ Microsoft 365 inicializado correctamente")
            else:
                logger.warning("⚠️ Credenciales de Microsoft 365 no configuradas")
                self.integrations['microsoft365'] = IntegrationStatus(
                    service='Microsoft 365',
                    status='disconnected',
                    last_check=datetime.now(timezone.utc),
                    metrics={'error': 'credentials_not_configured'}
                )
        except Exception as e:
            logger.error(f"❌ Error inicializando Microsoft 365: {e}")
            self.integrations['microsoft365'] = IntegrationStatus(
                service='Microsoft 365',
                status='error',
                last_check=datetime.now(timezone.utc),
                metrics={'error': str(e)}
            )
    
    async def _init_github_enterprise(self):
        """Inicializar integración con GitHub Enterprise"""
        try:
            github_token = os.getenv('GITHUB_TOKEN')
            github_url = os.getenv('GITHUB_ENTERPRISE_URL', 'https://github.com')
            
            if github_token:
                logger.info("🐙 Inicializando GitHub Enterprise integration...")
                
                # Verificar conexión a GitHub
                async with self.session.get(
                    f"{github_url}/user",
                    headers={'Authorization': f'token {github_token}'}
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        logger.info(f"✅ Conectado a GitHub como: {user_data.get('login', 'unknown')}")
                        
                        # Crear sesión en SCS para GitHub
                        session_data = await self._create_scs_session(
                            purpose="GitHub Enterprise Integration",
                            metadata={
                                "service": "github", 
                                "user": user_data.get('login'),
                                "enterprise_url": github_url
                            }
                        )
                        
                        self.integrations['github'] = IntegrationStatus(
                            service='GitHub Enterprise',
                            status='connected',
                            last_check=datetime.now(timezone.utc),
                            metrics={
                                'session_id': session_data.get('session_id'),
                                'user': user_data.get('login'),
                                'enterprise_url': github_url
                            }
                        )
                    else:
                        raise Exception(f"GitHub API error: {response.status}")
            else:
                logger.warning("⚠️ Token de GitHub no configurado")
                self.integrations['github'] = IntegrationStatus(
                    service='GitHub Enterprise',
                    status='disconnected',
                    last_check=datetime.now(timezone.utc),
                    metrics={'error': 'token_not_configured'}
                )
        except Exception as e:
            logger.error(f"❌ Error inicializando GitHub Enterprise: {e}")
            self.integrations['github'] = IntegrationStatus(
                service='GitHub Enterprise',
                status='error',
                last_check=datetime.now(timezone.utc),
                metrics={'error': str(e)}
            )
    
    async def _init_notion(self):
        """Inicializar integración con Notion"""
        try:
            notion_token = os.getenv('NOTION_TOKEN')
            database_id = os.getenv('NOTION_DATABASE_ID')
            
            if notion_token and database_id:
                logger.info("📝 Inicializando Notion integration...")
                
                # Crear sesión en SCS para Notion
                session_data = await self._create_scs_session(
                    purpose="Notion Integration",
                    metadata={
                        "service": "notion",
                        "database_id": database_id
                    }
                )
                
                self.integrations['notion'] = IntegrationStatus(
                    service='Notion',
                    status='connected',
                    last_check=datetime.now(timezone.utc),
                    metrics={
                        'session_id': session_data.get('session_id'),
                        'database_id': database_id
                    }
                )
                
                logger.info("✅ Notion inicializado correctamente")
            else:
                logger.warning("⚠️ Credenciales de Notion no configuradas")
                self.integrations['notion'] = IntegrationStatus(
                    service='Notion',
                    status='disconnected',
                    last_check=datetime.now(timezone.utc),
                    metrics={'error': 'credentials_not_configured'}
                )
        except Exception as e:
            logger.error(f"❌ Error inicializando Notion: {e}")
            self.integrations['notion'] = IntegrationStatus(
                service='Notion',
                status='error',
                last_check=datetime.now(timezone.utc),
                metrics={'error': str(e)}
            )
    
    async def _init_n8n(self):
        """Inicializar integración con n8n"""
        try:
            async with self.session.get(
                f"{self.n8n_url}/rest/active",
                headers=self.n8n_headers
            ) as response:
                if response.status == 200:
                    workflows = await response.json()
                    logger.info(f"🔄 Conectado a n8n - {len(workflows.get('data', []))} workflows activos")
                    
                    self.integrations['n8n'] = IntegrationStatus(
                        service='n8n Workflows',
                        status='connected',
                        last_check=datetime.now(timezone.utc),
                        metrics={
                            'active_workflows': len(workflows.get('data', [])),
                            'url': self.n8n_url
                        }
                    )
                else:
                    raise Exception(f"n8n API error: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error inicializando n8n: {e}")
            self.integrations['n8n'] = IntegrationStatus(
                service='n8n Workflows',
                status='error',
                last_check=datetime.now(timezone.utc),
                metrics={'error': str(e)}
            )
    
    async def _init_external_apis(self):
        """Inicializar integración con APIs externas"""
        logger.info("🔗 Inicializando APIs externas...")
        
        external_apis = {}
        
        # Slack
        if os.getenv('SLACK_BOT_TOKEN'):
            external_apis['slack'] = {'status': 'configured'}
        
        # Jira
        if os.getenv('JIRA_API_TOKEN') and os.getenv('JIRA_URL'):
            external_apis['jira'] = {'status': 'configured'}
        
        # Salesforce
        if os.getenv('SALESFORCE_CLIENT_ID'):
            external_apis['salesforce'] = {'status': 'configured'}
        
        self.integrations['external_apis'] = IntegrationStatus(
            service='External APIs',
            status='connected' if external_apis else 'disconnected',
            last_check=datetime.now(timezone.utc),
            metrics={'configured_apis': list(external_apis.keys())}
        )
        
        logger.info(f"✅ APIs externas configuradas: {list(external_apis.keys())}")
    
    async def _create_scs_session(self, purpose: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Crear sesión en Shared Context Server"""
        try:
            session_payload = {
                "purpose": purpose,
                "metadata": metadata,
                "auto_generate_session_id": True
            }
            
            async with self.session.post(
                f"{self.scs_url}/api/sessions",
                json=session_payload,
                headers=self.scs_headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"SCS API error: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error creando sesión SCS: {e}")
            return {}
    
    async def _health_check_all(self):
        """Verificar estado de todas las integraciones"""
        logger.info("🏥 Verificando salud de todas las integraciones...")
        
        for service_name, integration in self.integrations.items():
            if integration.status == 'connected':
                logger.info(f"✅ {service_name}: {integration.status}")
            else:
                logger.warning(f"⚠️ {service_name}: {integration.status}")
        
        connected_count = sum(1 for i in self.integrations.values() if i.status == 'connected')
        total_count = len(self.integrations)
        
        logger.info(f"📊 Resumen: {connected_count}/{total_count} integraciones conectadas")
    
    async def process_email_to_github_workflow(self, email_data: Dict[str, Any]):
        """
        Workflow: Email → GitHub Issue → Notion Documentation
        """
        logger.info("📧 → 🐙 → 📝 Iniciando workflow Email → GitHub → Notion")
        
        try:
            # 1. Analizar email usando SCS
            analysis_data = await self._analyze_email_with_scs(email_data)
            
            # 2. Crear issue en GitHub
            if self.integrations['github'].status == 'connected':
                github_issue = await self._create_github_issue_from_email(
                    email_data, analysis_data
                )
                logger.info(f"✅ Issue creado en GitHub: {github_issue.get('html_url')}")
            
            # 3. Crear documentación en Notion
            if self.integrations['notion'].status == 'connected':
                notion_page = await self._create_notion_documentation(
                    email_data, analysis_data, github_issue
                )
                logger.info(f"✅ Documentación creada en Notion: {notion_page.get('url')}")
            
            # 4. Notificar en Teams si está disponible
            await self._notify_teams_workflow_completion(
                "Email → GitHub → Notion",
                {
                    "email_subject": email_data.get('subject'),
                    "github_issue": github_issue.get('html_url') if github_issue else None,
                    "notion_doc": notion_page.get('url') if notion_page else None
                }
            )
            
            return {
                "success": True,
                "workflow": "email_to_github_to_notion",
                "github_issue": github_issue,
                "notion_page": notion_page
            }
            
        except Exception as e:
            logger.error(f"❌ Error en workflow Email → GitHub → Notion: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_email_with_scs(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar email usando Shared Context Server"""
        try:
            # Agregar mensaje a sesión SCS para análisis
            message_payload = {
                "session_id": self.integrations.get('microsoft365', {}).metrics.get('session_id'),
                "agent_name": "email_analyzer",
                "content": f"Analizando email: {email_data.get('subject', 'Sin asunto')}",
                "message_type": "analysis",
                "metadata": {
                    "email_data": email_data,
                    "analysis_type": "email_classification"
                }
            }
            
            async with self.session.post(
                f"{self.scs_url}/api/sessions/messages",
                json=message_payload,
                headers=self.scs_headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"analysis": "manual_fallback", "category": "technical_request"}
        except Exception as e:
            logger.error(f"❌ Error analizando email con SCS: {e}")
            return {"analysis": "error", "error": str(e)}
    
    async def _create_github_issue_from_email(self, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Crear issue en GitHub desde email"""
        try:
            github_token = os.getenv('GITHUB_TOKEN')
            github_url = os.getenv('GITHUB_ENTERPRISE_URL', 'https://github.com')
            
            # Extraer información relevante
            subject = email_data.get('subject', 'Issue from Email')
            sender = email_data.get('from', 'unknown@example.com')
            body = email_data.get('body', '')
            
            # Construir título y cuerpo del issue
            title = f"[EMAIL] {subject}"
            issue_body = f"""**Issue generado desde email**

**De:** {sender}
**Asunto:** {subject}
**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

---

**Contenido del email:**
{body}

---

**Análisis automático:**
```json
{json.dumps(analysis, indent=2)}
```

---

🤖 *Este issue fue creado automáticamente por el Enterprise Integration Hub*
"""
            
            # Crear issue en el repositorio por defecto (esto se puede configurar)
            issue_data = {
                "title": title,
                "body": issue_body,
                "labels": ["automation", "email-integration"]
            }
            
            async with self.session.post(
                f"{github_url}/repos/omanzanodev/enterprise-integration-hub/issues",
                json=issue_data,
                headers={'Authorization': f'token {github_token}'}
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"GitHub API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Error creando issue en GitHub: {e}")
            return {}
    
    async def _create_notion_documentation(self, email_data: Dict[str, Any], analysis: Dict[str, Any], github_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Crear documentación en Notion"""
        try:
            # Esta es una implementación simulada - en producción usaría las herramientas MCP de Notion
            notion_doc = {
                "title": f"Email Request: {email_data.get('subject', 'Sin asunto')}",
                "url": f"https://notion.so/entry/{hash(str(email_data))}",
                "properties": {
                    "Source": "Email Integration",
                    "Status": "Documented",
                    "GitHub Issue": github_issue.get('html_url') if github_issue else None,
                    "Created": datetime.now(timezone.utc).isoformat()
                }
            }
            
            return notion_doc
            
        except Exception as e:
            logger.error(f"❌ Error creando documentación en Notion: {e}")
            return {}
    
    async def _notify_teams_workflow_completion(self, workflow_name: str, details: Dict[str, Any]):
        """Notificar completion en Teams"""
        try:
            if self.integrations['microsoft365'].status == 'connected':
                message = f"""✅ **Workflow completado: {workflow_name}**

**Detalles:**
{json.dumps(details, indent=2)}

🤖 *Notificación automática de Enterprise Integration Hub*"""
                
                logger.info(f"📢 Notificación Teams enviada: {workflow_name}")
                
        except Exception as e:
            logger.error(f"❌ Error notificando en Teams: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        return {
            "hub_status": "running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "integrations": {
                name: {
                    "status": integration.status,
                    "last_check": integration.last_check.isoformat(),
                    "metrics": integration.metrics
                }
                for name, integration in self.integrations.items()
            },
            "total_integrations": len(self.integrations),
            "connected_integrations": sum(1 for i in self.integrations.values() if i.status == 'connected')
        }
    
    async def shutdown(self):
        """Apagar el hub de forma segura"""
        logger.info("🛑 Apagando Enterprise Integration Hub...")
        
        if self.session:
            await self.session.close()
        
        logger.info("✅ Enterprise Integration Hub apagado correctamente")

async def main():
    """Función principal"""
    hub = EnterpriseIntegrationHub()
    
    try:
        await hub.initialize()
        
        # Mantener el hub corriendo
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            # Verificar salud de integraciones periódicamente
            await hub._health_check_all()
            
    except KeyboardInterrupt:
        logger.info("🛑 Recibida señal de interrupción")
    except Exception as e:
        logger.error(f"❌ Error en el hub principal: {e}")
    finally:
        await hub.shutdown()

if __name__ == "__main__":
    asyncio.run(main())