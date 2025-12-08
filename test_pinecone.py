"""
Test Pinecone Connection
Run this script to verify your Pinecone setup is working correctly.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from pinecone import Pinecone, ServerlessSpec
    
    # Get API key from environment or use provided one
    api_key = os.getenv('PINECONE_API_KEY')
    if not api_key:
        print("⚠️ PINECONE_API_KEY not found in environment variables")
        print("   Please set it in your .env file or provide it below")
        api_key = input("Enter your Pinecone API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        exit(1)
    
    print("🌲 Connecting to Pinecone...")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Get index name from environment or use default
    index_name = os.getenv('PINECONE_INDEX_NAME', 'rag-bot-index')
    print(f"📋 Checking index: {index_name}")
    
    # List existing indexes
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    print(f"📊 Existing indexes: {existing_indexes}")
    
    # Check if index exists
    if index_name in existing_indexes:
        print(f"✅ Index '{index_name}' exists!")
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"📈 Index stats: {stats}")
        
        # Test query (if there are vectors)
        if stats.total_vector_count > 0:
            print(f"\n🔍 Testing query...")
            # Create a dummy query vector (384 dimensions for all-MiniLM-L6-v2)
            test_vector = [0.1] * 384
            results = index.query(
                vector=test_vector,
                top_k=3,
                include_metadata=True
            )
            print(f"✅ Query successful! Found {len(results.matches)} matches")
            if results.matches:
                print(f"   Top match score: {results.matches[0].score:.3f}")
        else:
            print("ℹ️ Index is empty (no vectors yet)")
            print("   This is normal if you haven't uploaded any RAG entries yet")
    else:
        print(f"⚠️ Index '{index_name}' does not exist")
        print("   The bot will create it automatically on first run")
        print("   Or you can create it manually in the Pinecone dashboard")
        
        # Optionally create it
        create = input(f"\nWould you like to create '{index_name}' now? (y/n): ").strip().lower()
        if create == 'y':
            print(f"🌲 Creating index '{index_name}'...")
            try:
                pc.create_index(
                    name=index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
                    )
                )
                print(f"✅ Index '{index_name}' created successfully!")
            except Exception as e:
                print(f"❌ Failed to create index: {e}")
    
    print("\n✅ Pinecone connection test completed successfully!")
    
except ImportError:
    print("❌ Pinecone package not installed!")
    print("   Run: pip install pinecone-client")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

