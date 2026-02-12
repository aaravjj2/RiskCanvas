import os
import subprocess
from pathlib import Path

def test_artifacts_directory_is_gitignored():
    """
    Test that artifacts directory is properly gitignored.
    This test ensures that generated report files won't be committed to git.
    """
    # Create a test file in the artifacts directory
    test_file_path = Path("../artifacts/test_file.txt")
    test_file_path.touch()

    # Check if the file is tracked by git
    result = subprocess.run(['git', 'ls-files', str(test_file_path)],
                           capture_output=True, text=True)

    # The file should not be listed in git (i.e., it should be gitignored)
    assert result.returncode == 1, f"File {test_file_path} should be gitignored but is tracked"
    assert result.stdout.strip() == "", f"File {test_file_path} should not be in git tracking"

    # Clean up
    test_file_path.unlink()

def test_report_files_not_committed():
    """
    Test that report files are not committed to git.
    This test ensures that generated reports don't end up in the repository.
    """
    # Test that artifacts directory is gitignored
    result = subprocess.run(['git', 'ls-files', 'artifacts/'],
                           capture_output=True, text=True)

    # No files in artifacts should be tracked by git
    assert result.returncode == 1, "artifacts/ directory should be gitignored"
    assert result.stdout.strip() == "", "No files in artifacts/ should be tracked"