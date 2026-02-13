set dotenv-load := true
set fallback := true
set positional-arguments := true

# cli

# CLI entrypoint
@cli *args:
  postgres-cli {{args}}

# Initialize a new repository
@init *args:
  init {{args}}

# Backup a database cluster
@backup *args:
  backup {{args}}

# Copy snapshots
@copy *args:
  copy {{args}}

# Remove snapshots
@forget *args:
  forget {{args}}

# Extract data from a snapshot
@restore *args:
  restore {{args}}

# List all snapshots
@snapshots *args:
  restore {{args}}

# Remove stale locks
@unlock *args:
  unlock {{args}}
