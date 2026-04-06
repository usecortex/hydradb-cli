# HydraDB CLI

Command line interface for [HydraDB](https://hydradb.com) -- memory, recall, and ingestion from the terminal.

## Setup

**Requirements:** Python 3.10+

```bash
git clone https://github.com/usecortex/hydradb-cli.git
cd hydradb-cli
pip install .
```

Verify it worked:

```bash
hydradb --version
```

Then authenticate with your HydraDB API key and tenant ID:

```bash
hydradb login --api-key YOUR_API_KEY --tenant-id YOUR_TENANT_ID
```

Or use environment variables instead of `login`:

```bash
export HYDRA_DB_API_KEY=your_api_key
export HYDRA_DB_TENANT_ID=your_tenant_id
```

## Commands

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
│   └── delete <id>                Delete a tenant
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

### Authentication

```bash
# Interactive (prompts for API key)
hydradb login --tenant-id my-tenant

# Non-interactive
hydradb login --api-key YOUR_KEY --tenant-id my-tenant

# Check current auth
hydradb whoami

# Logout
hydradb logout
```

### Memories

```bash
# Add a memory
hydradb memories add --text "User prefers dark mode and weekly email summaries"

# Add without inference
hydradb memories add --text "Raw meeting notes..." --no-infer --title "Meeting Notes"

# Add markdown content
hydradb memories add --text "# Preferences\n- Dark mode" --markdown

# List all memories
hydradb memories list

# Delete a memory
hydradb memories delete mem_abc123 --yes
```

### Knowledge Base

```bash
# Upload files
hydradb knowledge upload ./contract.pdf ./notes.docx

# Upload with upsert
hydradb knowledge upload ./updated-report.pdf --upsert

# Upload text directly
hydradb knowledge upload-text --text "Q4 pricing: Starter $29, Pro $79" --title "Pricing"

# Check processing status
hydradb knowledge verify source_abc123

# Delete knowledge sources
hydradb knowledge delete source_abc123 source_def456 --yes
```

### Recall

```bash
# Search knowledge base
hydradb recall full "What did the team say about pricing?"

# Search with thinking mode
hydradb recall full "contract terms" --mode thinking --max-results 20

# Search user memories
hydradb recall preferences "What does the user prefer?"

# Keyword/boolean search
hydradb recall keyword "pricing AND enterprise" --operator and
```

### Fetch & Inspect

```bash
# List sources
hydradb fetch sources
hydradb fetch sources --kind knowledge --page-size 10

# Get content of a source
hydradb fetch content source_abc123

# Get a download URL
hydradb fetch content source_abc123 --mode url

# View graph relations
hydradb fetch relations source_abc123
```

### Tenant Management

```bash
hydradb tenant create my-new-tenant
hydradb tenant monitor
hydradb tenant list-sub-tenants
hydradb tenant delete old-tenant --yes
```

### Configuration

```bash
hydradb config show
hydradb config set tenant_id my-tenant
hydradb config set base_url https://api.hydradb.com
```

Valid keys: `api_key`, `tenant_id`, `sub_tenant_id`, `base_url`

### JSON Output

Every command supports `--output json` (or `-o json`). The flag goes before the subcommand:

```bash
hydradb -o json memories list
hydradb -o json recall full "pricing" | jq '.chunks[0].chunk_content'
```
