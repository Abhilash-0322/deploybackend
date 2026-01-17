"""
Aptos Client Wrapper

Provides a simplified interface for interacting with the Aptos blockchain
using the official Aptos Python SDK.
"""

import httpx
from typing import Any, Optional
from app.config import get_settings


class AptosClient:
    """
    Wrapper around Aptos REST API for blockchain interaction.
    
    Provides methods for:
    - Fetching account resources and modules
    - Retrieving transaction history
    - Getting module metadata and ABIs
    """
    
    def __init__(self, node_url: Optional[str] = None):
        """
        Initialize the Aptos client.
        
        Args:
            node_url: Aptos fullnode URL. Defaults to config setting.
        """
        settings = get_settings()
        self.node_url = node_url or settings.aptos_node_url
        self._client = httpx.AsyncClient(
            base_url=self.node_url,
            timeout=30.0,
            headers={"Content-Type": "application/json"}
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get_account(self, address: str) -> dict[str, Any]:
        """
        Get account information.
        
        Args:
            address: Account address (with or without 0x prefix)
            
        Returns:
            Account data including sequence number and authentication key
        """
        address = self._normalize_address(address)
        response = await self._client.get(f"/accounts/{address}")
        response.raise_for_status()
        return response.json()
    
    async def get_account_resources(self, address: str) -> list[dict[str, Any]]:
        """
        Get all resources for an account.
        
        Args:
            address: Account address
            
        Returns:
            List of account resources
        """
        address = self._normalize_address(address)
        response = await self._client.get(f"/accounts/{address}/resources")
        response.raise_for_status()
        return response.json()
    
    async def get_account_resource(
        self, 
        address: str, 
        resource_type: str
    ) -> dict[str, Any]:
        """
        Get a specific resource for an account.
        
        Args:
            address: Account address
            resource_type: Full resource type (e.g., "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>")
            
        Returns:
            Resource data
        """
        address = self._normalize_address(address)
        response = await self._client.get(
            f"/accounts/{address}/resource/{resource_type}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_account_modules(self, address: str) -> list[dict[str, Any]]:
        """
        Get all modules deployed to an account.
        
        Args:
            address: Account address
            
        Returns:
            List of module metadata including bytecode and ABI
        """
        address = self._normalize_address(address)
        response = await self._client.get(f"/accounts/{address}/modules")
        response.raise_for_status()
        return response.json()
    
    async def get_account_module(
        self, 
        address: str, 
        module_name: str
    ) -> dict[str, Any]:
        """
        Get a specific module from an account.
        
        Args:
            address: Account address
            module_name: Name of the module
            
        Returns:
            Module metadata including bytecode and ABI
        """
        address = self._normalize_address(address)
        response = await self._client.get(
            f"/accounts/{address}/module/{module_name}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_account_transactions(
        self,
        address: str,
        limit: int = 25,
        start: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Get transactions for an account.
        
        Args:
            address: Account address
            limit: Maximum number of transactions to return
            start: Starting sequence number
            
        Returns:
            List of transactions
        """
        address = self._normalize_address(address)
        params = {"limit": limit}
        if start is not None:
            params["start"] = start
        
        response = await self._client.get(
            f"/accounts/{address}/transactions",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_transaction_by_hash(self, txn_hash: str) -> dict[str, Any]:
        """
        Get a transaction by its hash.
        
        Args:
            txn_hash: Transaction hash
            
        Returns:
            Transaction data
        """
        response = await self._client.get(f"/transactions/by_hash/{txn_hash}")
        response.raise_for_status()
        return response.json()
    
    async def get_transactions(
        self,
        limit: int = 25,
        start: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Get recent transactions from the blockchain.
        
        Args:
            limit: Maximum number of transactions
            start: Starting version number
            
        Returns:
            List of transactions
        """
        params = {"limit": limit}
        if start is not None:
            params["start"] = start
        
        response = await self._client.get("/transactions", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_ledger_info(self) -> dict[str, Any]:
        """
        Get current ledger information.
        
        Returns:
            Ledger info including chain ID, epoch, and block height
        """
        response = await self._client.get("/")
        response.raise_for_status()
        return response.json()
    
    async def simulate_transaction(
        self,
        sender: str,
        payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Simulate a transaction without submitting.
        
        Args:
            sender: Sender address
            payload: Transaction payload
            
        Returns:
            Simulation results
        """
        # This requires constructing a proper transaction - simplified for now
        response = await self._client.post(
            "/transactions/simulate",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address format."""
        if not address.startswith("0x"):
            address = f"0x{address}"
        return address


# Singleton instance
_client: Optional[AptosClient] = None


async def get_aptos_client() -> AptosClient:
    """Get or create the global Aptos client instance."""
    global _client
    if _client is None:
        _client = AptosClient()
    return _client
