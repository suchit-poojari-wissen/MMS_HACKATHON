"""
Complete End-to-End GraphRAG Pipeline
- Builds Knowledge Graph from JSONL
- Creates Vector Index
- Queries using RAG
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json

from neo4j_graphrag.llm import AzureOpenAILLM
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
# from neo4j_graphrag.schema import GraphSchema
from neo4j_graphrag.experimental.components.schema import GraphSchema
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    NodeType,
    PropertyType,
    RelationshipType,
)

# ============================================================
# CONFIGURATION
# ============================================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

JSONL_FILE = "chunks copy.jsonl"
INDEX_NAME = "chunk-embeddings"

# ============================================================
# STEP 1: Initialize Neo4j Driver
# ============================================================
def init_driver():
    """Initialize Neo4j database driver"""
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        encrypted=True,
        trust="TRUST_ALL_CERTIFICATES",
        connection_timeout=30,
        max_connection_lifetime=3600
    )
    
    try:
        driver.verify_connectivity()
        print("✓ Neo4j Connection successful!")
        return driver
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        exit()

# ============================================================
# STEP 2: Configure LLM & Embeddings
# ============================================================
def init_llm():
    """Initialize Azure OpenAI LLM"""
    return AzureOpenAILLM(
        model_name=os.getenv("AZURE_LLM_MODEL_NAME", "gpt-5-mini"),
        azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT", "gpt-5-mini"),
        azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
        api_version=os.getenv("AZURE_API_VERSION", "2024-12-01-preview"),
        api_key=os.getenv("AZURE_LLM_API_KEY"),
    )

def init_embeddings():
    """Initialize Azure OpenAI Embeddings"""
    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "embedding"),
        model=os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
        azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
        api_version=os.getenv("AZURE_API_VERSION", "2024-12-01-preview"),
        api_key=os.getenv("AZURE_EMBEDDING_API_KEY"),
    )

# ============================================================
# STEP 3: Define Schema (Sophisticated Knowledge Graph)
# ============================================================
def get_schema():
    """Define schema for knowledge graph - optimized for FAA documentation"""
    
    return GraphSchema(
        node_types=[
            NodeType(
                label="Document",
                properties=[
                    PropertyType(name="title", type="STRING"),
                    PropertyType(name="source", type="STRING"),
                    PropertyType(name="type", type="STRING"),
                ],
            ),
            NodeType(
                label="Chapter",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="number", type="STRING"),
                ],
            ),
            NodeType(
                label="Section",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="number", type="STRING"),
                ],
            ),
            NodeType(
                label="Procedure",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="description", type="STRING"),
                    PropertyType(name="steps", type="STRING"),
                ],
            ),
            NodeType(
                label="Equipment",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="type", type="STRING"),
                    PropertyType(name="description", type="STRING"),
                ],
            ),
            NodeType(
                label="SafetyConcept",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="hazard_level", type="STRING"),
                    PropertyType(name="description", type="STRING"),
                ],
            ),
            NodeType(
                label="Person",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="role", type="STRING"),
                ],
            ),
            NodeType(
                label="Organization",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="type", type="STRING"),
                ],
            ),
            NodeType(
                label="Topic",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="description", type="STRING"),
                ],
            ),
            NodeType(
                label="Concept",
                properties=[
                    PropertyType(name="name", type="STRING"),
                    PropertyType(name="definition", type="STRING"),
                ],
            ),
        ],
        relationship_types=[
            RelationshipType(label="CONTAINS"),
            RelationshipType(label="PARENT_OF"),
            RelationshipType(label="HAS_PROCEDURE"),
            RelationshipType(label="HAS_EQUIPMENT"),
            RelationshipType(label="HAS_SAFETY_CONCERN"),
            RelationshipType(label="REQUIRES"),
            RelationshipType(label="PUBLISHED_BY"),
            RelationshipType(label="CONTRIBUTED_BY"),
            RelationshipType(label="WORKS_FOR"),
            RelationshipType(label="HAS_ROLE"),
            RelationshipType(label="RELATED_TO"),
            RelationshipType(label="MENTIONS"),
            RelationshipType(label="BELONGS_TO"),
            RelationshipType(label="AFFECTS"),
        ],
        patterns=[
            ("Document", "CONTAINS", "Chapter"),
            ("Chapter", "CONTAINS", "Section"),
            ("Section", "HAS_PROCEDURE", "Procedure"),
            ("Procedure", "HAS_EQUIPMENT", "Equipment"),
            ("Procedure", "HAS_SAFETY_CONCERN", "SafetyConcept"),
            ("Procedure", "REQUIRES", "Equipment"),
            ("Document", "PUBLISHED_BY", "Organization"),
            ("Document", "CONTRIBUTED_BY", "Person"),
            ("Person", "WORKS_FOR", "Organization"),
            ("Person", "HAS_ROLE", "Topic"),
            ("Section", "RELATED_TO", "Topic"),
            ("Concept", "RELATED_TO", "Concept"),
            ("Equipment", "BELONGS_TO", "Topic"),
            ("SafetyConcept", "AFFECTS", "Procedure"),
        ],
    )

# ============================================================
# STEP 4: Clear Database
# ============================================================
def clear_database(driver):
    """Clear all nodes from database"""
    print("\nClearing existing graph...")
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            deleted = result.single()["deleted"]
            print(f"✓ Deleted {deleted} nodes")
    except Exception as e:
        print(f"i Clear operation: {str(e)}")

# ============================================================
# STEP 5: Load JSONL Data (Filter & Concatenate)
# ============================================================
def should_process_chunk(chunk_data):
    """Filter criteria: only process chunks that make sense"""
    # Skip header/title sections
    section_type = chunk_data.get("metadata", {}).get("section_type", "").lower()
    if section_type in ["title", "header", "footer", "table_of_contents"]:
        return False
    
    # Skip chunks with very little content
    token_count = chunk_data.get("token_count", 0)
    if token_count < 20:  # Minimum 20 tokens to be meaningful
        return False
    
    # Skip if no content
    content = chunk_data.get("content", "").strip()
    if not content:
        return False
    
    return True

def load_jsonl_data(file_path):
    """Load JSONL data with filtering and concatenate"""
    print(f"\nLoading data from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return None
    
    text_content = ""
    chunk_count = 0
    skipped_count = 0
    total_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        chunk_data = json.loads(line)
                        total_count += 1
                        
                        # Apply filtering
                        if should_process_chunk(chunk_data):
                            content = chunk_data.get("content", "").strip()
                            text_content += content + "\n\n"
                            chunk_count += 1
                        else:
                            skipped_count += 1
                    
                    except json.JSONDecodeError:
                        skipped_count += 1
                        continue
        
        print(f"✓ Loaded {chunk_count} valid chunks (skipped {skipped_count} from {total_count} total)")
        print(f"✓ Total text: {len(text_content)} characters")
        return text_content if text_content else None
    
    except Exception as e:
        print(f"✗ Error loading file: {str(e)}")
        return None

# ============================================================
# STEP 6: Build Knowledge Graph
# ============================================================
async def build_knowledge_graph(driver, llm, embedder, text_content):
    """Build KG from text using SimpleKGPipeline"""
    
    print("\n" + "="*60)
    print("BUILDING KNOWLEDGE GRAPH")
    print("="*60)
    
    kg_builder = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        embedder=embedder,
        schema=get_schema(),
        from_pdf=False,
        on_error="IGNORE",
        perform_entity_resolution=True,
    )
    
    try:
        result = await kg_builder.run_async(
            text=text_content,
            document_metadata={
                "source": JSONL_FILE,
                "type": "jsonl_document",
                "processed": "yes"
            }
        )
        
        print(f"\n✓ Knowledge Graph Built Successfully!")
        return result
    
    except Exception as e:
        print(f"✗ KG Building failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================
# STEP 7: Create Vector Index
# ============================================================
def create_vector_index(driver, index_name):
    """Create vector index for semantic search"""
    print("\n" + "="*60)
    print("CREATING VECTOR INDEX")
    print("="*60)
    
    with driver.session() as session:
        try:
            session.run(f"""
                CREATE VECTOR INDEX `{index_name}` 
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """)
            print(f"✓ Vector index '{index_name}' created")
        except Exception as e:
            if "already exists" in str(e):
                print(f"ℹ Index '{index_name}' already exists")
            else:
                print(f"⚠ Index creation: {str(e)}")

# ============================================================
# STEP 8: View Graph Statistics
# ============================================================
def show_graph_stats(driver):
    """Display knowledge graph statistics"""
    print("\n" + "="*60)
    print("KNOWLEDGE GRAPH STATISTICS")
    print("="*60)
    
    with driver.session() as session:
        # Node counts
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        print("\nNode Types:")
        for record in result:
            labels = record["labels"]
            count = record["count"]
            label_str = ":".join(labels) if labels else "unlabeled"
            print(f"  {label_str}: {count}")
        
        # Relationship counts
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
        print("\nRelationship Types:")
        for record in result:
            rel_type = record["type"]
            count = record["count"]
            print(f"  {rel_type}: {count}")

# ============================================================
# MAIN EXECUTION
# ============================================================
async def main():
    """Execute complete GraphRAG pipeline"""
    
    print("\n" + "="*60)
    print("GRAPHRAG KNOWLEDGE GRAPH BUILDER")
    print("="*60)
    
    # Initialize components
    driver = init_driver()
    llm = init_llm()
    embedder = init_embeddings()
    
    # Load data (with filtering, concatenated)
    text_content = load_jsonl_data(JSONL_FILE)
    if not text_content:
        print("✗ Failed to load data")
        driver.close()
        return
    
    # Clear database
    clear_database(driver)
    
    print("\n✓ Data loaded successfully.")
    
    # Build KG
    result = await build_knowledge_graph(driver, llm, embedder, text_content)
    if not result:
        driver.close()
        return
    
    # Show statistics
    show_graph_stats(driver)
    
    # Create vector index
    create_vector_index(driver, INDEX_NAME)
    
    print("\n" + "="*60)
    print("✓ KNOWLEDGE GRAPH BUILT SUCCESSFULLY!")
    print("Use rag_query.py to query the graph")
    print("="*60)
    
    driver.close()

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    asyncio.run(main())
