from typing import Dict, List, Optional, Any
import re
from enum import Enum
from dataclasses import dataclass
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class AgentType(Enum):
    GENERAL_ANALYST = "general_analyst"
    SALES_ANALYST = "sales_analyst" 
    CUSTOMER_ANALYST = "customer_analyst"
    FINANCIAL_ANALYST = "financial_analyst"
    HR_ANALYST = "hr_analyst"
    TECHNICAL_ANALYST = "technical_analyst"

@dataclass
class AgentCapability:
    keywords: List[str]
    patterns: List[str]
    weight: float
    description: str

class AgentRouter:
    def __init__(self):
        self.agent_capabilities = self._initialize_agent_capabilities()
        logger.info("Agent Router initialized with Vietnamese/English capabilities")
    
    def _initialize_agent_capabilities(self) -> Dict[AgentType, AgentCapability]:
        """Initialize agent capabilities with Vietnamese and English support"""
        return {
            AgentType.SALES_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "doanh thu", "bán hàng", "khách hàng", "sản phẩm", "đơn hàng", 
                    "bán chạy", "doanh số", "thu nhập", "lợi nhuận",
                    # English
                    "revenue", "sales", "customer", "product", "order", 
                    "selling", "turnover", "income", "profit"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"doanh\s*thu.*?(tháng|năm|quý)",
                    r"bán.*?(nhiều|chạy|tốt).*?nhất",
                    r"khách.*?hàng.*?(mua|đặt)",
                    r"sản.*?phẩm.*?(bán|hot)",
                    r"top.*?(bán|doanh thu)",
                    # English patterns
                    r"revenue.*?(month|year|quarter)",
                    r"best.*?selling",
                    r"top.*?(sales|revenue)",
                    r"customer.*?(purchase|buy)",
                    r"sales.*?(analysis|report)"
                ],
                weight=0.8,
                description="Chuyên gia phân tích bán hàng và doanh thu"
            ),
            
            AgentType.CUSTOMER_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "khách hàng", "người dùng", "phân khúc", "nhóm khách", 
                    "hành vi", "thói quen", "sở thích", "phân tích khách hàng",
                    # English
                    "customer", "user", "client", "segment", "behavior", 
                    "demographics", "analysis", "profile"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"khách.*?hàng.*?(nào|loại|nhóm)",
                    r"phân.*?tích.*?khách.*?hàng",
                    r"nhóm.*?khách",
                    r"hành.*?vi.*?khách",
                    r"phân.*?khúc.*?khách",
                    # English patterns
                    r"customer.*?(analysis|segment)",
                    r"user.*?(behavior|profile)",
                    r"client.*?(analysis|group)",
                    r"demographic.*?analysis"
                ],
                weight=0.8,
                description="Chuyên gia phân tích khách hàng và hành vi"
            ),
            
            AgentType.FINANCIAL_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "tài chính", "lợi nhuận", "chi phí", "ngân sách", "đầu tư",
                    "tiền", "thu chi", "báo cáo tài chính", "kế toán",
                    # English
                    "financial", "finance", "profit", "cost", "budget", 
                    "expense", "investment", "accounting", "money"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"lợi.*?nhuận",
                    r"chi.*?phí",
                    r"tài.*?chính",
                    r"thu.*?chi",
                    r"ngân.*?sách",
                    # English patterns
                    r"profit.*?(margin|analysis)",
                    r"financial.*?(report|analysis)",
                    r"cost.*?analysis",
                    r"budget.*?(analysis|report)"
                ],
                weight=0.8,
                description="Chuyên gia phân tích tài chính và chi phí"
            ),
            
            AgentType.HR_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "nhân viên", "lương", "phòng ban", "quản lý", "hiệu suất",
                    "tuyển dụng", "đánh giá", "kpi", "năng suất",
                    # English
                    "employee", "staff", "salary", "department", "manager", 
                    "performance", "hr", "human resource", "recruitment"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"nhân.*?viên.*?(nào|top|tốt)",
                    r"phòng.*?ban",
                    r"lương.*?(cao|thấp).*?nhất",
                    r"hiệu.*?suất.*?nhân.*?viên",
                    r"đánh.*?giá.*?nhân.*?viên",
                    # English patterns
                    r"employee.*?(performance|evaluation)",
                    r"staff.*?(analysis|report)",
                    r"salary.*?(analysis|comparison)",
                    r"department.*?(performance|analysis)"
                ],
                weight=0.8,
                description="Chuyên gia phân tích nhân sự và hiệu suất"
            ),
            
            AgentType.TECHNICAL_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "hệ thống", "kỹ thuật", "cơ sở dữ liệu", "bảng", "cột",
                    "dữ liệu", "cấu trúc", "truy vấn", "sql",
                    # English
                    "technical", "system", "database", "table", "column",
                    "data", "structure", "query", "sql", "schema"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"cấu.*?trúc.*?(bảng|dữ liệu)",
                    r"thông.*?tin.*?(bảng|cột)",
                    r"mô.*?tả.*?(dữ liệu|bảng)",
                    r"kiểu.*?dữ.*?liệu",
                    # English patterns
                    r"table.*?structure",
                    r"data.*?(type|structure)",
                    r"database.*?(schema|info)",
                    r"column.*?(info|description)"
                ],
                weight=0.7,
                description="Chuyên gia phân tích kỹ thuật và cấu trúc dữ liệu"
            ),
            
            AgentType.GENERAL_ANALYST: AgentCapability(
                keywords=[
                    # Vietnamese
                    "tổng quan", "mô tả", "hiển thị", "xem", "cho biết",
                    "thống kê", "báo cáo", "phân tích chung",
                    # English
                    "overview", "summary", "show", "display", "describe",
                    "general", "basic", "statistics", "report"
                ],
                patterns=[
                    # Vietnamese patterns
                    r"tổng.*?quan",
                    r"cho.*?biết",
                    r"hiển.*?thị.*?dữ.*?liệu",
                    r"xem.*?dữ.*?liệu",
                    r"mô.*?tả.*?tập.*?dữ.*?liệu",
                    # English patterns
                    r"show.*?me.*?data",
                    r"overview.*?of.*?data",
                    r"describe.*?dataset",
                    r"what.*?is.*?this.*?data"
                ],
                weight=0.5,
                description="Chuyên gia phân tích dữ liệu tổng quát"
            )
        }
    
    def route_question(self, question: str, dataset_context: Optional[Dict] = None) -> AgentType:
        """Route question to the most appropriate agent"""
        logger.info(f"Routing question: {question[:100]}...")
        
        question_lower = question.lower()
        agent_scores = {}
        
        # Calculate scores for each agent
        for agent_type, capability in self.agent_capabilities.items():
            score = self._calculate_agent_score(question_lower, capability)
            
            # Add context bonus if available
            if dataset_context:
                score += self._calculate_context_bonus(agent_type, dataset_context)
            
            agent_scores[agent_type] = score
        
        # Find the best agent
        best_agent = max(agent_scores, key=agent_scores.get)
        best_score = agent_scores[best_agent]
        
        # Use threshold to decide
        if best_score < 0.3:
            best_agent = AgentType.GENERAL_ANALYST
            logger.info("No specific agent matched well, using General Analyst")
        else:
            logger.info(f"Selected {best_agent.value} with score {best_score:.2f}")
        
        return best_agent
    
    def _calculate_agent_score(self, question: str, capability: AgentCapability) -> float:
        """Calculate matching score for an agent"""
        score = 0.0
        
        # Keyword matching (exact match gets higher score)
        keyword_matches = 0
        for keyword in capability.keywords:
            if keyword in question:
                # Exact word match gets bonus
                if re.search(r'\b' + re.escape(keyword) + r'\b', question):
                    keyword_matches += 1.5
                else:
                    keyword_matches += 1
        
        keyword_score = (keyword_matches / len(capability.keywords)) * capability.weight
        
        # Pattern matching
        pattern_matches = 0
        for pattern in capability.patterns:
            if re.search(pattern, question, re.IGNORECASE):
                pattern_matches += 1
        
        pattern_score = (pattern_matches / max(len(capability.patterns), 1)) * capability.weight * 1.2
        
        score = keyword_score + pattern_score
        return min(score, 1.0)
    
    def _calculate_context_bonus(self, agent_type: AgentType, context: Dict) -> float:
        """Add bonus score based on dataset context"""
        bonus = 0.0
        
        table_name = context.get('table_name', '').lower()
        dataset_name = context.get('dataset_name', '').lower()
        description = context.get('description', '').lower()
        
        # Context keywords for each agent type
        context_mappings = {
            AgentType.SALES_ANALYST: [
                'sales', 'ban_hang', 'doanh_thu', 'orders', 'don_hang', 
                'products', 'san_pham', 'revenue'
            ],
            AgentType.CUSTOMER_ANALYST: [
                'customers', 'khach_hang', 'users', 'nguoi_dung', 'clients'
            ],
            AgentType.HR_ANALYST: [
                'employees', 'nhan_vien', 'staff', 'hr', 'luong', 'salary',
                'phong_ban', 'department'
            ],
            AgentType.FINANCIAL_ANALYST: [
                'finance', 'tai_chinh', 'accounting', 'ke_toan', 'budget', 
                'ngan_sach', 'cost', 'chi_phi'
            ],
            AgentType.TECHNICAL_ANALYST: [
                'system', 'he_thong', 'technical', 'ky_thuat', 'config',
                'cau_hinh', 'logs', 'nhat_ky'
            ]
        }
        
        if agent_type in context_mappings:
            context_keywords = context_mappings[agent_type]
            for keyword in context_keywords:
                if (keyword in table_name or 
                    keyword in dataset_name or 
                    keyword in description):
                    bonus += 0.3
                    break  # Only one bonus per agent
        
        return min(bonus, 0.5)
    
    def get_agent_suggestions(self, question: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Get top N agent suggestions with confidence scores"""
        question_lower = question.lower()
        suggestions = []
        
        for agent_type, capability in self.agent_capabilities.items():
            score = self._calculate_agent_score(question_lower, capability)
            
            # Determine confidence level
            if score > 0.7:
                confidence = "high"
            elif score > 0.4:
                confidence = "medium"
            else:
                confidence = "low"
            
            suggestions.append({
                'agent': agent_type.value,
                'score': round(score, 3),
                'description': capability.description,
                'confidence': confidence
            })
        
        # Sort by score and return top N
        return sorted(suggestions, key=lambda x: x['score'], reverse=True)[:top_n]

# Global router instance
agent_router = AgentRouter()