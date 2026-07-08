"""
Pipeline stages base classes
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class PipelineContext:
    """Context object passed between pipeline stages"""
    document_id: int
    pipeline_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value in data"""
        self.data[key] = value
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0


class PipelineStage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Execute the stage logic
        
        Args:
            context: Pipeline context with current state
            
        Returns:
            Updated pipeline context
        """
        pass
    
    async def before_execute(self, context: PipelineContext) -> PipelineContext:
        """Hook called before stage execution"""
        return context
    
    async def after_execute(self, context: PipelineContext) -> PipelineContext:
        """Hook called after stage execution"""
        return context
    
    async def on_error(self, context: PipelineContext, error: Exception) -> PipelineContext:
        """Hook called when an error occurs"""
        context.add_error(f"{self.name}: {str(error)}")
        return context
    
    def validate_config(self) -> bool:
        """Validate stage configuration"""
        return True


@dataclass
class StageResult:
    """Result of a stage execution"""
    success: bool
    stage_name: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
