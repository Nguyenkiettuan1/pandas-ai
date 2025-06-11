#!/usr/bin/env python3
"""
Test the enhanced PandasAI system with LLM Factory
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_enhanced_system():
    """Test the enhanced system"""
    print("🧪 Testing Enhanced PandasAI System")
    print("=" * 50)
    
    # Test 1: Health check
    print("🔍 Step 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: Get datasets
    print("\n📊 Step 2: Get Datasets")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/datasets/")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('data'):
                datasets = data['data']
                print(f"✅ Found {len(datasets)} datasets")
                for ds in datasets[:3]:  # Show first 3
                    print(f"  - ID: {ds['id']}, Name: {ds['name']}")
                
                # Use first dataset for testing
                test_dataset_id = datasets[0]['id']
                dataset_name = datasets[0]['name']
                print(f"\n🎯 Using dataset: {dataset_name} (ID: {test_dataset_id})")
            else:
                print("❌ No datasets found")
                return
        else:
            print(f"❌ Failed to get datasets: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting datasets: {e}")
        return
    
    # Test 3: Test agent suggestions
    print("\n🤖 Step 3: Test Agent Suggestions")
    try:
        suggestion_payload = {
            "question": "Tổng cộng có bao nhiêu nhân viên?",
            "dataset_id": test_dataset_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/queries/suggestions/",
            json=suggestion_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data['data']
                print(f"✅ Recommended agent: {result['recommended_agent']}")
                print(f"✅ Available suggestions: {len(result['all_suggestions'])}")
            else:
                print(f"❌ Agent suggestions failed: {data.get('message')}")
        else:
            print(f"❌ Agent suggestions error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing agent suggestions: {e}")
    
    # Test 4: Test Vietnamese statistical query
    print("\n🇻🇳 Step 4: Test Vietnamese Statistical Query")
    test_questions = [
        "Tổng cộng có bao nhiêu nhân viên?",
        "Nhân viên nào có mức lương cao nhất?",
        "Trung bình lương theo phòng ban?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Query {i}: {question}")
        try:
            query_payload = {
                "question": question,
                "dataset_id": test_dataset_id,
                "session_id": f"test_session_{i}"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/queries/?profile_name=general_analyst",
                json=query_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = data['data']
                    print(f"✅ Success - Execution time: {result.get('execution_time')}ms")
                    print(f"📋 Result: {str(result.get('result'))[:100]}...")
                    print(f"🤖 Profile used: {result.get('profile_used')}")
                else:
                    print(f"❌ Query failed: {data.get('message')}")
                    if data.get('error'):
                        print(f"   Error: {data['error'].get('error_message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Enhanced System Test Completed!")
    print("\n💡 Enhanced Features:")
    print("  1. LLM Factory for efficient LLM management")
    print("  2. YAML-based agent profiles")
    print("  3. Enhanced prompts for natural language + statistics")
    print("  4. Smart fallback mechanisms")
    print("  5. Auto-routing to appropriate agents")

if __name__ == "__main__":
    test_enhanced_system()
