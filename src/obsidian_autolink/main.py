"""Main script for Obsidian AutoLink."""

import os
from pathlib import Path

from .config import ModelSettings
from .knowledge_graph import ObsidianKnowledgeGraph


def main():
    """Main function to create knowledge graph from Obsidian vault."""
    try:
        # Load configuration
        print("Loading configuration...")
        settings = ModelSettings()
        
        # Validate vault path
        vault_path = Path(settings.obsidian_vault_path)
        if not vault_path.exists():
            print(f"Error: Vault path does not exist: {vault_path}")
            return
            
        print(f"Vault path: {vault_path}")
        print(f"Neo4j URI: {settings.neo4j_uri}")
        print(f"OpenAI Model: {settings.openai_model}")
        
        # Create knowledge graph
        kg = ObsidianKnowledgeGraph(settings)
        
        try:
            # Connect to database
            print("Connecting to Neo4j...")
            kg.connect()
            
            # Setup pipeline
            print("Setting up pipeline...")
            kg.setup_pipeline()
            
            # Create knowledge graph
            kg.create_knowledge_graph()
            
            # Get and display statistics
            print("\nKnowledge Graph Statistics:")
            stats = kg.get_graph_stats()
            
            print("Nodes by type:")
            for node_type, count in stats["nodes"].items():
                print(f"  {node_type}: {count}")
                
            print("Relationships by type:")
            for rel_type, count in stats["relationships"].items():
                print(f"  {rel_type}: {count}")
                
        finally:
            # Always disconnect
            kg.disconnect()
            
    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
