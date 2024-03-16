from blinker import signal

# Define the signals at the top level of the module
entity_created = signal('entity-created')
entity_updated = signal('entity-updated')
entity_deleted = signal('entity-deleted')
