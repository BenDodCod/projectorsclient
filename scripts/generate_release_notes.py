"""
Generate release notes from git commit history.

This script extracts commits since the last tag and formats them as
markdown release notes, grouped by type (feat, fix, docs, chore, etc.).

Usage:
    python scripts/generate_release_notes.py [version]
    python scripts/generate_release_notes.py 2.0.1

Output:
    RELEASE_NOTES.md in project root (or returned as string if called from code)
"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.__version__ import __version__, __version_full__


def get_last_tag() -> str:
    """Get the most recent git tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # No tags found
            return None

    except Exception:
        return None


def get_commits_since_tag(tag: str = None) -> List[str]:
    """
    Get list of commits since specified tag (or all commits if no tag).

    Returns list of commit messages in format: "hash|date|author|subject|body"
    """
    try:
        # Format: hash|date|author|subject|body
        format_str = '%H|%aI|%an|%s|%b'

        if tag:
            # Get commits since tag
            cmd = ['git', 'log', f'{tag}..HEAD', f'--pretty=format:{format_str}']
        else:
            # Get all commits (no previous tag)
            cmd = ['git', 'log', f'--pretty=format:{format_str}']

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            commits = result.stdout.strip().split('\n')
            return [c for c in commits if c]  # Filter empty lines
        else:
            return []

    except Exception as e:
        print(f"WARNING: Failed to get commits: {e}", file=sys.stderr)
        return []


def parse_commit(commit_line: str) -> Dict:
    """
    Parse a commit line into structured data.

    Format: hash|date|author|subject|body
    """
    parts = commit_line.split('|', 4)

    if len(parts) < 4:
        return None

    hash_val, date, author, subject = parts[:4]
    body = parts[4] if len(parts) > 4 else ''

    # Parse conventional commit format: type(scope): message
    # Examples: feat: add feature, fix(ui): fix bug, docs: update readme
    commit_pattern = r'^(\w+)(?:\(([^)]+)\))?: (.+)$'
    match = re.match(commit_pattern, subject)

    if match:
        commit_type = match.group(1).lower()
        scope = match.group(2) if match.group(2) else ''
        message = match.group(3)
    else:
        # No conventional format - treat as 'other'
        commit_type = 'other'
        scope = ''
        message = subject

    # Check for breaking changes
    is_breaking = 'BREAKING CHANGE' in body or subject.endswith('!')

    return {
        'hash': hash_val[:7],  # Short hash
        'full_hash': hash_val,
        'date': date,
        'author': author,
        'type': commit_type,
        'scope': scope,
        'message': message,
        'body': body.strip(),
        'breaking': is_breaking
    }


def group_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """Group commits by type."""
    grouped = defaultdict(list)

    # Type categories with display names
    type_map = {
        'feat': 'Features',
        'fix': 'Bug Fixes',
        'docs': 'Documentation',
        'style': 'Styles',
        'refactor': 'Refactoring',
        'perf': 'Performance',
        'test': 'Tests',
        'build': 'Build',
        'ci': 'CI/CD',
        'chore': 'Chores',
        'revert': 'Reverts',
        'other': 'Other Changes'
    }

    for commit in commits:
        if commit:
            commit_type = commit['type']
            # Map to known category or 'other'
            category = type_map.get(commit_type, 'Other Changes')
            grouped[category].append(commit)

    return grouped


def format_commit(commit: Dict) -> str:
    """Format a single commit as markdown list item."""
    message = commit['message']
    scope = f"**{commit['scope']}**: " if commit['scope'] else ''
    hash_link = commit['hash']

    # Add breaking change indicator
    breaking = ' :warning: **BREAKING**' if commit['breaking'] else ''

    return f"- {scope}{message} ({hash_link}){breaking}"


def generate_release_notes_content(version: str, previous_tag: str = None) -> str:
    """
    Generate release notes content as markdown string.

    Args:
        version: Version for this release (e.g., "2.0.1")
        previous_tag: Previous git tag to compare against

    Returns:
        Markdown formatted release notes
    """
    # Get commits
    commits_raw = get_commits_since_tag(previous_tag)

    if not commits_raw:
        return f"# Release {version}\n\nNo changes since last release.\n"

    # Parse commits
    commits = [parse_commit(c) for c in commits_raw]
    commits = [c for c in commits if c]  # Filter None

    # Group by type
    grouped = group_commits(commits)

    # Build markdown
    lines = []
    lines.append(f"# Release {version}")
    lines.append('')
    lines.append(f"**Release Date:** {datetime.now().strftime('%Y-%m-%d')}")

    if previous_tag:
        lines.append(f"**Previous Version:** {previous_tag}")

    lines.append(f"**Total Changes:** {len(commits)} commits")
    lines.append('')

    # Add breaking changes section if any
    breaking_commits = [c for c in commits if c['breaking']]
    if breaking_commits:
        lines.append('## :warning: Breaking Changes')
        lines.append('')
        for commit in breaking_commits:
            lines.append(format_commit(commit))
        lines.append('')

    # Add sections for each commit type
    # Order: Features, Bug Fixes, then alphabetically
    priority_order = ['Features', 'Bug Fixes']
    other_sections = sorted([k for k in grouped.keys() if k not in priority_order])
    section_order = priority_order + other_sections

    for section in section_order:
        if section in grouped:
            lines.append(f'## {section}')
            lines.append('')

            for commit in grouped[section]:
                lines.append(format_commit(commit))

            lines.append('')

    # Add contributors section
    authors = set(c['author'] for c in commits)
    if authors:
        lines.append('## Contributors')
        lines.append('')
        lines.append(f"Thank you to all {len(authors)} contributor(s) to this release:")
        lines.append('')
        for author in sorted(authors):
            lines.append(f"- {author}")
        lines.append('')

    # Footer
    lines.append('---')
    lines.append('')
    lines.append('**Full Changelog:** ', end='')
    if previous_tag:
        lines.append(f'[{previous_tag}...v{version}](../../compare/{previous_tag}...v{version})')
    else:
        lines.append('First release')
    lines.append('')

    return '\n'.join(lines)


def save_release_notes(content: str, output_path: Path = None):
    """Save release notes to file."""
    if output_path is None:
        output_path = project_root / 'RELEASE_NOTES.md'

    output_path.write_text(content, encoding='utf-8')
    return output_path


def main():
    """Main entry point."""
    # Get version from command line or use current version
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = __version__

    print(f"Generating release notes for version {version}...")
    print()

    # Get last tag
    last_tag = get_last_tag()

    if last_tag:
        print(f"Comparing against previous tag: {last_tag}")
    else:
        print("No previous tags found - generating notes for all commits")

    print()

    # Generate notes
    content = generate_release_notes_content(version, last_tag)

    # Save to file
    output_path = save_release_notes(content)

    print(f"Release notes saved to: {output_path}")
    print()

    # Print preview (first 20 lines)
    lines = content.split('\n')
    print("Preview:")
    print("-" * 70)
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    print("-" * 70)
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: Failed to generate release notes: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
