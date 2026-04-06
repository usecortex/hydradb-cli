"""User memory commands: add, list, delete."""

import sys
from typing import Optional

import typer

from hydradb_cli.client import HydraDBClientError
from hydradb_cli.output import print_error, print_result
from hydradb_cli.utils.common import (
    get_client,
    handle_api_error,
    require_tenant_id,
    resolve_sub_tenant_id,
)

app = typer.Typer(help="Manage user memories.")


@app.command()
def add(
    text: Optional[str] = typer.Option(
        None,
        "--text",
        "-t",
        help="Text content to store as a memory. Use '-' to read from stdin.",
    ),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
    infer: bool = typer.Option(
        True,
        "--infer/--no-infer",
        help="Whether HydraDB should extract insights and build knowledge graph.",
    ),
    markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Treat the text as markdown content.",
    ),
    title: Optional[str] = typer.Option(
        None, "--title", help="Optional title for the memory."
    ),
    source_id: Optional[str] = typer.Option(
        None,
        "--source-id",
        help="Source identifier to group related memories.",
    ),
    user_name: Optional[str] = typer.Option(
        None,
        "--user-name",
        help="User name for personalization.",
    ),
    upsert: bool = typer.Option(
        True,
        "--upsert/--no-upsert",
        help="Update existing memories with the same source_id.",
    ),
) -> None:
    """Add a user memory to HydraDB.

    Memories are used by agents for learning about users. HydraDB automatically
    extracts insights, preferences, and builds a knowledge graph from the content.

    Examples:

        hydradb memories add --text "User prefers dark mode" --tenant-id my-tenant

        echo "Meeting notes..." | hydradb memories add --text - --tenant-id my-tenant
    """
    if text is None:
        # Check if stdin has data
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        if not text:
            print_error("No text provided. Use --text or pipe content via stdin.")

    # Handle stdin marker
    if text == "-":
        if sys.stdin.isatty():
            typer.echo("Reading from stdin (Ctrl+D to finish)...", err=True)
        text = sys.stdin.read().strip()
        if not text:
            print_error("No input received from stdin.")

    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.add_memory(
            tenant_id=tid,
            text=text,
            sub_tenant_id=stid,
            infer=infer,
            is_markdown=markdown,
            title=title,
            source_id=source_id,
            user_name=user_name,
            upsert=upsert,
        )

        def fmt(r: dict) -> str:
            success_count = r.get("success_count", 0)
            failed_count = r.get("failed_count", 0)
            preview = text[:80] + "..." if len(text) > 80 else text
            lines = [
                f"  Memory added ({success_count} success, {failed_count} failed)",
                f"  Content: \"{preview}\"",
            ]
            results = r.get("results", [])
            for item in results:
                sid = item.get("source_id", "unknown")
                status = item.get("status", "unknown")
                lines.append(f"  Source ID: {sid} (status: {status})")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)


@app.command("list")
def list_memories(
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
) -> None:
    """List all user memories for a tenant.

    Examples:

        hydradb memories list --tenant-id my-tenant
    """
    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.list_memories(tenant_id=tid, sub_tenant_id=stid)

        def fmt(r: dict) -> str:
            memories = r.get("user_memories", [])
            if not memories:
                return "  No memories found."
            lines = [f"  Found {len(memories)} memories:\n"]
            for i, mem in enumerate(memories, 1):
                mid = mem.get("memory_id", "unknown")
                content = mem.get("memory_content", "")
                preview = content[:120] + "..." if len(content) > 120 else content
                lines.append(f"  {i}. [{mid}]")
                lines.append(f"     {preview}\n")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)


@app.command()
def delete(
    memory_id: str = typer.Argument(help="ID of the memory to delete."),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt.",
    ),
) -> None:
    """Delete a specific user memory by its ID.

    Use 'hydradb memories list' to find memory IDs.

    Examples:

        hydradb memories delete mem_abc123 --tenant-id my-tenant
    """
    if not confirm:
        typer.confirm(
            f"Delete memory '{memory_id}'? This action is irreversible.",
            abort=True,
        )

    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.delete_memory(
            tenant_id=tid,
            memory_id=memory_id,
            sub_tenant_id=stid,
        )

        def fmt(r: dict) -> str:
            if r.get("user_memory_deleted"):
                return f"  Memory '{memory_id}' deleted."
            return f"  Memory '{memory_id}' was not found or already deleted."

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
