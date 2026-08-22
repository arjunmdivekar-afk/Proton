"""Custom exceptions for Proton."""


class ProtonException(Exception):
    """Base exception for all Proton errors."""
    pass


class ConfigurationError(ProtonException):
    """Raised when configuration is invalid or missing."""
    pass


class ConnectionError(ProtonException):
    """Raised when connecting to a model provider/host fails."""
    pass


class ProviderError(ProtonException):
    """Raised when a model provider returns an error."""
    pass


class SecurityError(ProtonException):
    """Raised when an operation violates security policy or sandbox boundaries."""
    pass


class ToolExecutionError(ProtonException):
    """Raised when a tool execution fails."""
    pass


class ApprovalDeniedError(ProtonException):
    """Raised when user denies approval for a tool or command."""
    pass


class RAGError(ProtonException):
    """Raised when document ingestion or retrieval fails."""
    pass


class PluginError(ProtonException):
    """Raised when plugin loading or execution fails."""
    pass
