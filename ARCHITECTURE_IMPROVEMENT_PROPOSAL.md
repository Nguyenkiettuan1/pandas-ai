# Architecture Improvement Proposal: Flexible Dataset Context Management

## 🎯 Vấn đề hiện tại

Hệ thống hiện tại yêu cầu `dataset_id` bắt buộc trong mọi API calls, gây ra:
- **Tight coupling**: Mọi operation đều ràng buộc với 1 dataset cụ thể
- **Limited scalability**: Khó mở rộng cho multi-dataset scenarios  
- **Poor UX**: User phải luôn specify dataset_id explicitly
- **Architecture rigidity**: Khó implement cross-dataset features

## 🚀 Giải pháp đề xuất

### 1. **Context-Based Architecture**

#### A. **Session-based Context Management**
```python
# New approach - Session context
POST /sessions/  # Create working session
{
    "workspace_name": "Sales Analysis",
    "default_dataset_id": 123,  # Optional
    "context_datasets": [123, 456, 789]  # Multiple datasets
}

# Query without explicit dataset_id
POST /sessions/{session_id}/queries/
{
    "question": "Show me sales data",  # Auto-detect dataset
    "context_hint": "sales"  # Optional context
}
```

#### B. **Workspace Concept**
```python
# Workspace groups related datasets
POST /workspaces/
{
    "name": "Q4 Analytics",
    "datasets": [
        {"id": 123, "role": "primary", "tags": ["sales", "revenue"]},
        {"id": 456, "role": "secondary", "tags": ["customers", "demographics"]},
        {"id": 789, "role": "reference", "tags": ["products", "inventory"]}
    ]
}

# Query with workspace context
POST /workspaces/{workspace_id}/queries/
{
    "question": "Compare Q3 vs Q4 sales performance",
    "auto_select_datasets": true  # System selects relevant datasets
}
```

### 2. **Smart Dataset Selection**

#### A. **Auto-Detection Service**
```python
class DatasetSelectionService:
    async def auto_select_datasets(
        self, 
        question: str,
        available_datasets: List[Dataset],
        context: WorkspaceContext = None
    ) -> List[Dataset]:
        """
        Analyze question and automatically select relevant datasets
        """
        # NLP analysis of question
        # Match with dataset metadata
        # Return ranked list of relevant datasets
```

#### B. **Query Intent Analysis**
```python
class QueryIntentAnalyzer:
    async def analyze_query_scope(self, question: str) -> QueryScope:
        """
        Determine if query needs:
        - Single dataset (current behavior)  
        - Multiple datasets (cross-analysis)
        - Dataset discovery (find relevant data)
        """
```

### 3. **Backward Compatible API Design**

#### A. **Legacy Support**
```python
# Option 1: Explicit dataset_id (current behavior)
POST /queries/
{
    "question": "Show top customers",
    "dataset_id": 123  # Explicit - works as before
}

# Option 2: Context-based (new behavior)
POST /queries/
{
    "question": "Show top customers", 
    "session_id": "session_123",  # Use session context
    # dataset_id omitted - auto-selected
}

# Option 3: Workspace-based (advanced)
POST /queries/
{
    "question": "Compare sales across regions",
    "workspace_id": "workspace_456",  # Use workspace context
    "scope": "cross_dataset"  # Enable multi-dataset analysis
}
```

#### B. **Progressive Enhancement**
```python
class QueryService:
    async def process_query(
        self,
        question: str,
        dataset_id: Optional[int] = None,      # Legacy mode
        session_id: Optional[str] = None,      # Session mode  
        workspace_id: Optional[str] = None,    # Workspace mode
        auto_select: bool = True               # Enable auto-selection
    ):
        # Determine query strategy based on provided parameters
        if dataset_id:
            return await self._process_single_dataset(question, dataset_id)
        elif session_id:
            return await self._process_with_session_context(question, session_id)
        elif workspace_id:
            return await self._process_with_workspace_context(question, workspace_id)
        else:
            return await self._process_with_auto_detection(question)
```

### 4. **Implementation Strategy**

#### Phase 1: Foundation (Week 1-2)
- [ ] Implement Session management
- [ ] Add Workspace concept
- [ ] Create Context management service
- [ ] Maintain backward compatibility

#### Phase 2: Smart Selection (Week 3-4)  
- [ ] Build Dataset selection service
- [ ] Implement Query intent analyzer
- [ ] Add Cross-dataset capabilities
- [ ] Enhanced agent routing

#### Phase 3: Advanced Features (Week 5-6)
- [ ] Multi-dataset query processing
- [ ] Context persistence
- [ ] Advanced workspace features
- [ ] Performance optimization

### 5. **Database Schema Additions**

```sql
-- Sessions for context management
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    user_id VARCHAR(255),  -- Future: user management
    default_dataset_id INTEGER REFERENCES datasets(id),
    context_datasets JSONB,  -- Array of dataset IDs with metadata
    settings JSONB,  -- Session-specific settings
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Workspaces for grouping datasets
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id VARCHAR(255),  -- Future: user management
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Dataset assignments to workspaces
CREATE TABLE workspace_datasets (
    workspace_id UUID REFERENCES workspaces(id),
    dataset_id INTEGER REFERENCES datasets(id),
    role VARCHAR(50),  -- 'primary', 'secondary', 'reference'
    tags TEXT[],  -- Array of tags for smart selection
    priority INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, dataset_id)
);

-- Query context tracking
CREATE TABLE query_contexts (
    query_id INTEGER REFERENCES queries(id),
    session_id UUID REFERENCES sessions(id),
    workspace_id UUID REFERENCES workspaces(id),
    selected_datasets INTEGER[],  -- Auto-selected datasets
    selection_strategy VARCHAR(50),  -- How datasets were selected
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6. **API Routes Enhancement**

```python
# New context-aware routes
app.include_router(session_router, prefix="/api/v1/sessions")
app.include_router(workspace_router, prefix="/api/v1/workspaces")

# Enhanced query routes
@query_router.post("/", response_model=Dict[str, Any])
async def process_query(
    query_request: EnhancedQueryRequest,  # Support multiple context types
    db: Session = Depends(get_db)
):
    """
    Process query with flexible context:
    - dataset_id: Legacy single-dataset mode
    - session_id: Session-based context
    - workspace_id: Workspace-based context
    - auto_detect: Smart dataset selection
    """
```

### 7. **Benefits of New Architecture**

#### Immediate Benefits:
- ✅ **Backward compatible**: Existing code continues to work
- ✅ **Flexible context**: Multiple ways to specify datasets
- ✅ **Better UX**: Users don't always need to know dataset_id
- ✅ **Smart selection**: System can auto-choose relevant datasets

#### Long-term Benefits:
- 🚀 **Scalable**: Easy to add multi-dataset features
- 🚀 **Extensible**: Support for complex analytics scenarios
- 🚀 **User-friendly**: Natural language queries without technical details
- 🚀 **Future-ready**: Foundation for advanced features

### 8. **Migration Path**

#### Step 1: Add new services alongside existing ones
#### Step 2: Introduce new API endpoints with context support
#### Step 3: Gradually migrate existing endpoints to use new architecture
#### Step 4: Deprecate legacy patterns (optional, for clean architecture)

### 9. **Example Usage Scenarios**

#### Scenario 1: Legacy Mode (Unchanged)
```python
# Existing code continues to work
response = await client.post("/queries/", json={
    "question": "Show sales data",
    "dataset_id": 123
})
```

#### Scenario 2: Session Mode (New)
```python
# Create session with context
session = await client.post("/sessions/", json={
    "name": "Q4 Analysis",
    "context_datasets": [123, 456]
})

# Query without specifying dataset
response = await client.post("/queries/", json={
    "question": "Show sales data",
    "session_id": session["data"]["id"]
})
```

#### Scenario 3: Smart Mode (Advanced)
```python
# Let system auto-detect relevant datasets
response = await client.post("/queries/", json={
    "question": "Compare sales performance across all regions",
    "auto_select": True,
    "scope": "cross_dataset"
})
```

## 🎯 Conclusion

Kiến trúc này giải quyết được vấn đề "luôn phải truyền dataset_id" mà vẫn:
- ✅ Maintain backward compatibility
- ✅ Enable flexible context management  
- ✅ Support future scalability requirements
- ✅ Provide multiple usage patterns for different scenarios

Bạn có muốn tôi bắt đầu implement Phase 1 của architecture này không?
