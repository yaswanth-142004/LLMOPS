"""
Simple test script to verify the FastAPI application is working
"""
import asyncio
import httpx
import json

async def test_api():
    """Test the library API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("🔍 Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed!")
            else:
                print("❌ Health check failed!")
                return
            
            # Test root endpoint
            print("\n🔍 Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("✅ Root endpoint working!")
                print(json.dumps(response.json(), indent=2))
            
            # Test creating an author
            print("\n📝 Testing author creation...")
            author_data = {
                "first_name": "Test",
                "last_name": "Author",
                "biography": "Test biography",
                "nationality": "Test Country"
            }
            response = await client.post(f"{base_url}/authors/", json=author_data)
            if response.status_code == 201:
                author = response.json()
                print(f"✅ Author created: {author['first_name']} {author['last_name']}")
                author_id = author['id']
                
                # Test getting the author
                print(f"\n🔍 Testing get author by ID: {author_id}...")
                response = await client.get(f"{base_url}/authors/{author_id}")
                if response.status_code == 200:
                    print("✅ Get author by ID working!")
                
                # Test getting all authors
                print("\n🔍 Testing get all authors...")
                response = await client.get(f"{base_url}/authors/")
                if response.status_code == 200:
                    authors = response.json()
                    print(f"✅ Retrieved {len(authors)} authors")
                
            else:
                print(f"❌ Author creation failed: {response.status_code}")
                print(response.text)
            
            print("\n🎉 Basic API tests completed!")
            
        except httpx.ConnectError:
            print("❌ Cannot connect to the API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🧪 LIBRARY MANAGEMENT API TESTS")
    print("="*60)
    print("Make sure the API server is running:")
    print("  python src/app.py")
    print("  or")
    print("  uvicorn src.app:app --reload")
    print("="*60)
    
    asyncio.run(test_api())
