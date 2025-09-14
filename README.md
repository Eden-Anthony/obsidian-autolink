# Obsidian AutoLink

Automatically add links to Obsidian vaults using Neo4j GraphRAG.

## Overview

This project helps you automatically add links to your Obsidian vault by creating a knowledge graph of your notes and using it to suggest relevant connections between them.

## Features

- **Knowledge Graph Creation**: Uses Neo4j GraphRAG to create a knowledge graph from your Obsidian vault
- **Batch Processing**: Processes files in configurable batches for better performance and memory usage
- **Entity Recognition**: Identifies entities like Person, Book, Topic, Organisation, Article, and Paper
- **Relationship Mapping**: Discovers relationships between entities and notes
- **Automatic Linking**: Suggests and adds `[[links]]` to connect related notes
- **Configurable Parameters**: Adjustable batch size for optimal performance

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your configuration:
   ```env
   # Neo4j Configuration
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=password
   NEO4J_DATABASE=neo4j
   AURA_INSTANCEID=your_aura_instance_id
   AURA_INSTANCENAME=your_aura_instance_name

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o-mini

   # Obsidian Configuration
   OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
   ```

3. Run the knowledge graph creation:
   ```bash
   uv run obsidian-autolink
   ```

   Or with custom batch size:
   ```bash
   uv run obsidian-autolink --batch-size 20
   ```

## Usage

The project is designed to be run step by step:

1. **Knowledge Graph Creation** (current step): Creates a knowledge graph from your vault
2. **Link Generation**: Uses the knowledge graph to suggest links between notes
3. **Note Updates**: Automatically updates notes with the suggested links

## Project Structure

- `src/obsidian_autolink/config.py`: Configuration management using Pydantic
- `src/obsidian_autolink/knowledge_graph.py`: Knowledge graph creation using Neo4j GraphRAG
- `src/obsidian_autolink/main.py`: Main script to run the knowledge graph creation

## Requirements

- Python 3.12+
- Neo4j database (local or Aura)
- OpenAI API key
- Obsidian vault with markdown files
