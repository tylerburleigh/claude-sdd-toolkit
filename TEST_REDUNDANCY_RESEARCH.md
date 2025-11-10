# Test Redundancy Research

## Test Suite Analysis

- **Pytest defaults** – repository-level configuration uses `testpaths = src/claude_skills/claude_skills/tests`, while the package’s `pyproject.toml` still points discovery at `claude_skills/tests`.
  ```21:21:pytest.ini
  testpaths = src/claude_skills/claude_skills/tests
  ```
  ```50:55:src/claude_skills/pyproject.toml
  [tool.pytest.ini_options]
  testpaths = ["claude_skills/tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = "-v --tb=short"
  ```

- **Legacy `tests/` suite** – contains unit coverage for spec mutation primitives and integration tests that shell out to the `sdd` executable.
  ```52:74:tests/test_add_node.py
  def test_add_task_to_phase(self):
      spec = create_minimal_spec()
      node_data = {"node_id": "task-1-1", "type": "task", "title": "Implement feature X"}
      result = add_node(spec, "phase-1", node_data)
      assert result["success"] is True
      assert "task-1-1" in spec["hierarchy"]["phase-1"]["children"]
      assert spec["hierarchy"]["task-1-1"]["total_tasks"] == 1
  ```
  ```40:68:tests/integration/test_json_output_integration.py
  result_compact = subprocess.run(
      ['sdd', 'progress', sample_spec_id, '--json', '--compact'],
      capture_output=True,
      text=True
  )
  result_pretty = subprocess.run(
      ['sdd', 'progress', sample_spec_id, '--json', '--no-compact'],
      capture_output=True,
      text=True
  )
  assert result_compact.returncode == 0
  assert result_pretty.returncode == 0
  assert result_compact.stdout != result_pretty.stdout
  ```
  ```196:228:tests/integration/test_run_tests_ai_consultation_integration.py
  result = subprocess.run(
      ["sdd", "test", "consult",
       "assertion",
       "--error", sample_test_error,
       "--hypothesis", sample_hypothesis,
       "--dry-run"],
      capture_output=True,
      text=True,
      timeout=10
  )
  assert result.returncode in [0, 1]
  ```

- **Legacy-only coverage** – fidelity review workflows, AI tool subprocess behaviors, and streaming/cache orchestration exist only in `tests/`.
  ```196:223:tests/integration/test_ai_tools_integration.py
  def test_gemini_command_executes_successfully(self, path_with_mock_tools):
      cmd = build_tool_command("gemini", "test prompt", model="gemini-exp-1114")
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
      assert result.returncode == 0
      assert "Gemini response to: test prompt" in result.stdout
  ```
  ```39:118:tests/test_sdd_fidelity_review.py
  def test_fidelity_reviewer_init_with_spec_path():
      spec_path = Path("/fake/specs")
      with patch('claude_skills.sdd_fidelity_review.review.load_json_spec') as mock_load:
          mock_load.return_value = {"title": "Test Spec", "hierarchy": {}}
          reviewer = FidelityReviewer("test-spec-001", spec_path=spec_path)
          assert reviewer.spec_path == spec_path
          mock_load.assert_called_once_with("test-spec-001", spec_path)
  ```
  ```25:111:tests/integration/test_streaming_cache.py
  cache = CacheManager()
  cache.set("test-key", {"result": "cached data"}, ttl_hours=1)
  result = cache.get("test-key")
  assert result is not None
  assert result["result"] == "cached data"
  ```

- **Package-scoped suite** – lives under `src/claude_skills/claude_skills/tests/`, uses shared helpers, and prefers module invocation via `python -m`.
  ```106:142:src/claude_skills/claude_skills/tests/integration/cli_runner.py
  if os.environ.get("SDD_TEST_USE_BIN") and shutil.which("sdd"):
      command = ["sdd"] + args
  else:
      command = [sys.executable, "-m", "claude_skills.cli.sdd.__init__"] + args
  return subprocess.run(command, check=check, env=effective_env, **subprocess_kwargs)
  ```

- **Modern coverage themes** – transactional spec modification, JSON formatting utilities, and run-tests CLI checks now reside inside the package suite.
  ```128:178:src/claude_skills/claude_skills/tests/integration/test_modify_validation.py
  result = add_node(
      sample_spec,
      "phase-1",
      {"node_id": "task-1-3", "type": "invalid_type", "title": "Task 1.3"}
  )
  assert not result["success"]
  assert "Invalid node type" in result["message"]
  assert sample_spec == original_spec
  ```
  ```50:82:src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_cli_utils.py
  data = {"status": "\x1b[32mcompleted\x1b[0m"}
  result = format_json_output(data, strip_ansi=True)
  parsed = json.loads(result)
  assert parsed["status"] == "completed"
  ```
  ```186:228:src/claude_skills/claude_skills/tests/integration/test_run_tests_doc_integration.py
  result = run_cli(
      "test", "check-tools",
      "--json",
      capture_output=True,
      text=True
  )
  assert result.returncode in [0, 1]
  output = json.loads(result.stdout)
  if "tools" in output:
      for tool_info in output["tools"].values():
          if isinstance(tool_info, dict):
              assert "available" in tool_info or "status" in tool_info
  ```

## Overlap and Gaps

- **Redundant behaviors** – JSON formatting and spec mutation tests appear in both suites.
  ```24:54:tests/test_json_output.py
  output_json(data)
  captured = capsys.readouterr()
  parsed = json.loads(captured.out)
  assert parsed == data
  assert "\n" in captured.out
  ```

- **Unique legacy scenarios** – fidelity review artifacts, AI tool subprocess integration, and streaming/cache workflows are absent from the package suite (no references to `FidelityReviewer`, `streaming_cache`, or `ToolResponse` there).

- **Package-only coverage** – new suite validates unified CLI behavior, global flag normalization, and module-level helpers that legacy tests never exercised.

## Execution Environment Differences

- Legacy integration tests require the installed `sdd` executable and real subprocess environments.
- Package integration tests default to local module invocation with curated environment setup via `cli_runner`.

## Consolidation Options

- Port legacy-only coverage into the package suite using `run_cli` or module-level fixtures.
- Decide whether to keep a minimal legacy folder for real-binary smoke tests; if not, delete `tests/` once coverage is duplicated.
- Align pytest discovery configuration to avoid silent omissions.

## Recommendations

1. Harmonize pytest configuration (`pytest.ini` and `pyproject.toml`) so developers run the intended suite.
2. Migrate fidelity review, AI tool subprocess, and streaming/cache tests into `src/claude_skills/claude_skills/tests/`.
3. Evaluate the necessity of real CLI smoke tests; retain or redesign a trimmed set if end-to-end checks against the installed binary are still required.
4. Update contributor documentation after consolidation to point at the canonical test directory and describe any optional end-to-end collections.

