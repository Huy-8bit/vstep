class AppError(Exception):
    def __init__(self, status: int, message: str, code: str = "application_error"):
        self.status = status
        self.message = message
        self.code = code
