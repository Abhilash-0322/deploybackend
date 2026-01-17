"""
Smart Contract Parser

Fetches and parses Move module metadata from the Aptos blockchain.
Extracts function signatures, entry points, and module structure for analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

from app.core.aptos_client import get_aptos_client


class FunctionVisibility(str, Enum):
    """Move function visibility levels."""
    PRIVATE = "private"
    PUBLIC = "public"
    FRIEND = "friend"
    ENTRY = "entry"


@dataclass
class FunctionSignature:
    """Represents a Move function signature."""
    name: str
    visibility: FunctionVisibility
    is_entry: bool
    generic_type_params: list[dict[str, Any]] = field(default_factory=list)
    params: list[str] = field(default_factory=list)
    return_types: list[str] = field(default_factory=list)


@dataclass
class StructDefinition:
    """Represents a Move struct definition."""
    name: str
    is_native: bool
    abilities: list[str] = field(default_factory=list)
    generic_type_params: list[dict[str, Any]] = field(default_factory=list)
    fields: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Parsed information about a Move module."""
    address: str
    name: str
    friends: list[str] = field(default_factory=list)
    functions: list[FunctionSignature] = field(default_factory=list)
    structs: list[StructDefinition] = field(default_factory=list)
    exposed_functions: list[str] = field(default_factory=list)
    bytecode: Optional[str] = None


class ContractParser:
    """
    Parser for Move smart contracts on Aptos.
    
    Extracts module structure, function signatures, and metadata
    from deployed contracts for security analysis.
    """
    
    async def get_module_info(
        self,
        address: str,
        module_name: str
    ) -> ModuleInfo:
        """
        Get parsed information about a specific module.
        
        Args:
            address: Account address where module is deployed
            module_name: Name of the module
            
        Returns:
            Parsed module information
        """
        client = await get_aptos_client()
        module_data = await client.get_account_module(address, module_name)
        return self._parse_module(address, module_data)
    
    async def get_all_modules(self, address: str) -> list[ModuleInfo]:
        """
        Get information about all modules deployed to an address.
        
        Args:
            address: Account address
            
        Returns:
            List of parsed module information
        """
        client = await get_aptos_client()
        modules_data = await client.get_account_modules(address)
        return [self._parse_module(address, m) for m in modules_data]
    
    async def get_module_names(self, address: str) -> list[str]:
        """
        Get names of all modules deployed to an address.
        
        Args:
            address: Account address
            
        Returns:
            List of module names
        """
        client = await get_aptos_client()
        modules_data = await client.get_account_modules(address)
        return [self._extract_module_name(m) for m in modules_data]
    
    def _parse_module(self, address: str, module_data: dict) -> ModuleInfo:
        """Parse raw module data into ModuleInfo."""
        abi = module_data.get("abi", {})
        
        module_name = abi.get("name", "unknown")
        
        # Parse functions
        functions = []
        exposed_functions = []
        for func in abi.get("exposed_functions", []):
            func_sig = self._parse_function(func)
            functions.append(func_sig)
            if func_sig.is_entry or func_sig.visibility == FunctionVisibility.PUBLIC:
                exposed_functions.append(func_sig.name)
        
        # Parse structs
        structs = []
        for struct in abi.get("structs", []):
            structs.append(self._parse_struct(struct))
        
        # Get friends
        friends = abi.get("friends", [])
        
        return ModuleInfo(
            address=address,
            name=module_name,
            friends=friends,
            functions=functions,
            structs=structs,
            exposed_functions=exposed_functions,
            bytecode=module_data.get("bytecode")
        )
    
    def _parse_function(self, func_data: dict) -> FunctionSignature:
        """Parse a function from ABI data."""
        visibility_str = func_data.get("visibility", "private")
        visibility = FunctionVisibility(visibility_str)
        
        return FunctionSignature(
            name=func_data.get("name", ""),
            visibility=visibility,
            is_entry=func_data.get("is_entry", False),
            generic_type_params=func_data.get("generic_type_params", []),
            params=func_data.get("params", []),
            return_types=func_data.get("return", [])
        )
    
    def _parse_struct(self, struct_data: dict) -> StructDefinition:
        """Parse a struct from ABI data."""
        return StructDefinition(
            name=struct_data.get("name", ""),
            is_native=struct_data.get("is_native", False),
            abilities=struct_data.get("abilities", []),
            generic_type_params=struct_data.get("generic_type_params", []),
            fields=struct_data.get("fields", [])
        )
    
    def _extract_module_name(self, module_data: dict) -> str:
        """Extract module name from raw data."""
        abi = module_data.get("abi", {})
        return abi.get("name", "unknown")
    
    def analyze_access_patterns(self, module: ModuleInfo) -> dict[str, Any]:
        """
        Analyze access control patterns in a module.
        
        Returns:
            Analysis results including potential issues
        """
        analysis = {
            "total_functions": len(module.functions),
            "entry_functions": 0,
            "public_functions": 0,
            "friend_functions": 0,
            "has_signer_params": [],
            "potential_issues": []
        }
        
        for func in module.functions:
            if func.is_entry:
                analysis["entry_functions"] += 1
            if func.visibility == FunctionVisibility.PUBLIC:
                analysis["public_functions"] += 1
            if func.visibility == FunctionVisibility.FRIEND:
                analysis["friend_functions"] += 1
            
            # Check for signer parameters (access control)
            has_signer = any("signer" in param.lower() for param in func.params)
            if has_signer:
                analysis["has_signer_params"].append(func.name)
            
            # Flag entry functions without signer (potential issue)
            if func.is_entry and not has_signer:
                analysis["potential_issues"].append({
                    "function": func.name,
                    "issue": "Entry function without signer parameter",
                    "severity": "medium"
                })
        
        # Check for excessive friends
        if len(module.friends) > 5:
            analysis["potential_issues"].append({
                "issue": f"Large number of friend modules ({len(module.friends)})",
                "severity": "low"
            })
        
        return analysis


# Singleton instance
_parser: Optional[ContractParser] = None


def get_contract_parser() -> ContractParser:
    """Get or create the contract parser instance."""
    global _parser
    if _parser is None:
        _parser = ContractParser()
    return _parser
