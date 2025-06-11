"""
Demo script to test the PandasAI Q&A System
"""
import requests
import json
import logging

# Setup demo logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        logger.info(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def test_list_profiles():
    """Test listing available agent profiles"""
    try:
        response = requests.get("http://localhost:8000/api/v1/profiles")
        logger.info(f"List profiles: {response.status_code}")
        if response.status_code == 200:
            profiles = response.json()
            logger.info(f"Available profiles: {len(profiles['profiles'])}")
            for profile in profiles['profiles']:
                logger.info(f"  - {profile['name']}: {profile['description']}")
            return profiles['profiles']
        else:
            logger.error(f"Error: {response.text}")
            return []
    except Exception as e:
        logger.error(f"List profiles failed: {e}")
        return []

def test_list_tools():
    """Test listing available tools"""
    try:
        response = requests.get("http://localhost:8000/api/v1/tools")
        logger.info(f"List tools: {response.status_code}")
        if response.status_code == 200:
            tools = response.json()
            logger.info(f"Available tools: {len(tools['tools'])}")
            for tool in tools['tools']:
                logger.info(f"  - {tool['name']}: {tool['description']} (enabled: {tool['enabled']})")
            return tools['tools']
        else:
            logger.error(f"Error: {response.text}")
            return []
    except Exception as e:
        logger.error(f"List tools failed: {e}")
        return []

def test_create_dataset():
    """Test creating a dataset"""
    data = {
        "name": "Test Sales Data",
        "description": "A test dataset for demo purposes",
        "table_name": "test_sales"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/datasets/", json=data)
        print(f"Create dataset: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Created dataset with ID: {result['id']}")
            return result['id']
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Create dataset failed: {e}")
        return None

def test_list_datasets():
    """Test listing datasets"""
    try:
        response = requests.get(f"{BASE_URL}/datasets/")
        print(f"List datasets: {response.status_code}")
        if response.status_code == 200:
            datasets = response.json()
            print(f"Found {len(datasets)} datasets")
            for dataset in datasets:
                print(f"  - {dataset['name']} (ID: {dataset['id']})")
            return datasets
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"List datasets failed: {e}")
        return []

def test_process_query_with_profile(dataset_id, profile_name="general_analyst"):
    """Test processing a natural language query with specific profile"""
    data = {
        "question": "What is the total sales amount?",
        "dataset_id": dataset_id,
        "session_id": "demo_session_123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/queries/?profile_name={profile_name}", json=data)
        logger.info(f"Process query with {profile_name}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Query result with profile {profile_name}: {json.dumps(result, indent=2)}")
            return result
        else:
            logger.error(f"Error: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Process query failed: {e}")
        return None

def test_get_insights(dataset_id, profile_name="general_analyst"):
    """Test getting automated insights for a dataset"""
    try:
        response = requests.post(f"{BASE_URL}/queries/insights/{dataset_id}?profile_name={profile_name}")
        logger.info(f"Get insights with {profile_name}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Insights: {json.dumps(result, indent=2)}")
            return result
        else:
            logger.error(f"Error: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Get insights failed: {e}")
        return None

def test_chat(dataset_id):
    """Test chat endpoint"""
    data = {
        "question": "Show me the top 5 customers by revenue",
        "dataset_id": dataset_id,
        "session_id": "demo_session_123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/conversations/chat/", json=data)
        print(f"Chat: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Chat result: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Chat failed: {e}")
        return None

def run_demo():
    """Run the complete demo"""
    logger.info("=== PandasAI Q&A System Demo ===")
    
    # 1. Health check
    logger.info("1. Testing health check...")
    if not test_health_check():
        logger.error("❌ Server is not running. Please start the server first.")
        return
    logger.info("✅ Server is running")
    
    # 2. List profiles
    logger.info("2. Listing available profiles...")
    profiles = test_list_profiles()
    if profiles:
        logger.info("✅ Profiles listed")
    
    # 3. List tools
    logger.info("3. Listing available tools...")
    tools = test_list_tools()
    if tools:
        logger.info("✅ Tools listed")
    
    # 4. Create dataset
    logger.info("4. Creating test dataset...")
    dataset_id = test_create_dataset()
    if not dataset_id:
        logger.error("❌ Failed to create dataset")
        return
    logger.info("✅ Dataset created")
    
    # 5. List datasets
    logger.info("5. Listing datasets...")
    datasets = test_list_datasets()
    logger.info("✅ Datasets listed")
    
    # 6. Process query with different profiles
    logger.info("6. Processing queries with different profiles...")
    
    # Test with general analyst
    query_result = test_process_query_with_profile(dataset_id, "general_analyst")
    if query_result:
        logger.info("✅ Query processed with general_analyst")
    
    # Test with sales specialist if available
    if any(p['name'] == 'sales_specialist' for p in profiles):
        sales_result = test_process_query_with_profile(dataset_id, "sales_specialist")
        if sales_result:
            logger.info("✅ Query processed with sales_specialist")
    
    # 7. Get insights
    logger.info("7. Getting automated insights...")
    insights = test_get_insights(dataset_id, "general_analyst")
    if insights:
        logger.info("✅ Insights generated")
    
    # 8. Test chat
    logger.info("8. Testing chat endpoint...")
    chat_result = test_chat(dataset_id)
    if chat_result:
        logger.info("✅ Chat tested")
    
    logger.info("=== Demo completed successfully ===")

if __name__ == "__main__":
    run_demo()
