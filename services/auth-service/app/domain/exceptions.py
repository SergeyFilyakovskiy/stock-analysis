class AuthServiceError(Exception):
    """Базовое исключение сервиса"""

class UserAlreadyExistsError(AuthServiceError):
    def __init__(self, email: str):
        super().__init__(f"User with email '{email}' already exists")

class UserNotFoundError(AuthServiceError):
    pass

class UserInactiveError(AuthServiceError):
    pass

class InvalidCredentialsError(AuthServiceError):
    pass

class TooManyAttemptsError(AuthServiceError):
    pass

class InvalidTokenError(AuthServiceError):
    pass