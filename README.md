# HydraDB CLI

Agent-friendly command line interface for [HydraDB](https://hydradb.com) -- memory, recall, and ingestion from the terminal.

HydraDB is plug-and-play context infrastructure for AI. The CLI gives agents and developers a lightweight, scriptable interface to all HydraDB operations without MCP setup or server dependencies.

## Prerequisites

- **Python 3.10 or higher** -- check with `python3 --version`
- **pip** -- Python package installer (ships with Python)
- **A HydraDB account** -- sign up at [hydradb.com](https://hydradb.com) to get your API key
- **A tenant ID** -- created during onboarding or via `hydradb tenant create`

## Installation

### From source (recommended for now)

```bash
git clone https://github.com/usecortex/hydradb-cli.git
cd hydradb-cli
pip install .
```

### For development

```bash
git clone https://github.com/usecortex/hydradb-cli.git
cd hydradb-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
```

### Verify the installation

```bash
hydradb --version
# hydradb-cli 0.1.0
```

### Shell completion (optional)

```bash
hydradb --install-completion
```

## Setup

### Step 1: Get your API key

Log in to [hydradb.com](https://hydradb.com) and copy your API key from the dashboard. It starts with `sk_prod_` or `sk_test_`.

### Step 2: Authenticate

```bash
# Interactive (prompts for API key)
hydradb login --tenant-id my-tenant

# Non-interactive (for agents and CI/CD)
hydradb login --api-key sk_prod_YOUR_KEY --tenant-id my-tenant
```

This saves your credentials to `~/.hydradb/config.json` (file permissions `600`).

### Step 3: Verify

```bash
hydradb whoami
```

You should see your tenant ID and a masked API key.

### Alternative: Environment variables (no login needed)

If you prefer not to store credentials on disk, set environment variables instead:

```bash
export HYDRA_DB_API_KEY=sk_prod_YOUR_KEY
export HYDRA_DB_TENANT_ID=my-tenant
```

## Quick Start

```bash
# Store a user preference
hydradb memories add --text "User prefers dark mode and weekly email summaries"

# Recall it later
hydradb recall preferences "What does the user prefer?"

# Upload a document to the knowledge base
hydradb knowledge upload ./report.pdf

# Search the knowledge base
hydradb recall full "What did the team say about pricing?"
```

## Commands

Below is the full command tree. Every command supports `--help` for detailed usage.

```
hydradb
├── login                          Authenticate and save credentials
├── logout                         Remove stored credentials
├── whoami                         Show current auth status
│
├── tenant
│   ├── create <id>                Create a new tenant
│   ├── monitor [id]               Get tenant status and statistics
│   ├── list-sub-tenants [id]      List sub-tenant IDs
│   └── delete <id>                Delete a tenant (irreversible)
│
├── memories
│   ├── add                        Add a user memory
│   ├── list                       List all user memories
│   └── delete <id>                Delete a memory by ID
│
├── knowledge
│   ├── upload <files...>          Upload files (PDF, DOCX, TXT, etc.)
│   ├── upload-text                Upload text content directly
│   ├── verify <ids...>            Check processing status
│   └── delete <ids...>            Delete knowledge sources
│
├── recall
│   ├── full <query>               Search over knowledge base
│   ├── preferences <query>        Search over user memories
│   └── keyword <query>            Keyword/boolean search
│
├── fetch
│   ├── sources                    List all ingested sources
│   ├── content <id>               Fetch full content of a source
│   └── relations <id>             View knowledge graph relations
│
└── config
    ├── show                       Show current configuration
    └── set <key> <value>          Set a configuration value
```

## Command Details

### Authentication

```bash
# Login with API key and tenant
hydradb login --api-key YOUR_KEY --tenant-id my-tenant

# Check current auth
hydradb whoami

# Logout (removes ~/.hydradb/config.json)
hydradb logout
```

### Memories

Store and retrieve user-specific context (preferences, conversations, traits).

```bash
# Add a memory (with inference enabled by default)
hydradb memories add --text "User prefers Nike shoes and runs 5K daily"

# Add without inference
hydradb memories add --text "Raw meeting notes..." --no-infer --title "Meeting Notes"

# Add markdown content
hydradb memories add --text "# Preferences\n- Dark mode\n- Email digest" --markdown

# Pipe content from stdin
echo "User mentioned they love hiking" | hydradb memories add --text -

# List all memories
hydradb memories list

# Delete a specific memory
hydradb memories delete mem_abc123 --yes
```

### Knowledge Base

Ingest documents and text into the searchable knowledge base.

```bash
# Upload files
hydradb knowledge upload ./contract.pdf ./notes.docx

# Upload with upsert (update if source ID exists)
hydradb knowledge upload ./updated-report.pdf --upsert

# Upload text directly
hydradb knowledge upload-text --text "Q4 pricing: Starter $29, Pro $79" --title "Pricing"

# Check processing status
hydradb knowledge verify source_abc123

# Delete knowledge sources
hydradb knowledge delete source_abc123 source_def456 --yes
```

### Recall (Context Retrieval)

Search across your stored memories and knowledge.

```bash
# Search the knowledge base (documents, files)
hydradb recall full "What did the team say about pricing?"

# Use thinking mode for deeper graph traversal
hydradb recall full "contract terms" --mode thinking --max-results 20

# Search user memories and preferences
hydradb recall preferences "What does the user prefer?"

# Keyword search with boolean operators
hydradb recall keyword "pricing AND enterprise" --operator and

# Phrase search over memories
hydradb recall keyword "John Smith" --operator phrase --search-mode memories
```

### Fetch & Inspect

Browse and inspect raw data stored in HydraDB.

```bash
# List all sources
hydradb fetch sources

# List only knowledge sources, paginated
hydradb fetch sources --kind knowledge --page-size 10

# Get full content of a source
hydradb fetch content source_abc123

# Get a presigned download URL instead
hydradb fetch content source_abc123 --mode url

# View knowledge graph relations
hydradb fetch relations source_abc123
```

### Tenant Management

```bash
# Create a new tenant
hydradb tenant create my-new-tenant

# Check tenant status
hydradb tenant monitor

# List sub-tenants
hydradb tenant list-sub-tenants

# Delete a tenant (requires confirmation)
hydradb tenant delete old-tenant --yes
```

### Configuration

```bash
# Show current config (file path, values, sources)
hydradb config show

# Set a config value
hydradb config set tenant_id my-tenant
hydradb config set base_url https://api.hydradb.com
```

Valid config keys: `api_key`, `tenant_id`, `sub_tenant_id`, `base_url`

## JSON Output Mode

Every command supports `--output json` (or `-o json`) for machine-readable output. The flag goes **before** the subcommand:

```bash
# Human-readable (default)
hydradb memories list

# JSON output
hydradb -o json memories list

# Pipe to jq
hydradb -o json recall full "pricing" | jq '.chunks[0].chunk_content'

# Use in shell scripts
RESULT=$(hydradb -o json recall full "user preferences")
echo "$RESULT" | jq '.chunks | length'
```

Set the default output format via environment variable:

```bash
export HYDRADB_OUTPUT=json
hydradb memories list  # now outputs JSON by default
```

## Environment Variables

Environment variables always override config file values:

| Variable | Description |
|----------|-------------|
| `HYDRA_DB_API_KEY` | API key (Bearer token) |
| `HYDRA_DB_TENANT_ID` | Default tenant ID |
| `HYDRA_DB_SUB_TENANT_ID` | Default sub-tenant ID |
| `HYDRA_DB_BASE_URL` | API base URL (default: `https://api.hydradb.com`) |
| `HYDRADB_OUTPUT` | Default output format (`human` or `json`) |

### Configuration priority

1. Command-line flags (highest)
2. Environment variables
3. Config file (`~/.hydradb/config.json`)
4. Built-in defaults (lowest)

## Agent Integration

The CLI is designed for AI agents (Claude Code, Cursor, Codex, etc.) to use directly:

```bash
# Agent workflow: store context, then recall it later
hydradb login --api-key $HYDRA_DB_API_KEY --tenant-id agent-workspace

# Store information
hydradb memories add --text "User wants weekly reports in PDF format"

# Later, recall relevant context
hydradb -o json recall preferences "report format" | jq '.chunks[].chunk_content'

# Upload a document for the knowledge base
hydradb knowledge upload ./spec.pdf

# Search the knowledge base
hydradb -o json recall full "technical requirements" --mode thinking
```

### Chaining commands

```bash
# Upload and verify in sequence
hydradb knowledge upload ./doc.pdf
hydradb knowledge verify $(hydradb -o json knowledge upload ./doc.pdf | jq -r '.results[0].source_id')

# List memories and delete the first one
FIRST_MEM=$(hydradb -o json memories list | jq -r '.user_memories[0].memory_id')
hydradb memories delete "$FIRST_MEM" --yes
```

## Terminology

HydraDB uses specific terminology that the CLI mirrors exactly:

| Term | Meaning |
|------|---------|
| **Tenant** | Top-level organizational unit (like a database) |
| **Sub-tenant** | Isolated collection within a tenant |
| **Memory** | User-specific data (preferences, conversations, traits) |
| **Knowledge** | Document-based data (PDFs, files, text sources) |
| **Recall** | Context retrieval (semantic search + graph traversal) |
| **Full Recall** | Search over knowledge sources |
| **Recall Preferences** | Search over user memories |
| **Boolean Recall** | Deterministic keyword matching |

## Development

```bash
git clone https://github.com/usecortex/hydradb-cli.git
cd hydradb-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest

# Run tests
python -m pytest tests/ -v

# Run the CLI
hydradb --help
```

## Links

- **HydraDB Website:** [hydradb.com](https://hydradb.com)
- **Documentation:** [docs.hydradb.com](https://docs.hydradb.com)
- **Python SDK:** [hydra-db-python on PyPI](https://pypi.org/project/hydra-db-python/)

## License

MIT
