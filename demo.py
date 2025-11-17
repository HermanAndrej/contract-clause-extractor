"""End-to-end demo script for the Contract Clause Extractor."""
import asyncio
import httpx
import os
from pathlib import Path


async def demo():
    """Run end-to-end demo of the extraction service."""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Contract Clause Extractor - E2E Demo")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code != 200:
                print("❌ Server is not healthy. Please start the server first.")
                return
    except Exception as e:
        print(f"❌ Cannot connect to server at {base_url}")
        print("   Please make sure the server is running:")
        print("   uvicorn app.main:app --reload")
        return
    
    print("✅ Server is running")
    print()
    
    # Step 1: List existing extractions
    print("Step 1: Listing existing extractions...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/extractions?page=1&page_size=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {data['total']} existing extraction(s)")
                if data['items']:
                    print("   Recent extractions:")
                    for item in data['items'][:3]:
                        print(f"     - {item['filename']} ({item['status']})")
            else:
                print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Step 2: Create a sample PDF (if we can't find one)
    print("Step 2: Preparing test document...")
    test_file_path = None
    
    # Look for test files in current directory
    test_files = list(Path(".").glob("*.pdf")) + list(Path(".").glob("*.docx"))
    
    if test_files:
        test_file_path = test_files[0]
        print(f"   Found test file: {test_file_path}")
    else:
        print("   ⚠️  No PDF or DOCX files found in current directory")
        print("   Please provide a contract file to test with")
        print("   You can create a simple test by:")
        print("   1. Creating a PDF with some legal text")
        print("   2. Or using the API directly with:")
        print(f"      curl -X POST '{base_url}/api/extract' \\")
        print("           -F 'file=@your_contract.pdf'")
        return
    
    # Step 3: Upload and extract
    print()
    print("Step 3: Uploading and extracting clauses...")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path.name, f, "application/pdf")}
                response = await client.post(
                    f"{base_url}/api/extract",
                    files=files
                )
            
            if response.status_code == 201:
                data = response.json()
                document_id = data["document_id"]
                print(f"   ✅ Extraction completed!")
                print(f"   Document ID: {document_id}")
                print(f"   Filename: {data['metadata']['filename']}")
                print(f"   Status: {data['metadata']['status']}")
                print(f"   Total clauses: {data['metadata']['total_clauses']}")
                print(f"   Processing time: {data['metadata']['processing_time_seconds']:.2f}s")
                print()
                
                # Step 4: Display extracted clauses
                print("Step 4: Extracted clauses:")
                print("-" * 60)
                for idx, clause in enumerate(data['clauses'][:5], 1):  # Show first 5
                    print(f"\nClause {idx}:")
                    print(f"  ID: {clause['clause_id']}")
                    print(f"  Title: {clause['title']}")
                    print(f"  Type: {clause.get('clause_type', 'N/A')}")
                    if clause.get('page_number'):
                        print(f"  Page: {clause['page_number']}")
                    print(f"  Content: {clause['content'][:200]}...")
                
                if len(data['clauses']) > 5:
                    print(f"\n  ... and {len(data['clauses']) - 5} more clauses")
                
                print()
                
                # Step 5: Retrieve extraction by ID
                print("Step 5: Retrieving extraction by ID...")
                response = await client.get(f"{base_url}/api/extractions/{document_id}")
                if response.status_code == 200:
                    print(f"   ✅ Successfully retrieved extraction")
                    retrieved_data = response.json()
                    print(f"   Clauses retrieved: {len(retrieved_data['clauses'])}")
                else:
                    print(f"   ❌ Failed to retrieve: {response.status_code}")
                
            else:
                print(f"   ❌ Extraction failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except httpx.TimeoutException:
        print("   ⏱️  Request timed out (extraction may take a while)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print()
    print("API Documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(demo())

