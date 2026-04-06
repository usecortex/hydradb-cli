"""Output formatting for HydraDB CLI.

Supports two modes:
- human: Rich-formatted tables and text (default)
- json: Raw JSON for agent/script consumption
"""

import json
from typing import Any, Callable, Optional

import typer

# Global output format state
_output_format: str = "human"


def set_output_format(fmt: str) -> None:
    global _output_format
    _output_format = fmt


def get_output_format() -> str:
    return _output_format


def print_json(data: Any) -> None:
    """Print data as formatted JSON to stdout."""
    typer.echo(json.dumps(data, indent=2, default=str))


def print_success(message: str) -> None:
    """Print a success message in human mode. In json mode, this is a no-op.

    For json mode, use print_result() to emit a single JSON response per command.
    """
    if _output_format != "json":
        typer.echo(f"  {message}")


def print_error(message: str, exit_code: int = 1) -> None:
    """Print an error message and exit."""
    if _output_format == "json":
        typer.echo(json.dumps({"success": False, "error": message}))
    else:
        typer.echo(f"  Error: {message}", err=True)
    raise typer.Exit(code=exit_code)


def print_result(data: Any, human_formatter: Optional[Callable[[Any], str]] = None) -> None:
    """Print API result — JSON in json mode, formatted in human mode.

    Args:
        data: The raw API response dict.
        human_formatter: Optional callable(data) -> str for human-readable output.
    """
    if _output_format == "json":
        print_json(data)
    elif human_formatter:
        typer.echo(human_formatter(data))
    else:
        # Fallback: pretty-print JSON even in human mode
        print_json(data)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple table in human mode, or JSON array in json mode."""
    if _output_format == "json":
        items = []
        for row in rows:
            items.append(dict(zip(headers, row)))
        print_json(items)
        return

    if not rows:
        typer.echo("  No results.")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Print header
    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    typer.echo(f"  {header_line}")
    typer.echo(f"  {'  '.join('-' * w for w in col_widths)}")

    # Print rows
    for row in rows:
        row_line = "  ".join(
            str(cell).ljust(col_widths[i]) if i < len(col_widths) else str(cell)
            for i, cell in enumerate(row)
        )
        typer.echo(f"  {row_line}")
