import sys
import json
import click

from .compressor import Compressor
from . import synonym_db


@click.group()
def main():
    pass


@main.command()
@click.option("--domain", "-d", default="legal-pt", show_default=True)
@click.option("--model", "-m", default="gpt-4o", show_default=True)
@click.option("--safe-only", is_flag=True, default=False, help="Only use safe substitutions")
@click.argument("file", type=click.File("r"), default="-")
def compress(domain, model, safe_only, file):
    """Compress text by replacing words with token-cheaper synonyms."""
    text = file.read()
    result = Compressor(domain, model, safe_only=safe_only).compress(text)
    click.echo(result.text, nl=False)


@main.command()
@click.option("--domain", "-d", default="legal-pt", show_default=True)
@click.option("--model", "-m", default="gpt-4o", show_default=True)
@click.option("--safe-only", is_flag=True, default=False)
@click.argument("file", type=click.File("r"), default="-")
def analyze(domain, model, safe_only, file):
    """Show what would be substituted without modifying text."""
    text = file.read()
    result = Compressor(domain, model, safe_only=safe_only).analyze(text)

    if not result.substitutions:
        click.echo("No substitutions found.")
        return

    for sub in result.substitutions:
        click.echo(f"  {sub.original} → {sub.replacement}  (-{sub.tokens_saved} token{'s' if sub.tokens_saved != 1 else ''})")

    click.echo(f"\nTotal: -{result.tokens_saved} tokens across {result.substitution_count} substitution(s)")


@main.command()
@click.option("--domain", "-d", default="legal-pt", show_default=True)
@click.option("--model", "-m", default="gpt-4o", show_default=True)
@click.option("--safe-only", is_flag=True, default=False)
@click.option("--json", "as_json", is_flag=True, default=False)
@click.argument("file", type=click.File("r"), default="-")
def stats(domain, model, safe_only, as_json, file):
    """Token count before/after with savings breakdown."""
    text = file.read()
    s = Compressor(domain, model, safe_only=safe_only).stats(text)

    if as_json:
        click.echo(json.dumps(s, indent=2))
        return

    click.echo(f"Original : {s['original_tokens']} tokens")
    click.echo(f"Compressed: {s['compressed_tokens']} tokens")
    click.echo(f"Saved    : {s['tokens_saved']} tokens ({s['savings_pct']}%)")
    click.echo(f"Changes  : {s['substitutions']} substitution(s)")


@main.group()
def dict():
    """Manage synonym dictionaries."""
    pass


@dict.command("list")
@click.option("--domain", "-d", default="legal-pt", show_default=True)
@click.option("--model", "-m", default="gpt-4o", show_default=True)
def dict_list(domain, model):
    """List all entries with token savings."""
    entries = synonym_db.load(domain, model)
    for word, entry in sorted(entries.items()):
        safe_marker = "✓" if entry.safe else "~"
        click.echo(f"  [{safe_marker}] {word} → {entry.replacement}  (-{entry.savings_for(model)} token(s))")
