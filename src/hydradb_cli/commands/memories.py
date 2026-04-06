"""User memory commands: add, list, delete."""

import sys
from typing import Optional

import httpx
import typer

from hydradb_cli.client import HydraDBClientError
from hydradb_cli.output import print_error, print_result
from hydradb_cli.utils.common import (
    get_client,
    handle_api_error,
    handle_network_error,
    read_stdin_safe,
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

        echo "Meeting notes..." | hydradb memories add --tenant-id my-tenant
    """
    if text == "-":
        if sys.stdin.isatty():
            typer.echo("Reading from stdin (Ctrl+D to finish)...", err=True)
            text = sys.stdin.read().strip()
        else:
            stdin_data = read_stdin_safe()
            text = stdin_data
        if not text:
            print_error("No input received from stdin.")

    if text is None:
        stdin_data = read_stdin_safe()
        if stdin_data:
            text = stdin_data
        else:
            print_error(
                "No text provided. Use --text 'your text', "
                "pipe via stdin, or use --text - for interactive input."
            )

    if not text or not text.strip():
        print_error("Memory text cannot be empty or whitespace-only.")

    text = text.strip()

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
                error = item.get("error")
                lines.append(f"  Source ID: {sid} (status: {status})")
                if error:
                    lines.append(f"  Error: {error}")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


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
    except httpx.RequestError as e:
        handle_network_error(e)


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
    if not memory_id.strip():
        print_error("Memory ID cannot be empty.")

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
            deleted = r.get("user_memory_deleted")
            success = r.get("success")
            if deleted and success:
                return f"  Memory '{memory_id}' deleted."
            elif success and not deleted:
                return f"  Memory '{memory_id}' was not found or already deleted."
            else:
                return f"  Could not confirm deletion of memory '{memory_id}'."

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)
