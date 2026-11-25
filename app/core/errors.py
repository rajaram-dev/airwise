"""Domain exceptions. HTTP mapping is added in the API layer."""


class AirWiseError(Exception):
    """Base class for all AirWise domain errors."""


class AirDataUnavailableError(AirWiseError):
    """Raised when air quality data cannot be fetched or parsed."""


class LocationNotFoundError(AirWiseError):
    """Raised when a location search returns no results."""


class AIUnavailableError(AirWiseError):
    """Raised when the AI service fails, times out or returns invalid output."""
