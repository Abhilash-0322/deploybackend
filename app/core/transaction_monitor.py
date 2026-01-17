"""
Transaction Monitor

Real-time monitoring of Aptos blockchain transactions.
Polls for new transactions and streams them for analysis.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from collections import deque

from app.config import get_settings
from app.core.aptos_client import get_aptos_client


@dataclass
class TransactionEvent:
    """Represents a monitored transaction event."""
    hash: str
    version: int
    sender: str
    type: str
    timestamp: datetime
    success: bool
    gas_used: int
    payload: dict[str, Any] = field(default_factory=dict)
    changes: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class TransactionMonitor:
    """
    Real-time transaction monitor for Aptos blockchain.
    
    Polls for new transactions and notifies registered callbacks
    when new transactions are detected.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._running = False
        self._callbacks: list[Callable[[TransactionEvent], None]] = []
        self._async_callbacks: list[Callable[[TransactionEvent], Any]] = []
        self._last_version: Optional[int] = None
        self._recent_transactions: deque[TransactionEvent] = deque(maxlen=100)
        self._monitored_addresses: set[str] = set()
        self._task: Optional[asyncio.Task] = None
    
    def add_callback(self, callback: Callable[[TransactionEvent], None]):
        """Add a synchronous callback for new transactions."""
        self._callbacks.append(callback)
    
    def add_async_callback(self, callback: Callable[[TransactionEvent], Any]):
        """Add an async callback for new transactions."""
        self._async_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        if callback in self._async_callbacks:
            self._async_callbacks.remove(callback)
    
    def add_monitored_address(self, address: str):
        """Add an address to monitor specifically."""
        if not address.startswith("0x"):
            address = f"0x{address}"
        self._monitored_addresses.add(address.lower())
    
    def remove_monitored_address(self, address: str):
        """Remove an address from monitoring."""
        if not address.startswith("0x"):
            address = f"0x{address}"
        self._monitored_addresses.discard(address.lower())
    
    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running
    
    @property
    def recent_transactions(self) -> list[TransactionEvent]:
        """Get recent transactions."""
        return list(self._recent_transactions)
    
    async def start(self):
        """Start the transaction monitor."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop the transaction monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        client = await get_aptos_client()
        
        # Get initial ledger version
        try:
            ledger_info = await client.get_ledger_info()
            self._last_version = int(ledger_info.get("ledger_version", 0))
        except Exception as e:
            print(f"Error getting initial ledger info: {e}")
            self._last_version = 0
        
        while self._running:
            try:
                await self._poll_transactions(client)
            except Exception as e:
                print(f"Error polling transactions: {e}")
            
            await asyncio.sleep(self.settings.monitor_poll_interval)
    
    async def _poll_transactions(self, client):
        """Poll for new transactions."""
        try:
            transactions = await client.get_transactions(
                limit=self.settings.max_transactions_per_query,
                start=self._last_version
            )
            
            for tx_data in transactions:
                tx_version = int(tx_data.get("version", 0))
                if tx_version > (self._last_version or 0):
                    self._last_version = tx_version
                    
                    event = self._parse_transaction(tx_data)
                    if event:
                        # Check if we should process this transaction
                        if self._should_process(event):
                            self._recent_transactions.append(event)
                            await self._notify_callbacks(event)
        
        except Exception as e:
            print(f"Error in poll: {e}")
    
    def _parse_transaction(self, tx_data: dict) -> Optional[TransactionEvent]:
        """Parse raw transaction data into TransactionEvent."""
        try:
            # Get timestamp
            timestamp_str = tx_data.get("timestamp", "0")
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str) / 1_000_000)
            except (ValueError, TypeError):
                timestamp = datetime.now()
            
            return TransactionEvent(
                hash=tx_data.get("hash", ""),
                version=int(tx_data.get("version", 0)),
                sender=tx_data.get("sender", ""),
                type=tx_data.get("type", "unknown"),
                timestamp=timestamp,
                success=tx_data.get("success", False),
                gas_used=int(tx_data.get("gas_used", 0)),
                payload=tx_data.get("payload", {}),
                changes=tx_data.get("changes", []),
                raw=tx_data
            )
        except Exception as e:
            print(f"Error parsing transaction: {e}")
            return None
    
    def _should_process(self, event: TransactionEvent) -> bool:
        """Check if transaction should be processed."""
        # If no specific addresses monitored, process all
        if not self._monitored_addresses:
            return True
        
        # Check if sender is in monitored list
        sender = event.sender.lower() if event.sender else ""
        return sender in self._monitored_addresses
    
    async def _notify_callbacks(self, event: TransactionEvent):
        """Notify all registered callbacks."""
        # Sync callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Callback error: {e}")
        
        # Async callbacks
        for callback in self._async_callbacks:
            try:
                await callback(event)
            except Exception as e:
                print(f"Async callback error: {e}")
    
    async def get_address_transactions(
        self,
        address: str,
        limit: int = 25
    ) -> list[TransactionEvent]:
        """Get recent transactions for a specific address."""
        client = await get_aptos_client()
        transactions = await client.get_account_transactions(address, limit=limit)
        
        events = []
        for tx_data in transactions:
            event = self._parse_transaction(tx_data)
            if event:
                events.append(event)
        
        return events


# Singleton instance
_monitor: Optional[TransactionMonitor] = None


def get_transaction_monitor() -> TransactionMonitor:
    """Get or create the transaction monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = TransactionMonitor()
    return _monitor
