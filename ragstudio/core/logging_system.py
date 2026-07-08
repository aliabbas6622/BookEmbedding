"""
Structured logging system for RAG Studio
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys


class StructuredLogger:
    """Structured JSON logger for RAG Studio"""
    
    def __init__(self, name: str, log_dir: Optional[str] = None, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with structured output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
        
        # File handler for JSON logs
        if log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = self.log_dir / f"{name}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """Log a structured message"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": logging.getLevelName(level),
            "message": message,
            **kwargs
        }
        
        # Log the message
        self.logger.log(level, json.dumps(log_entry))
        
        return log_entry
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        return self._log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        return self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        return self._log_structured(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        return self._log_structured(logging.DEBUG, message, **kwargs)
    
    def stage_log(
        self,
        pipeline_id: str,
        stage_name: str,
        action: str,
        status: str = "info",
        **kwargs
    ):
        """Log a pipeline stage event"""
        level_map = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "success": logging.INFO
        }
        
        return self._log_structured(
            level_map.get(status, logging.INFO),
            f"[{stage_name}] {action}",
            pipeline_id=pipeline_id,
            stage_name=stage_name,
            action=action,
            status=status,
            **kwargs
        )
    
    def job_log(
        self,
        job_id: str,
        document_id: int,
        action: str,
        status: str = "info",
        **kwargs
    ):
        """Log a job event"""
        level_map = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "success": logging.INFO
        }
        
        return self._log_structured(
            level_map.get(status, logging.INFO),
            f"[Job {job_id}] {action}",
            job_id=job_id,
            document_id=document_id,
            action=action,
            status=status,
            **kwargs
        )


class LogFilter:
    """Filter and search through logs"""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
    
    def search_logs(
        self,
        log_file: str,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        contains: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs with filters"""
        results = []
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            return results
        
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                
                # Apply filters
                if level and entry.get("level") != level:
                    continue
                
                if start_time:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time < start_time:
                        continue
                
                if end_time:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time > end_time:
                        continue
                
                if contains and contains.lower() not in entry.get("message", "").lower():
                    continue
                
                if pipeline_id and entry.get("pipeline_id") != pipeline_id:
                    continue
                
                if stage_name and entry.get("stage_name") != stage_name:
                    continue
                
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_stage_history(
        self,
        pipeline_id: str,
        stage_name: str
    ) -> List[Dict[str, Any]]:
        """Get history for a specific stage in a pipeline"""
        results = []
        
        # Search all log files
        for log_file in self.log_dir.glob("*.log"):
            entries = self.search_logs(
                log_file.name,
                pipeline_id=pipeline_id,
                stage_name=stage_name,
                limit=1000
            )
            results.extend(entries)
        
        # Sort by timestamp
        results.sort(key=lambda x: x.get("timestamp", ""))
        
        return results
    
    def export_logs(
        self,
        log_file: str,
        output_path: str,
        **filters
    ) -> int:
        """Export filtered logs to a file"""
        entries = self.search_logs(log_file, **filters, limit=10000)
        
        with open(output_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        
        return len(entries)


# Global logger instance
_default_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "ragstudio", log_dir: Optional[str] = None) -> StructuredLogger:
    """Get or create a logger instance"""
    global _default_logger
    
    if _default_logger is None:
        _default_logger = StructuredLogger(name, log_dir)
    
    return _default_logger
