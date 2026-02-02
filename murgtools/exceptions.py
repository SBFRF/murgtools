"""Custom exceptions for murgtools library.

This module defines a hierarchy of exceptions for better error handling
and more descriptive error messages across the murgtools package.
"""


class MurgToolsError(Exception):
    """Base exception for all murgtools errors.

    All custom exceptions in murgtools inherit from this class,
    allowing users to catch all murgtools-specific errors with a single
    except clause if desired.
    """
    pass


class DataNotFoundError(MurgToolsError):
    """Raised when requested data is not available.

    This exception is raised when a data query returns no results,
    such as when requesting data outside the available time range
    or from a non-existent gauge.

    Attributes:
        message (str): Explanation of why data was not found.
    """
    pass


class InvalidGaugeError(MurgToolsError):
    """Raised when an invalid gauge name or number is specified.

    This exception provides helpful information about valid gauge options
    when an invalid gauge identifier is provided.

    Attributes:
        gauge_name: The invalid gauge identifier that was provided.
        valid_gauges: List of valid gauge options (if available).
        message (str): Full error message.

    Examples:
        >>> raise InvalidGaugeError('invalid-gauge', valid_gauges=['waverider-26m', 'waverider-17m'])
        InvalidGaugeError: Invalid gauge: 'invalid-gauge'. Valid options: ['waverider-26m', 'waverider-17m']
    """

    def __init__(self, gauge_name, valid_gauges=None, message=None):
        """Initialize InvalidGaugeError.

        Args:
            gauge_name: The invalid gauge identifier.
            valid_gauges: Optional list/tuple of valid gauge identifiers.
            message: Optional custom message. If not provided, a default
                message is generated from gauge_name and valid_gauges.
        """
        self.gauge_name = gauge_name
        self.valid_gauges = valid_gauges
        if message is None:
            message = f"Invalid gauge: '{gauge_name}'"
            if valid_gauges:
                message += f". Valid options: {valid_gauges}"
        self.message = message
        super().__init__(self.message)


class InvalidTimeRangeError(MurgToolsError):
    """Raised when time range is invalid or contains no data.

    This exception is raised when:
    - Start time is after end time
    - The time range contains no data
    - The time range is outside available data bounds

    Attributes:
        start_time: The start of the requested time range.
        end_time: The end of the requested time range.
        message (str): Explanation of the time range error.
    """

    def __init__(self, message, start_time=None, end_time=None):
        """Initialize InvalidTimeRangeError.

        Args:
            message: Description of the time range error.
            start_time: Optional start time for context.
            end_time: Optional end time for context.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.message = message
        super().__init__(self.message)


class NetworkError(MurgToolsError):
    """Raised when network operations fail.

    This exception wraps network-related errors such as connection failures,
    timeouts, or server errors when accessing THREDDS or other data servers.

    Attributes:
        url (str): The URL that failed (if applicable).
        original_error: The underlying exception that caused the failure.
        message (str): Description of the network error.
    """

    def __init__(self, message, url=None, original_error=None):
        """Initialize NetworkError.

        Args:
            message: Description of the network error.
            url: Optional URL that failed.
            original_error: Optional underlying exception.
        """
        self.url = url
        self.original_error = original_error
        self.message = message
        super().__init__(self.message)


class InvalidParameterError(MurgToolsError):
    """Raised when a function parameter is invalid.

    This exception is raised when a function receives an argument
    that doesn't meet its requirements (wrong type, out of range,
    invalid format, etc.).

    Attributes:
        parameter_name (str): Name of the invalid parameter.
        value: The invalid value that was provided.
        expected: Description of what was expected.
        message (str): Full error message.
    """

    def __init__(self, message, parameter_name=None, value=None, expected=None):
        """Initialize InvalidParameterError.

        Args:
            message: Description of the parameter error.
            parameter_name: Optional name of the invalid parameter.
            value: Optional invalid value that was provided.
            expected: Optional description of expected value/type.
        """
        self.parameter_name = parameter_name
        self.value = value
        self.expected = expected
        self.message = message
        super().__init__(self.message)
