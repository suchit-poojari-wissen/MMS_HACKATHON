"""
RAG Query Interface
- Connects to existing Neo4j Knowledge Graph
- Takes a question as input
- Returns answers using GraphRAG
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

import sys

from neo4j_graphrag.llm import AzureOpenAILLM
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG

# ============================================================
# CONFIGURATION
# ============================================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

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
        return None

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
# STEP 3: Check if Knowledge Graph exists
# ============================================================
def check_kg_exists(driver):
    """Verify that the knowledge graph has been built"""
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
            count = result.single()["count"]
            
            if count == 0:
                print("⚠ Knowledge graph is empty!")
                print("  Please run graphrag_pipeline.py first to build the graph.")
                return False
            
            print(f"✓ Knowledge graph found ({count} nodes)")
            return True
    except Exception as e:
        print(f"✗ Error checking graph: {str(e)}")
        return False

# ============================================================
# STEP 4: Setup RAG Pipeline
# ============================================================
def setup_rag_pipeline(driver, embedder, llm):
    """Setup RAG for querying"""
    try:
        retriever = VectorRetriever(
            driver=driver,
            index_name=INDEX_NAME,
            embedder=embedder,
            return_properties=["text", "source", "chunk_id"]
        )
        
        rag = GraphRAG(retriever=retriever, llm=llm)
        print("✓ RAG Pipeline initialized")
        return rag
    except Exception as e:
        print(f"✗ Failed to setup RAG: {str(e)}")
        return None

# ============================================================
# STEP 5: Query Knowledge Graph
# ============================================================
def query_kg(rag, question):
    """Query the knowledge graph with a single question"""
    
    print("\n" + "="*60)
    print(f"QUERY: {question}")
    print("="*60)
    
    try:
        # Call the RAG search method - just pass the query text
        response = rag.search(query_text=question)
        
        print(f"\n✓ Answer:\n")
        print(response)
        
        return response
    
    except Exception as e:
        print(f"✗ Query error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    """Main RAG query interface"""
    
    print("\n" + "="*60)
    print("RAG QUERY INTERFACE")
    print("="*60)
    
    # Initialize components
    driver = init_driver()
    if not driver:
        return
    
    # Check if KG exists
    if not check_kg_exists(driver):
        driver.close()
        return
    
    # Initialize LLM and embeddings
    llm = init_llm()
    embedder = init_embeddings()
    
    # Setup RAG
    rag = setup_rag_pipeline(driver, embedder, llm)
    if not rag:
        driver.close()
        return
    
    # Get question from command line or user input
    if len(sys.argv) > 1:
        # Question from command line
        question = " ".join(sys.argv[1:])
        answer = query_kg(rag, question)
    else:
        # Interactive mode
        print("\n" + "="*60)
        print("INTERACTIVE MODE")
        print("Enter your questions (type 'quit' to exit)")
        print("="*60 + "\n")
        
        while True:
            question = input("Q: ").strip()
            
            if question.lower() in ["quit", "exit", "q"]:
                print("✓ Goodbye!")
                break
            
            if not question:
                continue
            
            answer = query_kg(rag, question)
            print()
    
    driver.close()

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    main()
