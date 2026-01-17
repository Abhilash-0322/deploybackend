"""
WebSocket Handler

Real-time WebSocket endpoint for streaming alerts and updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

from app.core.transaction_monitor import get_transaction_monitor, TransactionEvent
from app.ai.policy_engine import get_policy_engine
from app.ai.risk_scorer import get_risk_scorer


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


# Global connection manager
manager = ConnectionManager()


async def handle_transaction_event(event: TransactionEvent):
    """Handle a new transaction event and broadcast alerts."""
    policy_engine = get_policy_engine()
    risk_scorer = get_risk_scorer()
    
    # Check compliance
    compliance_result = policy_engine.check_transaction(
        sender=event.sender,
        gas_used=event.gas_used,
        payload=event.payload
    )
    
    # Calculate quick risk score
    risk_score = risk_scorer.calculate_risk_score(compliance_result=compliance_result)
    
    # Create alert message
    alert = {
        "type": "transaction_alert",
        "timestamp": datetime.now().isoformat(),
        "transaction_hash": event.hash,
        "sender": event.sender,
        "risk_level": risk_score.level.value,
        "risk_score": risk_score.score,
        "success": event.success,
        "gas_used": event.gas_used,
        "violations": [
            {
                "policy": v.policy_name,
                "severity": v.severity.value,
                "message": v.message
            }
            for v in compliance_result.violations
        ]
    }
    
    # Broadcast if there are violations or high risk
    if not compliance_result.passed or risk_score.score >= 30:
        await manager.broadcast(alert)
    
    # Also broadcast new transaction notification
    tx_notification = {
        "type": "new_transaction",
        "timestamp": datetime.now().isoformat(),
        "transaction_hash": event.hash,
        "sender": event.sender,
        "success": event.success,
        "gas_used": event.gas_used
    }
    await manager.broadcast(tx_notification)


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts.
    
    Clients connect to receive:
    - New transaction notifications
    - Compliance violation alerts
    - High-risk transaction warnings
    """
    await manager.connect(websocket)
    
    # Register transaction callback
    monitor = get_transaction_monitor()
    monitor.add_async_callback(handle_transaction_event)
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to Aptos Compliance Agent",
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        while True:
            # Keep connection alive and handle client messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client commands
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON"
                    })
            
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming client messages."""
    msg_type = message.get("type", "")
    
    if msg_type == "subscribe_address":
        # Subscribe to a specific address
        address = message.get("address", "")
        if address:
            monitor = get_transaction_monitor()
            monitor.add_monitored_address(address)
            await websocket.send_json({
                "type": "subscribed",
                "address": address
            })
    
    elif msg_type == "unsubscribe_address":
        # Unsubscribe from an address
        address = message.get("address", "")
        if address:
            monitor = get_transaction_monitor()
            monitor.remove_monitored_address(address)
            await websocket.send_json({
                "type": "unsubscribed",
                "address": address
            })
    
    elif msg_type == "pong":
        # Client responded to ping
        pass
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
