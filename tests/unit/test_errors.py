"""Tests that every ADR Toolkit domain exception shares a common base and
a stable error_code (docs/adr-toolkit-audit-report.md §2.4 4.3)."""
from scripts.core.config import ConfigError
from scripts.core.constraints import ConstraintsError
from scripts.core.errors import AdrToolkitError
from scripts.core.frontmatter import FrontmatterError
from scripts.core.git_paths import GitPathsError
from scripts.core.lifecycle import InvalidTransitionError
from scripts.core.repository_paths import PathEscapesRootError

EXPECTED = {
    ConfigError: "CONFIG_ERROR",
    FrontmatterError: "BAD_FRONTMATTER",
    ConstraintsError: "BAD_CONSTRAINTS",
    InvalidTransitionError: "INVALID_TRANSITION",
    GitPathsError: "GIT_LS_FILES_FAILED",
    PathEscapesRootError: "PATH_ESCAPES_ROOT",
}


def test_every_domain_exception_is_an_adr_toolkit_error():
    for cls in EXPECTED:
        assert issubclass(cls, AdrToolkitError)


def test_every_domain_exception_has_its_documented_error_code():
    for cls, expected_code in EXPECTED.items():
        assert cls.error_code == expected_code
