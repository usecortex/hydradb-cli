# HydraDB CLI

Agent-friendly command line interface for [HydraDB](https://hydradb.com) -- memory, recall, and ingestion from the terminal.

HydraDB is plug-and-play context infrastructure for AI. The CLI gives agents and developers a lightweight, scriptable interface to all HydraDB operations without MCP setup or server dependencies.

## Why a CLI?

> "Agents are better at using CLIs than MCPs" -- [Composio](https://composio.dev/cli)

- **No server required** -- single `pip install`, ready to use
- **Agent-native** -- JSON output mode for LLM agents and automation
- **Stateless commands** -- every command is deterministic and composable
- **Lightweight** -- no MCP, no Docker, no configuration servers

## Installation

Install from source:

```bash
git clone https://github.com/usecortex/hydradb-cli.git
cd hydradb-cli
pip install -e .
```

Verify the installation:

```bash
hydradb --version
```

## Quick Start

### 1. Authenticate

```bash
# Interactive (prompts for API key)
hydradb login --tenant-id my-tenant

# Non-interactive (for agents and scripts)
hydradb login --api-key YOUR_API_KEY --tenant-id my-tenant

# Or use environment variables (no login needed)
export HYDRA_DB_API_KEY=your_api_key
export HYDRA_DB_TENANT_ID=my-tenant
```

### 2. Add a memory

```bash
hydradb memories add --text "User prefers dark mode and weekly email summaries"
```

### 3. Recall context

```bash
hydradb recall preferences "What does the user prefer?"
```

### 4. Upload knowledge

```bash
hydradb knowledge upload ./report.pdf
```

### 5. Search knowledge

```bash
hydradb recall full "What did the team say about pricing?"
```

## Command Reference

### Authentication

| Command | Description |
|---------|-------------|
| `hydradb login` | Authenticate and save credentials to `~/.hydradb/config.json` |
| `hydradb logout` | Remove stored credentials |
| `hydradb whoami` | Show current auth status and configuration |

```bash
# Login with API key and default tenant
hydradb login --api-key YOUR_KEY --tenant-id my-tenant

# Check who you are
hydradb whoami

# Logout
hydradb logout
```

### Tenant Management

| Command | Description |
|---------|-------------|
| `hydradb tenant create <id>` | Create a new tenant |
| `hydradb tenant monitor [id]` | Get tenant status and statistics |
| `hydradb tenant list-sub-tenants [id]` | List sub-tenant IDs |
| `hydradb tenant delete <id>` | Delete a tenant (irreversible) |

```bash
hydradb tenant create my-new-tenant
hydradb tenant monitor
hydradb tenant list-sub-tenants
hydradb tenant delete old-tenant --yes
```

### User Memories

| Command | Description |
|---------|-------------|
| `hydradb memories add` | Add a user memory |
| `hydradb memories list` | List all user memories |
| `hydradb memories delete <id>` | Delete a memory by ID |

```bash
# Add a memory with inference (default)
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

| Command | Description |
|---------|-------------|
| `hydradb knowledge upload <files...>` | Upload files (PDF, DOCX, TXT, etc.) |
| `hydradb knowledge upload-text` | Upload text content |
| `hydradb knowledge verify <ids...>` | Check processing status |
| `hydradb knowledge delete <ids...>` | Delete knowledge sources |

```bash
# Upload documents
hydradb knowledge upload ./contract.pdf ./notes.docx

# Upload with upsert
hydradb knowledge upload ./updated-report.pdf --upsert

# Upload text content
hydradb knowledge upload-text --text "Q4 pricing: Starter $29, Pro $79, Enterprise $199" --title "Pricing"

# Check if processing is complete
hydradb knowledge verify source_abc123

# Delete knowledge sources
hydradb knowledge delete HydraDoc1234 HydraDoc5678 --yes
```

### Recall (Context Retrieval)

| Command | Description |
|---------|-------------|
| `hydradb recall full <query>` | Search over knowledge base (documents, files) |
| `hydradb recall preferences <query>` | Search over user memories and preferences |
| `hydradb recall keyword <query>` | Deterministic keyword/boolean search |

```bash
# Search knowledge base
hydradb recall full "What did the team say about pricing?"

# Search with thinking mode (deeper graph traversal)
hydradb recall full "contract terms" --mode thinking --max-results 20

# Search user memories
hydradb recall preferences "What does the user prefer?"

# Keyword search with boolean operators
hydradb recall keyword "pricing AND enterprise" --operator and

# Search memories specifically
hydradb recall keyword "John Smith" --operator phrase --search-mode memories
```

### Fetch & Inspect

| Command | Description |
|---------|-------------|
| `hydradb fetch sources` | List all ingested sources |
| `hydradb fetch content <id>` | Fetch full content of a source |
| `hydradb fetch relations <id>` | View knowledge graph relations |

```bash
# List all sources
hydradb fetch sources

# List only knowledge sources
hydradb fetch sources --kind knowledge

# Get full content of a source
hydradb fetch content source_abc123

# Get a presigned URL instead
hydradb fetch content source_abc123 --mode url

# View graph relations
hydradb fetch relations source_abc123
```

### Configuration

| Command | Description |
|---------|-------------|
| `hydradb config show` | Show current configuration |
| `hydradb config set <key> <value>` | Set a configuration value |

```bash
hydradb config show
hydradb config set tenant_id my-tenant
hydradb config set base_url https://api.hydradb.com
```

## JSON Output Mode

Every command supports `--output json` (or `-o json`) for agent and script consumption. The flag must come before the command name.

```bash
# Human-readable (default)
hydradb memories list

# JSON output for agents
hydradb -o json memories list

# Pipe to jq for filtering
hydradb -o json recall full "pricing" | jq '.chunks[0].chunk_content'

# Use in shell scripts
RESULT=$(hydradb -o json recall full "user preferences")
echo "$RESULT" | jq '.chunks | length'
```

You can also set the default output format via environment variable:

```bash
export HYDRADB_OUTPUT=json
hydradb memories list  # now outputs JSON by default
```

## Configuration

### Config File

Credentials and defaults are stored in `~/.hydradb/config.json` (permissions: `600`).

```bash
hydradb config show
```

### Environment Variables

Environment variables always override config file values:

| Variable | Description |
|----------|-------------|
| `HYDRA_DB_API_KEY` | API key (Bearer token) |
| `HYDRA_DB_TENANT_ID` | Default tenant ID |
| `HYDRA_DB_SUB_TENANT_ID` | Default sub-tenant ID |
| `HYDRA_DB_BASE_URL` | API base URL (default: `https://api.hydradb.com`) |
| `HYDRADB_OUTPUT` | Default output format (`human` or `json`) |

### Priority Order

1. Command-line flags (highest)
2. Environment variables
3. Config file (`~/.hydradb/config.json`)
4. Built-in defaults (lowest)

## Agent Integration

The CLI is designed for AI agents (Claude Code, OpenClaw, Codex, etc.) to use directly:

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

### Chaining Commands

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

## Planned Features

- Custom embeddings management (`hydradb embeddings add/recall/filter/delete`)
- Batch operations for bulk memory and knowledge management
- Shell completion installation (`hydradb --install-completion`)

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
