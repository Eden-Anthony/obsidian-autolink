#!/usr/bin/env python3
"""Utility script to clear all entities and relationships from the knowledge graph."""

from obsidian_autolink.knowledge_graph import ObsidianKnowledgeGraph
from obsidian_autolink.config import ModelSettings
import sys
from pathlib import Path

# Add the src directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))


def clear_knowledge_graph():
    """Clear all entities and relationships from the knowledge graph."""
    try:
        # Load configuration from environment variables and .env file
        print("Loading configuration...")
        settings = ModelSettings()

        print(f"Neo4j URI: {settings.neo4j_uri}")
        print(f"Neo4j Database: {settings.neo4j_database}")

        # Create knowledge graph instance
        kg = ObsidianKnowledgeGraph(settings)

        try:
            # Connect to database
            print("Connecting to Neo4j...")
            kg.connect()

            # Get current statistics before clearing
            print("\nCurrent Knowledge Graph Statistics:")
            stats = kg.get_graph_stats()

            total_nodes = sum(stats["nodes"].values())
            total_relationships = sum(stats["relationships"].values())

            print(f"Total nodes: {total_nodes}")
            print(f"Total relationships: {total_relationships}")

            if total_nodes == 0 and total_relationships == 0:
                print("Knowledge graph is already empty.")
                return

            # Confirm deletion
            print(
                f"\n⚠️  WARNING: This will delete ALL {total_nodes} nodes and {total_relationships} relationships!")
            confirmation = input(
                "Are you sure you want to proceed? Type 'yes' to confirm: ")

            if confirmation.lower() != 'yes':
                print("Operation cancelled.")
                return

            # Clear the knowledge graph
            print("\nClearing knowledge graph...")
            with kg.driver.session() as session:
                # Delete all relationships first (to avoid constraint violations)
                print("Deleting relationships...")
                result = session.run("MATCH ()-[r]->() DELETE r")
                relationships_deleted = result.consume().counters.relationships_deleted

                # Delete all nodes
                print("Deleting nodes...")
                result = session.run("MATCH (n) DELETE n")
                nodes_deleted = result.consume().counters.nodes_deleted

                print(
                    f"✅ Deleted {nodes_deleted} nodes and {relationships_deleted} relationships")

            # Verify the graph is empty
            print("\nVerifying knowledge graph is empty...")
            final_stats = kg.get_graph_stats()
            final_nodes = sum(final_stats["nodes"].values())
            final_relationships = sum(final_stats["relationships"].values())

            if final_nodes == 0 and final_relationships == 0:
                print("✅ Knowledge graph successfully cleared!")
            else:
                print(
                    f"⚠️  Warning: Some data may remain ({final_nodes} nodes, {final_relationships} relationships)")

        finally:
            # Always disconnect
            kg.disconnect()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    clear_knowledge_graph()
