"""Obsidian AutoLink - Automatically add links to Obsidian vaults using Neo4j GraphRAG."""

from .config import ModelSettings
from .knowledge_graph import ObsidianKnowledgeGraph
from .main import main

__version__ = "0.1.0"
__all__ = ["ModelSettings", "ObsidianKnowledgeGraph", "main"]
