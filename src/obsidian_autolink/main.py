"""Main script for Obsidian AutoLink."""

import os
import argparse
from pathlib import Path

from .config import ModelSettings
from .knowledge_graph import ObsidianKnowledgeGraph


def main():
    """Main function to create knowledge graph from Obsidian vault."""
    parser = argparse.ArgumentParser(description="Create knowledge graph from Obsidian vault")
    parser.add_argument("--batch-size", type=int, default=20, 
                       help="Number of files per batch (default: 20)")
    
    args = parser.parse_args()
    
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
        print(f"OpenAI Embedding Model: {settings.openai_embedding_model}")
        print(f"Batch Size: {args.batch_size}")
        
        # Create knowledge graph
        kg = ObsidianKnowledgeGraph(settings)
        
        try:
            # Connect to database
            print("Connecting to Neo4j...")
            kg.connect()
            
            # Setup pipeline
            print("Setting up pipeline...")
            kg.setup_pipeline()
            
            # Create knowledge graph with batch processing
            kg.create_knowledge_graph(batch_size=args.batch_size)
            
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
