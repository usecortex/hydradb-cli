"""Fetch commands: content, sources, relations."""

from typing import Optional

import httpx
import typer

from hydradb_cli.client import HydraDBClientError
from hydradb_cli.output import print_error, print_result
from hydradb_cli.utils.common import (
    get_client,
    handle_api_error,
    handle_network_error,
    require_tenant_id,
    resolve_sub_tenant_id,
)

app = typer.Typer(help="Fetch and inspect stored data.")

VALID_FETCH_MODES = {"content", "url", "both"}
VALID_SOURCE_KINDS = {"knowledge", "memories"}


@app.command()
def content(
    source_id: str = typer.Argument(help="Source ID to fetch content for."),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
    mode: str = typer.Option(
        "content",
        "--mode",
        help="Fetch mode: 'content' (text), 'url' (presigned URL), or 'both'.",
    ),
) -> None:
    """Fetch the full content of a source by its ID.

    Returns the original text content that was ingested. Use 'hydradb fetch sources'
    to find source IDs.

    Examples:

        hydradb fetch content source_abc123 --tenant-id my-tenant

        hydradb fetch content source_abc123 --mode url --tenant-id my-tenant
    """
    if not source_id.strip():
        print_error("Source ID cannot be empty.")

    if mode not in VALID_FETCH_MODES:
        print_error(f"--mode must be one of: {', '.join(sorted(VALID_FETCH_MODES))}. Got '{mode}'.")

    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.fetch_content(
            tenant_id=tid,
            source_id=source_id,
            sub_tenant_id=stid,
            mode=mode,
        )

        def fmt(r: dict) -> str:
            lines = [f"  Source: {source_id}"]
            content_text = r.get("content", "")
            content_b64 = r.get("content_base64", "")
            url = r.get("presigned_url", "")
            content_type = r.get("content_type", "")
            size = r.get("size_bytes")

            if content_type:
                lines.append(f"  Type: {content_type}")
            if size is not None:
                lines.append(f"  Size: {size} bytes")
            if url:
                lines.append(f"  URL: {url}")
            if content_text:
                lines.append(f"\n{content_text}")
            elif content_b64:
                lines.append(f"\n  [Binary content, {len(content_b64)} chars base64-encoded]")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        if e.status_code == 404:
            print_error(
                f"Source '{source_id}' not found. This can happen if the file was uploaded "
                f"under a different sub-tenant. Try specifying --sub-tenant-id explicitly."
            )
        else:
            handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command()
def sources(
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
    kind: Optional[str] = typer.Option(
        None,
        "--kind",
        help="Filter by kind: 'knowledge' or 'memories'.",
    ),
    page: Optional[int] = typer.Option(
        None, "--page", help="Page number (1-indexed)."
    ),
    page_size: Optional[int] = typer.Option(
        None, "--page-size", help="Items per page (1-100)."
    ),
) -> None:
    """List all ingested sources (knowledge and/or memories).

    Shows source IDs, titles, types, and metadata. Use source IDs with
    'hydradb fetch content' to retrieve full content.

    Examples:

        hydradb fetch sources --tenant-id my-tenant

        hydradb fetch sources --kind knowledge --page-size 20 --tenant-id my-tenant
    """
    if kind and kind not in VALID_SOURCE_KINDS:
        print_error(f"--kind must be one of: {', '.join(sorted(VALID_SOURCE_KINDS))}. Got '{kind}'.")

    if page is not None and page < 1:
        print_error(f"--page must be at least 1, got {page}.")

    if page_size is not None and (page_size < 1 or page_size > 100):
        print_error(f"--page-size must be between 1 and 100, got {page_size}.")

    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.list_data(
            tenant_id=tid,
            sub_tenant_id=stid,
            kind=kind,
            page=page,
            page_size=page_size,
        )

        def fmt(r: dict) -> str:
            sources_list = r.get("sources", [])
            memories_list = r.get("user_memories", [])

            if sources_list:
                lines = [f"  Found {len(sources_list)} source(s):\n"]
                for i, src in enumerate(sources_list, 1):
                    sid = src.get("id", "unknown")
                    title = src.get("title", "")
                    stype = src.get("type", "")
                    title_str = f" — {title}" if title else ""
                    type_str = f" ({stype})" if stype else ""
                    lines.append(f"  {i}. [{sid}]{title_str}{type_str}")
                total = r.get("total")
                pagination = r.get("pagination", {})
                if total is not None:
                    lines.append(f"\n  Total: {total}")
                if pagination.get("has_next"):
                    current = pagination.get("page", 1)
                    lines.append(f"  Next page: --page {current + 1}")
                return "\n".join(lines)

            if memories_list:
                lines = [f"  Found {len(memories_list)} memory/memories:\n"]
                for i, mem in enumerate(memories_list, 1):
                    mid = mem.get("memory_id", "unknown")
                    content = mem.get("memory_content", "")
                    preview = content[:100] + "..." if len(content) > 100 else content
                    lines.append(f"  {i}. [{mid}] {preview}")
                return "\n".join(lines)

            return "  No sources found."

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command()
def relations(
    source_id: str = typer.Argument(help="Source ID to fetch graph relations for."),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID. Uses default if not specified."
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None, "--sub-tenant-id", help="Sub-tenant ID."
    ),
    is_memory: Optional[bool] = typer.Option(
        None,
        "--is-memory/--is-knowledge",
        help="Whether the source is a memory (vs knowledge).",
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Maximum number of relations to return."
    ),
) -> None:
    """Fetch knowledge graph relations for a source.

    Shows entity relationships extracted from the source content.

    Examples:

        hydradb fetch relations source_abc123 --tenant-id my-tenant

        hydradb fetch relations mem_123 --is-memory --tenant-id my-tenant
    """
    if not source_id.strip():
        print_error("Source ID cannot be empty.")

    if limit is not None and limit < 1:
        print_error(f"--limit must be at least 1, got {limit}.")

    tid = require_tenant_id(tenant_id)
    stid = resolve_sub_tenant_id(sub_tenant_id)
    client = get_client()

    try:
        result = client.graph_relations(
            tenant_id=tid,
            source_id=source_id,
            sub_tenant_id=stid,
            is_memory=is_memory,
            limit=limit,
        )

        def fmt(r: dict) -> str:
            relations_list = r.get("relations", [])
            if not relations_list:
                return f"  No graph relations found for source '{source_id}'."

            lines = [f"  Graph relations for '{source_id}':\n"]
            for rel in relations_list:
                triplets = rel.get("triplets", [])
                for t in triplets:
                    src = t.get("source", {}).get("name", "?")
                    pred = t.get("relation", {}).get("canonical_predicate", "related to")
                    tgt = t.get("target", {}).get("name", "?")
                    lines.append(f"  ({src}) --[{pred}]--> ({tgt})")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)
