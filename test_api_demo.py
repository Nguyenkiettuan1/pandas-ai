# filepath: d:\PandasAI\test_api_demo.py
"""
Script demo để test tất cả API endpoints sau khi setup database
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    """Class để test các API endpoints"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test health check endpoint"""
        print("🔍 Testing Health Check...")
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health Check: {data}")
                    return True
                else:
                    print(f"❌ Health Check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health Check error: {e}")
            return False
    
    async def test_get_datasets(self):
        """Test lấy danh sách datasets"""
        print("\n📊 Testing Get Datasets...")
        try:
            async with self.session.get(f"{BASE_URL}/datasets/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Found {len(data.get('data', []))} datasets")
                    for dataset in data.get('data', [])[:3]:  # Show first 3
                        print(f"   📋 {dataset['name']} (ID: {dataset['id']}) -> {dataset['table_name']}")
                    return data.get('data', [])
                else:
                    print(f"❌ Get datasets failed: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Get datasets error: {e}")
            return []
    
    async def test_natural_language_queries(self, datasets):
        """Test natural language queries với AI agent"""
        if not datasets:
            print("⚠️  No datasets available for testing queries")
            return
        
        print("\n🤖 Testing Natural Language Queries...")
        
        # Lấy dataset đầu tiên (thường là sales)
        dataset_id = datasets[0]['id']
        
        test_questions = [
            "Tổng doanh thu trong tháng này là bao nhiêu?",
            "Top 5 sản phẩm bán chạy nhất?",
            "Doanh thu theo từng vùng miền?",
            "Khách hàng nào có tổng mua hàng cao nhất?",
            "So sánh doanh thu tháng này với tháng trước?"
        ]
        
        for i, question in enumerate(test_questions[:3], 1):  # Test 3 câu đầu
            print(f"\n🔎 Test {i}: '{question}'")
            try:
                payload = {
                    "question": question,
                    "dataset_id": dataset_id,
                    "session_id": f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "profile_name": "sales_specialist"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/queries/ask/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200 and data.get('status') == 'success':
                        answer = data.get('data', {}).get('answer', 'No answer')
                        execution_time = data.get('metadata', {}).get('execution_time_seconds', 0)
                        print(f"✅ Answer: {answer}")
                        print(f"⏱️  Execution time: {execution_time:.2f}s")
                    else:
                        print(f"❌ Query failed: {data.get('message', 'Unknown error')}")
                        
            except Exception as e:
                print(f"❌ Query error: {e}")
    
    async def test_dataset_insights(self, datasets):
        """Test dataset insights"""
        if not datasets:
            return
        
        print("\n🔮 Testing Dataset Insights...")
        
        dataset_id = datasets[0]['id']
        try:
            async with self.session.get(f"{BASE_URL}/datasets/{dataset_id}/insights") as response:
                data = await response.json()
                
                if response.status == 200:
                    insights = data.get('data', {})
                    print(f"✅ Dataset insights generated:")
                    for key, value in list(insights.items())[:5]:  # Show first 5 insights
                        print(f"   📊 {key}: {value}")
                else:
                    print(f"❌ Insights failed: {data.get('message', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ Insights error: {e}")
    
    async def test_query_history(self, datasets):
        """Test query history"""
        if not datasets:
            return
        
        print("\n📚 Testing Query History...")
        
        dataset_id = datasets[0]['id']
        try:
            async with self.session.get(f"{BASE_URL}/queries/history/{dataset_id}") as response:
                data = await response.json()
                
                if response.status == 200:
                    queries = data.get('data', [])
                    print(f"✅ Found {len(queries)} historical queries")
                    for query in queries[:3]:  # Show first 3
                        print(f"   🔍 '{query['question']}' -> {query.get('result_summary', 'No result')[:50]}...")
                else:
                    print(f"❌ History failed: {data.get('message', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ History error: {e}")
    
    async def test_create_dataset(self):
        """Test tạo dataset mới"""
        print("\n➕ Testing Create Dataset...")
        
        try:
            payload = {
                "name": "Demo Test Dataset",
                "description": "Dataset tạo từ API test",
                "file_path": "/demo/test.csv",
                "table_name": "demo_test_table"
            }
            
            async with self.session.post(
                f"{BASE_URL}/datasets/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ Dataset created: {data.get('data', {}).get('name', 'Unknown')}")
                    return data.get('data', {}).get('id')
                else:
                    print(f"❌ Create dataset failed: {data.get('message', 'Unknown error')}")
                    return None
                    
        except Exception as e:
            print(f"❌ Create dataset error: {e}")
            return None
    
    async def test_conversation_flow(self, datasets):
        """Test conversation flow"""
        if not datasets:
            return
        
        print("\n💬 Testing Conversation Flow...")
        
        session_id = f"conversation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dataset_id = datasets[0]['id']
        
        conversation_questions = [
            "Doanh thu hôm nay thế nào?",
            "So với hôm qua tăng hay giảm?",
            "Sản phẩm nào bán được nhiều nhất hôm nay?"
        ]
        
        for i, question in enumerate(conversation_questions, 1):
            print(f"\n💭 Conversation step {i}: '{question}'")
            try:
                payload = {
                    "question": question,
                    "dataset_id": dataset_id,
                    "session_id": session_id,
                    "profile_name": "sales_specialist"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/queries/ask/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        answer = data.get('data', {}).get('answer', 'No answer')
                        print(f"🤖 AI: {answer[:100]}...")
                    else:
                        print(f"❌ Conversation step failed: {data.get('message', 'Unknown error')}")
                        
            except Exception as e:
                print(f"❌ Conversation error: {e}")

async def main():
    """Main function để chạy tất cả tests"""
    print("🧪 Starting API Demo Tests")
    print("=" * 50)
    
    async with APITester() as tester:
        # Test basic connectivity
        if not await tester.test_health_check():
            print("❌ Server is not running. Please start the server first:")
            print("   python main.py")
            return
        
        # Test datasets
        datasets = await tester.test_get_datasets()
        
        if not datasets:
            print("⚠️  No datasets found. Please run setup_database.py first:")
            print("   python setup_database.py")
            return
        
        # Test các chức năng chính
        await tester.test_natural_language_queries(datasets)
        await tester.test_dataset_insights(datasets)
        await tester.test_query_history(datasets)
        await tester.test_conversation_flow(datasets)
        
        # Test create dataset (optional)
        new_dataset_id = await tester.test_create_dataset()
        if new_dataset_id:
            print(f"✅ Successfully created new dataset with ID: {new_dataset_id}")
    
    print("\n🎉 API Demo Tests Completed!")
    print("\n💡 Try these URLs in your browser:")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("   🔍 Interactive: http://localhost:8000/redoc")
    print("   🏥 Health: http://localhost:8000/api/v1/health")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        print("Make sure the server is running: python main.py")
