"""Domain exceptions for IRR Analytics Terminal."""


class CashFlowError(ValueError):
    """Raised when cash-flow input cannot be analyzed."""


class UploadError(CashFlowError):
    """Raised when an uploaded cash-flow file cannot be normalized."""
