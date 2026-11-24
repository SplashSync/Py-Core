#
#  This file is part of SplashSync Project.
#
#  Copyright (C) Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

"""Documentation: llms.txt index, pages reader, ``splashpy docs`` command and packages check."""

from __future__ import annotations

import importlib.util
import io
import re
import tarfile
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

from splashpy import cli, documentation
from splashpy.dictionary import SplDocs
from splashpy.documentation import DocsError, DocsSource, docs_source, repository_source

ROOT = Path(__file__).resolve().parents[2]
"""Repository root."""


def packaged(tmp_path: Path, index: bool = True) -> DocsSource:
    """Build a packaged documentation layout: index and pages in the same directory."""
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "objects.md").write_text("# Objects\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not a page", encoding="utf-8")
    (tmp_path / "sub.md").mkdir()
    if index:
        (tmp_path / SplDocs.INDEX).write_text("# splashpy\n", encoding="utf-8")
    return DocsSource(tmp_path / SplDocs.INDEX, tmp_path)


def load_checker() -> ModuleType:
    """Load the packages checker script (tools are not a package)."""
    spec = importlib.util.spec_from_file_location("packages_check", ROOT / "tools" / "packages" / "check.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_llms_index_matches_pages() -> None:
    """Every documentation page is listed in llms.txt, and every listed page exists."""
    index = (ROOT / SplDocs.INDEX).read_text(encoding="utf-8")
    listed = set(re.findall(r"\]\(docs/([\w-]+)\.md\)", index))
    assert listed == set(repository_source().names())
    assert index.startswith("# splashpy\n")


def test_repository_source() -> None:
    """Editable installs read the repository: index at the root, pages in docs/, plans excluded."""
    source = docs_source()
    assert source.index == ROOT / SplDocs.INDEX
    assert "contracts" in source.names()
    assert "plan" not in source.names()
    assert source.read_index().startswith("# splashpy")
    assert source.read_page("contracts") == source.read_page("contracts.md")
    assert source.read_page("contracts").startswith("# Contracts")


def test_unknown_pages_are_refused() -> None:
    """Only listed pages are read: unknown names and paths are refused with the available pages."""
    source = repository_source()
    for name in ("missing", "../README", "plan/contracts", "/etc/passwd"):
        with pytest.raises(DocsError, match="available: configuration"):
            source.read_page(name)


def test_packaged_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Built packages read their own pages first; without them, the repository is used."""
    source = packaged(tmp_path)
    assert source.names() == ["objects"]
    assert source.read_page("objects") == "# Objects\n"
    monkeypatch.setattr(documentation, "packaged_source", lambda: source)
    assert docs_source() is source
    monkeypatch.setattr(documentation, "packaged_source", lambda: packaged(tmp_path / "x", index=False))
    assert docs_source().index == ROOT / SplDocs.INDEX


def test_packaged_source_location() -> None:
    """The packaged documentation lives in splashpy/docs/."""
    source = documentation.packaged_source()
    assert str(source.index).endswith(f"splashpy/{SplDocs.DIRECTORY}/{SplDocs.INDEX}")


def test_missing_documentation(tmp_path: Path) -> None:
    """Without documentation, the index is an error and no page is listed."""
    source = repository_source(tmp_path)
    assert source.names() == []
    with pytest.raises(DocsError, match="not available"):
        source.read_index()


def test_docs_command(capsys: pytest.CaptureFixture[str]) -> None:
    """``splashpy docs`` prints the index and the pages, ``splashpy docs <page>`` one page."""
    assert cli.main(["docs"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("# splashpy")
    assert "Pages: configuration, contracts," in output
    assert cli.main(["docs", "testing"]) == 0
    assert capsys.readouterr().out.startswith("# Testing a Connector")
    assert cli.main(["docs", "nope"]) == 1
    assert capsys.readouterr().out == ""


def test_docs_command_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without documentation, the command fails cleanly."""
    monkeypatch.setattr(cli, "docs_source", lambda: repository_source(tmp_path))
    assert cli.main(["docs"]) == 1


def write_wheel(path: Path, names: list[str]) -> None:
    """Write a fake wheel with the given files."""
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, "x")


def write_sdist(path: Path, names: list[str]) -> None:
    """Write a fake source distribution with the given files."""
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            info = tarfile.TarInfo(f"splashpy-3.0.0/{name}")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))


def test_packages_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Built packages must ship the documentation and never the planning notes."""
    checker = load_checker()
    good = tmp_path / "good"
    good.mkdir()
    write_wheel(good / "splashpy-3.0.0-py3-none-any.whl", list(checker.REQUIRED))
    write_sdist(good / "splashpy-3.0.0.tar.gz", ["docs/objects.md", "llms.txt"])
    assert checker.main(["check", str(good)]) == 0
    assert "Packages OK." in capsys.readouterr().out
    bad = tmp_path / "bad"
    bad.mkdir()
    write_wheel(bad / "splashpy-3.0.0-py3-none-any.whl", ["splashpy/docs/plan/odoo.md"])
    write_sdist(bad / "splashpy-3.0.0.tar.gz", ["docs/plan/odoo.md"])
    errors = checker.check(bad)
    assert len(errors) == len(checker.REQUIRED) + 2
    assert checker.check(tmp_path / "empty") == [f"No wheel found in {tmp_path / 'empty'}."]
