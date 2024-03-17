import os

from .memory import InMemoryDatabase
from .nexus import NexusDBIntegration
from .nebulagraph import NebulaGraphIntegration

db_type = os.getenv("DATABASE_TYPE", "memory").lower()

if db_type == "nexusdb":
  CurrentDBIntegration = NexusDBIntegration
elif db_type == "nebulagraph":
  CurrentDBIntegration = NebulaGraphIntegration
else:
  CurrentDBIntegration = InMemoryDatabase
