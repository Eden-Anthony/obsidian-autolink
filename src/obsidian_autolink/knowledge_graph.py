"""Knowledge graph creation module for Obsidian AutoLink."""

import os
from pathlib import Path
from typing import List, Dict, Any

from neo4j import GraphDatabase
from neo4j_graphrag.pipelines import SimpleKGPipeline
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings

from .config import ModelSettings


class ObsidianKnowledgeGraph:
    """Creates and manages a knowledge graph from Obsidian vault content."""
    
    def __init__(self, settings: ModelSettings):
        """Initialize the knowledge graph with configuration settings."""
        self.settings = settings
        self.driver = None
        self.pipeline = None
        
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
            raise RuntimeError("Database connection not established. Call connect() first.")
            
        # Initialize OpenAI LLM
        llm = OpenAILLM(
            model_name=self.settings.openai_model,
            # model_params={"temperature": 0}
        )
        
        # Initialize OpenAI embeddings
        embeddings = OpenAIEmbeddings(model=self.settings.openai_embedding_model)
        
        # Create the SimpleKGPipeline
        self.pipeline = SimpleKGPipeline(
            driver=self.driver,
            llm=llm,
            embeddings=embeddings,
            entity_types=["Person", "Book", "Topic", "Organisation", "Article", "Paper"],
            relationship_types=["MENTIONS", "RELATES_TO", "WRITTEN_BY", "ABOUT", "PART_OF"]
        )
        
    def read_vault_files(self) -> List[Dict[str, Any]]:
        """Read all markdown files from the Obsidian vault."""
        vault_path = Path(self.settings.obsidian_vault_path)
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {vault_path}")
            
        markdown_files = []
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
                print(f"Warning: Could not read file {file_path}: {e}")
                continue
                
        return markdown_files
        
    def create_knowledge_graph(self) -> None:
        """Create the knowledge graph from Obsidian vault content."""
        if not self.pipeline:
            raise RuntimeError("Pipeline not set up. Call setup_pipeline() first.")
            
        print("Reading vault files...")
        vault_files = self.read_vault_files()
        print(f"Found {len(vault_files)} markdown files")
        
        if not vault_files:
            print("No markdown files found in the vault.")
            return
            
        print("Creating knowledge graph...")
        try:
            # Process each file through the pipeline
            for i, file_data in enumerate(vault_files, 1):
                print(f"Processing file {i}/{len(vault_files)}: {file_data['title']}")
                
                # Create a document for the pipeline
                document = {
                    "text": file_data["content"],
                    "metadata": {
                        "title": file_data["title"],
                        "file_path": file_data["file_path"],
                        "relative_path": file_data["relative_path"]
                    }
                }
                
                # Process the document
                self.pipeline.run([document])
                
            print("Knowledge graph creation completed!")
            
        except Exception as e:
            print(f"Error creating knowledge graph: {e}")
            raise
            
    def get_graph_stats(self) -> Dict[str, int]:
        """Get statistics about the created knowledge graph."""
        if not self.driver:
            raise RuntimeError("Database connection not established.")
            
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
            for record in result:
                labels = record["labels"]
                if labels:
                    label = labels[0]  # Take the first label
                    node_counts[label] = record["count"]
                    
            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
            rel_counts = {}
            for record in rel_result:
                rel_counts[record["rel_type"]] = record["count"]
                
        return {
            "nodes": node_counts,
            "relationships": rel_counts
        }
