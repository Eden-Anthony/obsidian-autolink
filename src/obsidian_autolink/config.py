from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelSettings(BaseSettings):
    """Configuration settings for the Obsidian AutoLink application."""
    
    # Neo4j configuration
    neo4j_uri: str = Field(..., description="Neo4j database URI")
    neo4j_username: str = Field(..., description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field(..., description="Neo4j database name")
    aura_instance_id: str = Field(..., description="Neo4j Aura instance ID")
    aura_instance_name: str = Field(..., description="Neo4j Aura instance name")
    
    # OpenAI configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-5-mini", description="OpenAI model to use")
    openai_embedding_model: str = Field(default="text-embedding-3-large", description="OpenAI embedding model to use")
    
    # Obsidian configuration
    obsidian_vault_path: str = Field(..., description="Path to the Obsidian vault")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
