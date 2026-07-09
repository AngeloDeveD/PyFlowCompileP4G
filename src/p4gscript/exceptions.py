class P4GScriptError(Exception):
    """Base exception for p4gscript errors."""


class DuplicateNameError(P4GScriptError):
    """Raised when a message, selection, or procedure name is reused."""


class RenderError(P4GScriptError):
    """Raised when a project cannot be rendered safely."""


class CompilerError(P4GScriptError):
    """Raised when AtlusScriptCompiler returns a non-zero exit code."""


class BitAllocationError(P4GScriptError):
    """Raised when the SDK cannot reserve a free bit."""


class SafetyError(P4GScriptError):
    """Raised when a safety policy blocks an operation."""
