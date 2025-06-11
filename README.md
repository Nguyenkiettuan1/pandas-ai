# PandasAI Q&A System

A natural language Q&A system built with PandasAI, FastAPI, and PostgreSQL that allows users to query databases using natural language through AI agents.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Multiple Dataset Support**: Manage and query multiple datasets
- **Conversation Memory**: Maintain context across queries in a session
- **Query History**: Track and review previous queries and results
- **CSV Upload**: Easily upload CSV files to create datasets
- **RESTful API**: Full REST API for integration with other applications
- **AI-Powered**: Uses OpenAI and PandasAI for intelligent data analysis

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **AI/ML**: PandasAI, OpenAI, LangChain
- **ORM**: SQLAlchemy
- **Data Processing**: Pandas

## Project Structure

```
app/
├── routes/        # FastAPI route handlers separated by domain
│   ├── dataset_routes.py     # Dataset management endpoints
│   ├── query_routes.py       # Query processing endpoints
│   └── conversation_routes.py # Conversation/chat endpoints
├── schemas/       # Pydantic models for request/response validation
│   ├── dataset_schemas.py    # Dataset-related schemas
│   ├── query_schemas.py      # Query-related schemas
│   ├── conversation_schemas.py # Conversation schemas
│   └── common_schemas.py     # Shared/common schemas
├── models/        # SQLAlchemy database models
│   ├── dataset.py           # Dataset model
│   ├── query.py             # Query model
│   └── conversation.py      # Conversation model
├── services/      # Business logic services
│   ├── dataset_service.py   # Dataset management logic
│   ├── query_service.py     # Query processing logic
│   └── conversation_service.py # Conversation management
├── agents/        # AI agents for natural language processing
│   └── pandas_agent.py      # PandasAI integration agent
└── core/          # Core configuration and utilities
    ├── config.py            # Application configuration
    └── database.py          # Database connection and setup
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL
- OpenAI API key

### Installation

1. Clone the repository and navigate to the project directory

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/pandasai_db
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```

5. Set up PostgreSQL database:
```bash
# Create database
createdb pandasai_db
```

6. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### Datasets
- `POST /api/v1/datasets/` - Create a new dataset
- `GET /api/v1/datasets/` - Get all datasets
- `GET /api/v1/datasets/{id}` - Get specific dataset
- `PUT /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset
- `POST /api/v1/datasets/upload-csv/` - Upload CSV file

### Queries
- `POST /api/v1/queries/` - Process natural language query
- `GET /api/v1/queries/history/` - Get query history

### Conversations
- `GET /api/v1/conversations/{session_id}` - Get conversation history
- `POST /api/v1/conversations/chat/` - Chat with conversation context

## Usage Examples

### 1. Upload a CSV Dataset
```python
import requests

# Upload CSV file
with open('sales_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/datasets/upload-csv/',
        files={'file': f},
        data={'name': 'Sales Data', 'description': 'Monthly sales data'}
    )
```

### 2. Ask Natural Language Questions
```python
# Query the dataset
query_data = {
    "question": "What were the total sales by month?",
    "dataset_id": 1,
    "session_id": "user123"
}

response = requests.post(
    'http://localhost:8000/api/v1/conversations/chat/',
    json=query_data
)

result = response.json()
print(result['result'])
```

### 3. Get Query History
```python
# Get previous queries
response = requests.get(
    'http://localhost:8000/api/v1/queries/history/?dataset_id=1&limit=10'
)

history = response.json()
for query in history:
    print(f"Q: {query['question']}")
    print(f"A: {query['result']}")
    print(f"Time: {query['execution_time']}ms")
    print("---")
```

## Running the Demo

A demo script is provided to test all the API endpoints:

```bash
# Make sure the server is running first
python main.py

# In another terminal, run the demo
python demo.py
```

The demo will:
1. Check if the server is running
2. Create a test dataset
3. List all datasets
4. Process a natural language query
5. Test the chat endpoint with conversation context

## Example Questions You Can Ask

- "What is the average sales by region?"
- "Show me the top 10 customers by revenue"
- "What was the trend in sales over the last 6 months?"
- "Which products have the highest profit margin?"
- "Create a chart showing monthly revenue"

## Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pandasai_db
DB_USER=username
DB_PASSWORD=password

# API
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True

# AI
OPENAI_API_KEY=sk-...
```

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
python main.py
```

### Database Migrations

For production use, consider using Alembic for database migrations:

```bash
# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support, please open an issue in the repository.
