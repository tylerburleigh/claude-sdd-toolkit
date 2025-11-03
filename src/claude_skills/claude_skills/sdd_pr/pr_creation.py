"""PR creation and approval workflow for AI-generated pull requests.

This module handles the final steps of PR creation: displaying drafts to users,
pushing branches, creating PRs via gh CLI, and updating spec metadata.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import save_json_spec
from claude_skills.common.git_metadata import update_pr_metadata
from claude_skills.sdd_update.git_pr import (
    push_branch,
    create_pull_request,
    check_gh_available,
)

logger = logging.getLogger(__name__)


def show_pr_draft_and_wait(
    pr_title: str,
    pr_body: str,
    spec_id: str,
    branch_name: str,
    base_branch: str,
    printer: PrettyPrinter
) -> None:
    """Display PR draft to user and provide next steps.

    This function does NOT implement interactive approval. It displays the draft
    and returns, allowing the Claude Code agent to ask the user if they want to
    proceed. The agent then invokes the creation command with --approve flag.

    Args:
        pr_title: Draft PR title
        pr_body: Draft PR body (markdown formatted)
        spec_id: Specification ID
        branch_name: Feature branch name
        base_branch: Base branch name
        printer: PrettyPrinter instance for formatted output
    """
    printer.info("")
    printer.header("="*70)
    printer.header("Pull Request Draft")
    printer.header("="*70)
    printer.info("")

    # Show PR title
    printer.info(f"Title: {pr_title}")
    printer.info(f"Branch: {branch_name} → {base_branch}")
    printer.info("")
    printer.info("-"*70)
    printer.info("")

    # Show PR body (use print for multi-line content to preserve formatting)
    print(pr_body)

    printer.info("")
    printer.info("-"*70)
    printer.info("")

    # Show next steps
    printer.info("To create this PR, run:")
    printer.result("  sdd create-pr", f"{spec_id} --approve")
    printer.info("")
    printer.info("To regenerate with different instructions:")
    printer.result("  Skill(sdd-toolkit:sdd-pr)", "with new analysis prompt")
    printer.info("")
    printer.header("="*70)
    printer.info("")


def create_pr_with_ai_description(
    repo_root: Path,
    branch_name: str,
    base_branch: str,
    pr_title: str,
    pr_body: str,
    spec_data: Dict[str, Any],
    spec_id: str,
    specs_dir: Path,
    printer: PrettyPrinter
) -> bool:
    """Create PR with AI-generated description and update spec metadata.

    This function:
    1. Checks if gh CLI is available
    2. Pushes the branch to remote
    3. Creates PR via gh CLI
    4. Updates spec metadata with PR URL and number

    Args:
        repo_root: Path to repository root directory
        branch_name: Feature branch name to push
        base_branch: Base branch name (e.g., 'main')
        pr_title: PR title
        pr_body: PR body (markdown formatted)
        spec_data: Loaded spec JSON data
        spec_id: Specification ID
        specs_dir: Path to specs directory
        printer: PrettyPrinter instance for formatted output

    Returns:
        True if PR created successfully and metadata updated, False otherwise
    """
    printer.info("")
    printer.header("Creating Pull Request")
    printer.info("="*70)
    printer.info("")

    # Step 0: Check if gh CLI is available
    if not check_gh_available():
        printer.error("GitHub CLI (gh) not found")
        printer.info("")
        printer.info("Install gh from: https://cli.github.com/")
        printer.info("")
        printer.info("Or create PR manually:")
        printer.info(f"  1. Push branch: git push -u origin {branch_name}")
        printer.info(f"  2. Visit: https://github.com/{{owner}}/{{repo}}/compare/{branch_name}")
        printer.info("")
        return False

    # Step 1: Push branch to remote
    printer.action(f"Pushing branch '{branch_name}' to remote...")
    push_success, push_error = push_branch(repo_root, branch_name)

    if not push_success:
        printer.error(f"Branch push failed: {push_error}")
        printer.info("")
        printer.info("Try pushing manually:")
        printer.result("  git push -u origin", branch_name)
        printer.info("")
        return False

    printer.success("Branch pushed successfully")
    printer.info("")

    # Step 2: Create PR via gh CLI
    printer.action("Creating pull request via gh CLI...")
    pr_success, pr_url, pr_number, pr_error = create_pull_request(
        repo_root=repo_root,
        title=pr_title,
        body=pr_body,
        base_branch=base_branch
    )

    if not pr_success:
        printer.error(f"PR creation failed: {pr_error}")
        printer.info("")
        printer.info("Create PR manually:")
        printer.info(f"  Visit: https://github.com/{{owner}}/{{repo}}/compare/{branch_name}")
        printer.info("")
        return False

    printer.success(f"Pull request created: {pr_url}")
    printer.info(f"PR #{pr_number}")
    printer.info("")

    # Step 3: Update spec metadata with PR information
    printer.action("Updating spec metadata...")

    update_pr_metadata(
        spec=spec_data,
        pr_url=pr_url,
        pr_number=pr_number,
        status='open'
    )

    # Save spec with PR metadata
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.warning("Failed to save PR metadata to spec")
        printer.info("")
        printer.info("PR was created successfully, but spec metadata update failed")
        printer.info(f"Manually add PR info to: {specs_dir}/{spec_id}.json")
        printer.info("")
        return True  # PR was created, just metadata update failed

    printer.success("PR metadata added to spec")
    printer.info("")
    printer.header("="*70)
    printer.success("Pull request created successfully!")
    printer.info("")
    printer.info(f"View PR: {pr_url}")
    printer.info("")

    return True


def validate_pr_readiness(
    spec_data: Dict[str, Any],
    printer: PrettyPrinter
) -> bool:
    """Validate that spec is ready for PR creation.

    Checks:
    - Spec is marked as completed
    - Git metadata exists (branch_name, base_branch)
    - Repository is in clean state (all changes committed)

    Args:
        spec_data: Loaded spec JSON data
        printer: PrettyPrinter for error messages

    Returns:
        True if ready for PR creation, False otherwise
    """
    # Check spec completion
    metadata = spec_data.get('metadata', {})
    status = metadata.get('status', 'unknown')

    if status != 'completed':
        printer.error(f"Spec status is '{status}', expected 'completed'")
        printer.info("Complete the spec first with: sdd complete-spec")
        return False

    # Check git metadata
    git_metadata = metadata.get('git', {})
    branch_name = git_metadata.get('branch_name')
    base_branch = git_metadata.get('base_branch')

    if not branch_name:
        printer.error("Missing git metadata: branch_name")
        printer.info("Spec must have git.branch_name in metadata")
        return False

    if not base_branch:
        printer.error("Missing git metadata: base_branch")
        printer.info("Spec must have git.base_branch in metadata")
        return False

    return True
