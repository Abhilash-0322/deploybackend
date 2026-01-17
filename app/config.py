"""
Configuration settings for the AI Compliance Agent.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Aptos Network
    aptos_node_url: str = Field(
        default="https://fullnode.testnet.aptoslabs.com/v1",
        description="Aptos fullnode API URL"
    )
    aptos_network: str = Field(
        default="testnet",
        description="Aptos network (testnet, mainnet, devnet)"
    )
    
    # Groq (for AI analysis)
    groq_api_key: str = Field(
        default="",
        description="Groq API key for AI analysis"
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use (llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.)"
    )
    
    # MongoDB
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL"
    )
    mongodb_db_name: str = Field(
        default="aptos_compliance",
        description="MongoDB database name"
    )
    
    # On-Demand.io AI Agents API
    ondemand_api_key: str = Field(
        default="",
        description="On-Demand.io API key for AI agents"
    )
    ondemand_api_url: str = Field(
        default="https://api.on-demand.io/chat/v1",
        description="On-Demand.io Chat API base URL"
    )
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True)
    cors_origins: str = Field(
        default="http://localhost:3000,https://chainsentinel-fohdkm7jx-abhilash-maruyas-projects.vercel.app,https://chainsentinel.vercel.app,https://chainsentinel-ai.onrender.com",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # Compliance Thresholds
    max_transaction_value: int = Field(
        default=1000000000000,  # 10,000 APT in octas
        description="Maximum allowed transaction value"
    )
    risk_threshold_high: int = Field(default=70)
    risk_threshold_critical: int = Field(default=90)
    
    # Monitoring
    monitor_poll_interval: int = Field(
        default=5,
        description="Transaction polling interval in seconds"
    )
    max_transactions_per_query: int = Field(default=25)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
