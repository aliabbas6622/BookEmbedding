"""
Frontend Navigation & Routing System
Handles all page transitions, route guards, and navigation state
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PageType(Enum):
    """Types of pages in the application"""
    DASHBOARD = "dashboard"
    UPLOAD = "upload"
    PIPELINE = "pipeline"
    DOCUMENTS = "documents"
    CHUNKS = "chunks"
    EMBEDDINGS = "embeddings"
    VECTOR_INDEX = "vector_index"
    SETTINGS = "settings"
    API_SETTINGS = "api_settings"
    RAG_PLAYGROUND = "rag_playground"
    PROVIDERS = "providers"
    MONITORING = "monitoring"
    HELP = "help"


@dataclass
class RouteConfig:
    """Configuration for a single route"""
    path: str
    page_type: PageType
    title: str
    icon: str
    description: str
    requires_auth: bool = True
    requires_active_pipeline: bool = False
    requires_document: bool = False
    parent_route: Optional[str] = None
    children: List[str] = field(default_factory=list)
    allowed_roles: List[str] = field(default_factory=lambda: ["admin", "user"])
    query_params: List[str] = field(default_factory=list)
    default_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationState:
    """Current navigation state"""
    current_page: PageType
    current_path: str
    previous_page: Optional[PageType] = None
    previous_path: Optional[str] = None
    history: List[str] = field(default_factory=list)
    breadcrumbs: List[Dict[str, str]] = field(default_factory=list)
    query_params: Dict[str, Any] = field(default_factory=dict)
    path_params: Dict[str, Any] = field(default_factory=dict)


class NavigationManager:
    """
    Manages navigation between pages, route validation, and state tracking
    """
    
    def __init__(self):
        self.routes: Dict[str, RouteConfig] = {}
        self.page_routes: Dict[PageType, str] = {}
        self.navigation_state: Optional[NavigationState] = None
        self.route_guards: Dict[str, List[Callable]] = {}
        self._initialize_routes()
    
    def _initialize_routes(self):
        """Initialize all application routes"""
        
        # Dashboard
        self.add_route(RouteConfig(
            path="/",
            page_type=PageType.DASHBOARD,
            title="Dashboard",
            icon="📊",
            description="Overview of documents, pipelines, and system status",
            requires_auth=True
        ))
        
        # Upload
        self.add_route(RouteConfig(
            path="/upload",
            page_type=PageType.UPLOAD,
            title="Upload Documents",
            icon="📤",
            description="Upload and validate PDF documents",
            requires_auth=True,
            query_params=["auto_start"]
        ))
        
        # Pipeline Management
        self.add_route(RouteConfig(
            path="/pipeline",
            page_type=PageType.PIPELINE,
            title="Pipeline Management",
            icon="⚙️",
            description="Configure and monitor document processing pipelines",
            requires_auth=True,
            query_params=["document_id", "session_id"]
        ))
        
        self.add_route(RouteConfig(
            path="/pipeline/monitor",
            page_type=PageType.MONITORING,
            title="Pipeline Monitoring",
            icon="📈",
            description="Real-time monitoring of pipeline execution",
            requires_auth=True,
            requires_active_pipeline=True,
            parent_route="/pipeline",
            query_params=["session_id"]
        ))
        
        # Documents
        self.add_route(RouteConfig(
            path="/documents",
            page_type=PageType.DOCUMENTS,
            title="Documents Library",
            icon="📚",
            description="Browse and manage processed documents",
            requires_auth=True
        ))
        
        self.add_route(RouteConfig(
            path="/documents/{document_id}",
            page_type=PageType.DOCUMENTS,
            title="Document Details",
            icon="📄",
            description="View document details and metadata",
            requires_auth=True,
            requires_document=True,
            parent_route="/documents",
            query_params=["view_mode"]
        ))
        
        self.add_route(RouteConfig(
            path="/documents/{document_id}/chunks",
            page_type=PageType.CHUNKS,
            title="Document Chunks",
            icon="🔪",
            description="View and manage text chunks",
            requires_auth=True,
            requires_document=True,
            parent_route="/documents/{document_id}",
            query_params=["page", "limit", "search"]
        ))
        
        self.add_route(RouteConfig(
            path="/documents/{document_id}/embeddings",
            page_type=PageType.EMBEDDINGS,
            title="Embeddings",
            icon="🔢",
            description="View embedding vectors and statistics",
            requires_auth=True,
            requires_document=True,
            parent_route="/documents/{document_id}",
            query_params=["embedding_provider", "dimensionality"]
        ))
        
        # Vector Index
        self.add_route(RouteConfig(
            path="/vector-index",
            page_type=PageType.VECTOR_INDEX,
            title="Vector Index",
            icon="🗂️",
            description="Manage vector indexes and configurations",
            requires_auth=True
        ))
        
        self.add_route(RouteConfig(
            path="/vector-index/{index_id}",
            page_type=PageType.VECTOR_INDEX,
            title="Index Details",
            icon="📋",
            description="View index details and statistics",
            requires_auth=True,
            parent_route="/vector-index",
            query_params=["view_metrics"]
        ))
        
        # Settings
        self.add_route(RouteConfig(
            path="/settings",
            page_type=PageType.SETTINGS,
            title="General Settings",
            icon="🔧",
            description="Application configuration and preferences",
            requires_auth=True,
            allowed_roles=["admin"]
        ))
        
        self.add_route(RouteConfig(
            path="/settings/api",
            page_type=PageType.API_SETTINGS,
            title="API & Provider Settings",
            icon="🔌",
            description="Configure API keys and provider settings",
            requires_auth=True,
            parent_route="/settings",
            allowed_roles=["admin"]
        ))
        
        # RAG Playground
        self.add_route(RouteConfig(
            path="/rag-playground",
            page_type=PageType.RAG_PLAYGROUND,
            title="RAG Playground",
            icon="🎮",
            description="Test and evaluate RAG retrieval and generation",
            requires_auth=True,
            query_params=["conversation_id", "model_comparison"]
        ))
        
        self.add_route(RouteConfig(
            path="/rag-playground/chat/{conversation_id}",
            page_type=PageType.RAG_PLAYGROUND,
            title="Chat Session",
            icon="💬",
            description="Continue chat conversation",
            requires_auth=True,
            parent_route="/rag-playground"
        ))
        
        # Providers
        self.add_route(RouteConfig(
            path="/providers",
            page_type=PageType.PROVIDERS,
            title="Provider Management",
            icon="🔗",
            description="Configure and test external providers",
            requires_auth=True,
            allowed_roles=["admin"],
            query_params=["provider_type", "test_connection"]
        ))
        
        # Help
        self.add_route(RouteConfig(
            path="/help",
            page_type=PageType.HELP,
            title="Help & Documentation",
            icon="❓",
            description="User guides and API documentation",
            requires_auth=False
        ))
    
    def add_route(self, config: RouteConfig):
        """Add a new route configuration"""
        self.routes[config.path] = config
        self.page_routes[config.page_type] = config.path
        logger.info(f"Registered route: {config.path} -> {config.page_type.value}")
    
    def add_route_guard(self, path: str, guard_func: Callable):
        """Add a guard function to a route"""
        if path not in self.route_guards:
            self.route_guards[path] = []
        self.route_guards[path].append(guard_func)
    
    def navigate(self, path: str, params: Optional[Dict] = None, 
                 query_params: Optional[Dict] = None) -> bool:
        """
        Navigate to a new page
        
        Args:
            path: Route path (can include path parameters)
            params: Path parameters (e.g., document_id)
            query_params: Query string parameters
            
        Returns:
            True if navigation successful, False otherwise
        """
        params = params or {}
        query_params = query_params or {}
        
        # Find matching route
        route_config = self._match_route(path)
        if not route_config:
            logger.error(f"No route found for path: {path}")
            return False
        
        # Execute route guards
        if not self._execute_guards(route_config.path, params, query_params):
            logger.warning(f"Route guards failed for: {path}")
            return False
        
        # Validate requirements
        if not self._validate_requirements(route_config, params, query_params):
            logger.warning(f"Route requirements not met for: {path}")
            return False
        
        # Update navigation state
        self._update_state(route_config, path, params, query_params)
        
        logger.info(f"Navigated to: {path} ({route_config.page_type.value})")
        return True
    
    def _match_route(self, path: str) -> Optional[RouteConfig]:
        """Match a path to a route configuration"""
        # Exact match
        if path in self.routes:
            return self.routes[path]
        
        # Pattern match for dynamic routes
        for route_path, config in self.routes.items():
            if self._match_dynamic_route(route_path, path):
                return config
        
        return None
    
    def _match_dynamic_route(self, pattern: str, path: str) -> bool:
        """Check if path matches a dynamic route pattern"""
        pattern_parts = pattern.split('/')
        path_parts = path.split('/')
        
        if len(pattern_parts) != len(path_parts):
            return False
        
        for p_pattern, p_path in zip(pattern_parts, path_parts):
            if p_pattern.startswith('{') and p_pattern.endswith('}'):
                continue  # Dynamic parameter
            if p_pattern != p_path:
                return False
        
        return True
    
    def _execute_guards(self, path: str, params: Dict, query_params: Dict) -> bool:
        """Execute all guard functions for a route"""
        guards = self.route_guards.get(path, [])
        
        for guard in guards:
            try:
                if not guard(params, query_params):
                    return False
            except Exception as e:
                logger.error(f"Guard execution failed: {e}")
                return False
        
        return True
    
    def _validate_requirements(self, config: RouteConfig, 
                               params: Dict, query_params: Dict) -> bool:
        """Validate route requirements"""
        # Check document requirement
        if config.requires_document:
            if 'document_id' not in params and 'document_id' not in query_params:
                logger.warning("Document ID required but not provided")
                return False
        
        # Check active pipeline requirement
        if config.requires_active_pipeline:
            if 'session_id' not in params and 'session_id' not in query_params:
                logger.warning("Active pipeline session required")
                return False
        
        return True
    
    def _update_state(self, config: RouteConfig, path: str, 
                      params: Dict, query_params: Dict):
        """Update navigation state"""
        previous_state = self.navigation_state
        
        # Build breadcrumbs
        breadcrumbs = self._build_breadcrumbs(config)
        
        # Create new state
        self.navigation_state = NavigationState(
            current_page=config.page_type,
            current_path=path,
            previous_page=previous_state.current_page if previous_state else None,
            previous_path=previous_state.current_path if previous_state else None,
            history=(previous_state.history + [previous_state.current_path] 
                    if previous_state else []),
            breadcrumbs=breadcrumbs,
            query_params=query_params,
            path_params=params
        )
    
    def _build_breadcrumbs(self, config: RouteConfig) -> List[Dict[str, str]]:
        """Build breadcrumb trail for current route"""
        breadcrumbs = []
        
        # Add dashboard
        dashboard_route = self.page_routes.get(PageType.DASHBOARD, "/")
        breadcrumbs.append({
            "label": "Dashboard",
            "path": dashboard_route
        })
        
        # Add parent routes
        current_parent = config.parent_route
        while current_parent:
            parent_config = self.routes.get(current_parent)
            if parent_config:
                breadcrumbs.insert(1, {
                    "label": parent_config.title,
                    "path": current_parent
                })
                current_parent = parent_config.parent_route
            else:
                break
        
        # Add current route
        breadcrumbs.append({
            "label": config.title,
            "path": config.path
        })
        
        return breadcrumbs
    
    def get_current_state(self) -> Optional[NavigationState]:
        """Get current navigation state"""
        return self.navigation_state
    
    def go_back(self) -> bool:
        """Navigate to previous page"""
        if not self.navigation_state or not self.navigation_state.previous_path:
            return False
        
        return self.navigate(self.navigation_state.previous_path)
    
    def get_available_routes(self, page_type: Optional[PageType] = None) -> List[RouteConfig]:
        """Get list of available routes, optionally filtered by page type"""
        if page_type:
            return [r for r in self.routes.values() if r.page_type == page_type]
        return list(self.routes.values())
    
    def get_child_routes(self, parent_path: str) -> List[RouteConfig]:
        """Get all child routes of a parent route"""
        return [r for r in self.routes.values() if r.parent_route == parent_path]
    
    def build_url(self, path: str, params: Optional[Dict] = None,
                  query_params: Optional[Dict] = None) -> str:
        """Build a complete URL with parameters"""
        params = params or {}
        query_params = query_params or {}
        
        # Replace path parameters
        url = path
        for key, value in params.items():
            url = url.replace(f"{{{key}}}", str(value))
        
        # Add query parameters
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            url = f"{url}?{query_string}"
        
        return url


# Global navigation manager instance
navigation_manager = NavigationManager()


def get_navigation_manager() -> NavigationManager:
    """Get the global navigation manager instance"""
    return navigation_manager
