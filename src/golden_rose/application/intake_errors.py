class IntakeError(Exception):
    """A value-safe intake failure; never carries submitted fields."""

    def __init__(self, code: str, status: int = 409, *, missing_fields: list[str] | None = None):
        super().__init__(code)
        self.code = code
        self.status = status
        self.missing_fields = missing_fields
