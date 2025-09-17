#!/usr/bin/env python3
"""Test script to demonstrate note-entity linking functionality."""

import asyncio
from src.obsidian_autolink.config import ModelSettings
from src.obsidian_autolink.knowledge_graph import ObsidianKnowledgeGraph


async def test_note_linking():
    """Test the note-entity linking functionality."""
    # Load configuration
    settings = ModelSettings()

    # Create knowledge graph
    kg = ObsidianKnowledgeGraph(settings)

    try:
        # Connect to database
        print("Connecting to Neo4j...")
        kg.connect()

        # Setup pipeline
        print("Setting up pipeline...")
        kg.setup_pipeline()

        # Test with a small batch
        print("Processing a small batch of files...")
        kg.create_knowledge_graph(batch_size=5)

        # Test querying entities in notes
        print("\n=== Testing Note-Entity Queries ===")

        # Get all notes
        with kg.driver.session() as session:
            notes_result = session.run(
                "MATCH (n:Note) RETURN n.title as title LIMIT 3")
            notes = [record["title"] for record in notes_result]

        for note_title in notes:
            print(f"\nEntities in note '{note_title}':")
            entities = kg.get_entities_in_note(note_title)
            for entity in entities[:3]:  # Show first 3 entities
                print(
                    f"  - {entity.get('name', 'Unknown')} ({entity.get('types', [])})")

        # Test finding notes with specific entities
        print(f"\nNotes containing 'AI' or 'machine learning':")
        ai_notes = kg.get_notes_with_entity("AI")
        for note in ai_notes[:3]:  # Show first 3 notes
            print(f"  - {note.get('title', 'Unknown')}")

        # Show graph statistics
        print("\n=== Graph Statistics ===")
        stats = kg.get_graph_stats()
        print("Nodes by type:")
        for node_type, count in stats["nodes"].items():
            print(f"  {node_type}: {count}")
        print("Relationships by type:")
        for rel_type, count in stats["relationships"].items():
            print(f"  {rel_type}: {count}")

    finally:
        kg.disconnect()


if __name__ == "__main__":
    asyncio.run(test_note_linking())
