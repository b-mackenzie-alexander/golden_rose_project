import os

os.environ.setdefault("GOLDEN_ROSE_ENVIRONMENT", "test")
os.environ.setdefault("GOLDEN_ROSE_AUTH_MODE", "synthetic")
os.environ.setdefault(
    "GOLDEN_ROSE_DATABASE_URL",
    "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
)
os.environ.setdefault(
    "GOLDEN_ROSE_SYNTHETIC_STAFF_ID",
    "22222222-2222-4222-8222-222222222222",
)
