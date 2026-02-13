set dotenv-load := true
set fallback := true
set positional-arguments := true

# cli

# CLI entrypoint
@cli *args:
  postgres-cli {{args}}

# Backup a database cluster
@backup *args:
  backup {{args}}

# Check the configuration
@check *args:
  check {{args}}

# Retrieve information about backups
@info *args:
  info {{args}}

# Restore a database cluster
@restore *args:
  restore {{args}}

# Create the required stanza data
@stanza-create *args:
  stanza-create {{args}}

# Allow pgBackRest processes to run
@start *args:
  start {{args}}

# Stop pgBackRest processes from running
@stop *args:
  stop {{args}}
