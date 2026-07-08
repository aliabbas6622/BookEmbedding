"""
Pipeline stage base class
All pipeline stages must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StageStatus(Enum):
    """Status of a pipeline stage"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a pipeline stage execution"""
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class PipelineContext:
    """Context passed between pipeline stages"""
    session_id: str
    config: Dict[str, Any]
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get data from context"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set data in context"""
        self.data[key] = value
    
    def add_error(self, error: str):
        """Add an error to the context"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0


class PipelineStage(ABC):
    """Abstract base class for pipeline stages"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return stage name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return stage description"""
        pass
    
    @property
    def required_inputs(self) -> List[str]:
        """Return list of required input keys"""
        return []
    
    @property
    def optional_inputs(self) -> List[str]:
        """Return list of optional input keys"""
        return []
    
    @property
    def outputs(self) -> List[str]:
        """Return list of output keys this stage produces"""
        return []
    
    @abstractmethod
    def execute(self, context: PipelineContext) -> StageResult:
        """
        Execute the pipeline stage
        
        Args:
            context: Pipeline context with input data
            
        Returns:
            StageResult with execution status and output data
        """
        pass
    
    def validate_inputs(self, context: PipelineContext) -> bool:
        """Validate that required inputs are present"""
        for input_key in self.required_inputs:
            if input_key not in context.data:
                return False
        return True
    
    def cleanup(self, context: PipelineContext):
        """Cleanup resources after stage execution"""
        pass
