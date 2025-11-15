#!/usr/bin/env python3
"""
Enterprise Integration Hub Dashboard
Dashboard en tiempo real para monitorear todas las integraciones empresariales
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import os

import aiohttp
from aiohttp import web
import aiohttp_cors

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationMetric:
    """Métrica de una integración"""
    service: str
    status: str
    response_time: float
    success_rate: float
    last_success: datetime
    last_error: datetime
    total_requests: int
    error_count: int
    uptime_percentage: float

@dataclass
class WorkflowExecution:
    """Ejecución de workflow"""
    workflow_id: str
    workflow_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: str

class IntegrationDashboard:
    """Dashboard de monitoreo de integraciones"""
    
    def __init__(self):
        self.app = web.Application()
        self.scs_url = os.getenv('SCS_URL', 'http://localhost:23456')
        self.scs_api_key = os.getenv('SCS_API_KEY')
        self.n8n_url = os.getenv('N8N_URL', 'http://localhost:5678')
        self.n8n_api_key = os.getenv('N8N_API_KEY')
        
        # Almacenamiento de métricas
        self.integration_metrics: Dict[str, IntegrationMetric] = {}
        self.workflow_executions: List[WorkflowExecution] = []
        self.system_events: List[Dict[str, Any]] = []
        
        # Configurar CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Configurar rutas
        self._setup_routes()
        self._add_cors_routes(cors)
        
        # Session HTTP
        self.session = None
    
    def _setup_routes(self):
        """Configurar rutas del dashboard"""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_system_status)
        self.app.router.add_get('/api/metrics', self.get_integration_metrics)
        self.app.router.add_get('/api/workflows', self.get_workflow_executions)
        self.app.router.add_get('/api/events', self.get_system_events)
        self.app.router.add_post('/api/webhook', self.handle_webhook)
        self.app.router.add_get('/health', self.health_check)
    
    def _add_cors_routes(self, cors):
        """Agregar CORS a todas las rutas"""
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def serve_dashboard(self, request):
        """Servir HTML del dashboard"""
        html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Integration Hub Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @keyframes pulse-green {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .status-online { animation: pulse-green 2s infinite; }
        .metric-card { transition: all 0.3s ease; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-network-wired mr-3 text-blue-600"></i>
                        Enterprise Integration Hub
                    </h1>
                    <p class="text-gray-600 mt-2">Dashboard de Monitoreo en Tiempo Real</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-right">
                        <p class="text-sm text-gray-500">Última actualización</p>
                        <p class="text-lg font-semibold" id="lastUpdate">--:--:--</p>
                    </div>
                    <button onclick="refreshData()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
                        <i class="fas fa-sync-alt mr-2"></i>Actualizar
                    </button>
                </div>
            </div>
        </div>

        <!-- System Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="metric-card bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Integraciones Activas</p>
                        <p class="text-3xl font-bold text-green-600" id="activeIntegrations">0</p>
                    </div>
                    <i class="fas fa-plug text-3xl text-green-500"></i>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Workflows Hoy</p>
                        <p class="text-3xl font-bold text-blue-600" id="workflowsToday">0</p>
                    </div>
                    <i class="fas fa-cogs text-3xl text-blue-500"></i>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Tasa de Éxito</p>
                        <p class="text-3xl font-bold text-blue-600" id="successRate">0%</p>
                    </div>
                    <i class="fas fa-check-circle text-3xl text-blue-500"></i>
                </div>
            </div>
            
            <div class="metric-card bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">Tiempo Respuesta</p>
                        <p class="text-3xl font-bold text-purple-600" id="avgResponseTime">0ms</p>
                    </div>
                    <i class="fas fa-tachometer-alt text-3xl text-purple-500"></i>
                </div>
            </div>
        </div>

        <!-- Integration Status -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-server mr-2 text-gray-600"></i>
                    Estado de Integraciones
                </h2>
                <div id="integrationStatus" class="space-y-3">
                    <!-- Integration statuses will be inserted here -->
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-chart-line mr-2 text-gray-600"></i>
                    Rendimiento del Sistema
                </h2>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>
        </div>

        <!-- Recent Workflows -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-bold text-gray-800 mb-4">
                <i class="fas fa-history mr-2 text-gray-600"></i>
                Ejecuciones Recientes de Workflows
            </h2>
            <div class="overflow-x-auto">
                <table class="min-w-full table-auto">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Duración</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Inicio</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="workflowExecutions" class="bg-white divide-y divide-gray-200">
                        <!-- Workflow executions will be inserted here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- System Events -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">
                <i class="fas fa-bell mr-2 text-gray-600"></i>
                Eventos del Sistema
            </h2>
            <div id="systemEvents" class="space-y-2 max-h-96 overflow-y-auto">
                <!-- System events will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        let performanceChart;
        
        async function initChart() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Tiempo de Respuesta (ms)',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        async function refreshData() {
            try {
                // Actualizar timestamp
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                
                // Obtener datos del sistema
                const [status, metrics, workflows, events] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/metrics').then(r => r.json()),
                    fetch('/api/workflows').then(r => r.json()),
                    fetch('/api/events').then(r => r.json())
                ]);
                
                // Actualizar métricas principales
                updateMainMetrics(status);
                
                // Actualizar estado de integraciones
                updateIntegrationStatus(metrics);
                
                // Actualizar ejecuciones de workflows
                updateWorkflowExecutions(workflows);
                
                // Actualizar eventos del sistema
                updateSystemEvents(events);
                
                // Actualizar gráfico de rendimiento
                updatePerformanceChart(metrics);
                
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        function updateMainMetrics(status) {
            document.getElementById('activeIntegrations').textContent = status.connected_integrations || 0;
            
            // Calcular workflows del día
            const today = new Date().toISOString().split('T')[0];
            const workflowsToday = status.workflow_executions?.filter(w => 
                w.start_time.startsWith(today)
            ).length || 0;
            document.getElementById('workflowsToday').textContent = workflowsToday;
            
            // Calcular tasa de éxito
            const totalRequests = Object.values(status.integrations || {})
                .reduce((sum, integration) => sum + (integration.metrics?.total_requests || 0), 0);
            const totalErrors = Object.values(status.integrations || {})
                .reduce((sum, integration) => sum + (integration.metrics?.error_count || 0), 0);
            const successRate = totalRequests > 0 ? ((totalRequests - totalErrors) / totalRequests * 100).toFixed(1) : 0;
            document.getElementById('successRate').textContent = successRate + '%';
            
            // Tiempo promedio de respuesta
            const avgResponseTime = Object.values(status.integrations || {})
                .reduce((sum, integration) => sum + (integration.metrics?.response_time || 0), 0) / 
                Object.keys(status.integrations || {}).length || 0;
            document.getElementById('avgResponseTime').textContent = Math.round(avgResponseTime) + 'ms';
        }
        
        function updateIntegrationStatus(metrics) {
            const container = document.getElementById('integrationStatus');
            container.innerHTML = '';
            
            Object.entries(metrics).forEach(([service, metric]) => {
                const statusColor = metric.status === 'connected' ? 'green' : 
                                 metric.status === 'error' ? 'red' : 'yellow';
                const statusIcon = metric.status === 'connected' ? 'check-circle' : 
                                 metric.status === 'error' ? 'times-circle' : 'exclamation-triangle';
                
                const div = document.createElement('div');
                div.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
                div.innerHTML = `
                    <div class="flex items-center">
                        <i class="fas fa-${statusIcon} text-${statusColor}-500 mr-3"></i>
                        <div>
                            <p class="font-semibold text-gray-800">${service}</p>
                            <p class="text-sm text-gray-500">Uptime: ${metric.uptime_percentage?.toFixed(1) || 0}%</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-semibold text-gray-600">${metric.response_time || 0}ms</p>
                        <p class="text-xs text-gray-500">${metric.success_rate || 0}% éxito</p>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function updateWorkflowExecutions(workflows) {
            const tbody = document.getElementById('workflowExecutions');
            tbody.innerHTML = '';
            
            workflows.slice(0, 10).forEach(workflow => {
                const statusColor = workflow.status === 'success' ? 'green' : 
                                 workflow.status === 'error' ? 'red' : 'yellow';
                const statusIcon = workflow.status === 'success' ? 'check' : 
                                 workflow.status === 'error' ? 'times' : 'clock';
                
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-4 py-2 text-sm font-medium text-gray-900">${workflow.workflow_name}</td>
                    <td class="px-4 py-2 text-sm">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${statusColor}-100 text-${statusColor}-800">
                            <i class="fas fa-${statusIcon} mr-1"></i>${workflow.status}
                        </span>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-500">${workflow.duration || 0}ms</td>
                    <td class="px-4 py-2 text-sm text-gray-500">${new Date(workflow.start_time).toLocaleString()}</td>
                    <td class="px-4 py-2 text-sm">
                        <button class="text-blue-600 hover:text-blue-900" onclick="showWorkflowDetails('${workflow.workflow_id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        function updateSystemEvents(events) {
            const container = document.getElementById('systemEvents');
            container.innerHTML = '';
            
            events.slice(0, 20).forEach(event => {
                const div = document.createElement('div');
                div.className = 'flex items-start space-x-3 p-3 bg-gray-50 rounded-lg';
                div.innerHTML = `
                    <i class="fas fa-info-circle text-blue-500 mt-1"></i>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-800">${event.message}</p>
                        <p class="text-xs text-gray-500">${new Date(event.timestamp).toLocaleString()}</p>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function updatePerformanceChart(metrics) {
            if (!performanceChart) return;
            
            const now = new Date();
            const timeLabel = now.toLocaleTimeString();
            
            // Agregar nuevo punto de datos
            if (performanceChart.data.labels.length > 20) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
            }
            
            performanceChart.data.labels.push(timeLabel);
            
            // Calcular tiempo de respuesta promedio
            const avgResponseTime = Object.values(metrics)
                .reduce((sum, metric) => sum + (metric.response_time || 0), 0) / 
                Object.keys(metrics).length || 0;
            
            performanceChart.data.datasets[0].data.push(avgResponseTime);
            performanceChart.update('none');
        }
        
        function showWorkflowDetails(workflowId) {
            // Implementar modal con detalles del workflow
            alert('Detalles del workflow: ' + workflowId);
        }
        
        // Inicialización
        document.addEventListener('DOMContentLoaded', async () => {
            await initChart();
            await refreshData();
            
            // Actualizar datos cada 30 segundos
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type='text/html')
    
    async def get_system_status(self, request):
        """Obtener estado del sistema"""
        try:
            # Obtener estado de Shared Context Server
            scs_status = await self._get_scs_status()
            
            # Obtener estado de n8n
            n8n_status = await self._get_n8n_status()
            
            # Calcular métricas agregadas
            total_integrations = len(self.integration_metrics)
            connected_integrations = sum(1 for m in self.integration_metrics.values() if m.status == 'connected')
            
            return web.json_response({
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_integrations": total_integrations,
                "connected_integrations": connected_integrations,
                "integration_health": scs_status,
                "n8n_status": n8n_status,
                "workflow_executions": len(self.workflow_executions),
                "system_events": len(self.system_events)
            })
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def get_integration_metrics(self, request):
        """Obtener métricas de integraciones"""
        try:
            metrics_dict = {}
            for service, metric in self.integration_metrics.items():
                metrics_dict[service] = {
                    **asdict(metric),
                    "last_success": metric.last_success.isoformat() if metric.last_success else None,
                    "last_error": metric.last_error.isoformat() if metric.last_error else None
                }
            
            return web.json_response(metrics_dict)
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def get_workflow_executions(self, request):
        """Obtener ejecuciones de workflows"""
        try:
            executions = []
            for execution in self.workflow_executions[-50:]:  # Últimas 50 ejecuciones
                executions.append({
                    **asdict(execution),
                    "start_time": execution.start_time.isoformat(),
                    "end_time": execution.end_time.isoformat()
                })
            
            return web.json_response(executions)
        except Exception as e:
            logger.error(f"Error obteniendo ejecuciones: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def get_system_events(self, request):
        """Obtener eventos del sistema"""
        try:
            return web.json_response(self.system_events[-100:])  # Últimos 100 eventos
        except Exception as e:
            logger.error(f"Error obteniendo eventos: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_webhook(self, request):
        """Manejar webhooks de integraciones"""
        try:
            data = await request.json()
            
            # Procesar webhook según el tipo
            webhook_type = data.get('type', 'unknown')
            
            # Agregar evento del sistema
            self.system_events.append({
                "type": "webhook_received",
                "source": webhook_type,
                "message": f"Webhook recibido de {webhook_type}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            ])
            
            # Mantener solo los últimos 500 eventos
            if len(self.system_events) > 500:
                self.system_events = self.system_events[-500:]
            
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def _get_scs_status(self):
        """Obtener estado de Shared Context Server"""
        try:
            async with self.session.get(
                f"{self.scs_url}/health",
                headers={"X-API-Key": self.scs_api_key}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_n8n_status(self):
        """Obtener estado de n8n"""
        try:
            async with self.session.get(
                f"{self.n8n_url}/rest/active",
                headers={"X-N8N-API-KEY": self.n8n_api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "connected",
                        "active_workflows": len(data.get('data', []))
                    }
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def add_system_event(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Agregar evento del sistema"""
        self.system_events.append({
            "type": event_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {}
        })
        
        # Mantener solo los últimos 500 eventos
        if len(self.system_events) > 500:
            self.system_events = self.system_events[-500:]
    
    def add_workflow_execution(self, execution: WorkflowExecution):
        """Agregar ejecución de workflow"""
        self.workflow_executions.append(execution)
        
        # Mantener solo las últimas 1000 ejecuciones
        if len(self.workflow_executions) > 1000:
            self.workflow_executions = self.workflow_executions[-1000:]
        
        # Agregar evento del sistema
        self.add_system_event(
            "workflow_execution",
            f"Workflow {execution.workflow_name} ejecutado con estado {execution.status}",
            {
                "workflow_id": execution.workflow_id,
                "duration": execution.duration,
                "status": execution.status
            }
        )
    
    async def start(self):
        """Iniciar el dashboard"""
        self.session = aiohttp.ClientSession()
        
        # Inicializar métricas básicas
        await self._initialize_metrics()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        
        logger.info("🚀 Dashboard iniciado en http://localhost:8080")
        
        return runner
    
    async def _initialize_metrics(self):
        """Inicializar métricas de integraciones"""
        default_integrations = [
            'shared-context-server', 'microsoft365', 'github', 'notion', 
            'n8n', 'external_apis'
        ]
        
        for integration in default_integrations:
            self.integration_metrics[integration] = IntegrationMetric(
                service=integration,
                status='unknown',
                response_time=0.0,
                success_rate=100.0,
                last_success=datetime.now(timezone.utc),
                last_error=datetime.now(timezone.utc),
                total_requests=0,
                error_count=0,
                uptime_percentage=100.0
            )
    
    async def stop(self):
        """Detener el dashboard"""
        if self.session:
            await self.session.close()
        logger.info("🛑 Dashboard detenido")

async def main():
    """Función principal"""
    dashboard = IntegrationDashboard()
    
    try:
        runner = await dashboard.start()
        
        # Mantener el dashboard corriendo
        while True:
            await asyncio.sleep(60)
            
            # Simular actualización de métricas
            for service, metric in dashboard.integration_metrics.items():
                # Simular pequeñas variaciones en las métricas
                import random
                metric.response_time = max(10, metric.response_time + random.uniform(-5, 5))
                metric.success_rate = max(90, min(100, metric.success_rate + random.uniform(-1, 1)))
        
    except KeyboardInterrupt:
        logger.info("🛑 Recibida señal de interrupción")
    except Exception as e:
        logger.error(f"❌ Error en el dashboard: {e}")
    finally:
        await dashboard.stop()

if __name__ == "__main__":
    asyncio.run(main())