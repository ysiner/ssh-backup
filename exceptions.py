class AuthenticationError(Exception):
    """Raised when authentication to a device fails."""
    pass

class SSHKeyError(Exception):
    """Raised when there is an issue with SSH key authentication."""
    pass

class DeviceConnectionError(Exception):
    """Raised when connection to a device cannot be established."""
    pass
