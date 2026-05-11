"""
Git tools for version control and commit operations.

Provides MCP-compatible functions for creating commits, managing branches,
and tracking changes to the PBIP project.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from git import Repo, GitCommandError
    HAS_GIT = True
except ImportError:
    HAS_GIT = False

from .models import GitCommitInfo


class GitTools:
    """Tools for Git operations."""

    def __init__(self, pbip_root: Path):
        """
        Initialize Git tools.

        Args:
            pbip_root: Root path of PBIP project
        """
        self.pbip_root = Path(pbip_root)

        if HAS_GIT:
            try:
                self.repo = Repo(self.pbip_root)
            except Exception:
                # Initialize repo if it doesn't exist
                self.repo = Repo.init(self.pbip_root)
        else:
            self.repo = None

    def git_commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
        author: str = "Power BI Agent",
        email: str = "agent@powerbi.local",
    ) -> Dict[str, Any]:
        """
        Create a git commit for PBIP changes.

        Args:
            message: Commit message
            files: Optional list of specific files to commit (None for all)
            author: Author name
            email: Author email

        Returns:
            Commit information
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            # Stage files
            if files:
                for file in files:
                    self.repo.index.add(file)
            else:
                # Stage all changes
                self.repo.index.add(["."])

            # Check if there are changes to commit
            if not self.repo.index.diff("HEAD"):
                return {
                    "success": False,
                    "error": "No changes to commit",
                }

            # Create commit
            commit = self.repo.index.commit(
                message,
                author_name=author,
                author_email=email,
            )

            return {
                "success": True,
                "message": f"Commit created successfully",
                "commit_hash": commit.hexsha[:8],
                "full_hash": commit.hexsha,
                "author": f"{author} <{email}>",
                "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "message": commit.message,
                "files_changed": list(self.repo.index.diff("HEAD~1"))
                if self.repo.head.is_valid() and self.repo.head.commit.parents
                else [],
            }

        except GitCommandError as e:
            return {
                "success": False,
                "error": f"Git command failed: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Commit failed: {str(e)}",
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current Git status.

        Returns:
            Status information
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            # Untracked files
            untracked = self.repo.untracked_files

            # Changed files
            changed_files = []
            for item in self.repo.index.diff(None):
                changed_files.append(item.a_path)

            # Staged files
            staged_files = []
            for item in self.repo.index.diff("HEAD"):
                staged_files.append(item.a_path)

            return {
                "success": True,
                "branch": self.repo.active_branch.name if self.repo.head.is_valid() else "no-branch",
                "untracked_count": len(untracked),
                "changed_count": len(changed_files),
                "staged_count": len(staged_files),
                "untracked_files": untracked,
                "changed_files": changed_files,
                "staged_files": staged_files,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get status: {str(e)}",
            }

    def get_commit_history(self, max_commits: int = 10) -> Dict[str, Any]:
        """
        Get recent commit history.

        Args:
            max_commits: Maximum number of commits to return

        Returns:
            Commit history
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            if not self.repo.head.is_valid():
                return {
                    "success": True,
                    "commits": [],
                    "count": 0,
                }

            commits = []
            for commit in self.repo.iter_commits(max_count=max_commits):
                commit_info = GitCommitInfo(
                    commit_hash=commit.hexsha[:8],
                    message=commit.message.strip(),
                    author=commit.author.name,
                    timestamp=datetime.fromtimestamp(commit.committed_date),
                )
                commits.append(commit_info.to_dict())

            return {
                "success": True,
                "commits": commits,
                "count": len(commits),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get commit history: {str(e)}",
            }

    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Create a new branch.

        Args:
            branch_name: Name of new branch

        Returns:
            Operation result
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            new_branch = self.repo.create_head(branch_name)
            return {
                "success": True,
                "message": f"Branch created: {branch_name}",
                "branch_name": branch_name,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create branch: {str(e)}",
            }

    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Switch to a different branch.

        Args:
            branch_name: Target branch name

        Returns:
            Operation result
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            self.repo.heads[branch_name].checkout()
            return {
                "success": True,
                "message": f"Switched to branch: {branch_name}",
                "current_branch": branch_name,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to switch branch: {str(e)}",
            }

    def list_branches(self) -> Dict[str, Any]:
        """
        List all branches.

        Returns:
            Branch list
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            branches = []
            for branch in self.repo.heads:
                is_active = branch == self.repo.active_branch if self.repo.head.is_valid() else False
                branches.append({
                    "name": branch.name,
                    "is_active": is_active,
                })

            return {
                "success": True,
                "branches": branches,
                "count": len(branches),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list branches: {str(e)}",
            }

    def rollback_changes(self, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Rollback uncommitted changes.

        Args:
            files: Optional list of files to rollback (None for all)

        Returns:
            Operation result
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            if files:
                for file in files:
                    self.repo.index.checkout(file)
                return {
                    "success": True,
                    "message": f"Rolled back {len(files)} files",
                    "files": files,
                }
            else:
                self.repo.index.checkout(force=True)
                return {
                    "success": True,
                    "message": "All changes rolled back",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Rollback failed: {str(e)}",
            }

    def tag_release(self, tag_name: str, message: str = "") -> Dict[str, Any]:
        """
        Create a release tag.

        Args:
            tag_name: Name of tag
            message: Tag message

        Returns:
            Operation result
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            tag = self.repo.create_tag(tag_name, ref="HEAD", message=message)
            return {
                "success": True,
                "message": f"Tag created: {tag_name}",
                "tag_name": tag_name,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Tag creation failed: {str(e)}",
            }

    def get_diff(self, commit_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Get diff between commits or current and HEAD.

        Args:
            commit_hash: Optional specific commit to diff

        Returns:
            Diff information
        """
        if not HAS_GIT or not self.repo:
            return {
                "success": False,
                "error": "GitPython not installed or git not available",
            }

        try:
            if commit_hash:
                # Diff specific commit
                commit = self.repo.commit(commit_hash)
                diffs = commit.parents[0].diff(commit) if commit.parents else []
            else:
                # Diff current changes
                diffs = self.repo.index.diff(None)

            diff_info = []
            for diff_item in diffs:
                diff_info.append({
                    "file": diff_item.a_path,
                    "change_type": diff_item.change_type,
                })

            return {
                "success": True,
                "diffs": diff_info,
                "count": len(diff_info),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Diff retrieval failed: {str(e)}",
            }
