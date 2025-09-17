"""Knowledge graph creation module for Obsidian AutoLink."""

import os
import asyncio
from pathlib import Path
from itertools import batched
from rich.progress import Progress
from rich.console import Console
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j import GraphDatabase
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from typing import TypedDict, List, Dict, Any
from .config import ModelSettings


class VaultFile(TypedDict):
    file_path: str
    title: str
    content: str
    relative_path: str


class ObsidianKnowledgeGraph:
    """Creates and manages a knowledge graph from Obsidian vault content."""

    def __init__(self, settings: ModelSettings):
        """Initialize the knowledge graph with configuration settings."""
        self.settings = settings
        self.driver: GraphDatabase.driver | None = None
        self.pipeline: SimpleKGPipeline | None = None
        self.console = Console()

    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        self.driver = GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_username, self.settings.neo4j_password)
        )

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def setup_pipeline(self) -> None:
        """Set up the SimpleKGPipeline with OpenAI models."""
        if not self.driver:
            raise RuntimeError(
                "Database connection not established. Call connect() first.")

        # Initialize OpenAI LLM
        llm = OpenAILLM(
            model_name=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            # model_params={"temperature": 0}
        )

        # Initialize OpenAI embeddings
        embedder = OpenAIEmbeddings(
            model=self.settings.openai_embedding_model,
            api_key=self.settings.openai_api_key,
        )

        # Create the SimpleKGPipeline
        self.pipeline = SimpleKGPipeline(
            driver=self.driver,
            llm=llm,
            embedder=embedder,
            from_pdf=False,  # We're processing text, not PDFs
            entities=["Person", "Book", "Topic", "Meeting", "Event", "Location",
                      "Organisation", "Article", "Paper", "Note"],
            relations=["MENTIONS", "RELATES_TO", "WRITTEN_BY",
                       "ABOUT", "PART_OF", "EXTRACTED_FROM", "APPEARS_IN"],
        )

    def read_vault_files(self) -> list[VaultFile]:
        """Read all markdown files from the Obsidian vault."""
        vault_path = Path(self.settings.obsidian_vault_path)
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

        markdown_files: list[VaultFile] = []
        for file_path in vault_path.rglob("*.md"):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in file_path.parts):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract title from filename or first heading
                title = file_path.stem
                if content.startswith('# '):
                    first_line = content.split('\n')[0]
                    title = first_line[2:].strip()

                markdown_files.append({
                    "file_path": str(file_path),
                    "title": title,
                    "content": content,
                    "relative_path": str(file_path.relative_to(vault_path))
                })

            except Exception as e:
                self.console.print(
                    f"Warning: Could not read file {file_path}: {e}")
                continue

        return markdown_files

    def create_knowledge_graph(self, batch_size: int = 10) -> None:
        """Create the knowledge graph from Obsidian vault content with batch processing."""
        if not self.pipeline:
            raise RuntimeError(
                "Pipeline not set up. Call setup_pipeline() first.")

        self.console.print("Reading vault files...")
        vault_files = self.read_vault_files()
        self.console.print(f"Found {len(vault_files)} markdown files")

        if not vault_files:
            self.console.print("No markdown files found in the vault.")
            return

        self.console.print(
            f"Creating knowledge graph with batch size {batch_size}...")
        try:
            # Process files in batches using asyncio
            asyncio.run(self._process_files_in_batches_async(
                vault_files, batch_size))
            self.console.print("Knowledge graph creation completed!")

        except Exception as e:
            self.console.print(f"Error creating knowledge graph: {e}")
            raise

    async def _process_files_in_batches_async(self, vault_files: list[VaultFile], batch_size: int) -> None:
        """Process files in batches using async pipeline with concurrent processing."""
        # Create batches of files using itertools.batched
        file_batches = list(batched(vault_files, batch_size))

        self.console.print(f"Processing {len(file_batches)} batches...")
        with Progress() as progress:
            task_id = progress.add_task(
                "Processing batches", total=len(file_batches))
            for file_batch in file_batches:
                # Process all files in the batch concurrently
                await self._process_batch_concurrently(file_batch)
                progress.advance(task_id)

    async def _process_batch_concurrently(self, file_batch: list[VaultFile]) -> None:
        """Process all files in a batch concurrently using asyncio.gather."""
        # Create async tasks for each file
        tasks = []
        for file_data in file_batch:
            task = self._process_single_file(file_data)
            tasks.append(task)

        # Process all files concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.console.print(
                    f"Error processing file {file_batch[i]['title']}: {result}")

    async def _process_single_file(self, file_data: VaultFile) -> None:
        """Process a single file through the async pipeline."""
        try:
            # First, create a Note node for this file
            await self._create_note_node(file_data)

            # Then process the content for entities
            result = await self.pipeline.run_async(text=file_data["title"] + "\n" + file_data["content"])

            # Link any extracted entities to this note
            await self._link_entities_to_note(file_data["title"])

            return result
        except Exception as e:
            raise Exception(f"Error processing {file_data['title']}: {e}")

    def get_graph_stats(self) -> dict[str, int]:
        """Get statistics about the created knowledge graph."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")

        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            result = session.run(
                "MATCH (n) RETURN labels(n) as labels, count(n) as count")
            for record in result:
                labels = record["labels"]
                if labels:
                    label = labels[0]  # Take the first label
                    node_counts[label] = record["count"]

            # Count relationships
            rel_result = session.run(
                "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
            rel_counts = {}
            for record in rel_result:
                rel_counts[record["rel_type"]] = record["count"]

        return {
            "nodes": node_counts,
            "relationships": rel_counts
        }

    async def _create_note_node(self, file_data: VaultFile) -> None:
        """Create a Note node for the given file."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")

        with self.driver.session() as session:
            # Create or update the Note node
            query = """
            MERGE (n:Note {title: $title})
            SET n.file_path = $file_path,
                n.relative_path = $relative_path,
                n.content_preview = $content_preview,
                n.created_date = datetime()
            RETURN n
            """

            content_preview = file_data["content"][:500] + "..." if len(
                file_data["content"]) > 500 else file_data["content"]

            session.run(query, {
                "title": file_data["title"],
                "file_path": file_data["file_path"],
                "relative_path": file_data["relative_path"],
                "content_preview": content_preview
            })

    async def _link_entities_to_note(self, note_title: str) -> None:
        """Link all entities extracted in the current session to the note."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")

        with self.driver.session() as session:
            # Find the note
            note_query = "MATCH (n:Note {title: $title}) RETURN n"
            note_result = session.run(note_query, {"title": note_title})
            note_record = note_result.single()

            if not note_record:
                self.console.print(
                    f"Warning: Note '{note_title}' not found for linking")
                return

            # Link all non-Note entities to this note
            link_query = """
            MATCH (n:Note {title: $title})
            MATCH (e) 
            WHERE e <> n AND NOT e:Note
            MERGE (e)-[:EXTRACTED_FROM]->(n)
            MERGE (n)-[:APPEARS_IN]->(e)
            """

            session.run(link_query, {"title": note_title})

    def get_entities_in_note(self, note_title: str) -> List[Dict[str, Any]]:
        """Get all entities that appear in a specific note."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")

        with self.driver.session() as session:
            query = """
            MATCH (n:Note {title: $title})-[:APPEARS_IN]->(e)
            RETURN e, labels(e) as entity_types
            """

            result = session.run(query, {"title": note_title})
            entities = []

            for record in result:
                entity = dict(record["e"])
                entity["types"] = record["entity_types"]
                entities.append(entity)

            return entities

    def get_notes_with_entity(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all notes that contain a specific entity."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")

        with self.driver.session() as session:
            query = """
            MATCH (e)-[:EXTRACTED_FROM]->(n:Note)
            WHERE e.name CONTAINS $entity_name OR e.title CONTAINS $entity_name
            RETURN n, labels(e) as entity_types
            """

            result = session.run(query, {"entity_name": entity_name})
            notes = []

            for record in result:
                note = dict(record["n"])
                note["entity_types"] = record["entity_types"]
                notes.append(note)

            return notes
