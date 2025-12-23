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
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG
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

JSONL_FILE = "chunks.jsonl"
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
# STEP 5: Load JSONL Data
# ============================================================
def load_jsonl_data(file_path):
    """Load and concatenate JSONL data"""
    print(f"\nLoading data from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return None
    
    text_content = ""
    chunk_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        # Extract text from your JSONL structure
                        # Adjust keys based on your actual format
                        if isinstance(chunk, dict):
                            text = chunk.get('text', chunk.get('content', chunk.get('chunk', str(chunk))))
                        else:
                            text = str(chunk)
                        
                        text_content += text + "\n\n"
                        chunk_count += 1
                    except json.JSONDecodeError:
                        print(f"⚠ Skipping invalid JSON line")
                        continue
        
        print(f"✓ Loaded {chunk_count} chunks ({len(text_content)} characters)")
        return text_content
    
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
        schema=get_schema(),  # ✓ Sophisticated schema
        from_pdf=False,  # ✓ Using text (not PDF)
        on_error="IGNORE",  # Skip problematic chunks
        perform_entity_resolution=True,  # ✓ Merge duplicate entities
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
        print(f"  Result: {result.result}")
        return result
    
    except Exception as e:
        print(f"✗ KG Building failed: {str(e)}")
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
# STEP 8: Setup RAG Pipeline
# ============================================================
def setup_rag_pipeline(driver, embedder, llm, index_name):
    """Setup RAG for querying"""
    print("\n" + "="*60)
    print("SETTING UP RAG PIPELINE")
    print("="*60)
    
    retriever = VectorRetriever(
        driver=driver,
        index_name=index_name,
        embedder=embedder,
        return_properties=["text", "source"]
    )
    
    rag = GraphRAG(retriever=retriever, llm=llm)
    print("✓ RAG Pipeline initialized")
    return rag

# ============================================================
# STEP 9: Query Knowledge Graph
# ============================================================
async def query_knowledge_graph(rag):
    """Query the RAG pipeline"""
    
    print("\n" + "="*60)
    print("QUERYING KNOWLEDGE GRAPH")
    print("="*60)
    
    # Example queries
    queries = [
        "What are the main topics discussed?",
        "Who are the key people mentioned?",
        "What organizations are referenced?",
        "What events or activities are described?",
    ]
    
    for query in queries:
        print(f"\nQ: {query}")
        print("-" * 60)
        try:
            response = rag.search(
                query_text=query,
                retriever_config={"top_k": 3}
            )
            print(f"A: {response.answer}")
        except Exception as e:
            print(f"✗ Query error: {str(e)}")

# ============================================================
# STEP 10: View Graph Statistics
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
    print("GRAPHRAG COMPLETE PIPELINE")
    print("="*60)
    
    # Initialize components
    driver = init_driver()
    llm = init_llm()
    embedder = init_embeddings()
    
    # Load data
    text_content = load_jsonl_data(JSONL_FILE)
    if not text_content:
        print("✗ Failed to load data")
        driver.close()
        return
    
    # Clear database
    clear_database(driver)
    
    print("\n✓ Basic setup working! Data loaded successfully.")
    print("✓ Ready to build knowledge graph.")
    
    # Build KG
    # result = await build_knowledge_graph(driver, llm, embedder, text_content)
    # if not result:
    #     driver.close()
    #     return
    
    # # Show statistics
    # show_graph_stats(driver)
    
    # # Create vector index
    # create_vector_index(driver, INDEX_NAME)
    
    # # Setup RAG
    # rag = setup_rag_pipeline(driver, embedder, llm, INDEX_NAME)
    
    # # Query
    # await query_knowledge_graph(rag)
    
    print("\n" + "="*60)
    print("✓ BASIC PIPELINE TEST PASSED!")
    print("="*60)
    
    driver.close()

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    asyncio.run(main())
