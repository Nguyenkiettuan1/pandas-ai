#!/usr/bin/env python3
"""
Test script for Vietnamese Q&A system with PandasAI
This script tests the Vietnamese business data queries using the actual API structure.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Vietnamese test queries for business data
VIETNAMESE_QUERIES = [
    "Mã nhân viên NV001 là của ai?",
    "Hóa đơn mã HD001 có giá bao nhiêu?", 
    "Nhân viên nào ở phòng Kinh doanh?",
    "Sản phẩm nào có giá cao nhất?",
    "Tổng doanh thu trong tháng này là bao nhiêu?",
    "Khách hàng nào mua nhiều nhất?",
    "Có bao nhiêu đơn hàng chưa thanh toán?",
    "Danh sách tất cả sản phẩm Smartphone",
    "Nhân viên nào có thâm niên cao nhất?",
    "Khách hàng VIP có những ai?"
]

class VietnameseQATest:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_server_health(self):
        """Test if server is running and healthy"""
        print("🔍 Testing server health...")
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server is healthy: {data}")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Server connection error: {e}")
            return False
    
    async def get_available_datasets(self):
        """Get list of available datasets"""
        print("\n📊 Getting available datasets...")
        try:
            async with self.session.get(f"{API_BASE}/datasets/") as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        datasets = result.get('data', [])
                        print(f"✅ Found {len(datasets)} datasets:")
                        for dataset in datasets:
                            print(f"   📋 ID: {dataset['id']} - {dataset['name']} ({dataset['table_name']})")
                        return datasets
                    else:
                        print(f"❌ Dataset API returned error: {result.get('message')}")
                        return []
                else:
                    print(f"❌ Failed to get datasets: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   Error response: {error_text[:200]}...")
                    return []
        except Exception as e:
            print(f"❌ Error getting datasets: {e}")
            return []
    
    async def test_vietnamese_queries(self, dataset_id):
        """Test Vietnamese natural language queries"""
        print(f"\n🇻🇳 Testing Vietnamese queries on dataset {dataset_id}...")
        
        successful_queries = 0
        total_queries = len(VIETNAMESE_QUERIES)
        session_id = f"vn_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for i, question in enumerate(VIETNAMESE_QUERIES, 1):
            print(f"\n📝 Query {i}/{total_queries}: '{question}'")
            
            try:
                payload = {
                    "question": question,
                    "dataset_id": dataset_id,
                    "session_id": session_id
                }
                
                async with self.session.post(
                    f"{API_BASE}/queries/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    result = await response.json()
                    
                    if response.status == 200 and result.get('status') == 'success':
                        data = result.get('data', {})
                        answer = data.get('answer', data.get('result', 'No answer'))
                        metadata = result.get('metadata', {})
                        execution_time = metadata.get('execution_time_seconds', metadata.get('execution_time', 0))
                        
                        print(f"   ✅ Answer: {answer}")
                        print(f"   ⏱️  Time: {execution_time:.2f}s")
                        successful_queries += 1
                    else:
                        error_msg = result.get('message', result.get('error', 'Unknown error'))
                        print(f"   ❌ Query failed: {error_msg}")
                        if 'error_details' in result:
                            print(f"   📋 Details: {result['error_details']}")
                            
            except Exception as e:
                print(f"   ❌ Query error: {e}")
                
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        print(f"\n📊 Query Results: {successful_queries}/{total_queries} successful")
        return successful_queries, total_queries
    
    async def test_query_history(self, dataset_id):
        """Test query history functionality"""
        print(f"\n📚 Testing query history for dataset {dataset_id}...")
        
        try:
            # Test with dataset filter
            async with self.session.get(f"{API_BASE}/queries/history/?dataset_id={dataset_id}&limit=5") as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        history = result.get('data', [])
                        print(f"✅ Found {len(history)} historical queries:")
                        for query in history[:3]:  # Show first 3
                            question = query.get('question', 'Unknown question')
                            result_text = str(query.get('result', ''))[:100]
                            created_at = query.get('created_at', 'Unknown time')
                            print(f"   🔍 Q: {question}")
                            print(f"      A: {result_text}...")
                            print(f"      📅 {created_at}")
                        return True
                    else:
                        print(f"❌ History API error: {result.get('message')}")
                        return False
                else:
                    print(f"❌ History request failed: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text[:200]}...")
                    return False
        except Exception as e:
            print(f"❌ History error: {e}")
            return False
    
    async def test_dataset_insights(self, dataset_id):
        """Test dataset insights functionality"""
        print(f"\n🔮 Testing dataset insights for dataset {dataset_id}...")
        
        try:
            async with self.session.get(f"{API_BASE}/datasets/{dataset_id}/insights") as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        insights = result.get('data', {})
                        print(f"✅ Generated insights:")
                        # Show first few insights
                        count = 0
                        for key, value in insights.items():
                            if count >= 3:  # Limit to first 3
                                break
                            print(f"   📊 {key}: {str(value)[:100]}...")
                            count += 1
                        return True
                    else:
                        print(f"❌ Insights API error: {result.get('message')}")
                        return False
                else:
                    print(f"❌ Insights request failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Insights error: {e}")
            return False

async def main():
    """Main test function"""
    print("🚀 Starting Vietnamese Q&A System Test")
    print("=" * 60)
    
    async with VietnameseQATest() as tester:
        # 1. Test server health
        if not await tester.test_server_health():
            print("\n❌ Server is not available. Please start the server with: python main.py")
            return
        
        # 2. Get datasets
        datasets = await tester.get_available_datasets()
        if not datasets:
            print("\n❌ No datasets available. Please run: python setup_business_data.py")
            return
        
        # 3. Select dataset for testing
        business_dataset = None
        for dataset in datasets:
            # Look for Vietnamese business data
            if any(keyword in dataset['name'].lower() for keyword in ['nhan_vien', 'business', 'vietnamese']):
                business_dataset = dataset
                break
        
        if not business_dataset:
            # Use first available dataset
            business_dataset = datasets[0]
        
        dataset_id = business_dataset['id']
        dataset_name = business_dataset['name']
        
        print(f"\n🎯 Using dataset: {dataset_name} (ID: {dataset_id})")
        
        # 4. Test Vietnamese queries
        successful, total = await tester.test_vietnamese_queries(dataset_id)
        
        # 5. Test query history
        history_success = await tester.test_query_history(dataset_id)
        
        # 6. Test dataset insights
        insights_success = await tester.test_dataset_insights(dataset_id)
        
        # 7. Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Server health: OK")
        print(f"✅ Datasets found: {len(datasets)}")
        print(f"✅ Vietnamese queries: {successful}/{total} successful ({(successful/total)*100:.1f}%)")
        print(f"✅ Query history: {'OK' if history_success else 'Failed'}")
        print(f"✅ Dataset insights: {'OK' if insights_success else 'Failed'}")
        
        if successful >= total * 0.5:  # At least 50% success rate
            print("\n🎉 Vietnamese Q&A system is working! Most queries were successful.")
        else:
            print("\n⚠️  Some tests failed. Common issues:")
            print("   - LLM not configured (need OPENAI_API_KEY or PANDASAI_API_KEY)")
            print("   - Database connection issues")
            print("   - Data not properly seeded")
            
        print(f"\n💡 Next steps:")
        print(f"   - Configure LLM in .env file")
        print(f"   - Start server: python main.py")
        print(f"   - Test with web interface at: {BASE_URL}/docs")

if __name__ == "__main__":
    asyncio.run(main())
