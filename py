[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "alma-platform"
version = "1.0.0"
description = "ALMA Financial Exchange Control Platform"
requires-python = ">=3.9"

# Minimal dependencies for Streamlit Cloud
dependencies = [
    "streamlit>=1.28.0",
    "pandas>=2.0.0",
    "plotly>=5.15.0",
    "python-dotenv>=1.0.0",
]

# Optional database dependencies (only if using database)
[project.optional-dependencies]
database = [
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.28.0", 
    "psycopg2-binary>=2.9.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["alma*", "app*"]