import yaml
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class AgentProfile:
    """Agent profile configuration"""
    name: str
    description: str
    version: str
    created_by: str
    created_date: str
    config: Dict[str, Any]
    capabilities: List[str]
    supported_data_types: List[str]
    tools: List[Dict[str, Any]]
    example_prompts: List[str]
    error_handling: Dict[str, Any]
    domain_knowledge: Optional[Dict[str, Any]] = None
    specialized_functions: Optional[List[str]] = None
    financial_ratios: Optional[Dict[str, Any]] = None
    compliance_standards: Optional[List[str]] = None
    security: Optional[Dict[str, Any]] = None

class AgentProfileManager:
    """Manager for loading and managing agent profiles"""
    
    def __init__(self, profiles_dir: str = "app/agents/profile_agent"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles: Dict[str, AgentProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all agent profiles from YAML files"""
        logger.info(f"Loading agent profiles from {self.profiles_dir}")
        
        if not self.profiles_dir.exists():
            logger.warning(f"Profiles directory {self.profiles_dir} does not exist")
            return
        
        yaml_files = list(self.profiles_dir.glob("*.yaml")) + list(self.profiles_dir.glob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as file:
                    profile_data = yaml.safe_load(file)
                
                profile = AgentProfile(**profile_data)
                self.profiles[profile.name] = profile
                
                logger.info(f"Loaded profile: {profile.name} v{profile.version}")
                
            except Exception as e:
                logger.error(f"Failed to load profile from {yaml_file}: {e}")
    
    def get_profile(self, name: str) -> Optional[AgentProfile]:
        """Get an agent profile by name"""
        profile = self.profiles.get(name)
        if not profile:
            logger.warning(f"Profile '{name}' not found")
        return profile
    
    def list_profiles(self) -> List[str]:
        """List all available profile names"""
        return list(self.profiles.keys())
    
    def get_profile_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get profile information summary"""
        profile = self.get_profile(name)
        if not profile:
            return None
        
        return {
            "name": profile.name,
            "description": profile.description,
            "version": profile.version,
            "capabilities": profile.capabilities,
            "supported_data_types": profile.supported_data_types,
            "tools_count": len(profile.tools),
            "example_prompts_count": len(profile.example_prompts)
        }
    
    def get_suitable_profiles(self, data_type: str) -> List[str]:
        """Get profiles suitable for a specific data type"""
        suitable_profiles = []
        
        for name, profile in self.profiles.items():
            if data_type.lower() in [dt.lower() for dt in profile.supported_data_types]:
                suitable_profiles.append(name)
        
        return suitable_profiles
    
    def validate_profile(self, profile: AgentProfile) -> bool:
        """Validate a profile configuration"""
        required_fields = ['name', 'description', 'config', 'capabilities', 'tools']
        
        for field in required_fields:
            if not hasattr(profile, field) or not getattr(profile, field):
                logger.error(f"Profile validation failed: missing {field}")
                return False
        
        # Validate tools
        for tool in profile.tools:
            if 'name' not in tool or 'description' not in tool:
                logger.error(f"Invalid tool configuration in profile {profile.name}")
                return False
        
        return True
    
    def reload_profiles(self):
        """Reload all profiles from disk"""
        logger.info("Reloading agent profiles")
        self.profiles.clear()
        self._load_profiles()

# Global profile manager instance
profile_manager = AgentProfileManager()
