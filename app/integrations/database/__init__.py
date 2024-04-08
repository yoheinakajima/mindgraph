import os

from .memory import InMemoryDatabase
from .nexus import NexusDBIntegration
from .nebulagraph import NebulaGraphIntegration
from .falkordb import FalkorDBIntegration
from .neo4j import Neo4jDBIntegration

db_type = os.getenv("DATABASE_TYPE", "memory").lower()

if db_type == "nexusdb":
  CurrentDBIntegration = NexusDBIntegration
elif db_type == "nebulagraph":
  CurrentDBIntegration = NebulaGraphIntegration
elif db_type == "falkordb":
  CurrentDBIntegration = FalkorDBIntegration
elif db_type == "neo4j":
  CurrentDBIntegration = Neo4jDBIntegration
else:
  CurrentDBIntegration = InMemoryDatabase
