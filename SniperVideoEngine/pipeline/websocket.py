"""
WebSocket Hub
Hub central para comunicação em tempo real.
"""
import asyncio
import json
import time
from typing import Dict, Set, Any, Optional, Callable
from fastapi import WebSocket


class WebSocketHub:
    """
    Hub central para gerenciar conexões WebSocket.
    
    Permite broadcast de atualizações para todos os clientes conectados.
    Suporta keepalive via ping/pong e broadcast periodico de metricas.
    """

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._global_connections: Set[WebSocket] = set()
        self._keepalive_task: Optional[asyncio.Task] = None
        self._dashboard_broadcast_task: Optional[asyncio.Task] = None
        self._dashboard_fetcher: Optional[Callable] = None

    # ─── Keepalive ────────────────────────────────────────────────────────

    async def start_keepalive(self, interval: int = 25):
        """
        Inicia keepalive ping/pong para todas as conexões.
        Clientes que não responderem em 2x interval são removidos.
        """
        if self._keepalive_task:
            self._keepalive_task.cancel()
        
        async def _ping_loop():
            while True:
                await asyncio.sleep(interval)
                await self._ping_all()
        
        self._keepalive_task = asyncio.create_task(_ping_loop())
        print(f"[WebSocket] Keepalive iniciado (intervalo: {interval}s)")

    async def _ping_all(self):
        """Envia ping para todas as conexões, remove as mortas."""
        dead = set()
        ping_msg = json.dumps({"type": "ping", "data": {"ts": time.time()}})
        
        all_conns = set(self._global_connections)
        for task_conns in self._connections.values():
            all_conns.update(task_conns)
        
        for conn in all_conns:
            try:
                await conn.send_text(ping_msg)
            except Exception:
                dead.add(conn)
        
        if dead:
            for conn in dead:
                self._global_connections.discard(conn)
                for tid in list(self._connections.keys()):
                    self._connections[tid].discard(conn)
            print(f"[WebSocket] Keepalive: {len(dead)} conexões mortas removidas")

    def stop_keepalive(self):
        """Para o keepalive."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

    # ─── Dashboard Broadcast ──────────────────────────────────────────────

    def set_dashboard_fetcher(self, fetcher: Callable):
        """
        Define a função que busca metricas do dashboard.
        Deve ser uma callable que retorna um dict com as metricas.
        """
        self._dashboard_fetcher = fetcher

    async def start_dashboard_broadcast(self, interval: int = 30):
        """
        Inicia broadcast periodico de metricas do dashboard.
        """
        if self._dashboard_broadcast_task:
            self._dashboard_broadcast_task.cancel()
        
        if not self._dashboard_fetcher:
            print("[WebSocket] Dashboard broadcast: nenhum fetcher configurado")
            return
        
        async def _dashboard_loop():
            while True:
                await asyncio.sleep(interval)
                try:
                    metrics = await self._dashboard_fetcher() if asyncio.iscoroutinefunction(self._dashboard_fetcher) else self._dashboard_fetcher()
                    await self.broadcast("dashboard_update", metrics)
                except Exception as e:
                    print(f"[WebSocket] Dashboard broadcast error: {e}")
        
        self._dashboard_broadcast_task = asyncio.create_task(_dashboard_loop())
        print(f"[WebSocket] Dashboard broadcast iniciado (intervalo: {interval}s)")

    def stop_dashboard_broadcast(self):
        """Para o broadcast do dashboard."""
        if self._dashboard_broadcast_task:
            self._dashboard_broadcast_task.cancel()
            self._dashboard_broadcast_task = None

    # ─── Conexões ─────────────────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, task_id: str = None):
        """
        Conecta um novo cliente WebSocket.
        
        Args:
            websocket: Conexão WebSocket
            task_id: ID da tarefa (opcional)
        """
        await websocket.accept()
        
        if task_id:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(websocket)
            print(f"[WebSocket] Cliente conectado para task: {task_id}")
        else:
            self._global_connections.add(websocket)
            print("[WebSocket] Cliente global conectado")

    def disconnect(self, websocket: WebSocket, task_id: str = None):
        """
        Desconecta um cliente.
        
        Args:
            websocket: Conexão WebSocket
            task_id: ID da tarefa (opcional)
        """
        if task_id and task_id in self._connections:
            self._connections[task_id].discard(websocket)
            if not self._connections[task_id]:
                del self._connections[task_id]
            print(f"[WebSocket] Cliente desconectado de task: {task_id}")
        else:
            self._global_connections.discard(websocket)
            print("[WebSocket] Cliente global desconectado")

    async def broadcast(self, event_type: str, data: Dict[str, Any], task_id: str = None):
        """
        Envia mensagem para todos os clientes conectados.
        
        Args:
            event_type: Tipo do evento
            data: Dados do evento
            task_id: ID da tarefa (opcional)
        """
        message = json.dumps({
            "type": event_type,
            "data": data,
        }, default=str)
        
        targets = set()
        
        if task_id and task_id in self._connections:
            targets.update(self._connections[task_id])
        
        targets.update(self._global_connections)
        
        disconnected = set()
        for connection in targets:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[WebSocket] Erro ao enviar mensagem: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            self._global_connections.discard(conn)
            for tid in list(self._connections.keys()):
                self._connections[tid].discard(conn)

    async def send_to_task(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """
        Envia mensagem apenas para clientes de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa
            event_type: Tipo do evento
            data: Dados do evento
        """
        await self.broadcast(event_type, data, task_id)

    def get_connected_clients(self, task_id: str = None) -> int:
        """
        Retorna número de clientes conectados.
        
        Args:
            task_id: ID da tarefa (opcional)
            
        Returns:
            Número de clientes conectados
        """
        if task_id:
            return len(self._connections.get(task_id, set()))
        return len(self._global_connections)

    def get_all_tasks(self) -> list:
        """Retorna lista de todas as tasks com conexões."""
        return list(self._connections.keys())

    def stop_all(self):
        """Para keepalive e dashboard broadcast."""
        self.stop_keepalive()
        self.stop_dashboard_broadcast()
