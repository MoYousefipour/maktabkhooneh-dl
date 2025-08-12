class MaktabDownloaderError(Exception):
    """Base exception for MaktabDownloader errors."""
    pass

class NotAuthenticatedError(MaktabDownloaderError):
    """Exception raised when authentication fails."""
    pass
