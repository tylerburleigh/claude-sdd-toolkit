import argparse
import importlib
import logging
import sys
import types

import pytest

from claude_skills.cli.sdd import registry

OPTIONAL_MODULES = (
    "claude_skills.sdd_render.cli",
    "claude_skills.sdd_fidelity_review.cli",
)


def _make_cli_parsers():
    parent_parser = argparse.ArgumentParser(add_help=False)
    root_parser = argparse.ArgumentParser(prog="sdd")
    subparsers = root_parser.add_subparsers(dest="command")
    return subparsers, parent_parser


def test_optional_modules_missing_are_logged_and_skipped(monkeypatch, caplog):
    real_import = importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name in OPTIONAL_MODULES:
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(registry.importlib, "import_module", fake_import)

    caplog.set_level(logging.WARNING, logger=registry.logger.name)

    subparsers, parent_parser = _make_cli_parsers()

    registry.register_all_subcommands(subparsers, parent_parser)

    warning_messages = [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING]

    assert any("sdd_render" in message for message in warning_messages)
    assert any("sdd_fidelity_review" in message for message in warning_messages)


def test_optional_modules_register_when_available(monkeypatch, caplog):
    real_import = importlib.import_module

    render_calls = []
    fidelity_calls = []

    render_module = types.SimpleNamespace(
        register_render=lambda *args, **kwargs: render_calls.append((args, kwargs))
    )
    fidelity_module = types.SimpleNamespace(
        register_commands=lambda *args, **kwargs: fidelity_calls.append((args, kwargs))
    )

    monkeypatch.setitem(sys.modules, OPTIONAL_MODULES[0], render_module)
    monkeypatch.setitem(sys.modules, OPTIONAL_MODULES[1], fidelity_module)

    def fake_import(name, *args, **kwargs):
        if name == OPTIONAL_MODULES[0]:
            return render_module
        if name == OPTIONAL_MODULES[1]:
            return fidelity_module
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(registry.importlib, "import_module", fake_import)

    caplog.set_level(logging.DEBUG, logger=registry.logger.name)

    subparsers, parent_parser = _make_cli_parsers()

    registry.register_all_subcommands(subparsers, parent_parser)

    assert render_calls, "Expected register_render to be invoked when module is available."
    assert fidelity_calls, "Expected register_commands to be invoked when module is available."

    debug_messages = [record.getMessage() for record in caplog.records if record.levelno == logging.DEBUG]
    assert any("sdd_render" in message for message in debug_messages)
    assert any("sdd_fidelity_review" in message for message in debug_messages)
