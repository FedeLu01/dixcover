class AppError(Exception):
    """Base class for all application-level errors."""
    pass


class DomainError(AppError):
    """Base for domain logic errors."""
    pass

class SubdomainAlreadyExistsError(DomainError):
    def __init__(self, subdomain: str):
        self.subdomain = subdomain
        self.message = f"Subdomain '{subdomain}' already exists."
        super().__init__(self.message)

class InvalidDomainFormatError(DomainError):
    def __init__(self, domain: str):
        self.message = f"The domain '{domain}' has an invalid format."
        super().__init__(self.message)

class ParsingError(DomainError):
    def __init__(self, data) -> None:
        self.message = f"Could't parse data: {data}"
        super().__init__(self.message)



class InfrastructureError(AppError):
    """Base for infrastructure-related errors (DB, API, etc)."""
    pass

class DatabaseConnectionError(InfrastructureError):
    def __init__(self, db_name: str):
        self.message = f"Could not connect to database '{db_name}'"
        super().__init__(self.message)

class ExternalAPIError(InfrastructureError):
    def __init__(self, service: str, detail: str = ""):
        self.message = f"Error with external service '{service}': {detail}"
        super().__init__(self.message)
