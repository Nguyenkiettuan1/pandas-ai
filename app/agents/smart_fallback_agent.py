#!/usr/bin/env python3
"""
Smart fallback agent that can handle common queries without LLM
"""
import re
import pandas as pd
from typing import Dict, Any, Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class SmartFallbackAgent:
    """Agent that handles common queries using pattern matching and pandas operations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize query patterns and their handlers"""
        return {
            # Row count patterns
            'row_count': {
                'patterns': [
                    r'how many rows?',
                    r'number of rows',
                    r'count.*rows?',
                    r'tổng.*số.*dòng',
                    r'có bao nhiêu.*dòng',
                    r'dataset.*size'
                ],
                'handler': self._handle_row_count
            },
            
            # Employee count patterns
            'employee_count': {
                'patterns': [
                    r'how many employees?',
                    r'number of employees',
                    r'tổng.*số.*nhân viên',
                    r'có bao nhiêu.*nhân viên',
                    r'count.*employees?'
                ],
                'handler': self._handle_employee_count
            },
            
            # Employee list patterns
            'employee_list': {
                'patterns': [
                    r'(\d+).*nhân viên.*mã số',
                    r'(\d+).*employees?.*ids?',
                    r'first.*(\d+).*employees?',
                    r'show.*(\d+).*employees?',
                    r'list.*employees?'
                ],
                'handler': self._handle_employee_list
            },
            
            # Column names
            'column_names': {
                'patterns': [
                    r'column names?',
                    r'what.*columns?',
                    r'field names?',
                    r'tên.*cột',
                    r'các.*trường'
                ],
                'handler': self._handle_column_names
            },
            
            # Employee names
            'employee_names': {
                'patterns': [
                    r'employee names?',
                    r'show.*names?',
                    r'tên.*nhân viên',
                    r'danh sách.*tên'
                ],
                'handler': self._handle_employee_names
            },
            
            # Gender counts
            'gender_count': {
                'patterns': [
                    r'nhân viên nam',
                    r'male employees?',
                    r'men.*count',
                    r'số.*nam',
                    r'nhân viên nữ',
                    r'female employees?',
                    r'women.*count',
                    r'số.*nữ'
                ],
                'handler': self._handle_gender_count
            },
            
            # Salary statistics
            'salary_stats': {
                'patterns': [
                    r'average.*salary',
                    r'mean.*salary',
                    r'lương.*trung bình',
                    r'mức lương.*trung bình',
                    r'highest.*salary',
                    r'max.*salary',
                    r'lương.*cao nhất',
                    r'lowest.*salary',
                    r'min.*salary',
                    r'lương.*thấp nhất'
                ],
                'handler': self._handle_salary_stats
            },
            
            # Department info
            'department_info': {
                'patterns': [
                    r'departments?',
                    r'phong ban',
                    r'divisions?',
                    r'teams?'
                ],
                'handler': self._handle_department_info
            }
        }
    
    def can_handle(self, question: str) -> bool:
        """Check if this agent can handle the question"""
        question_lower = question.lower()
        for category_data in self.patterns.values():
            for pattern in category_data['patterns']:
                if re.search(pattern, question_lower):
                    return True
        return False
    
    def process_question(self, question: str) -> str:
        """Process a question and return the result"""
        question_lower = question.lower()
        
        # Find matching pattern
        for category, category_data in self.patterns.items():
            for pattern in category_data['patterns']:
                match = re.search(pattern, question_lower)
                if match:
                    logger.info(f"Matched pattern '{pattern}' for category '{category}'")
                    try:
                        result = category_data['handler'](question, match)
                        return f"[Smart Analysis] {result}"
                    except Exception as e:
                        logger.error(f"Error in handler for {category}: {e}")
                        continue
        
        # If no pattern matches, provide general info
        return self._handle_general_info(question)
    
    def _handle_row_count(self, question: str, match: re.Match) -> str:
        """Handle row count questions"""
        count = len(self.df)
        return f"There are {count} rows in the dataset."
    
    def _handle_employee_count(self, question: str, match: re.Match) -> str:
        """Handle employee count questions"""
        count = len(self.df)
        return f"There are {count} employees in the dataset."
    
    def _handle_employee_list(self, question: str, match: re.Match) -> str:
        """Handle employee list questions"""
        # Try to extract number from question
        num_employees = 3  # default
        if match.groups():
            try:
                num_employees = int(match.group(1))
            except (ValueError, AttributeError):
                pass
        
        # Limit to reasonable number
        num_employees = min(num_employees, len(self.df))
        
        employees = self.df[['ma_nv', 'ho_ten']].head(num_employees)
        result = f"First {num_employees} employees and their IDs:\n"
        result += employees.to_string(index=False)
        return result
    
    def _handle_column_names(self, question: str, match: re.Match) -> str:
        """Handle column names questions"""
        columns = list(self.df.columns)
        return f"Column names: {', '.join(columns)}"
    
    def _handle_employee_names(self, question: str, match: re.Match) -> str:
        """Handle employee names questions"""
        names = self.df['ho_ten'].head(10).tolist()
        return f"Employee names:\n" + "\n".join(f"- {name}" for name in names)
    
    def _handle_gender_count(self, question: str, match: re.Match) -> str:
        """Handle gender count questions"""
        if 'nam' in question.lower() or 'male' in question.lower() or 'men' in question.lower():
            count = len(self.df[self.df['gioi_tinh'] == 'Nam'])
            return f"Total male employees: {count}"
        elif 'nữ' in question.lower() or 'female' in question.lower() or 'women' in question.lower():
            count = len(self.df[self.df['gioi_tinh'] == 'Nữ'])
            return f"Total female employees: {count}"
        else:
            male_count = len(self.df[self.df['gioi_tinh'] == 'Nam'])
            female_count = len(self.df[self.df['gioi_tinh'] == 'Nữ'])
            return f"Gender distribution: {male_count} male, {female_count} female employees"
    
    def _handle_salary_stats(self, question: str, match: re.Match) -> str:
        """Handle salary statistics questions"""
        if 'average' in question.lower() or 'mean' in question.lower() or 'trung bình' in question.lower():
            avg_salary = self.df['luong'].mean()
            return f"Average salary: {avg_salary:,.0f} VND"
        elif 'highest' in question.lower() or 'max' in question.lower() or 'cao nhất' in question.lower():
            max_salary = self.df['luong'].max()
            return f"Highest salary: {max_salary:,.0f} VND"
        elif 'lowest' in question.lower() or 'min' in question.lower() or 'thấp nhất' in question.lower():
            min_salary = self.df['luong'].min()
            return f"Lowest salary: {min_salary:,.0f} VND"
        else:
            stats = self.df['luong'].describe()
            return f"Salary statistics:\n- Average: {stats['mean']:,.0f} VND\n- Min: {stats['min']:,.0f} VND\n- Max: {stats['max']:,.0f} VND"
    
    def _handle_department_info(self, question: str, match: re.Match) -> str:
        """Handle department information questions"""
        departments = self.df['phong_ban'].value_counts()
        result = "Department distribution:\n"
        for dept, count in departments.items():
            result += f"- {dept}: {count} employees\n"
        return result.strip()
    
    def _handle_general_info(self, question: str) -> str:
        """Handle general questions with dataset overview"""
        row_count = len(self.df)
        col_count = len(self.df.columns)
        
        result = f"Dataset Overview:\n"
        result += f"- {row_count} employees\n"
        result += f"- {col_count} data fields\n"
        result += f"- Departments: {', '.join(self.df['phong_ban'].unique())}\n"
        result += f"- Average salary: {self.df['luong'].mean():,.0f} VND\n"
        result += f"\nFor specific questions, try asking about:\n"
        result += f"- Employee counts, names, or IDs\n"
        result += f"- Salary statistics\n"
        result += f"- Department information\n"
        result += f"- Gender distribution"
        
        return result
