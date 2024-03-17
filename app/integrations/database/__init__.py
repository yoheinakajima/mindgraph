import os

from .memory import InMemoryDatabase
from .nexus import NexusDBIntegration

db_type = os.getenv("DATABASE_TYPE", "memory").lower()

if db_type == "nexusdb":
  CurrentDBIntegration = NexusDBIntegration
elif db_type == "memory":
  CurrentDBIntegration = InMemoryDatabase