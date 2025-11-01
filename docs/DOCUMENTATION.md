# src Documentation

**Version:** 1.0.0
**Generated:** 2025-11-01 11:19:01

---

## 📊 Project Statistics

- **Total Files:** 164
- **Total Lines:** 52852
- **Total Classes:** 198
- **Total Functions:** 712
- **Avg Complexity:** 5.52
- **Max Complexity:** 42
- **High Complexity Functions:**
  - update_task_status (42)
  - generate_report (40)
  - format_execution_plan (39)
  - execute_verify_task (38)
  - get_cached_transcript_path (36)



## 🏛️ Classes

### `BaseParser`

**Language:** python
**Inherits from:** `ABC`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:252`

**Description:**
> Abstract base class for language-specific parsers.

All language parsers must inherit from this class and implement
the required abstract methods.

**Methods:**
- `__init__()`
- `parse_file()`
- `find_files()`
- `parse_all()`
- `_should_exclude()`
- `_get_relative_path()`

**Properties:**
- `language`
- `file_extensions`

---

### `CSSParser`

**Language:** python
**Inherits from:** `BaseParser`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/css.py:38`

**Description:**
> Parser for CSS files using tree-sitter.

**Methods:**
- `__init__()`
- `parse_file()`
- `_extract_css_structure()`
- `_count_selectors()`
- `_extract_at_rule_name()`
- `_get_node_text()`

**Properties:**
- `language`
- `file_extensions`

---

### `CallReference`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/schema.py:108`

**Description:**
> Represents a reference to a function call.

This structure is used to represent both:
- callers: functions that call this function
- calls: functions called by this function

Attributes:
    name: Name of the function
    file: File path where the function is defined/called
    line: Line number of the call site or definition
    call_type: Type of call (e.g., "function_call", "method_call",
               "class_instantiation")

Example:
    >>> ref = CallReference(
    ...     name="process_data",
    ...     file="src/utils.py",
    ...     line=42,
    ...     call_type="function_call"
    ... )
    >>> ref.to_dict()
    {'name': 'process_data', 'file': 'src/utils.py', 'line': 42,
     'call_type': 'function_call'}

**Methods:**
- `to_dict()`

---

### `CallSite`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:34`

**Description:**
> Represents a location where a function/method is called.

---

### `CodebaseAnalyzer`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parser.py:12`

**Description:**
> Analyzes Python codebase and extracts structure.

**Methods:**
- `__init__()`
- `analyze()`
- `_find_python_files()`
- `_analyze_file()`
- `_extract_class()`
- `_extract_function()`
- `_extract_imports()`
- `_get_name()`
- `_create_result()`

---

### `ConsultationResponse`

**Language:** python
**Inherits from:** `NamedTuple`
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:679`

**Description:**
> Represents a response from a tool consultation.

---

### `CrossReferenceGraph`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:66`

**Description:**
> Bidirectional graph tracking caller/callee relationships and
class instantiations across the codebase.

**Methods:**
- `__init__()`
- `add_call()`
- `add_instantiation()`
- `add_import()`
- `add_warning()`
- `get_callers()`
- `get_callees()`
- `get_instantiation_sites()`
- `get_instantiators()`
- `get_imported_by()`
- `get_imports()`
- `to_dict()`

---

### `DependencyAnalysis`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:8`

**Description:**
> Structured dependency diagnostics used by sdd-validate.

---

### `DiffReport`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:22`

**Description:**
> Complete diff report between before and after states.

---

### `DocumentationGenerator`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/generator.py:39`

**Description:**
> Main orchestrator for documentation generation.
Coordinates all stages: parsing, analysis, calculation, and formatting.
Supports multiple programming languages.

**Methods:**
- `__init__()`
- `generate()`
- `_convert_parse_result()`
- `save_markdown()`
- `save_json()`
- `generate_all()`

---

### `DocumentationQuery`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:26`

**Description:**
> Main class for querying codebase documentation.

**Methods:**
- `__init__()`
- `_resolve_docs_path()`
- `_find_documentation_dir()`
- `load()`
- `_normalize_data()`
- `_reindex()`
- `_assemble_module_entry()`
- `_compute_module_complexity()`
- `_get_docstring_excerpt()`
- `_resolve_module_key()`
- `_copy_module_info()`
- `apply_pattern_filter()`
- `_ensure_loaded()`
- `find_class()`
- `find_function()`
- `find_module()`
- `_get_module_info()`
- `get_high_complexity()`
- `get_dependencies()`
- `search_entities()`
- `get_context_for_area()`
- `describe_module()`
- `get_stats()`
- `list_classes()`
- `list_functions()`
- `list_modules()`
- `get_callers()`
- `get_callees()`
- `get_call_count()`
- `_create_graph_node()`
- `build_call_graph()`

---

### `DynamicPattern`

**Language:** python
**Inherits from:** `Enum`
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:23`

**Description:**
> Dynamic patterns that may affect cross-reference accuracy.

---

### `DynamicPatternWarning`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:56`

**Description:**
> Warning about a dynamic pattern that may affect accuracy.

---

### `EnhancedError`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:12`

**Description:**
> Enhanced error message with detailed location and fix information

**Methods:**
- `__str__()`

---

### `FieldChange`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:12`

**Description:**
> Represents a single field change.

---

### `FixAction`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:31`

**Description:**
> Represents a candidate auto-fix operation.

---

### `FixReport`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:44`

**Description:**
> Outcome of applying a set of fix actions.

---

### `GoParser`

**Language:** python
**Inherits from:** `BaseParser`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/go.py:40`

**Description:**
> Parser for Go files using tree-sitter.

**Methods:**
- `__init__()`
- `parse_file()`
- `_extract_package_name()`
- `_extract_type_declaration()`
- `_extract_struct()`
- `_extract_interface()`
- `_extract_function()`
- `_extract_method()`
- `_extract_imports()`
- `_extract_import_path()`
- `_estimate_complexity()`
- `_get_node_text()`

**Properties:**
- `language`
- `file_extensions`

---

### `HTMLParser`

**Language:** python
**Inherits from:** `BaseParser`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/html.py:38`

**Description:**
> Parser for HTML files using tree-sitter.

**Methods:**
- `__init__()`
- `parse_file()`
- `_extract_html_structure()`
- `_extract_attributes()`
- `_get_node_text()`

**Properties:**
- `language`
- `file_extensions`

---

### `ImportReference`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/schema.py:256`

**Description:**
> Represents a location where a class/module is imported.

Tracks import statements to enable dependency analysis and
understand how classes/modules are being used across the codebase.

Attributes:
    importer: File that imports the class/module
    line: Line number of import statement
    import_type: Type of import ("direct", "from", "dynamic")
    alias: Optional import alias (e.g., "import pandas as pd")

Example:
    >>> ref = ImportReference(
    ...     importer="app.py",
    ...     line=5,
    ...     import_type="from",
    ...     alias="User"
    ... )
    >>> ref.to_dict()
    {'importer': 'app.py', 'line': 5, 'import_type': 'from',
     'alias': 'User'}

**Methods:**
- `to_dict()`

---

### `InstantiationReference`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/schema.py:214`

**Description:**
> Represents a location where a class is instantiated.

Used to track where classes are being used/constructed throughout
the codebase, enabling reverse lookup from class to instantiation sites.

Attributes:
    instantiator: Name of function/method creating the instance
    file: File containing the instantiation
    line: Line number of instantiation
    context: Optional context (e.g., "module", "function", "method")

Example:
    >>> ref = InstantiationReference(
    ...     instantiator="create_user",
    ...     file="services/user.py",
    ...     line=42,
    ...     context="function"
    ... )
    >>> ref.to_dict()
    {'instantiator': 'create_user', 'file': 'services/user.py',
     'line': 42, 'context': 'function'}

**Methods:**
- `to_dict()`

---

### `InstantiationSite`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:46`

**Description:**
> Represents a location where a class is instantiated.

---

### `JSONGenerator`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/formatter.py:201`

**Description:**
> Generates JSON documentation.

**Methods:**
- `__init__()`
- `generate()`

---

### `JavaScriptParser`

**Language:** python
**Inherits from:** `BaseParser`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/javascript.py:41`

**Description:**
> Parser for JavaScript and TypeScript files using tree-sitter.

**Methods:**
- `__init__()`
- `parse_file()`
- `_extract_class()`
- `_extract_function()`
- `_extract_variable_functions()`
- `_extract_imports()`
- `_extract_exports()`
- `_is_exported()`
- `_estimate_complexity()`
- `_get_node_text()`

**Properties:**
- `language`
- `file_extensions`

---

### `JsonSpecValidationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:130`

**Description:**
> Results of JSON spec file validation

**Methods:**
- `count_all_issues()`
- `is_valid()`

---

### `Language`

**Language:** python
**Inherits from:** `Enum`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:15`

**Description:**
> Supported programming languages.

**Methods:**
- `from_extension()`

---

### `MarkdownGenerator`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/formatter.py:18`

**Description:**
> Generates Markdown documentation.

**Methods:**
- `__init__()`
- `generate()`
- `_header()`
- `_statistics()`
- `_language_breakdown()`
- `_classes()`
- `_functions()`
- `_dependencies()`

---

### `NormalizedValidationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:12`

**Description:**
> Aggregated validation statistics derived from a raw validation result.

**Properties:**
- `auto_fixable_total`
- `has_errors`
- `has_warnings`

---

### `ParseResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:164`

**Description:**
> Result of parsing a file or codebase.

**Methods:**
- `to_dict()`
- `merge()`

---

### `ParsedClass`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:102`

**Description:**
> Represents a class, struct, or interface in any language.

**Methods:**
- `to_dict()`

---

### `ParsedFunction`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:60`

**Description:**
> Represents a function or method in any language.

**Methods:**
- `to_dict()`

---

### `ParsedModule`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:134`

**Description:**
> Represents a module, file, or compilation unit.

**Methods:**
- `to_dict()`

---

### `ParsedParameter`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/base.py:52`

**Description:**
> Represents a function/method parameter.

---

### `ParserFactory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/factory.py:15`

**Description:**
> Factory for creating and managing language-specific parsers.

Automatically detects languages in a project and coordinates
parsing across multiple languages.

**Methods:**
- `__init__()`
- `register_parser()`
- `detect_languages()`
- `get_parser()`
- `parse_all()`
- `parse_file()`
- `get_language_statistics()`
- `_should_exclude()`
- `_print_summary()`

---

### `PrettyPrinter`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/printer.py:8`

**Description:**
> Utility for consistent, pretty console output optimized for Claude Code.

**Methods:**
- `__init__()`
- `_colorize()`
- `action()`
- `success()`
- `info()`
- `warning()`
- `error()`
- `header()`
- `detail()`
- `result()`
- `blank()`
- `item()`

---

### `PythonParser`

**Language:** python
**Inherits from:** `BaseParser`
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/python.py:34`

**Description:**
> Parser for Python source files using AST analysis.

**Methods:**
- `parse_file()`
- `_extract_class()`
- `_extract_function()`
- `_extract_imports()`
- `_get_name()`

**Properties:**
- `language`
- `file_extensions`

---

### `QueryResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:18`

**Description:**
> Represents a query result with metadata.

---

### `ReferenceType`

**Language:** python
**Inherits from:** `Enum`
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:14`

**Description:**
> Types of cross-references that can be tracked.

---

### `SDDContextGatherer`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:16`

**Description:**
> Helper class for gathering context for SDD tasks.

**Methods:**
- `__init__()`
- `get_task_context()`
- `suggest_files_for_task()`
- `find_similar_implementations()`
- `get_test_context()`
- `get_refactoring_candidates()`
- `get_impact_analysis()`
- `_extract_keywords()`
- `_deduplicate_results()`

---

### `SpecRenderer`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_render/renderer.py:7`

**Description:**
> Renders JSON spec data to human-readable markdown.

**Methods:**
- `__init__()`
- `to_markdown()`
- `_render_header()`
- `_render_objectives()`
- `_render_phase()`
- `_render_group()`
- `_render_task()`
- `_render_verification()`
- `_get_status_icon()`

---

### `SpecStatistics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/stats.py:13`

**Description:**
> Calculated statistics for a spec file.

---

### `SpecValidationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:56`

**Description:**
> Results of spec document validation

**Methods:**
- `count_all_issues()`
- `is_valid()`
- `calculate_completion()`

---

### `TestActivateSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_lifecycle.py:339`

**Description:**
> Test activate_spec() function.

**Methods:**
- `test_activate_spec_success()`
- `test_activate_spec_not_found()`
- `test_activate_spec_already_active()`

---

### `TestAddJournalEntry`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_journal.py:13`

**Description:**
> Test add_journal_entry() function.

**Methods:**
- `test_add_journal_entry_basic()`
- `test_add_journal_entry_with_task_id()`
- `test_add_journal_entry_custom_author()`
- `test_add_journal_entry_updates_timestamp()`
- `test_add_journal_entry_dry_run()`
- `test_add_journal_entry_invalid_spec()`

---

### `TestAddRevisionEntry`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_journal.py:222`

**Description:**
> Test add_revision_entry() function.

**Methods:**
- `test_add_revision_entry_basic()`
- `test_add_revision_entry_custom_author()`
- `test_add_revision_entry_multiple()`
- `test_add_revision_entry_dry_run()`

---

### `TestAddVerificationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_verification.py:14`

**Description:**
> Test add_verification_result() function.

**Methods:**
- `test_add_verification_result_passed()`
- `test_add_verification_result_failed()`
- `test_add_verification_result_partial()`
- `test_add_verification_result_updates_timestamp()`
- `test_add_verification_result_invalid_status()`
- `test_add_verification_result_nonexistent_verify_id()`
- `test_add_verification_result_dry_run()`
- `test_add_verification_result_minimal()`

---

### `TestAggregateTaskTimes`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_time_tracking.py:293`

**Description:**
> Test aggregate_task_times() function.

**Methods:**
- `_create_test_spec()`
- `test_aggregate_task_times_basic()`
- `test_aggregate_task_times_no_data()`
- `test_aggregate_task_times_partial_data()`
- `test_aggregate_task_times_nonexistent_spec()`
- `test_aggregate_task_times_empty_hierarchy()`
- `test_aggregate_task_times_mixed_node_types()`
- `test_aggregate_task_times_invalid_values()`
- `test_aggregate_task_times_precision()`
- `test_aggregate_task_times_with_printer()`
- `test_aggregate_task_times_single_task()`
- `test_aggregate_task_times_zero_hours()`
- `test_aggregate_task_times_negative_hours()`

---

### `TestBackupJsonSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:165`

**Description:**
> Tests for backup_json_spec function.

**Methods:**
- `test_create_backup_of_existing_json_spec()`
- `test_backup_nonexistent_json_spec()`
- `test_multiple_backups_dont_overwrite()`

---

### `TestBackwardsCompatibility`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:290`

**Description:**
> Tests for backwards compatibility with old command style.

**Methods:**
- `test_new_sdd_command_works()`

---

### `TestBaseParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_base.py:158`

**Description:**
> Test BaseParser abstract class.

**Methods:**
- `test_base_parser_is_abstract()`
- `test_base_parser_interface()`

---

### `TestCLIBasics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:68`

**Description:**
> Basic CLI functionality tests.

**Methods:**
- `test_cli_help()`
- `test_cli_version()`

---

### `TestCLIBasics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:69`

**Description:**
> Basic CLI functionality tests.

**Methods:**
- `test_cli_help()`
- `test_cli_shows_new_commands()`

---

### `TestCLIWorkflows`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:303`

**Description:**
> End-to-end CLI workflow tests.

**Methods:**
- `test_complete_task_discovery_workflow()`

---

### `TestCSSParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_css.py:17`

**Description:**
> Test CSS parser functionality.

**Methods:**
- `parser()`
- `test_parse_simple_css()`
- `test_parse_css_selectors()`
- `test_parse_css_variables()`
- `test_parse_media_queries()`
- `test_parse_keyframes()`
- `test_parse_imports()`
- `test_parse_empty_css()`
- `test_line_counting()`

---

### `TestCSSParserAdvanced`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_css.py:170`

**Description:**
> Advanced CSS parser tests.

**Methods:**
- `parser()`
- `test_parse_nested_rules()`
- `test_parse_mixins()`
- `test_parse_css_grid()`
- `test_parse_css_flexbox()`

---

### `TestCalculateTimeFromTimestamps`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_time_tracking.py:16`

**Description:**
> Test calculate_time_from_timestamps() function.

**Methods:**
- `test_calculate_time_basic()`
- `test_calculate_time_whole_hours()`
- `test_calculate_time_fractional()`
- `test_calculate_time_across_days()`
- `test_calculate_time_with_timezone_offset()`
- `test_calculate_time_invalid_format()`
- `test_calculate_time_negative_duration()`
- `test_calculate_time_same_timestamp()`
- `test_calculate_time_with_seconds()`
- `test_calculate_time_missing_z_suffix()`
- `test_calculate_time_one_hour()`
- `test_calculate_time_two_and_half_hours()`
- `test_calculate_time_six_minutes()`
- `test_calculate_time_over_24_hours()`
- `test_calculate_time_none_input()`
- `test_calculate_time_empty_string()`
- `test_calculate_time_both_none()`
- `test_calculate_time_end_none()`
- `test_calculate_time_whitespace_strings()`
- `test_calculate_time_very_large_difference()`
- `test_calculate_time_with_printer_none_input()`
- `test_calculate_time_with_printer_invalid_format()`
- `test_calculate_time_with_printer_negative_duration()`

---

### `TestCheckComplete`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:272`

**Description:**
> Tests for check_complete function.

**Methods:**
- `test_check_completed_spec()`
- `test_check_incomplete_spec()`
- `test_check_phase_complete()`
- `test_check_phase_incomplete()`
- `test_check_nonexistent_phase()`
- `test_check_invalid_spec()`

---

### `TestCheckCompleteCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:288`

**Description:**
> Tests for check-complete command.

**Methods:**
- `test_check_complete_spec()`
- `test_check_complete_phase()`
- `test_check_complete_json()`
- `test_check_complete_exit_code()`

---

### `TestCheckDependencies`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py:159`

**Description:**
> Tests for check_dependencies function.

**Methods:**
- `test_check_dependencies_no_blockers()`
- `test_check_dependencies_with_blockers()`
- `test_check_dependencies_nonexistent_task()`
- `test_check_dependencies_includes_blocks()`
- `test_check_dependencies_resolved_when_complete()`

---

### `TestCheckDepsCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:202`

**Description:**
> Tests for check-deps command.

**Methods:**
- `test_check_deps_no_blockers()`
- `test_check_deps_with_blockers()`
- `test_check_deps_json()`

---

### `TestCheckDepsCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:290`

**Description:**
> Tests for the check-deps command.

**Methods:**
- `test_check_deps_clean_spec()`
- `test_check_deps_with_cycles()`
- `test_check_deps_json()`
- `test_check_deps_with_bottleneck_threshold()`
- `test_check_deps_orphaned()`

---

### `TestCheckDocQueryAvailable`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py:21`

**Description:**
> Tests for check_doc_query_available function.

**Methods:**
- `test_doc_query_available()`
- `test_doc_query_not_found()`
- `test_doc_query_command_not_found()`
- `test_doc_query_timeout()`

---

### `TestCheckEnvironment`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py:118`

**Description:**
> Tests for check_environment function.

**Methods:**
- `test_check_environment_valid_project()`
- `test_check_environment_with_requirements()`
- `test_check_environment_missing_dependencies()`
- `test_check_environment_includes_config_files()`
- `test_check_environment_warnings()`

---

### `TestCheckSddIntegrationAvailable`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py:72`

**Description:**
> Tests for check_sdd_integration_available function.

**Methods:**
- `test_sdd_integration_available()`
- `test_sdd_integration_not_available()`

---

### `TestCheckSpecCompletion`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:124`

**Description:**
> Tests for check_spec_completion() function.

**Methods:**
- `test_all_tasks_complete()`
- `test_partial_completion()`
- `test_empty_spec()`
- `test_specific_phase_completion()`
- `test_nested_task_hierarchy()`
- `test_blocked_tasks_not_complete()`
- `test_in_progress_tasks_not_complete()`
- `test_no_spec_data()`
- `test_no_hierarchy()`
- `test_invalid_phase_id()`
- `test_percentage_calculation()`

---

### `TestClassSchemaEnhancements`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:1419`

**Description:**
> Test class schema v1.1 enhancements with usage tracking fields.

**Methods:**
- `parser()`
- `test_instantiation_reference_creation()`
- `test_instantiation_reference_to_dict()`
- `test_instantiation_reference_without_context()`
- `test_import_reference_creation()`
- `test_import_reference_to_dict()`
- `test_import_reference_without_alias()`
- `test_enhance_class_with_instantiated_by()`
- `test_enhance_class_with_imported_by()`
- `test_enhance_class_with_instantiation_count()`
- `test_enhance_class_without_instantiation_count()`
- `test_enhance_class_preserves_base_fields()`
- `test_enhance_class_with_empty_tracking()`
- `test_enhance_class_with_none_tracking()`
- `test_enhance_class_complete_example()`
- `test_different_import_types()`
- `test_instantiation_context_types()`

---

### `TestColdStartPerformance`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:304`

**Description:**
> Tests for CLI cold-start performance.

**Methods:**
- `test_help_fast_response()`
- `test_command_help_fast_response()`

---

### `TestCommandDelegation`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:251`

**Description:**
> Tests that unified CLI correctly delegates to command implementations.

**Methods:**
- `test_next_command_works()`
- `test_update_command_works()`
- `test_validate_command_works()`

---

### `TestCompleteSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_lifecycle.py:129`

**Description:**
> Test complete_spec() function.

**Methods:**
- `test_complete_spec_all_tasks_done()`
- `test_complete_spec_without_actual_hours()`
- `test_complete_spec_without_time_data()`
- `test_complete_spec_incomplete_tasks()`
- `test_complete_spec_dry_run()`
- `test_complete_spec_creates_metadata()`
- `test_complete_spec_updates_last_updated()`

---

### `TestCompleteTaskWorkflow`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_workflow.py:14`

**Description:**
> Test complete_task_workflow() function.

**Methods:**
- `_create_test_spec()`
- `test_complete_task_workflow_auto_calculates_time()`
- `test_complete_task_workflow_manual_hours_not_overridden()`
- `test_complete_task_workflow_no_started_at_no_calculation()`

---

### `TestCompletionDetection`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:346`

**Description:**
> Tests for automatic spec completion detection in sdd-next workflow.

**Methods:**
- `test_completion_detection_prepare_task()`
- `test_all_blocked_messaging()`
- `test_prepare_task_with_completion_and_blockers()`

---

### `TestCompletionDetection`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:649`

**Description:**
> Tests for automatic spec completion detection after update-status.

**Methods:**
- `test_completion_detection_after_update()`
- `test_completion_prompt_skipped_when_blocked()`
- `test_user_confirmation_flow()`
- `test_user_decline_flow()`

---

### `TestConsultation`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py:122`

**Description:**
> Tests for run_consultation().

**Methods:**
- `test_run_consultation_success()`
- `test_run_consultation_failure()`
- `test_run_consultation_dry_run()`
- `test_run_consultation_unknown_tool()`

---

### `TestContextSummary`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:247`

**Description:**
> Tests for create_context_summary().

**Methods:**
- `test_create_basic_summary()`
- `test_summary_with_readme()`
- `test_summary_structure()`

---

### `TestCountBlockedTasks`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:408`

**Description:**
> Tests for count_blocked_tasks() function.

**Methods:**
- `test_no_blocked_tasks()`
- `test_single_blocked_task()`
- `test_multiple_blocked_tasks()`
- `test_nested_blocked_tasks()`
- `test_invalid_node_id()`

---

### `TestCreateParserFactory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_factory.py:155`

**Description:**
> Test create_parser_factory helper function.

**Methods:**
- `test_create_factory_defaults()`
- `test_create_factory_with_options()`

---

### `TestDetectProject`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py:13`

**Description:**
> Tests for detect_project function.

**Methods:**
- `test_detect_node_project()`
- `test_detect_python_project()`
- `test_detect_project_includes_config_files()`
- `test_detect_project_extracts_dependencies()`
- `test_detect_project_extracts_dev_dependencies()`
- `test_detect_unknown_project()`

---

### `TestDiscoveryIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py:259`

**Description:**
> Integration tests for discovery operations.

**Methods:**
- `test_complete_task_discovery_workflow()`
- `test_task_progression_through_phase()`

---

### `TestEnsureDocumentationExists`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py:200`

**Description:**
> Tests for ensure_documentation_exists function.

**Methods:**
- `test_fast_path_docs_exist()`
- `test_docs_missing_no_generation()`
- `test_auto_generate_success()`
- `test_auto_generate_failure()`
- `test_auto_generate_timeout()`
- `test_prompt_user_mode()`

---

### `TestErrorHandling`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:355`

**Description:**
> Tests for error handling.

**Methods:**
- `test_invalid_command()`
- `test_missing_spec_file_argument()`
- `test_invalid_json_file()`

---

### `TestErrorHandling`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:223`

**Description:**
> Tests for error handling and edge cases.

**Methods:**
- `test_invalid_command()`
- `test_missing_required_arg()`

---

### `TestExecuteVerifyTask`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_integrations.py:135`

**Description:**
> Tests for execute_verify_task function.

**Methods:**
- `test_verify_task_not_found()`
- `test_manual_verification_task()`
- `test_verify_task_no_command_or_skill()`
- `test_run_tests_skill_success()`
- `test_run_tests_skill_failure()`
- `test_command_execution_success()`
- `test_execution_timeout()`
- `test_unknown_skill()`
- `test_duration_tracking()`
- `test_on_failure_retry_logic()`
- `test_on_failure_max_retries_exhausted()`
- `test_on_failure_consult_flag()`
- `test_on_failure_notification()`
- `test_on_failure_continue_on_failure()`
- `test_on_failure_custom_revert_status()`
- `test_on_failure_all_actions_combined()`
- `test_new_skill_sdd_validate()`
- `test_new_skill_code_doc()`
- `test_new_skill_doc_query()`
- `test_hierarchy_lookup()`
- `test_backward_compat_tasks_field()`

---

### `TestExtractFrontmatter`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:17`

**Description:**
> Tests for ``extract_frontmatter`` helper.

**Methods:**
- `test_extract_frontmatter_from_json_spec()`
- `test_extract_frontmatter_handles_missing_fields()`
- `test_extract_frontmatter_invalid_json()`
- `test_extract_frontmatter_markdown()`
- `test_extract_frontmatter_missing_file()`

---

### `TestFindCircularDeps`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_validation.py:53`

**Description:**
> Tests for find_circular_deps function.

**Methods:**
- `test_find_circular_deps_none()`
- `test_find_circular_deps_detected()`
- `test_find_circular_deps_shows_chains()`
- `test_find_orphaned_tasks()`

---

### `TestFindPattern`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_workflow.py:30`

**Description:**
> Tests for find_pattern function.

**Methods:**
- `test_find_pattern_simple()`
- `test_find_pattern_recursive()`

---

### `TestFindRelatedFiles`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py:167`

**Description:**
> Tests for find_related_files function.

**Methods:**
- `test_find_related_files_test_files()`
- `test_find_related_files_same_directory()`
- `test_find_related_files_similar_files()`
- `test_find_related_files_includes_source()`
- `test_find_related_files_nonexistent()`

---

### `TestFindSpecFile`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_paths.py:120`

**Description:**
> Tests for find_spec_file function.

**Methods:**
- `test_find_spec_file_in_pending()`
- `test_find_spec_file_pending_priority_over_active()`
- `test_find_spec_file_in_active()`
- `test_find_spec_file_not_found()`

---

### `TestFindSpecsCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:107`

**Description:**
> Tests for find-specs command.

**Methods:**
- `test_find_specs_basic()`
- `test_find_specs_verbose()`

---

### `TestFindSpecsDirectory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_paths.py:12`

**Description:**
> Tests for find_specs_directory function.

**Methods:**
- `test_find_specs_from_project_root()`
- `test_find_specs_with_explicit_path()`
- `test_find_specs_returns_none_when_not_found()`
- `test_find_specs_validates_structure()`
- `test_find_specs_from_subdirectory()`

---

### `TestFindTests`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py:68`

**Description:**
> Tests for find_tests function.

**Methods:**
- `test_find_tests_in_node_project()`
- `test_find_tests_in_python_project()`
- `test_find_tests_detects_framework()`
- `test_find_corresponding_test_file()`
- `test_find_tests_empty_project()`

---

### `TestFixCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:127`

**Description:**
> Tests for the fix command.

**Methods:**
- `test_fix_preview_clean_spec()`
- `test_fix_preview_with_issues()`
- `test_fix_preview_json()`
- `test_fix_dry_run()`
- `test_fix_apply_creates_backup()`
- `test_fix_apply_no_backup()`
- `test_fix_apply_json_output()`

---

### `TestFormatCompletionPrompt`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:708`

**Description:**
> Tests for format_completion_prompt() function.

**Methods:**
- `test_spec_level_prompt_with_hours()`
- `test_spec_level_prompt_without_hours_estimate()`
- `test_phase_level_prompt_with_hours()`
- `test_phase_level_prompt_without_hours()`
- `test_show_hours_input_disabled()`
- `test_empty_spec_prompt()`
- `test_nested_task_hierarchy()`
- `test_no_spec_data()`
- `test_invalid_phase_id()`
- `test_no_hierarchy()`
- `test_node_without_title()`
- `test_estimated_hours_zero()`
- `test_prompt_text_structure()`
- `test_completion_context_completeness()`

---

### `TestFormatOutputEnhanced`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_dev_tools/test_sdd_start_helper.py:107`

**Description:**
> Tests for enhanced format_output with last-accessed task info.

**Methods:**
- `test_format_output_shows_last_task()`
- `test_format_output_no_last_task()`
- `test_format_output_no_active_specs()`
- `test_format_output_no_specs_directory()`

---

### `TestFormatVerificationSummary`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_verification.py:219`

**Description:**
> Test format_verification_summary() function.

**Methods:**
- `test_format_verification_summary_all_passed()`
- `test_format_verification_summary_mixed_results()`
- `test_format_verification_summary_empty_list()`
- `test_format_verification_summary_includes_command()`
- `test_format_verification_summary_includes_notes()`

---

### `TestFrameworkDetection`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:21`

**Description:**
> Tests for detect_framework().

**Methods:**
- `test_detect_fastapi()`
- `test_detect_django()`
- `test_detect_flask()`
- `test_detect_multiple_frameworks()`
- `test_detect_no_framework()`
- `test_confidence_scores()`

---

### `TestGenerateSpecWithCategory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_templates.py:174`

**Description:**
> Test cases for generate_spec_from_template with default_category.

**Methods:**
- `test_generate_spec_with_category()`
- `test_generate_spec_without_category()`
- `test_generate_spec_all_categories()`
- `test_generate_spec_category_none()`

---

### `TestGetAllTasksInSubtree`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:49`

**Description:**
> Tests for get_all_tasks_in_subtree() function.

**Methods:**
- `test_single_task()`
- `test_nested_tasks()`
- `test_only_tasks_included()`
- `test_empty_hierarchy()`
- `test_node_with_no_children()`

---

### `TestGetJournalEntries`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:551`

**Description:**
> Tests for get_journal_entries function.

**Methods:**
- `test_get_all_journal_entries()`
- `test_get_journal_entries_filtered_by_task()`
- `test_get_journal_entries_empty()`
- `test_get_journal_entries_no_matching_task()`
- `test_get_journal_entries_invalid_spec()`

---

### `TestGetNextTask`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py:14`

**Description:**
> Tests for get_next_task function.

**Methods:**
- `test_get_next_task_returns_first_pending()`
- `test_get_next_task_skips_completed()`
- `test_get_next_task_respects_dependencies()`
- `test_get_next_task_from_current_phase()`
- `test_get_next_task_none_when_all_complete()`
- `test_get_next_task_empty_hierarchy()`
- `test_get_next_task_finds_verify_tasks()`

---

### `TestGetNode`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:197`

**Description:**
> Tests for get_node function.

**Methods:**
- `test_get_existing_task_node()`
- `test_get_existing_phase_node()`
- `test_get_nonexistent_node()`
- `test_get_node_from_empty_hierarchy()`
- `test_get_node_validates_structure()`

---

### `TestGetProgressSummary`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py:18`

**Description:**
> Tests for get_progress_summary function.

**Methods:**
- `test_get_progress_summary_simple_spec()`
- `test_progress_summary_calculates_percentage()`
- `test_progress_summary_with_all_completed()`
- `test_progress_summary_includes_current_phase()`

---

### `TestGetSessionInfo`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_dev_tools/test_sdd_start_helper.py:22`

**Description:**
> Tests for get_session_info command.

**Methods:**
- `test_get_session_info_with_last_task()`
- `test_get_session_info_no_last_task()`
- `test_get_session_info_no_specs_dir()`

---

### `TestGetSessionState`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_integrations.py:663`

**Description:**
> Tests for get_session_state function.

**Methods:**
- `test_no_specs_directory()`
- `test_active_specs_found()`
- `test_multiple_in_progress_tasks()`
- `test_completed_specs_ignored()`
- `test_invalid_json_specs_skipped()`

---

### `TestGetTask`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:129`

**Description:**
> Tests for get_task function.

**Methods:**
- `test_get_existing_task()`
- `test_get_task_with_metadata()`
- `test_get_task_with_dependencies()`
- `test_get_nonexistent_task()`
- `test_get_task_invalid_spec()`

---

### `TestGetTaskCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:188`

**Description:**
> Tests for get-task command.

**Methods:**
- `test_get_task_basic()`
- `test_get_task_json()`
- `test_get_task_nonexistent()`

---

### `TestGetTaskContextFromDocs`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py:95`

**Description:**
> Tests for get_task_context_from_docs function.

**Methods:**
- `test_get_context_success()`
- `test_get_context_tool_unavailable()`
- `test_get_context_command_failed()`
- `test_get_context_timeout()`
- `test_get_context_invalid_json()`

---

### `TestGetTaskInfo`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py:118`

**Description:**
> Tests for get_task_info function.

**Methods:**
- `test_get_task_info_existing_task()`
- `test_get_task_info_nonexistent_task()`
- `test_get_task_info_includes_all_fields()`
- `test_get_task_info_for_different_tasks()`

---

### `TestGetTaskJournal`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:732`

**Description:**
> Tests for get_task_journal function.

**Methods:**
- `test_get_task_journal()`

---

### `TestGetTaskWithJournal`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:773`

**Description:**
> Tests for get_task with include_journal parameter.

**Methods:**
- `test_get_task_with_journal()`
- `test_get_task_without_journal()`
- `test_get_task_with_journal_no_entries()`

---

### `TestGlobalFlags`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:327`

**Description:**
> Tests for global flags.

**Methods:**
- `test_quiet_flag()`
- `test_no_color_flag()`
- `test_verbose_flag()`
- `test_help_flag()`

---

### `TestGlobalFlags`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:161`

**Description:**
> Tests for global flags (--json, --quiet, --verbose).

**Methods:**
- `test_json_flag()`
- `test_quiet_flag()`
- `test_verbose_flag()`

---

### `TestGoParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_go.py:17`

**Description:**
> Test Go parser functionality.

**Methods:**
- `parser()`
- `test_parse_simple_function()`
- `test_parse_function_with_parameters()`
- `test_parse_multiple_return_values()`
- `test_parse_struct()`
- `test_parse_interface()`
- `test_parse_method()`
- `test_parse_imports()`
- `test_parse_package_name()`
- `test_parse_empty_file()`
- `test_line_counting()`

---

### `TestHTMLParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_html.py:17`

**Description:**
> Test HTML parser functionality.

**Methods:**
- `parser()`
- `test_parse_simple_html()`
- `test_parse_htmx_attributes()`
- `test_parse_custom_data_attributes()`
- `test_count_elements()`
- `test_parse_empty_html()`
- `test_line_counting()`

---

### `TestHTMLParserAdvanced`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_html.py:141`

**Description:**
> Advanced HTML parser tests.

**Methods:**
- `parser()`
- `test_parse_forms()`
- `test_parse_scripts_and_styles()`
- `test_parse_semantic_html5()`

---

### `TestInferTaskCategory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_templates.py:16`

**Description:**
> Test cases for infer_task_category() function.

**Methods:**
- `test_investigation_keywords()`
- `test_implementation_keywords()`
- `test_refactoring_keywords()`
- `test_decision_keywords()`
- `test_research_keywords()`
- `test_default_fallback()`
- `test_case_insensitivity()`
- `test_priority_order()`
- `test_empty_and_none_handling()`
- `test_task_type_parameter()`
- `test_multi_word_phrases()`

---

### `TestInitEnvironment`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_workflow.py:9`

**Description:**
> Tests for init_environment function.

**Methods:**
- `test_init_environment_from_specs_dir()`
- `test_init_environment_creates_directories()`

---

### `TestIntegrationWithGetSessionState`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_dev_tools/test_sdd_start_helper.py:234`

**Description:**
> Integration tests to ensure sdd_start_helper properly uses get_session_state.

**Methods:**
- `test_get_session_state_called_with_correct_path()`
- `test_multiple_in_progress_tasks_display()`

---

### `TestIsTaskComplete`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:16`

**Description:**
> Tests for is_task_complete() function.

**Methods:**
- `test_completed_task()`
- `test_pending_task()`
- `test_in_progress_task()`
- `test_blocked_task()`
- `test_no_status()`
- `test_none_task()`

---

### `TestJavaScriptParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_javascript.py:17`

**Description:**
> Test JavaScript parser functionality.

**Methods:**
- `parser()`
- `test_parse_simple_function()`
- `test_parse_arrow_function()`
- `test_parse_async_function()`
- `test_parse_simple_class()`
- `test_parse_class_with_inheritance()`
- `test_parse_imports()`
- `test_parse_exports()`
- `test_parse_typescript_types()`
- `test_parse_jsx_component()`
- `test_parse_empty_file()`
- `test_line_counting()`

---

### `TestJsonSpecIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:248`

**Description:**
> Integration tests for JSON spec operations.

**Methods:**
- `test_load_modify_save_workflow()`
- `test_backup_before_modification()`

---

### `TestJsonSpecValidationIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:559`

**Description:**
> Integration tests for state validation.

**Methods:**
- `test_complete_validation_workflow()`
- `test_validation_catches_multiple_issues()`

---

### `TestKeyFileIdentification`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:74`

**Description:**
> Tests for identify_key_files().

**Methods:**
- `test_identify_main_py()`
- `test_identify_config_files()`
- `test_prioritize_root_files()`
- `test_prioritize_with_docstrings()`
- `test_exclude_test_files_from_top()`
- `test_limit_key_files()`
- `test_with_readme()`

---

### `TestLanguageEnum`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_base.py:18`

**Description:**
> Test Language enum.

**Methods:**
- `test_language_values()`
- `test_language_from_string()`

---

### `TestLayerDetection`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:134`

**Description:**
> Tests for detect_layers().

**Methods:**
- `test_detect_routers_layer()`
- `test_detect_models_layer()`
- `test_detect_services_layer()`
- `test_detect_repositories_layer()`
- `test_detect_utils_layer()`
- `test_detect_middleware_layer()`
- `test_detect_config_layer()`
- `test_detect_tests_layer()`

---

### `TestListBlockers`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:491`

**Description:**
> Tests for list_blockers function.

**Methods:**
- `test_list_blocked_tasks()`
- `test_list_no_blockers()`
- `test_list_blockers_metadata()`
- `test_list_blockers_invalid_spec()`

---

### `TestListBlockersCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:416`

**Description:**
> Tests for list-blockers command.

**Methods:**
- `test_list_blockers_basic()`
- `test_list_blockers_json()`
- `test_list_blockers_no_blockers()`

---

### `TestListPhases`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py:74`

**Description:**
> Tests for list_phases function.

**Methods:**
- `test_list_phases_returns_all_phases()`
- `test_list_phases_structure()`
- `test_list_phases_calculates_task_counts()`
- `test_list_phases_with_complex_spec()`

---

### `TestListPhases`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:199`

**Description:**
> Tests for list_phases function.

**Methods:**
- `test_list_all_phases()`
- `test_list_phases_with_progress()`
- `test_list_phases_invalid_spec()`
- `test_list_phases_empty()`

---

### `TestListPhasesCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:241`

**Description:**
> Tests for list-phases command.

**Methods:**
- `test_list_phases_basic()`
- `test_list_phases_json()`
- `test_list_phases_help()`

---

### `TestListPhasesCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:273`

**Description:**
> Tests for list-phases command.

**Methods:**
- `test_list_phases()`
- `test_list_phases_json()`

---

### `TestLoadJsonSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:71`

**Description:**
> Tests for ``load_json_spec`` function.

**Methods:**
- `test_load_existing_json_spec()`
- `test_load_nonexistent_json_spec()`
- `test_load_invalid_json_spec()`
- `test_load_json_spec_with_dependencies()`

---

### `TestMoveSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_lifecycle.py:12`

**Description:**
> Test move_spec() function.

**Methods:**
- `test_move_spec_to_completed()`
- `test_move_spec_to_archived()`
- `test_move_spec_to_active()`
- `test_move_spec_invalid_target()`
- `test_move_spec_file_not_found()`
- `test_move_spec_target_exists()`
- `test_move_spec_dry_run()`

---

### `TestNextCommands`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:78`

**Description:**
> Tests for sdd-next commands (flat structure).

**Methods:**
- `test_verify_tools()`
- `test_find_specs()`

---

### `TestNextTaskCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:132`

**Description:**
> Tests for next-task command.

**Methods:**
- `test_next_task_success()`
- `test_next_task_json_output()`
- `test_next_task_nonexistent_spec()`

---

### `TestParseResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_base.py:104`

**Description:**
> Test ParseResult aggregation.

**Methods:**
- `test_empty_parse_result()`
- `test_parse_result_with_data()`
- `test_parse_result_merge()`

---

### `TestParsedDataStructures`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_base.py:37`

**Description:**
> Test parsed data structures.

**Methods:**
- `test_parsed_parameter_creation()`
- `test_parsed_function_creation()`
- `test_parsed_class_creation()`
- `test_parsed_module_creation()`

---

### `TestParserFactory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_factory.py:11`

**Description:**
> Test ParserFactory functionality.

**Methods:**
- `test_factory_creation()`
- `test_factory_with_languages_filter()`
- `test_factory_with_exclude_patterns()`
- `test_detect_languages_empty_project()`
- `test_detect_languages_python_project()`
- `test_detect_languages_multi_language_project()`
- `test_get_parser_for_language_python()`
- `test_get_parser_for_language_javascript()`
- `test_get_parser_for_language_unknown()`
- `test_parse_all_empty_project()`
- `test_parse_all_python_project()`
- `test_parse_all_with_language_filter()`
- `test_parse_all_respects_exclude_patterns()`

---

### `TestParserFactoryMultiLanguage`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_factory.py:174`

**Description:**
> Integration tests for multi-language parsing.

**Methods:**
- `test_parse_mixed_language_project()`
- `test_statistics_across_languages()`
- `test_verbose_output()`

---

### `TestPathIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_paths.py:193`

**Description:**
> Integration tests for path utilities.

**Methods:**
- `test_path_resolution_with_symlinks()`
- `test_specs_directory_traversal()`

---

### `TestPhaseTime`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:351`

**Description:**
> Tests for phase_time function.

**Methods:**
- `test_phase_with_time_data()`
- `test_phase_without_time_data()`
- `test_phase_time_variance_positive()`
- `test_phase_time_variance_negative()`
- `test_phase_time_nonexistent_phase()`
- `test_phase_time_invalid_spec()`

---

### `TestPhaseTimeCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:362`

**Description:**
> Tests for phase-time command.

**Methods:**
- `test_phase_time_basic()`
- `test_phase_time_json()`
- `test_phase_time_nonexistent_phase()`

---

### `TestPrepareTask`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py:213`

**Description:**
> Tests for prepare_task function.

**Methods:**
- `test_prepare_task_success()`
- `test_prepare_task_includes_dependencies()`
- `test_prepare_task_returns_metadata_only()`
- `test_prepare_task_nonexistent()`
- `test_prepare_task_auto_finds_next()`

---

### `TestPrettyPrinterColorMode`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:103`

**Description:**
> Tests for color/no-color modes.

**Methods:**
- `test_colored_output_contains_ansi_codes()`
- `test_no_color_output_lacks_ansi_codes()`

---

### `TestPrettyPrinterFormatting`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:165`

**Description:**
> Tests for message formatting.

**Methods:**
- `test_result_formatting_aligns_output()`
- `test_detail_with_indentation()`

---

### `TestPrettyPrinterInit`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:12`

**Description:**
> Tests for PrettyPrinter initialization.

**Methods:**
- `test_printer_default_initialization()`
- `test_printer_with_no_color()`
- `test_printer_with_verbose()`
- `test_printer_with_quiet()`

---

### `TestPrettyPrinterIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:197`

**Description:**
> Integration tests for PrettyPrinter.

**Methods:**
- `test_printer_combined_output_flow()`
- `test_printer_error_warning_flow()`

---

### `TestPrettyPrinterMethods`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:43`

**Description:**
> Tests for PrettyPrinter methods.

**Methods:**
- `test_printer_success_message()`
- `test_printer_error_message()`
- `test_printer_warning_message()`
- `test_printer_info_message()`
- `test_printer_action_message()`
- `test_printer_result_message()`
- `test_printer_detail_message()`

---

### `TestPrettyPrinterVerbosity`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py:128`

**Description:**
> Tests for verbosity modes.

**Methods:**
- `test_quiet_mode_minimal_output()`
- `test_quiet_mode_shows_errors()`
- `test_verbose_mode_shows_details()`

---

### `TestProgressCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:242`

**Description:**
> Tests for progress command.

**Methods:**
- `test_progress_command()`
- `test_progress_json()`

---

### `TestProgressIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py:180`

**Description:**
> Integration tests for progress calculation.

**Methods:**
- `test_complete_workflow_progress_tracking()`

---

### `TestProjectIntegration`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py:219`

**Description:**
> Integration tests for project analysis.

**Methods:**
- `test_complete_project_analysis_workflow()`
- `test_python_project_full_analysis()`

---

### `TestPromptContentValidation`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py:182`

**Description:**
> Tests to ensure prompts contain critical information.

**Methods:**
- `test_architecture_prompt_has_output_format()`
- `test_architecture_prompt_requests_component_analysis()`
- `test_ai_context_prompt_limits_output()`
- `test_prompts_include_context_summary()`

---

### `TestPromptFormatting`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py:20`

**Description:**
> Tests for prompt formatting functions.

**Methods:**
- `test_format_architecture_prompt_structure()`
- `test_format_architecture_prompt_key_files()`
- `test_format_ai_context_prompt_structure()`
- `test_format_ai_context_prompt_concise()`

---

### `TestPythonParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:11`

**Description:**
> Test Python parser functionality.

**Methods:**
- `parser()`
- `test_parse_simple_function()`
- `test_parse_function_with_parameters()`
- `test_parse_async_function()`
- `test_parse_function_with_decorators()`
- `test_parse_simple_class()`
- `test_parse_class_with_inheritance()`
- `test_parse_class_with_properties()`
- `test_parse_imports()`
- `test_parse_module_docstring()`
- `test_calculate_complexity()`
- `test_parse_empty_file()`
- `test_parse_syntax_error_file()`
- `test_line_counting()`

---

### `TestPythonParserAdvanced`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:252`

**Description:**
> Advanced Python parser tests.

**Methods:**
- `parser()`
- `test_parse_nested_classes()`
- `test_parse_class_methods()`
- `test_parse_type_hints()`

---

### `TestPythonParserCrossReferences`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:314`

**Description:**
> Test cross-reference tracking in Python parser.

**Methods:**
- `parser()`
- `test_track_simple_function_call()`
- `test_track_nested_function_calls()`
- `test_track_method_calls()`
- `test_track_calls_in_class_methods()`
- `test_track_module_level_calls()`
- `test_cross_reference_bidirectional()`
- `test_cross_reference_in_result()`
- `test_multiple_callers()`
- `test_call_tracking_with_decorators()`
- `test_empty_file_has_graph()`
- `test_line_numbers_tracked()`
- `test_import_tracking_integration()`
- `test_class_instantiation_detection()`
- `test_instantiation_vs_function_call()`
- `test_method_call_not_instantiation()`
- `test_multiple_instantiations()`
- `test_module_level_instantiation()`
- `test_get_instantiators_method()`
- `test_get_imports_method()`
- `test_bidirectional_symmetry_complete()`
- `test_get_instantiators_empty_result()`

---

### `TestPythonParserDynamicPatterns`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:856`

**Description:**
> Test dynamic pattern warning detection.

**Methods:**
- `parser()`
- `test_decorator_warning()`
- `test_eval_exec_warning()`
- `test_getattr_setattr_warning()`
- `test_dynamic_import_warning()`
- `test_warning_statistics()`
- `test_no_warnings_for_clean_code()`
- `test_warnings_in_to_dict()`
- `test_decorator_in_class_method()`
- `test_module_level_dynamic_pattern()`

---

### `TestQueryTasks`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py:26`

**Description:**
> Tests for query_tasks function.

**Methods:**
- `test_query_all_tasks()`
- `test_query_by_status_pending()`
- `test_query_by_status_blocked()`
- `test_query_by_status_completed()`
- `test_query_by_type_task()`
- `test_query_by_type_phase()`
- `test_query_by_parent()`
- `test_query_invalid_spec_id()`

---

### `TestQueryTasksCLI`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:99`

**Description:**
> Tests for query-tasks command.

**Methods:**
- `test_query_tasks_basic()`
- `test_query_tasks_status_filter()`
- `test_query_tasks_type_filter()`
- `test_query_tasks_format_simple()`
- `test_query_tasks_json_output()`
- `test_query_tasks_invalid_spec()`

---

### `TestReadingOrder`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:194`

**Description:**
> Tests for suggest_reading_order().

**Methods:**
- `test_reading_order_entry_first()`
- `test_reading_order_config_early()`
- `test_reading_order_models_before_routes()`

---

### `TestReadmeExtraction`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py:230`

**Description:**
> Tests for extract_readme().

**Methods:**
- `test_extract_readme_md()`
- `test_extract_readme_not_found()`

---

### `TestRecalculateProgress`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py:116`

**Description:**
> Tests for recalculate_progress function.

**Methods:**
- `test_recalculate_progress_updates_counts()`
- `test_recalculate_progress_propagates_to_parents()`

---

### `TestReportCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:192`

**Description:**
> Tests for the report command.

**Methods:**
- `test_report_markdown()`
- `test_report_json()`
- `test_report_stdout()`
- `test_report_with_dependencies()`
- `test_report_json_stdout()`
- `test_report_with_bottleneck_threshold()`

---

### `TestRoutingMatrix`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py:162`

**Description:**
> Tests for documentation type routing.

**Methods:**
- `test_routing_matrix_has_architecture()`
- `test_routing_matrix_has_ai_context()`
- `test_routing_matrix_valid_tools()`

---

### `TestSaveJsonSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py:108`

**Description:**
> Tests for save_json_spec function.

**Methods:**
- `test_save_new_json_spec()`
- `test_save_updates_existing_json_spec()`
- `test_save_json_spec_with_nonexistent_path_creates_dir()`

---

### `TestSchemaEnhancements`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py:1109`

**Description:**
> Test schema v1.1 enhancements with cross-reference fields.

**Methods:**
- `parser()`
- `test_call_reference_creation()`
- `test_call_reference_to_dict()`
- `test_enhance_function_with_callers()`
- `test_enhance_function_with_calls()`
- `test_enhance_function_with_call_count()`
- `test_enhance_function_without_call_count()`
- `test_enhance_function_preserves_base_fields()`
- `test_enhance_function_with_empty_cross_refs()`
- `test_enhance_function_with_none_cross_refs()`
- `test_enhance_function_complete_example()`
- `test_schema_version_constants()`
- `test_call_reference_different_types()`
- `test_enhance_with_method_calls()`

---

### `TestShouldGenerateDocs`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py:163`

**Description:**
> Tests for should_generate_docs function.

**Methods:**
- `test_should_not_generate_if_available()`
- `test_should_generate_if_missing()`
- `test_interactive_mode()`

---

### `TestShouldPromptCompletion`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py:502`

**Description:**
> Tests for should_prompt_completion() function.

**Methods:**
- `test_should_prompt_when_complete_and_no_blocks()`
- `test_should_not_prompt_when_incomplete()`
- `test_should_not_prompt_when_blocked_tasks_exist()`
- `test_should_not_prompt_when_in_progress()`
- `test_phase_level_prompt_check()`
- `test_all_complete_but_has_blocked_tasks()`
- `test_empty_spec_should_prompt()`
- `test_error_handling_no_spec_data()`
- `test_error_handling_no_hierarchy()`
- `test_error_handling_invalid_phase_id()`

---

### `TestSpecStats`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_validation.py:130`

**Description:**
> Tests for spec_stats function.

**Methods:**
- `test_spec_stats_basic()`
- `test_spec_stats_counts()`
- `test_spec_stats_with_json_spec()`
- `test_spec_stats_nonexistent()`

---

### `TestStatsCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:252`

**Description:**
> Tests for the stats command.

**Methods:**
- `test_stats_basic()`
- `test_stats_json()`
- `test_stats_deep_hierarchy()`
- `test_stats_verification_coverage()`

---

### `TestStatusReportCompletion`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_status_report.py:78`

**Description:**
> Tests for status-report completion detection.

**Methods:**
- `test_completion_message_in_status_report()`
- `test_non_interactive_behavior()`
- `test_command_hint_displayed()`
- `test_incomplete_spec_no_completion_message()`

---

### `TestSyncMetadataFromState`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_journal.py:312`

**Description:**
> Test sync_metadata_from_state() function.

**Methods:**
- `test_sync_metadata_calculates_progress()`
- `test_sync_metadata_sets_completed_status()`
- `test_sync_metadata_finds_current_phase()`
- `test_sync_metadata_dry_run()`

---

### `TestTaskInfoCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:172`

**Description:**
> Tests for task-info command.

**Methods:**
- `test_task_info_success()`
- `test_task_info_json()`

---

### `TestTemplates`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_templates.py:152`

**Description:**
> Test cases for template management functions.

**Methods:**
- `test_list_templates_returns_dict()`
- `test_get_template_valid()`
- `test_get_template_invalid()`

---

### `TestToolSelection`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py:86`

**Description:**
> Tests for AI tool selection.

**Methods:**
- `test_get_best_tool_for_architecture()`
- `test_get_best_tool_fallback()`
- `test_get_best_tool_no_tools()`
- `test_get_best_tool_unknown_type()`

---

### `TestTypeScriptParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_javascript.py:227`

**Description:**
> Test TypeScript-specific parsing.

**Methods:**
- `parser()`
- `test_parse_interface()`
- `test_parse_type_alias()`
- `test_parse_enum()`
- `test_parse_generic_function()`
- `test_parse_tsx_component()`

---

### `TestUnifiedCLIBasics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:41`

**Description:**
> Basic unified CLI functionality tests.

**Methods:**
- `test_cli_help()`
- `test_cli_no_args()`
- `test_cli_version_implicit()`

---

### `TestUpdateCommands`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:109`

**Description:**
> Tests for sdd-update commands (flat structure).

**Methods:**
- `test_status_report_help()`
- `test_update_command_exists()`

---

### `TestUpdateMetadata`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_journal.py:141`

**Description:**
> Test update_metadata() function.

**Methods:**
- `test_update_metadata_simple()`
- `test_update_metadata_numeric_value()`
- `test_update_metadata_creates_metadata_object()`
- `test_update_metadata_dry_run()`

---

### `TestUpdateParentStatus`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py:149`

**Description:**
> Tests for update_parent_status function.

**Methods:**
- `test_update_parent_when_all_children_complete()`
- `test_update_parent_when_some_children_in_progress()`

---

### `TestUpdateTaskStatus`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_status.py:16`

**Description:**
> Test update_task_status() function.

**Methods:**
- `_create_test_spec()`
- `test_started_at_resets_on_each_in_progress_transition()`
- `test_started_at_set_on_first_in_progress()`
- `test_completed_at_set_on_completion()`

---

### `TestUpdatedCLICommands`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:468`

**Description:**
> Tests for updated CLI commands using new JSON-only signatures.

**Methods:**
- `test_add_journal_new_signature()`
- `test_add_journal_with_task_id()`
- `test_add_journal_custom_author()`
- `test_sync_metadata_new_command()`
- `test_add_verification_new_signature()`
- `test_add_verification_failed_status()`
- `test_bulk_journal_new_signature()`
- `test_bulk_journal_specific_tasks()`

---

### `TestValidateCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:42`

**Description:**
> Tests for the validate command.

**Methods:**
- `test_validate_clean_spec_exit_0()`
- `test_validate_warnings_spec_exit_1()`
- `test_validate_errors_spec_exit_2()`
- `test_validate_json_output()`
- `test_validate_json_verbose()`
- `test_validate_verbose_output()`
- `test_validate_nonexistent_file()`
- `test_validate_with_report()`
- `test_validate_with_report_json_format()`

---

### `TestValidateCommands`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:135`

**Description:**
> Tests for sdd-validate commands (flat structure).

**Methods:**
- `test_validate_help()`
- `test_validate_command_exists()`

---

### `TestValidateDependencies`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:226`

**Description:**
> Tests for validate_dependencies function.

**Methods:**
- `test_valid_dependencies()`
- `test_circular_dependencies()`
- `test_dependency_on_nonexistent_task()`
- `test_bidirectional_dependency_consistency()`

---

### `TestValidateHierarchy`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:74`

**Description:**
> Tests for validate_hierarchy function.

**Methods:**
- `test_valid_hierarchy()`
- `test_orphaned_nodes()`
- `test_circular_parent_child()`

---

### `TestValidateJsonSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:499`

**Description:**
> Tests for validate_spec_hierarchy main function.

**Methods:**
- `test_validate_valid_json_spec()`
- `test_validate_state_with_structure_issues()`
- `test_validate_state_with_circular_deps()`
- `test_validate_state_with_orphaned_nodes()`
- `test_validation_result_structure()`
- `test_validation_counts_nodes_correctly()`

---

### `TestValidateMetadata`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:293`

**Description:**
> Tests for validate_metadata function.

**Methods:**
- `test_valid_metadata()`
- `test_task_missing_file_path()`
- `test_implementation_task_requires_file_path()`
- `test_investigation_task_no_file_path_required()`
- `test_missing_category_defaults_to_implementation()`
- `test_invalid_task_category_rejected()`
- `test_investigation_task_with_file_path_warns()`
- `test_backward_compat_no_category_with_file_path()`
- `test_backward_compat_old_style_spec()`

---

### `TestValidateNodes`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:122`

**Description:**
> Tests for validate_nodes function.

**Methods:**
- `test_valid_nodes()`
- `test_node_missing_required_fields()`
- `test_invalid_node_status()`
- `test_invalid_node_type()`

---

### `TestValidatePath`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_paths.py:64`

**Description:**
> Tests for validate_path function.

**Methods:**
- `test_validate_existing_file()`
- `test_validate_existing_directory()`
- `test_validate_nonexistent_path()`
- `test_validate_relative_path()`
- `test_validate_path_with_string_input()`
- `test_validate_multiple_paths()`

---

### `TestValidatePaths`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_validation.py:97`

**Description:**
> Tests for validate_paths function.

**Methods:**
- `test_validate_existing_paths()`
- `test_validate_mixed_paths()`
- `test_validate_paths_with_base_dir()`

---

### `TestValidateSpec`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_validation.py:14`

**Description:**
> Tests for validate_spec function.

**Methods:**
- `test_validate_valid_spec()`
- `test_validate_invalid_spec()`
- `test_validate_spec_checks_frontmatter()`
- `test_validate_spec_checks_json_spec()`
- `test_validate_nonexistent_spec()`

---

### `TestValidateSpecBeforeProceed`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_integrations.py:22`

**Description:**
> Tests for validate_spec_before_proceed function.

**Methods:**
- `test_valid_spec()`
- `test_spec_with_errors()`
- `test_spec_with_warnings()`
- `test_file_not_found()`
- `test_invalid_json()`
- `test_autofix_detection()`

---

### `TestValidateStructure`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:24`

**Description:**
> Tests for validate_structure function.

**Methods:**
- `test_valid_structure()`
- `test_missing_required_fields()`
- `test_empty_hierarchy()`
- `test_invalid_json_types()`

---

### `TestValidateTaskCounts`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py:182`

**Description:**
> Tests for validate_task_counts function.

**Methods:**
- `test_valid_task_counts()`
- `test_children_count_mismatch()`

---

### `TestValidateTimestampPair`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_time_tracking.py:213`

**Description:**
> Test validate_timestamp_pair() function.

**Methods:**
- `test_validate_timestamp_pair_valid()`
- `test_validate_timestamp_pair_none_start()`
- `test_validate_timestamp_pair_none_end()`
- `test_validate_timestamp_pair_empty_start()`
- `test_validate_timestamp_pair_invalid_format()`
- `test_validate_timestamp_pair_negative_disallowed()`
- `test_validate_timestamp_pair_negative_allowed()`
- `test_validate_timestamp_pair_with_printer()`

---

### `TestVerifyToolsCommand`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:93`

**Description:**
> Tests for verify-tools command.

**Methods:**
- `test_verify_tools_success()`

---

### `TokenMetrics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/parser.py:10`

**Description:**
> Token usage metrics extracted from a transcript.

**Properties:**
- `context_percentage`

---


## ⚡ Functions

### `_auto_register_parsers(factory) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/factory.py:249`
**Complexity:** 6

**Description:**
> Auto-register all available parsers.

This function attempts to import and register all known parsers.
If a parser's dependencies aren't available, it's skipped silently.

**Parameters:**
- `factory`: ParserFactory

---

### `_build_bidirectional_deps_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:643`
⚠️ **Complexity:** 11 (High)

**Description:**
> Synchronize bidirectional dependency relationships.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_counts_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:191`
**Complexity:** 4

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_date_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:355`
**Complexity:** 5

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_empty_title_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:522`
**Complexity:** 7

**Description:**
> Generate title from node ID for nodes with empty titles.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_enhanced_errors(messages) -> List[EnhancedError]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:124`
**Complexity:** 4

**Parameters:**
- `messages`: Iterable[str]

---

### `_build_hierarchy_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:319`
**Complexity:** 9

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_invalid_type_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:554`
**Complexity:** 6

**Description:**
> Normalize invalid node types.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_journal_entry(title, content, entry_type, author, task_id) -> Tuple[Dict[str, Any], str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:88`
**Complexity:** 2

**Description:**
> Construct a journal entry payload and return entry plus timestamp.

**Parameters:**
- `title`: str
- `content`: str
- `entry_type`: str
- `author`: str
- `task_id`: Optional[str]

---

### `_build_leaf_count_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:739`
**Complexity:** 9

**Description:**
> Fix leaf node total_tasks to be 1.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_metadata_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:213`
**Complexity:** 8

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_missing_deps_structure_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:703`
**Complexity:** 7

**Description:**
> Create dependencies dict structure.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_missing_fields_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:467`
⚠️ **Complexity:** 15 (High)

**Description:**
> Add missing required node fields with sensible defaults.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_orphan_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:772`
**Complexity:** 9

**Description:**
> Handle orphaned nodes by attaching to spec-root.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_placeholder_file_path_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:818`
⚠️ **Complexity:** 13 (High)

**Description:**
> Detect and flag placeholder file_path values for migration.

Detects file_path values that are actually placeholders like:
- investigation, implementation, refactoring, decision, research (category names)
- TBD, tbd, N/A, none, null (placeholder text)

These indicate old specs that need migration to use task_category instead.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_status_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:380`
**Complexity:** 8

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_task_category_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:250`
**Complexity:** 10

**Description:**
> Build auto-fix for missing or invalid task_category in task nodes.

This builder is special - it can be triggered by any metadata-related error on a task node,
not just task_category-specific errors. It proactively adds task_category to tasks that are
missing it, even when the validation doesn't report it as an error (backward compatibility).

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_build_tool_commands(failure_type) -> Dict[str, List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:299`
**Complexity:** 1

**Description:**
> Build tool command templates from configuration.

Args:
    failure_type: Optional failure type for model override selection

Returns:
    Dict mapping tool names to command templates

**Parameters:**
- `failure_type`: Optional[str]

---

### `_build_verification_type_action(error, spec_data) -> Optional[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:610`
**Complexity:** 9

**Description:**
> Fix verification_type for verify nodes.

**Parameters:**
- `error`: EnhancedError
- `spec_data`: Dict[str, Any]

---

### `_bump_version(current_version, bump) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:48`
**Complexity:** 5

**Description:**
> Determine the next semantic version based on bump type.

**Parameters:**
- `current_version`: Optional[str]
- `bump`: str

---

### `_calculate_diff(before, after, task_id) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:181`
**Complexity:** 8

**Parameters:**
- `before`: Dict[str, Any]
- `after`: Dict[str, Any]
- `task_id`: str

---

### `_category_from_field(field) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:57`
**Complexity:** 3

**Parameters:**
- `field`: str

---

### `_check_all_task_deps(spec_data, args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:439`
⚠️ **Complexity:** 12 (High)

**Description:**
> Check dependencies for all tasks in the spec.

**Parameters:**
- `spec_data`: None
- `args`: None
- `printer`: None

---

### `_clean_stale_sessions(dir_entry) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:222`
**Complexity:** 9

**Description:**
> Remove sessions with dead PIDs from the cache entry.

Modifies dir_entry in place.

Args:
    dir_entry: Directory entry from cache with 'sessions' dict

**Parameters:**
- `dir_entry`: None

---

### `_coerce_scalar(value) -> Any`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:139`
**Complexity:** 5

**Parameters:**
- `value`: str

---

### `_collect_messages(result, fields, severity) -> List[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:65`
**Complexity:** 4

**Parameters:**
- `result`: JsonSpecValidationResult
- `fields`: Iterable[str]
- `severity`: str

---

### `_compare_dicts(node_id, dict_name, before, after) -> List[FieldChange]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:142`
**Complexity:** 5

**Description:**
> Compare two dictionaries and return field changes.

**Parameters:**
- `node_id`: str
- `dict_name`: str
- `before`: Dict[str, Any]
- `after`: Dict[str, Any]

---

### `_compare_nodes(node_id, before, after) -> List[FieldChange]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:89`
**Complexity:** 6

**Description:**
> Compare two node dicts and return list of changes.

**Parameters:**
- `node_id`: str
- `before`: Dict[str, Any]
- `after`: Dict[str, Any]

---

### `_context_to_json(context) -> Dict[str, List[Dict[str, Any]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:172`
**Complexity:** 1

**Parameters:**
- `context`: Dict[str, List[QueryResult]]

---

### `_dependencies_to_dict(analysis) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:49`
**Complexity:** 2

**Parameters:**
- `analysis`: None

---

### `_derive_default_journal(task_id, task_title, actual_hours, note) -> Tuple[str, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:30`
**Complexity:** 4

**Parameters:**
- `task_id`: str
- `task_title`: str
- `actual_hours`: Optional[float]
- `note`: Optional[str]

---

### `_detect_source_directory() -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:17`
**Complexity:** 7

**Description:**
> Auto-detect the source directory for coverage reporting.

Returns:
    Source directory path if found, None otherwise

---

### `_determine_layer(file_path) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:303`
**Complexity:** 5

**Description:**
> Determine architectural layer from file path.

Args:
    file_path: Path to file

Returns:
    Layer name (Presentation, Business Logic, Data, Utility, Core, External)

**Parameters:**
- `file_path`: str

---

### `_determine_severity(message, severity_hint) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:40`
**Complexity:** 7

**Parameters:**
- `message`: str
- `severity_hint`: str

---

### `_dump_json(payload) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:82`
**Complexity:** 1

**Parameters:**
- `payload`: object

---

### `_dump_json(payload) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:46`
**Complexity:** 1

**Parameters:**
- `payload`: Any

---

### `_dump_json(payload) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:38`
**Complexity:** 1

**Parameters:**
- `payload`: Any

---

### `_ensure_journal_container(spec_data) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:114`
**Complexity:** 3

**Description:**
> Ensure spec_data has a journal container.

**Parameters:**
- `spec_data`: Dict[str, Any]

---

### `_ensure_metrics_dir() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:52`
**Complexity:** 1

**Description:**
> Ensure metrics directory exists.

---

### `_ensure_query(args, printer) -> Optional[DocumentationQuery]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:58`
⚠️ **Complexity:** 22 (High)

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `_exclude_patterns(extra) -> list[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:94`
**Complexity:** 2

**Parameters:**
- `extra`: Optional[Iterable[str]]

---

### `_extract_json_frontmatter(path) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:52`
**Complexity:** 10

**Parameters:**
- `path`: Path

---

### `_extract_location(message) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:30`
**Complexity:** 4

**Description:**
> Attempt to extract a node identifier from a validation message.

**Parameters:**
- `message`: str

---

### `_extract_markdown_frontmatter(path) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:87`
⚠️ **Complexity:** 14 (High)

**Parameters:**
- `path`: Path

---

### `_filter_actions_by_selection(actions, selection_criteria) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:84`
**Complexity:** 6

**Description:**
> Filter actions based on ID or category selection.

**Parameters:**
- `actions`: None
- `selection_criteria`: None

---

### `_find_entity(query, entity_name) -> Tuple[Optional[str], Optional[Dict[str, Any]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:128`
**Complexity:** 3

**Description:**
> Find entity and determine its type.

Args:
    query: DocumentationQuery instance
    entity_name: Name to search for

Returns:
    Tuple of (entity_type, entity_info) or (None, None) if not found

**Parameters:**
- `query`: Any
- `entity_name`: str

---

### `_format_age(seconds) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:1696`
**Complexity:** 4

**Description:**
> Format age in seconds as human-readable string.

**Parameters:**
- `seconds`: int

---

### `_format_issue(number, issue, brief) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:119`
**Complexity:** 5

**Description:**
> Format an issue for display.

**Parameters:**
- `number`: int
- `issue`: Dict[str, Any]
- `brief`: bool

---

### `_format_model_summary(model_data) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:145`
⚠️ **Complexity:** 15 (High)

**Description:**
> Format individual model response for display.

Args:
    model_data: Normalized model response data

Returns:
    List of formatted lines

**Parameters:**
- `model_data`: Dict[str, Any]

---

### `_format_value(value) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:256`
**Complexity:** 4

**Description:**
> Format a value for display in diff output.

**Parameters:**
- `value`: Any

---

### `_generate_feasibility_review_prompt(spec_content, spec_id, title) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:257`
**Complexity:** 1

**Description:**
> Generate feasibility-focused review prompt.

**Parameters:**
- `spec_content`: str
- `spec_id`: str
- `title`: str

---

### `_generate_full_review_prompt(spec_content, spec_id, title) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:100`
**Complexity:** 1

**Description:**
> Generate full comprehensive review prompt.

**Parameters:**
- `spec_content`: str
- `spec_id`: str
- `title`: str

---

### `_generate_quick_review_prompt(spec_content, spec_id, title) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:162`
**Complexity:** 1

**Description:**
> Generate quick review prompt focusing on completeness and clarity.

**Parameters:**
- `spec_content`: str
- `spec_id`: str
- `title`: str

---

### `_generate_security_review_prompt(spec_content, spec_id, title) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:199`
**Complexity:** 1

**Description:**
> Generate security-focused review prompt.

**Parameters:**
- `spec_content`: str
- `spec_id`: str
- `title`: str

---

### `_get_parent_pid(pid, system) -> Optional[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:54`
**Complexity:** 4

**Description:**
> Get the parent PID of a given process.

Args:
    pid: Process ID to get parent of
    system: Platform system name (Linux, Darwin, Windows)

Returns:
    Parent PID or None if not found

**Parameters:**
- `pid`: int
- `system`: str

---

### `_get_parent_pid_linux(pid) -> Optional[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:75`
**Complexity:** 5

**Description:**
> Get parent PID on Linux using /proc filesystem.

**Parameters:**
- `pid`: int

---

### `_get_parent_pid_macos(pid) -> Optional[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:99`
**Complexity:** 3

**Description:**
> Get parent PID on macOS using ps command.

**Parameters:**
- `pid`: int

---

### `_get_parent_pid_windows(pid) -> Optional[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:115`
**Complexity:** 5

**Description:**
> Get parent PID on Windows using wmic or psutil.

**Parameters:**
- `pid`: int

---

### `_get_presets() -> Dict[str, Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:48`
**Complexity:** 2

**Description:**
> Get preset configurations.

The coverage preset auto-detects the source directory to avoid hard-coding.

Returns:
    Dictionary of preset configurations

---

### `_get_process_info_linux(pid) -> Optional[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:322`
**Complexity:** 6

**Description:**
> Get process info on Linux using /proc filesystem.

**Parameters:**
- `pid`: int

---

### `_get_process_info_macos(pid) -> Optional[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:353`
**Complexity:** 5

**Description:**
> Get process info on macOS using ps command.

**Parameters:**
- `pid`: int

---

### `_get_process_info_windows(pid) -> Optional[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:389`
**Complexity:** 6

**Description:**
> Get process info on Windows using wmic or psutil.

**Parameters:**
- `pid`: int

---

### `_get_recommendation_summary(consensus, recommendation) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:84`
**Complexity:** 3

**Description:**
> Get summary text for recommendation.

**Parameters:**
- `consensus`: Dict[str, Any]
- `recommendation`: str

---

### `_get_score_assessment(score) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:105`
**Complexity:** 5

**Description:**
> Get qualitative assessment for a score.

**Parameters:**
- `score`: float

---

### `_get_timestamp() -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:26`
**Complexity:** 1

---

### `_handle_error(args, printer, exc) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:98`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter
- `exc`: Exception

---

### `_interactive_select_fixes(actions, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:102`
**Complexity:** 10

**Description:**
> Interactively prompt user to select fixes.

**Parameters:**
- `actions`: None
- `printer`: None

---

### `_is_auto_fixable(category, normalized_message) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:51`
⚠️ **Complexity:** 21 (High)

**Parameters:**
- `category`: str
- `normalized_message`: str

---

### `_is_test_environment() -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:28`
**Complexity:** 4

**Description:**
> Detect if we're running in a test environment.

Returns True if any of the following conditions are met:
1. pytest is loaded in sys.modules
2. PYTEST_CURRENT_TEST environment variable is set
3. DISABLE_METRICS environment variable is set

---

### `_is_test_file(file_path) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:392`
**Complexity:** 1

**Description:**
> Check if file path indicates a test file.

**Parameters:**
- `file_path`: str

---

### `_maybe_json(args, payload) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:51`
**Complexity:** 2

**Parameters:**
- `args`: argparse.Namespace
- `payload`: Any

---

### `_maybe_json(args, payload) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:43`
**Complexity:** 2

**Parameters:**
- `args`: argparse.Namespace
- `payload`: Any

---

### `_merge_enhanced_issues(issues, enhanced_errors) -> Tuple[List[Dict[str, Any]], int, int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:83`
**Complexity:** 8

**Parameters:**
- `issues`: List[Dict[str, Any]]
- `enhanced_errors`: List[EnhancedError]

---

### `_normalize_node_type(value) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:589`
**Complexity:** 3

**Description:**
> Normalize node type to valid value.

**Parameters:**
- `value`: Any

---

### `_normalize_status(value) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:446`
**Complexity:** 3

**Parameters:**
- `value`: Any

---

### `_normalize_timestamp(value) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:415`
**Complexity:** 5

**Parameters:**
- `value`: Any

---

### `_normalized_to_dict(normalized) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:61`
**Complexity:** 1

**Parameters:**
- `normalized`: NormalizedValidationResult

---

### `_print_diff(diff, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:229`
**Complexity:** 8

**Parameters:**
- `diff`: Dict[str, Any]
- `printer`: PrettyPrinter

---

### `_print_if_json(args, payload, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:87`
**Complexity:** 2

**Parameters:**
- `args`: argparse.Namespace
- `payload`: object
- `printer`: PrettyPrinter

---

### `_print_results(args, results) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:179`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `results`: List[QueryResult]

---

### `_regenerate_documentation(specs_dir, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/lifecycle.py:184`
**Complexity:** 5

**Description:**
> Regenerate codebase documentation.

Args:
    specs_dir: Path to specs directory (used to locate project root)
    printer: Printer for output messages

Returns:
    True if regeneration succeeded, False otherwise

**Parameters:**
- `specs_dir`: Path
- `printer`: PrettyPrinter

---

### `_register_doc_cli(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/registry.py:56`
**Complexity:** 1

**Description:**
> Register the doc CLI as an SDD subcommand.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `_register_skills_dev_cli(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/registry.py:94`
**Complexity:** 1

**Description:**
> Register the skills-dev CLI as an SDD subcommand.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `_register_test_cli(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/registry.py:76`
**Complexity:** 1

**Description:**
> Register the test CLI as an SDD subcommand.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `_render_template(template_name, context) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:375`
**Complexity:** 2

**Description:**
> Render a journal template using string.Template.

**Parameters:**
- `template_name`: str
- `context`: Dict[str, Any]

---

### `_resolve_node_id(error, hierarchy) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:436`
**Complexity:** 5

**Parameters:**
- `error`: EnhancedError
- `hierarchy`: Dict[str, Any]

---

### `_results_to_json(results, include_meta) -> List[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:158`
**Complexity:** 3

**Parameters:**
- `results`: List[QueryResult]
- `include_meta`: bool

---

### `_rotate_metrics_file_if_needed() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:57`
**Complexity:** 5

**Description:**
> Rotate metrics file if it exceeds max size.

---

### `_run_tool_capture(tool, prompt) -> Tuple[bool, str, float]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:607`
**Complexity:** 1

**Description:**
> Run tool and capture output (internal helper for parallel execution).

Returns:
    Tuple of (success, output, duration)

**Parameters:**
- `tool`: str
- `prompt`: str

---

### `_serialize_fix_action(action) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:65`
**Complexity:** 1

**Parameters:**
- `action`: None

---

### `_should_exclude_path(file_path, exclude_patterns) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:14`
**Complexity:** 8

**Description:**
> Check if a file path should be excluded based on patterns.

Uses path component matching to avoid false positives.
For example, '.git' will match '.git/' but not '.github/'.

Args:
    file_path: Path to check
    exclude_patterns: List of patterns to exclude

Returns:
    True if file should be excluded

**Parameters:**
- `file_path`: Path
- `exclude_patterns`: List[str]

---

### `_simulate_workflow(state, task_id, actual_hours, note, journal_title, journal_content, journal_entry_type, author, revision_version, revision_changes) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:73`
⚠️ **Complexity:** 16 (High)

**Parameters:**
- `state`: Dict[str, Any]
- `task_id`: str
- `actual_hours`: Optional[float]
- `note`: Optional[str]
- `journal_title`: Optional[str]
- `journal_content`: Optional[str]
- `journal_entry_type`: str
- `author`: str
- `revision_version`: Optional[str]
- `revision_changes`: Optional[str]

---

### `_stats_to_dict(stats) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:45`
**Complexity:** 1

**Parameters:**
- `stats`: None

---

### `_status_to_exit_code(status) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:76`
**Complexity:** 3

**Parameters:**
- `status`: str

---

### `_suggest_fix(category, normalized_message) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:81`
⚠️ **Complexity:** 24 (High)

**Parameters:**
- `category`: str
- `normalized_message`: str

---

### `_validate_spec_structure(spec_data) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:278`
**Complexity:** 9

**Description:**
> Validate basic JSON spec file structure.

Args:
    spec_data: Spec data dictionary

Returns:
    True if valid, False otherwise

**Parameters:**
- `spec_data`: Dict

---

### `activate_spec(spec_id, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/lifecycle.py:84`
⚠️ **Complexity:** 12 (High)

**Description:**
> Activate a pending spec by moving it to the active folder.

Performs the following:
1. Finds spec file in pending/ folder
2. Updates metadata status to 'active'
3. Adds activated_date timestamp
4. Moves spec file to active/ folder

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    dry_run: If True, show changes without executing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `add_global_options(parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/options.py:20`
**Complexity:** 1

**Description:**
> Add global options available to all commands.

**Parameters:**
- `parser`: None

---

### `add_journal_entry(spec_id, title, content, task_id, entry_type, author, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:120`
**Complexity:** 10

**Description:**
> Add an entry to the journal array in the JSON spec file.

Args:
    spec_id: Specification ID
    title: Entry title (e.g., "Task 1-2 Started", "Blocker: Redis Dependency")
    content: Entry content (plain text)
    task_id: Optional task ID to reference
    entry_type: Type of entry (status_change, deviation, blocker, decision, note)
    author: Author of the entry (default: claude-code)
    specs_dir: Optional specs directory (auto-detected if not provided)
    dry_run: If True, show entry without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `title`: str
- `content`: str
- `task_id`: Optional[str]
- `entry_type`: str
- `author`: str
- `specs_dir`: Optional[Path]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `add_revision_entry(spec_id, version, changes, author, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:281`
**Complexity:** 10

**Description:**
> Add a revision entry to the JSON spec metadata.revisions array.

Args:
    spec_id: Specification ID
    version: Version string (e.g., "1.1", "2.0")
    changes: Description of changes
    author: Author of the changes
    specs_dir: Optional specs directory (auto-detected if not provided)
    dry_run: If True, show entry without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `version`: str
- `changes`: str
- `author`: str
- `specs_dir`: Optional[Path]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `add_spec_options(parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/options.py:80`
**Complexity:** 1

**Description:**
> Add common spec-related arguments.

**Parameters:**
- `parser`: None

---

### `add_task_options(parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/options.py:88`
**Complexity:** 1

**Description:**
> Add common task-related arguments.

**Parameters:**
- `parser`: None

---

### `add_verification_result(spec_id, verify_id, status, command, output, issues, notes, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/verification.py:17`
⚠️ **Complexity:** 18 (High)

**Description:**
> Add verification results to the JSON spec file hierarchy node metadata.

Args:
    spec_id: Specification ID
    verify_id: Verification identifier (e.g., 'verify-1-1')
    status: PASSED, FAILED, or PARTIAL
    command: Command that was run (if automated)
    output: Command output or test results
    issues: Issues found during verification
    notes: Additional notes
    specs_dir: Optional specs directory (auto-detected if not provided)
    dry_run: If True, show result without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `verify_id`: str
- `status`: str
- `command`: Optional[str]
- `output`: Optional[str]
- `issues`: Optional[str]
- `notes`: Optional[str]
- `specs_dir`: Optional[Path]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `aggregate_task_times(spec_id, specs_dir, printer) -> Optional[float]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/time_tracking.py:265`
**Complexity:** 8

**Description:**
> Aggregate actual_hours from all tasks in the spec hierarchy.

Traverses the hierarchy recursively and sums all actual_hours values
from task-level nodes that have time tracking data.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    printer: Optional printer for error messages

Returns:
    Total actual hours across all tasks, or None if no time data found

Examples:
    >>> aggregate_task_times("user-auth-2025-10-18-001", Path("specs/active"))
    18.5

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `analyze_code_quality(statistics) -> Dict[str, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/calculator.py:108`
**Complexity:** 5

**Description:**
> Analyze code quality based on calculated statistics.

Args:
    statistics: Dictionary of code statistics

Returns:
    Dictionary with quality assessment

**Parameters:**
- `statistics`: Dict[str, Any]

---

### `analyze_codebase(directory) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:15`
**Complexity:** 5

**Description:**
> Analyze codebase using doc-query if available.

Args:
    directory: Directory to analyze

Returns:
    Analysis results dictionary

**Parameters:**
- `directory`: Path

---

### `analyze_conftest(file_path) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:121`
**Complexity:** 7

**Description:**
> Analyze a conftest.py file for fixtures and configuration.

Args:
    file_path: Path to conftest.py file

Returns:
    Dictionary with analysis results

**Parameters:**
- `file_path`: Path

---

### `analyze_dependencies(spec_data) -> DependencyAnalysis`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:21`
⚠️ **Complexity:** 32 (High)

**Description:**
> Detect circular dependencies in JSON spec.

Performs comprehensive analysis of the dependency graph including:
- Circular dependency chains
- Orphaned tasks (references to non-existent dependencies)
- Impossible chains (mutual blocking scenarios)

Args:
    spec_data: JSON spec file data dictionary with 'hierarchy' key

Returns:
    Dictionary with analysis results:
    - has_circular: bool - True if any circular dependencies found
    - circular_chains: list - List of circular dependency chains
    - orphaned_tasks: list - Tasks with missing dependencies
    - impossible_chains: list - Tasks in deadlock situations

Example:
    >>> result = find_circular_dependencies(spec_data)
    >>> if result['has_circular']:
    ...     print(f"Found {len(result['circular_chains'])} circular chains")

**Parameters:**
- `spec_data`: Dict

---

### `analyze_impact(query, entity_name, depth) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:13`
**Complexity:** 3

**Description:**
> Analyze the impact of changing a function or class.

Calculates the "blast radius" showing all directly and indirectly affected code,
test coverage, and risk assessment with refactoring recommendations.

Args:
    query: DocumentationQuery instance
    entity_name: Name of the function or class to analyze
    depth: Maximum depth for indirect dependency traversal (default: 2)

Returns:
    Dictionary with keys:
    - entity_name: Name of the analyzed entity
    - entity_type: 'function' or 'class'
    - entity_info: Basic entity information
    - blast_radius: Dict with direct_dependents, indirect_dependents
    - test_coverage: Dict with test files and estimated coverage
    - risk_assessment: Dict with score, level, factors
    - recommendations: List of actionable recommendations
    - summary: Statistics about the impact

Example:
    >>> query = DocumentationQuery()
    >>> query.load()
    >>> result = analyze_impact(query, "load", depth=2)
    >>> print(f"Risk level: {result['risk_assessment']['level']}")

**Parameters:**
- `query`: Any
- `entity_name`: str
- `depth`: int

---

### `analyze_property_access(query, class_name, class_info, crud_ops) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:298`
⚠️ **Complexity:** 11 (High)

**Description:**
> Analyze property access patterns for the class.

Identifies which properties are accessed in which operations,
highlighting frequently accessed or modified properties.

Args:
    query: DocumentationQuery instance
    class_name: Name of the class
    class_info: Class information dictionary
    crud_ops: CRUD operations from detect_crud_operations()

Returns:
    Dictionary with property access statistics:
    - properties: List of property names
    - access_patterns: Dict mapping properties to access counts
    - mutation_hot_spots: Properties frequently modified

**Parameters:**
- `query`: Any
- `class_name`: str
- `class_info`: Dict[str, Any]
- `crud_ops`: Dict[str, List[Dict[str, Any]]]

---

### `analyze_response_similarity(response1, response2) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:759`
**Complexity:** 5

**Description:**
> Simple heuristic to find consensus points between two responses.

Args:
    response1: First response text
    response2: Second response text

Returns:
    List of consensus points (simplified)

**Parameters:**
- `response1`: str
- `response2`: str

---

### `analyze_spec_complexity(spec_file) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec_analysis.py:188`
**Complexity:** 4

**Description:**
> Analyze spec complexity metrics.

Provides insights into spec complexity including:
- Average tasks per phase
- Average subtasks per task
- Depth of task hierarchy
- Verification coverage ratio

Args:
    spec_file: Path to spec markdown file

Returns:
    Dictionary with complexity metrics

Example:
    >>> complexity = analyze_spec_complexity(Path("specs/active/my-spec.md"))
    >>> print(f"Average tasks per phase: {complexity['avg_tasks_per_phase']}")

**Parameters:**
- `spec_file`: Path

---

### `analyze_test_file(file_path) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:55`
**Complexity:** 6

**Description:**
> Analyze a test file for its structure.

Args:
    file_path: Path to the test file

Returns:
    Dictionary with analysis results

**Parameters:**
- `file_path`: Path

---

### `apply_fix_actions(actions, spec_path) -> FixReport`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:127`
⚠️ **Complexity:** 14 (High)

**Description:**
> Apply fix actions to a spec file.

**Parameters:**
- `actions`: Iterable[FixAction]
- `spec_path`: str

---

### `assert_json_structure() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:1007`
**Complexity:** 2

**Decorators:** `@pytest.fixture`

**Description:**
> Helper to assert JSON structure.

---

### `audit_spec(spec_id, specs_dir, printer) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/validation.py:166`
⚠️ **Complexity:** 16 (High)

**Description:**
> Perform deep audit of JSON spec.

More comprehensive than validate_spec, includes:
- Circular dependency detection
- Progress calculation verification
- Metadata completeness checks

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    printer: Optional printer for output

Returns:
    Dictionary with audit results

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `backup_json_spec(spec_id, specs_dir, suffix) -> Optional[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:247`
**Complexity:** 3

**Description:**
> Create a backup copy of the JSON spec file in the .backups/ directory.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    suffix: Backup file suffix (default: .backup)

Returns:
    Path to backup file if created, None otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `suffix`: str

---

### `batch_check_paths_exist(paths, base_directory) -> Dict[str, bool]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:244`
**Complexity:** 3

**Description:**
> Check multiple paths for existence.

Args:
    paths: List of path strings to check
    base_directory: Base directory for relative paths (defaults to cwd)

Returns:
    Dictionary mapping each path to its existence status (True/False)

Example:
    >>> existence = batch_check_paths_exist(["src/main.py", "tests/test.py"])
    >>> for path, exists in existence.items():
    ...     print(f"{path}: {'exists' if exists else 'missing'}")

**Parameters:**
- `paths`: List[str]
- `base_directory`: Optional[Path]

---

### `build_consensus(responses, spec_id, spec_title) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/synthesis.py:222`
**Complexity:** 3

**Description:**
> Build consensus from multiple model responses using AI synthesis.

This replaces fragile regex parsing with AI-based natural language synthesis.

Args:
    responses: List of response dicts from parse_response()
    spec_id: Specification ID
    spec_title: Specification title

Returns:
    Consensus dictionary with synthesis results

**Parameters:**
- `responses`: List[Dict[str, Any]]
- `spec_id`: str
- `spec_title`: str

---

### `build_data_flow(query, class_name, crud_ops) -> Dict[str, Dict[str, List[str]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:230`
**Complexity:** 10

**Description:**
> Build data flow organized by architectural layer.

Groups CRUD operations by layer (Presentation, Business Logic, Data, etc.)
to show how data flows through the architecture.

Args:
    query: DocumentationQuery instance
    class_name: Name of the class being traced
    crud_ops: CRUD operations from detect_crud_operations()

Returns:
    Dictionary mapping layer names to operation categories:
    {
        'Presentation': {'create': [...], 'read': [...], ...},
        'Business Logic': {'create': [...], 'read': [...], ...},
        ...
    }

**Parameters:**
- `query`: Any
- `class_name`: str
- `crud_ops`: Dict[str, List[Dict[str, Any]]]

---

### `build_pytest_command(preset, path, pattern, extra_args) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:129`
**Complexity:** 6

**Description:**
> Build the pytest command with the specified configuration.

Args:
    preset: Name of the preset to use
    path: Specific test file or directory to run
    pattern: Pattern to match test names (used with -k)
    extra_args: Additional arguments to pass to pytest

Returns:
    List of command arguments

**Parameters:**
- `preset`: Optional[str]
- `path`: Optional[str]
- `pattern`: Optional[str]
- `extra_args`: Optional[List[str]]

---

### `bulk_journal_tasks(spec_id, specs_dir, task_ids, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:386`
⚠️ **Complexity:** 21 (High)

**Description:**
> Add journal entries for multiple completed tasks at once.

Generates a journal entry for each task with:
- Task ID and title
- Completion timestamp
- Status change note

Args:
    spec_id: Specification ID
    specs_dir: Optional specs directory (auto-detected if not provided)
    task_ids: List of task IDs to journal (if None, journals all unjournaled tasks)
    dry_run: If True, show entries without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Optional[Path]
- `task_ids`: Optional[List[str]]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `calculate_blast_radius(query, entity_name, entity_type, entity_info, depth) -> Dict[str, List[Dict[str, Any]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:170`
⚠️ **Complexity:** 18 (High)

**Description:**
> Calculate the blast radius of changing an entity.

Finds all direct dependents and indirect dependents up to specified depth.

Args:
    query: DocumentationQuery instance
    entity_name: Name of the entity
    entity_type: 'function' or 'class'
    entity_info: Entity information dictionary
    depth: Maximum depth for traversal

Returns:
    Dictionary with:
    - direct_dependents: List of functions/classes that directly depend on entity
    - indirect_dependents: List of 2nd+ degree dependents

**Parameters:**
- `query`: Any
- `entity_name`: str
- `entity_type`: str
- `entity_info`: Dict[str, Any]
- `depth`: int

---

### `calculate_complexity(node) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/calculator.py:12`
**Complexity:** 4

**Description:**
> Calculate cyclomatic complexity for a function.

Args:
    node: AST node representing a function

Returns:
    Cyclomatic complexity score

**Parameters:**
- `node`: ast.FunctionDef

---

### `calculate_language_statistics(modules, functions) -> Dict[str, Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/calculator.py:66`
**Complexity:** 5

**Description:**
> Calculate statistics broken down by programming language.

Args:
    modules: List of module information dictionaries
    functions: List of function information dictionaries

Returns:
    Dictionary mapping language to its statistics

**Parameters:**
- `modules`: List[Dict]
- `functions`: List[Dict]

---

### `calculate_priority_score(func) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:99`
**Complexity:** 1

**Description:**
> Calculate priority score for a function.

Priority score = complexity × dependent_count
Higher score = higher priority for refactoring

Args:
    func: Function dictionary from documentation

Returns:
    Dictionary with:
    - name: Function name
    - file: File path
    - line: Line number
    - complexity: Cyclomatic complexity
    - dependent_count: Number of callers
    - priority_score: complexity × dependents
    - risk_level: 'high', 'medium', or 'low'

**Parameters:**
- `func`: Dict[str, Any]

---

### `calculate_risk_score(blast_radius, test_coverage, entity_info) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:399`
**Complexity:** 3

**Description:**
> Calculate risk score for changing the entity.

Uses formula: Risk = (direct * 3) + (indirect * 1) + (layers * 5) - (coverage * 0.1)

Args:
    blast_radius: Blast radius from calculate_blast_radius()
    test_coverage: Test coverage from find_test_coverage()
    entity_info: Entity information

Returns:
    Dictionary with:
    - score: Numeric risk score
    - level: 'low', 'medium', or 'high'
    - factors: Breakdown of risk factors

**Parameters:**
- `blast_radius`: Dict[str, List[Dict[str, Any]]]
- `test_coverage`: Dict[str, Any]
- `entity_info`: Dict[str, Any]

---

### `calculate_statistics(modules, functions) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/calculator.py:31`
**Complexity:** 1

**Description:**
> Calculate project-wide statistics with multi-language support.

Args:
    modules: List of module information dictionaries
    functions: List of function information dictionaries

Returns:
    Dictionary of calculated statistics including per-language breakdowns

**Parameters:**
- `modules`: List[Dict]
- `functions`: List[Dict]

---

### `calculate_statistics(spec_data) -> SpecStatistics`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/stats.py:29`
⚠️ **Complexity:** 13 (High)

**Description:**
> Compute statistics for a spec file.

**Parameters:**
- `spec_data`: Dict[str, Any]

---

### `calculate_time_from_timestamps(start_timestamp, end_timestamp, printer) -> Optional[float]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/time_tracking.py:57`
**Complexity:** 7

**Description:**
> Calculate decimal hours between two ISO 8601 timestamps.

Args:
    start_timestamp: ISO 8601 timestamp string (e.g., "2025-10-27T10:00:00Z")
    end_timestamp: ISO 8601 timestamp string (e.g., "2025-10-27T13:30:00Z")
    printer: Optional printer for error messages

Returns:
    Decimal hours between timestamps, or None if parsing fails

Examples:
    >>> calculate_time_from_timestamps("2025-10-27T10:00:00Z", "2025-10-27T13:30:00Z")
    3.5

**Parameters:**
- `start_timestamp`: str
- `end_timestamp`: str
- `printer`: Optional[PrettyPrinter]

---

### `call_tool(tool_name, prompt, timeout) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reviewer.py:92`
**Complexity:** 8

**Description:**
> Call an AI CLI tool with a prompt.

Args:
    tool_name: Name of tool to call
    prompt: Prompt to send
    timeout: Optional timeout override

Returns:
    Result dictionary with success, output, error

**Parameters:**
- `tool_name`: str
- `prompt`: str
- `timeout`: Optional[int]

---

### `capture_metrics(skill, command) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:124`
**Complexity:** 4

**Decorators:** `@contextmanager`

**Description:**
> Context manager for capturing metrics around a block of code.

Usage:
    with capture_metrics('sdd-next', 'discover'):
        # do work
        pass

Args:
    skill: Name of the skill
    command: Command being executed

**Parameters:**
- `skill`: str
- `command`: str

---

### `categorize_risk_level(priority_score, complexity, dependent_count) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:145`
**Complexity:** 3

**Description:**
> Categorize risk level for refactoring.

Args:
    priority_score: Priority score (complexity × dependents)
    complexity: Cyclomatic complexity
    dependent_count: Number of dependents

Returns:
    Risk level: 'high', 'medium', or 'low'

Risk Level Criteria:
    - High: score > 100 (complex + widely used)
    - Medium: score 50-100 (moderately risky)
    - Low: score < 50 (safer to refactor)

**Parameters:**
- `priority_score`: int
- `complexity`: int
- `dependent_count`: int

---

### `check_complete(spec_id, specs_dir, phase_id, task_id, printer) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:265`
⚠️ **Complexity:** 19 (High)

**Description:**
> Check if spec, phase, or task is ready to be marked complete.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    phase_id: Optional phase ID to check (if None, checks entire spec)
    task_id: Optional task ID to check (mutually exclusive with phase_id)
    printer: Optional printer for output

Returns:
    Dictionary with completion status and incomplete tasks

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `phase_id`: Optional[str]
- `task_id`: Optional[str]
- `printer`: Optional[PrettyPrinter]

---

### `check_dependencies(spec_data, task_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:173`
**Complexity:** 8

**Description:**
> Check dependency status for a task.

Args:
    spec_data: JSON spec file data
    task_id: Task identifier

Returns:
    Dictionary with dependency analysis

**Parameters:**
- `spec_data`: Dict
- `task_id`: str

---

### `check_doc_query_available() -> dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/doc_helper.py:15`
⚠️ **Complexity:** 12 (High)

**Description:**
> Check if doc-query documentation exists and is accessible.

Returns:
    dict: {
        "available": bool,           # True if doc-query can be used
        "message": str,              # Human-readable status message
        "stats": dict | None,        # Stats from doc-query if available
        "location": str | None       # Path to documentation
    }

Example:
    >>> result = check_doc_query_available()
    >>> if result["available"]:
    ...     print(f"Documentation found at {result['location']}")

---

### `check_docs_exist(docs_path) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:1446`
**Complexity:** 3

**Description:**
> Check if documentation files exist.

Args:
    docs_path: Path to docs directory or documentation.json

Returns:
    True if documentation exists

**Parameters:**
- `docs_path`: Optional[str]

---

### `check_documentation_staleness(docs_path, source_dir) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:1467`
⚠️ **Complexity:** 29 (High)

**Description:**
> Check if documentation is stale by comparing generation time with source file modifications.

Args:
    docs_path: Path to docs directory or documentation.json
    source_dir: Path to source directory to check. If None, uses parent of docs directory.

Returns:
    Dictionary with staleness information:
    {
        'is_stale': bool,
        'docs_generated_at': str (ISO timestamp),
        'latest_source_modification': str (ISO timestamp),
        'message': str (human-readable message),
        'docs_age_seconds': int,
        'newest_file': str (path to newest source file),
        'checked_files_count': int
    }

**Parameters:**
- `docs_path`: Optional[str]
- `source_dir`: Optional[str]

---

### `check_environment(directory, required_deps) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/project.py:224`
⚠️ **Complexity:** 14 (High)

**Description:**
> Check environmental requirements and configuration.

Args:
    directory: Directory to check (defaults to current directory)
    required_deps: Optional list of required dependencies to check

Returns:
    Dictionary with environment validation results

**Parameters:**
- `directory`: Optional[Path]
- `required_deps`: Optional[List[str]]

---

### `check_permissions(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py:28`
**Complexity:** 6

**Description:**
> Check if SDD permissions are configured for the project.

**Parameters:**
- `project_root`: None

---

### `check_permissions(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/setup_project_permissions.py:118`
**Complexity:** 2

**Description:**
> Check if SDD permissions are configured.

**Parameters:**
- `project_root`: None

---

### `check_sdd_integration_available() -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/doc_helper.py:90`
**Complexity:** 1

**Description:**
> Check if sdd-integration command is available in PATH.

Returns:
    bool: True if sdd-integration command exists and is executable

Example:
    >>> if check_sdd_integration_available():
    ...     context = get_task_context_from_docs("implement auth")

---

### `check_spec_completion(spec_data, phase_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:9`
**Complexity:** 10

**Description:**
> Check if a spec (or specific phase) is complete.

Analyzes the task hierarchy to determine if all tasks in the spec (or a
specific phase) have been completed. Returns comprehensive metadata about
completion status, progress, and any incomplete tasks.

Args:
    spec_data: JSON spec file data containing hierarchy and task information
    phase_id: Optional phase ID to check specific phase completion.
             If None, checks entire spec completion.

Returns:
    Dictionary with completion status and metadata:
    {
        "is_complete": bool,           # True if all tasks completed
        "total_tasks": int,            # Total task count in scope
        "completed_tasks": int,        # Number of completed tasks
        "percentage": int,             # Completion percentage (0-100)
        "incomplete_tasks": List[str], # IDs of incomplete tasks
        "node_id": str,                # The node checked (spec-root or phase-id)
        "can_finalize": bool,          # True if ready to mark as complete
        "error": Optional[str]         # Error message if check failed
    }

Example:
    >>> from claude_skills.common.spec import load_spec
    >>> from claude_skills.common.completion import check_spec_completion
    >>>
    >>> spec_data = load_spec("specs/active/my-spec.json")
    >>> result = check_spec_completion(spec_data)
    >>>
    >>> if result["is_complete"]:
    ...     print(f"Spec is complete! {result['completed_tasks']}/{result['total_tasks']} tasks done")
    ... else:
    ...     print(f"Incomplete tasks: {result['incomplete_tasks']}")

**Parameters:**
- `spec_data`: Dict
- `phase_id`: Optional[str]

---

### `check_tool_availability() -> Dict[str, bool]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:111`
**Complexity:** 2

**Description:**
> Check which external tools are installed and enabled.

Only checks tools that are enabled in the configuration.

Returns:
    Dict mapping tool names to availability status

---

### `check_tool_available(tool_name) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reviewer.py:40`
**Complexity:** 4

**Description:**
> Check if an AI CLI tool is available.

Args:
    tool_name: Name of the tool (gemini, codex, cursor-agent)

Returns:
    True if tool is available, False otherwise

**Parameters:**
- `tool_name`: str

---

### `cmd_activate_spec(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:366`
**Complexity:** 4

**Description:**
> Activate a pending spec by moving it to active folder.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_add_journal(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:222`
**Complexity:** 3

**Description:**
> Add journal entry.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_add_revision(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:246`
**Complexity:** 3

**Description:**
> Add revision entry.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_add_verification(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:292`
**Complexity:** 3

**Description:**
> Add verification result.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_analyze(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:215`
**Complexity:** 10

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_analyze(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/cli.py:69`
**Complexity:** 6

**Description:**
> Analyze codebase for planning.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_analyze_with_ai(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:272`
⚠️ **Complexity:** 17 (High)

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_audit_spec(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:458`
**Complexity:** 5

**Description:**
> Perform deep audit of JSON spec.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_bulk_journal(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:717`
**Complexity:** 4

**Description:**
> Bulk journal completed tasks.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_call_graph(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:748`
**Complexity:** 9

**Description:**
> Build and display call graph for a function.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_callees(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:712`
**Complexity:** 5

**Description:**
> Show functions called by the specified function.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_callers(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:676`
**Complexity:** 5

**Description:**
> Show functions that call the specified function.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_check(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/setup_permissions.py:121`
**Complexity:** 5

**Description:**
> Check if SDD permissions are configured.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_check_complete(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:589`
**Complexity:** 5

**Description:**
> Check if spec, phase, or task is ready to complete.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_check_deps(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:387`
⚠️ **Complexity:** 14 (High)

**Description:**
> Check task dependencies.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_check_deps(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:474`
⚠️ **Complexity:** 18 (High)

**Description:**
> Check for circular dependencies.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_check_environment(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:873`
⚠️ **Complexity:** 13 (High)

**Description:**
> Check environmental requirements.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_check_journaling(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:677`
**Complexity:** 8

**Description:**
> Check for unjournaled completed tasks.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_check_permissions(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py:22`
**Complexity:** 8

**Description:**
> Check if SDD permissions are configured for the project.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_check_tools(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:55`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_complete_spec(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:388`
**Complexity:** 3

**Description:**
> Mark spec as completed and move to completed folder.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_complete_task(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:744`
**Complexity:** 6

**Description:**
> Complete task workflow (status, journaling, metadata sync).

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_complexity(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:450`
**Complexity:** 5

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_consult(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:67`
⚠️ **Complexity:** 15 (High)

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_context(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:311`
**Complexity:** 5

**Description:**
> Handler for 'sdd context' command.

Args:
    args: Parsed arguments from ArgumentParser
    printer: PrettyPrinter instance for output

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_context(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:506`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_create(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/cli.py:20`
**Complexity:** 4

**Description:**
> Create a new specification.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_dependencies(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:484`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_describe_module(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:522`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_detect_project(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:802`
⚠️ **Complexity:** 12 (High)

**Description:**
> Detect project type and dependencies.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_discover(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:134`
**Complexity:** 1

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_execute_verify(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:48`
⚠️ **Complexity:** 29 (High)

**Description:**
> Execute a verification task automatically (Priority 1 Integration).

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_find_active_work(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py:80`
**Complexity:** 8

**Description:**
> Find all active SDD specifications with resumable work.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_find_circular_deps(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:916`
⚠️ **Complexity:** 12 (High)

**Description:**
> Find circular dependencies in JSON spec.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_find_class(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:417`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_find_function(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:428`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_find_module(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:439`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_find_pattern(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:781`
**Complexity:** 5

**Description:**
> Find files matching a pattern.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_find_related_files(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:956`
⚠️ **Complexity:** 11 (High)

**Description:**
> Find files related to a source file.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_find_specs(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:267`
**Complexity:** 8

**Description:**
> Find specs directories.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_find_tests(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:841`
**Complexity:** 9

**Description:**
> Find test files and patterns.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_fix(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:242`
⚠️ **Complexity:** 35 (High)

**Description:**
> Auto-fix validation issues in spec file.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_format_output(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py:162`
⚠️ **Complexity:** 17 (High)

**Description:**
> Format active work as human-readable text with last-accessed task info.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_format_plan(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:725`
**Complexity:** 4

**Description:**
> Format execution plan for display.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_format_verification_summary(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:317`
**Complexity:** 6

**Description:**
> Format verification results summary.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_gendocs(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/gendocs.py:14`
**Complexity:** 4

**Description:**
> Generate documentation for a skill.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_generate(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:108`
**Complexity:** 9

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_get_journal(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:538`
**Complexity:** 7

**Description:**
> Get journal entries for a spec or task.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_get_session_info(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py:280`
**Complexity:** 5

**Description:**
> Get session state information as JSON.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_get_task(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:514`
**Complexity:** 6

**Description:**
> Get detailed task information.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_impact(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:894`
**Complexity:** 8

**Description:**
> Analyze impact of changing a function or class.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_init_env(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:521`
**Complexity:** 6

**Description:**
> Initialize development environment.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_list_blockers(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:636`
**Complexity:** 6

**Description:**
> List all blocked tasks.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_list_classes(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:565`
**Complexity:** 7

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_list_functions(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:602`
**Complexity:** 7

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_list_modules(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:639`
**Complexity:** 7

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_list_phases(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:567`
**Complexity:** 6

**Description:**
> List all phases.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_list_tools(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/cli.py:175`
⚠️ **Complexity:** 14 (High)

**Description:**
> List available AI CLI tools.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_mark_blocked(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:178`
**Complexity:** 3

**Description:**
> Mark task as blocked.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_migrate(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/migrate.py:65`
**Complexity:** 1

**Description:**
> Show migration guidance.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_move_spec(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:350`
**Complexity:** 1

**Description:**
> Move spec to another folder.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_next_task(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:295`
**Complexity:** 10

**Description:**
> Find next actionable task.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_phase_time(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:613`
**Complexity:** 6

**Description:**
> Calculate time for a phase.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_prepare_task(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:546`
⚠️ **Complexity:** 21 (High)

**Description:**
> Prepare task for implementation.

This command integrates with the automatic completion detection system.
It calls prepare_task() from discovery.py which returns completion signals
when all tasks in a spec are finished.

Completion Signal Handling (from prepare_task() in discovery.py):
----------------------------------------------------------------
prepare_task() performs completion detection and returns different signals
based on the spec's state:

Scenario 1: No Actionable Tasks Available
    - Returned when: No pending/unblocked tasks found
    - Signal: success=False, spec_complete=False
    - completion_info present if tasks are blocked
    - Indicates: Tasks exist but are blocked by dependencies

Scenario 2: Spec/Phase Complete
    - Returned when: All tasks completed, no blocked tasks
    - Signal: success=True, spec_complete=True
    - completion_info contains should_prompt=True
    - Indicates: Ready to finalize and move to completed/

Scenario 3: Normal Task Found
    - Returned when: Found actionable task to work on
    - Signal: success=True, task_id set, spec_complete=False
    - Indicates: Continue normal workflow with returned task

The completion_info dict structure (from should_prompt_completion):
    {
        "should_prompt": bool,      # True if ready to complete
        "reason": str,               # Human-readable explanation
        "is_complete": bool,         # All tasks done
        "blocked_count": int,        # Number of blocked tasks
        "blocked_tasks": List[str],  # IDs of blocked tasks
        "node_id": str,              # Node that was checked
        "error": Optional[str]       # Error if check failed
    }

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_progress(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:488`
**Complexity:** 7

**Description:**
> Show overall progress.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_query_tasks(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:480`
⚠️ **Complexity:** 11 (High)

**Description:**
> Query and filter tasks.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_reconcile_state(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:658`
**Complexity:** 3

**Description:**
> Reconcile JSON spec to fix inconsistent task statuses.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_refactor_candidates(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:938`
**Complexity:** 8

**Description:**
> Find high-priority refactoring candidates.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_render(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_render/cli.py:16`
⚠️ **Complexity:** 12 (High)

**Description:**
> Render JSON spec to human-readable markdown.

Args:
    args: Command line arguments
    printer: Output printer

Returns:
    Exit code (0 for success, 1 for error)

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_report(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:379`
**Complexity:** 10

**Description:**
> Generate detailed validation report.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_review(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/cli.py:30`
⚠️ **Complexity:** 18 (High)

**Description:**
> Review a specification file using multiple AI models.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_run(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:146`
**Complexity:** 5

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_search(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:495`
**Complexity:** 3

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_spec_stats(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:1019`
**Complexity:** 10

**Description:**
> Show spec file statistics.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_stats(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:538`
**Complexity:** 4

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_stats(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:444`
**Complexity:** 5

**Description:**
> Show spec statistics and complexity metrics.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_status_report(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:436`
**Complexity:** 6

**Description:**
> Get status report.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_sync_metadata(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:777`
**Complexity:** 3

**Description:**
> Synchronize spec metadata with hierarchy data.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_task_info(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:346`
**Complexity:** 9

**Description:**
> Get detailed task information.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_template(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/cli.py:126`
**Complexity:** 7

**Description:**
> Work with spec templates.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_time_report(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:412`
**Complexity:** 6

**Description:**
> Generate time tracking report.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_trace_data(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:850`
**Complexity:** 8

**Description:**
> Trace data object lifecycle through the codebase.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_trace_entry(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:806`
**Complexity:** 8

**Description:**
> Trace execution flow from an entry function.

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_unblock_task(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:201`
**Complexity:** 3

**Description:**
> Unblock a task.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_update(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/setup_permissions.py:60`
**Complexity:** 8

**Description:**
> Update .claude/settings.json with SDD permissions.

**Parameters:**
- `args`: None
- `printer`: PrettyPrinter

---

### `cmd_update_frontmatter(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:268`
**Complexity:** 1

**Description:**
> Update metadata field in JSON spec.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_update_status(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:155`
**Complexity:** 3

**Description:**
> Update task status.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_validate(args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:163`
⚠️ **Complexity:** 12 (High)

**Parameters:**
- `args`: argparse.Namespace
- `printer`: PrettyPrinter

---

### `cmd_validate(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:147`
⚠️ **Complexity:** 16 (High)

**Description:**
> Validate JSON spec file.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_validate_paths(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:992`
**Complexity:** 7

**Description:**
> Validate and normalize paths.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_validate_spec(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:744`
**Complexity:** 10

**Description:**
> Validate spec file.

**Parameters:**
- `args`: None
- `printer`: None

---

### `cmd_verify_tools(args, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:248`
**Complexity:** 3

**Description:**
> Verify required tools are available.

**Parameters:**
- `args`: None
- `printer`: None

---

### `collect_all_fixtures(conftest_files, root) -> Dict[str, List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:257`
**Complexity:** 4

**Description:**
> Collect all fixtures from conftest files.

Args:
    conftest_files: List of conftest file paths
    root: Root directory path

Returns:
    Dictionary mapping fixture names to their locations

**Parameters:**
- `conftest_files`: List[Path]
- `root`: Path

---

### `collect_all_markers(test_files) -> Dict[str, int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:283`
**Complexity:** 3

**Description:**
> Collect all markers from test files with usage counts.

Args:
    test_files: List of test file paths

Returns:
    Dictionary mapping marker names to usage counts

**Parameters:**
- `test_files`: List[Path]

---

### `collect_fix_actions(result) -> List[FixAction]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/fix.py:56`
⚠️ **Complexity:** 14 (High)

**Description:**
> Translate a validation result into fix actions.

**Parameters:**
- `result`: JsonSpecValidationResult

---

### `compare_spec_files(md_spec_file, json_spec_file) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec_analysis.py:246`
**Complexity:** 6

**Description:**
> Compare markdown spec counts to JSON spec counts.

Identifies mismatches between the markdown spec document and JSON spec,
which may indicate synchronization issues.

Args:
    md_spec_file: Path to spec markdown file
    json_spec_file: Path to JSON spec file

Returns:
    Dictionary with comparison results and any discrepancies

Example:
    >>> comparison = compare_spec_files(md_path, json_path)
    >>> if comparison['has_mismatches']:
    ...     print("Warning: Markdown and JSON specs are out of sync")

**Parameters:**
- `md_spec_file`: Path
- `json_spec_file`: Path

---

### `complete_spec(spec_id, spec_file, specs_dir, skip_doc_regen, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/lifecycle.py:232`
⚠️ **Complexity:** 18 (High)

**Description:**
> Mark a spec as completed and move it to completed folder.

Performs the following:
1. Verifies all tasks are completed
2. Updates JSON metadata (status, completed_date, actual_hours auto-calculated from tasks)
3. Moves JSON spec file to completed/ folder
4. Regenerates codebase documentation (unless skip_doc_regen is True)

Args:
    spec_id: Specification ID
    spec_file: Path to JSON spec file (optional - will be auto-detected if not provided)
    specs_dir: Path to specs directory
    skip_doc_regen: If True, skip documentation regeneration
    dry_run: If True, show changes without executing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `spec_file`: Optional[Path]
- `specs_dir`: Path
- `skip_doc_regen`: bool
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `complete_task_workflow() -> Optional[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/workflow.py:253`
⚠️ **Complexity:** 35 (High)

**Description:**
> Complete a task with optional journaling, time tracking, and revision updates.

---

### `compose_ai_context_doc(research_findings, project_name, version) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:323`
**Complexity:** 1

**Description:**
> Compose AI_CONTEXT.md from research findings.

Args:
    research_findings: Raw research output from AI consultation
    project_name: Project name for header
    version: Project version

Returns:
    Formatted AI_CONTEXT.md content

**Parameters:**
- `research_findings`: str
- `project_name`: str
- `version`: str

---

### `compose_architecture_doc(research_findings, project_name, version) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:271`
**Complexity:** 1

**Description:**
> Compose ARCHITECTURE.md from research findings.

Args:
    research_findings: Raw research output from AI consultation
    project_name: Project name for header
    version: Project version

Returns:
    Formatted ARCHITECTURE.md content

**Parameters:**
- `research_findings`: str
- `project_name`: str
- `version`: str

---

### `compute_diff(before, after) -> DiffReport`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:30`
**Complexity:** 6

**Description:**
> Compute differences between before and after spec states.

Args:
    before: Spec data before fixes
    after: Spec data after fixes

Returns:
    DiffReport with all detected changes

**Parameters:**
- `before`: Dict[str, Any]
- `after`: Dict[str, Any]

---

### `consult_multi_agent(doc_type, prompt, pair, dry_run, verbose, printer) -> Dict[str, any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:453`
⚠️ **Complexity:** 18 (High)

**Description:**
> Consult multiple AI tools in parallel and synthesize responses.

Args:
    doc_type: Documentation type (architecture, ai_context)
    prompt: Formatted prompt
    pair: Which multi-agent pair to use
    dry_run: If True, show what would run
    verbose: Enable verbose output
    printer: Optional PrettyPrinter for consistent output (falls back to print if None)

Returns:
    Dictionary with synthesis results

**Parameters:**
- `doc_type`: str
- `prompt`: str
- `pair`: str
- `dry_run`: bool
- `verbose`: bool
- `printer`: Optional['PrettyPrinter']

---

### `consult_multi_agent(failure_type, error_message, hypothesis, test_code_path, impl_code_path, context, question, pair, dry_run, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:970`
⚠️ **Complexity:** 14 (High)

**Description:**
> Consult multiple agents in parallel and synthesize their responses.

Args:
    failure_type: Type of test failure
    error_message: Error message from pytest
    hypothesis: Your hypothesis about the root cause
    test_code_path: Path to test code file (optional)
    impl_code_path: Path to implementation code file (optional)
    context: Additional context (optional)
    question: Specific question (optional)
    pair: Which multi-agent pair to use (default, code-focus, discovery-focus)
    dry_run: If True, show what would be run without running
    printer: PrettyPrinter instance (creates default if None)

Returns:
    Exit code (0 if at least one consultation succeeded)

**Parameters:**
- `failure_type`: str
- `error_message`: str
- `hypothesis`: str
- `test_code_path`: Optional[str]
- `impl_code_path`: Optional[str]
- `context`: Optional[str]
- `question`: Optional[str]
- `pair`: str
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `consult_with_auto_routing(failure_type, error_message, hypothesis, test_code_path, impl_code_path, context, question, tool, dry_run, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:585`
**Complexity:** 10

**Description:**
> High-level consultation function with auto-routing.

Args:
    failure_type: Type of test failure
    error_message: Error message from pytest
    hypothesis: Your hypothesis about the root cause
    test_code_path: Path to test code file (optional)
    impl_code_path: Path to implementation code file (optional)
    context: Additional context (optional)
    question: Specific question (optional)
    tool: Tool to use ("auto" for auto-selection)
    dry_run: If True, show command without running
    printer: PrettyPrinter instance (creates default if None)

Returns:
    Exit code from consultation

**Parameters:**
- `failure_type`: str
- `error_message`: str
- `hypothesis`: str
- `test_code_path`: Optional[str]
- `impl_code_path`: Optional[str]
- `context`: Optional[str]
- `question`: Optional[str]
- `tool`: str
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `count_blocked_tasks(hierarchy, node_id) -> tuple`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:289`
**Complexity:** 5

**Description:**
> Count blocked tasks under a node.

Traverses the hierarchy tree starting from the given node and counts
all descendant tasks that have status="blocked". This is used to
prevent completion when there are unresolved blocking issues.

Args:
    hierarchy: The hierarchy dictionary from spec data
    node_id: Starting node ID to search from

Returns:
    Tuple of (count: int, blocked_task_ids: List[str])
    - count: Number of blocked tasks found
    - blocked_task_ids: List of task IDs with status="blocked"

**Parameters:**
- `hierarchy`: Dict
- `node_id`: str

---

### `count_spec_elements(spec_content) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec_analysis.py:100`
**Complexity:** 1

**Description:**
> Count tasks, phases, verifications, and subtasks in spec content.

Args:
    spec_content: Full spec markdown content as string

Returns:
    Dictionary with counts for each element type

Example:
    >>> with open("spec.md") as f:
    ...     content = f.read()
    >>> counts = count_spec_elements(content)
    >>> print(counts)
    {'task_count': 15, 'subtask_count': 42, 'phase_count': 3, 'verify_count': 8}

**Parameters:**
- `spec_content`: str

---

### `create_context_summary(framework_info, key_files, layers, statistics, readme_content) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:381`
**Complexity:** 9

**Description:**
> Create a structured summary of codebase context for AI analysis.

Args:
    framework_info: Framework detection result
    key_files: Identified key files
    layers: Layer grouping
    statistics: Code statistics
    readme_content: README content (optional)

Returns:
    Formatted context summary

**Parameters:**
- `framework_info`: Dict[str, Any]
- `key_files`: List[str]
- `layers`: Dict[str, List[str]]
- `statistics`: Dict[str, Any]
- `readme_content`: Optional[str]

---

### `create_cross_reference_graph() -> CrossReferenceGraph`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ast_analysis.py:317`
**Complexity:** 1

**Description:**
> Factory function to create a new CrossReferenceGraph.

Returns:
    New CrossReferenceGraph instance

---

### `create_global_parent_parser() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/options.py:5`
**Complexity:** 1

**Description:**
> Create a parent parser with global options that can be inherited by subparsers.

This allows global options like --verbose, --debug, etc. to work universally
across all command levels, including nested subcommands.

Returns:
    ArgumentParser configured with global options and add_help=False

---

### `create_parser_factory(project_root, exclude_patterns, languages) -> ParserFactory`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/parsers/factory.py:288`
**Complexity:** 1

**Description:**
> Create a ParserFactory with all available parsers registered.

Args:
    project_root: Root directory of project
    exclude_patterns: Patterns to exclude
    languages: Specific languages to parse

Returns:
    Configured ParserFactory instance

**Parameters:**
- `project_root`: Path
- `exclude_patterns`: Optional[List[str]]
- `languages`: Optional[List[Language]]

---

### `create_sample_spec_content(spec_id, title, estimated_hours, num_phases, tasks_per_phase, include_verify, include_subtasks) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:27`
**Complexity:** 9

**Description:**
> Create a sample spec JSON structure.

Args:
    spec_id: Specification identifier
    title: Specification title
    estimated_hours: Estimated hours for the spec
    num_phases: Number of phases to create
    tasks_per_phase: Number of tasks per phase
    include_verify: Whether to include verify nodes (default: False)
    include_subtasks: Whether to include subtask nodes (default: False)

Returns:
    Complete spec data dictionary

**Parameters:**
- `spec_id`: str
- `title`: str
- `estimated_hours`: float
- `num_phases`: int
- `tasks_per_phase`: int
- `include_verify`: bool
- `include_subtasks`: bool

---

### `create_sample_spec_data(spec_id, num_phases, tasks_per_phase, with_dependencies) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:174`
**Complexity:** 6

**Description:**
> Create sample JSON spec data.

**Parameters:**
- `spec_id`: str
- `num_phases`: int
- `tasks_per_phase`: int
- `with_dependencies`: bool

---

### `create_spec_interactive(title, template, specs_dir, default_category) -> Tuple[bool, str, Optional[Dict[str, Any]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:88`
**Complexity:** 6

**Description:**
> Create a new spec interactively.

Args:
    title: Optional spec title (will prompt if not provided)
    template: Template to use (simple, medium, complex, security)
    specs_dir: Directory to save spec (defaults to specs/active)
    default_category: Optional default task category (overrides automatic inference)
                     One of: investigation, implementation, refactoring, decision, research

Returns:
    Tuple of (success, message, spec_dict)

**Parameters:**
- `title`: Optional[str]
- `template`: str
- `specs_dir`: Path
- `default_category`: Optional[str]

---

### `create_temp_json_spec(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:1027`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Factory fixture to create temporary JSON specs.

**Parameters:**
- `tmp_path`: None

---

### `create_temp_spec_file(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:1017`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Factory fixture to create temporary JSON spec files.

**Parameters:**
- `tmp_path`: None

---

### `detect_available_tools() -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reviewer.py:78`
**Complexity:** 3

**Description:**
> Detect which AI CLI tools are installed and available.

Returns:
    List of available tool names

---

### `detect_crud_operations(query, class_name, class_info) -> Dict[str, List[Dict[str, Any]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:120`
**Complexity:** 10

**Description:**
> Detect Create, Read, Update, Delete operations for a class.

Uses heuristic analysis of function names, instantiation data,
and method calls to classify operations.

Args:
    query: DocumentationQuery instance
    class_name: Name of the class being traced
    class_info: Class information dictionary

Returns:
    Dictionary with keys 'create', 'read', 'update', 'delete',
    each containing a list of operation dictionaries with:
    - function: Function name performing the operation
    - file: File path
    - line: Line number
    - operation_type: Specific operation (e.g., 'constructor', 'getter', 'setter')

**Parameters:**
- `query`: Any
- `class_name`: str
- `class_info`: Dict[str, Any]

---

### `detect_framework(modules) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:120`
**Complexity:** 9

**Description:**
> Detect web framework and other major libraries.

Args:
    modules: List of module information from CodebaseAnalyzer

Returns:
    Dictionary with detected framework info

**Parameters:**
- `modules`: List[Dict[str, Any]]

---

### `detect_languages(project_root, exclude_patterns) -> Set[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:52`
**Complexity:** 7

**Description:**
> Detect programming languages present in a project.

Args:
    project_root: Root directory of the project
    exclude_patterns: Optional list of patterns to exclude from scanning

Returns:
    Set of detected language names

**Parameters:**
- `project_root`: Path
- `exclude_patterns`: Optional[List[str]]

---

### `detect_layers(modules) -> Dict[str, List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:256`
**Complexity:** 10

**Description:**
> Detect architectural layers by grouping modules.

Args:
    modules: List of module information

Returns:
    Dictionary mapping layer names to file paths

**Parameters:**
- `modules`: List[Dict[str, Any]]

---

### `detect_project(directory) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/project.py:13`
⚠️ **Complexity:** 21 (High)

**Description:**
> Detect project type and extract dependencies.

Args:
    directory: Directory to analyze (defaults to current directory)

Returns:
    Dictionary with project type, dependencies, and metadata

**Parameters:**
- `directory`: Optional[Path]

---

### `detect_unjournaled_tasks(spec_id, specs_dir, printer) -> List[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/validation.py:343`
**Complexity:** 7

**Description:**
> Find completed tasks that need journal entries.

Returns list of tasks with:
- task_id
- title
- completed_at timestamp
- parent_id (for context)

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    List of unjournaled task dictionaries, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `django_modules() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:108`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample Django module data.

---

### `doc_query_samples(tmp_path) -> Dict[str, Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/conftest.py:9`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create sample documentation payloads for doc_query tests.

**Parameters:**
- `tmp_path`: Path

---

### `enhance_class_with_usage_tracking(cls, instantiated_by, imported_by, instantiation_count) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/schema.py:297`
**Complexity:** 4

**Description:**
> Enhance ParsedClass with usage tracking fields for schema v1.1+.

This function extends the base ParsedClass schema with usage information
to enable queries like:
- "Where is this class instantiated?" (instantiated_by)
- "Which files import this class?" (imported_by)
- "How many times is this class instantiated?" (instantiation_count)

Args:
    cls: Base ParsedClass instance from parser
    instantiated_by: List of locations where class is instantiated
    imported_by: List of files that import this class
    instantiation_count: Optional count of total instantiations across
                        the entire codebase

Returns:
    Enhanced dictionary with all base ParsedClass fields plus:
    - instantiated_by: array of InstantiationReference objects
    - imported_by: array of ImportReference objects
    - instantiation_count: optional integer (only if provided)

Example:
    >>> from claude_skills.code_doc.parsers.python import PythonParser
    >>> parser = PythonParser(root_path, [])
    >>> result = parser.parse_file("models.py")
    >>> cls = result.classes[0]
    >>>
    >>> # Add usage tracking data
    >>> instantiations = [InstantiationReference("main", "app.py", 10)]
    >>> imports = [ImportReference("app.py", 1, "from", "User")]
    >>>
    >>> enhanced = enhance_class_with_usage_tracking(
    ...     cls,
    ...     instantiated_by=instantiations,
    ...     imported_by=imports,
    ...     instantiation_count=5
    ... )
    >>> assert 'instantiated_by' in enhanced
    >>> assert 'imported_by' in enhanced
    >>> assert enhanced['instantiation_count'] == 5

Note:
    This is a non-breaking enhancement. The base ParsedClass.to_dict()
    remains unchanged. This function provides an opt-in way to include
    usage tracking data in the output schema.

**Parameters:**
- `cls`: BaseParsedClass
- `instantiated_by`: Optional[List[InstantiationReference]]
- `imported_by`: Optional[List[ImportReference]]
- `instantiation_count`: Optional[int]

---

### `enhance_function_with_cross_refs(func, callers, calls, call_count) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/schema.py:149`
**Complexity:** 4

**Description:**
> Enhance ParsedFunction with cross-reference fields for schema v1.1+.

This function extends the base ParsedFunction schema with bidirectional
cross-reference information, enabling queries like:
- "What functions call this function?" (callers)
- "What functions does this function call?" (calls)
- "How many times is this function called?" (call_count)

Args:
    func: Base ParsedFunction instance from parser
    callers: List of functions that call this function (who calls me)
    calls: List of functions called by this function (who do I call)
    call_count: Optional total count of calls to this function across
               the entire codebase

Returns:
    Enhanced dictionary with all base ParsedFunction fields plus:
    - callers: array of CallReference objects
    - calls: array of CallReference objects
    - call_count: optional integer (only if provided)

Example:
    >>> from claude_skills.code_doc.parsers.python import PythonParser
    >>> parser = PythonParser(root_path, [])
    >>> result = parser.parse_file("example.py")
    >>> func = result.functions[0]
    >>>
    >>> # Add cross-reference data
    >>> callers = [CallReference("main", "app.py", 10, "function_call")]
    >>> calls = [CallReference("helper", "utils.py", 5, "function_call")]
    >>>
    >>> enhanced = enhance_function_with_cross_refs(
    ...     func, callers=callers, calls=calls, call_count=3
    ... )
    >>> assert 'callers' in enhanced
    >>> assert 'calls' in enhanced
    >>> assert enhanced['call_count'] == 3

Note:
    This is a non-breaking enhancement. The base ParsedFunction.to_dict()
    remains unchanged. This function provides an opt-in way to include
    cross-reference data in the output schema.

**Parameters:**
- `func`: BaseParsedFunction
- `callers`: Optional[List[CallReference]]
- `calls`: Optional[List[CallReference]]
- `call_count`: Optional[int]

---

### `ensure_backups_directory(specs_dir) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:462`
**Complexity:** 5

**Description:**
> Ensure the .backups/ directory exists within the specs directory.

Creates specs/.backups/ and its README.md if they don't exist.
This is called defensively from multiple entry points to ensure
the directory structure is always available.

Args:
    specs_dir: Path to the specs directory (containing active/completed/archived)

Returns:
    Path to the .backups directory

Example:
    >>> specs_dir = Path("/project/specs")
    >>> backups_dir = ensure_backups_directory(specs_dir)
    >>> print(backups_dir)  # /project/specs/.backups

**Parameters:**
- `specs_dir`: Path

---

### `ensure_directory(path) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:128`
**Complexity:** 2

**Description:**
> Ensure a directory exists, creating it if necessary.

Args:
    path: Path to directory

Returns:
    True if directory exists or was created, False on error

**Parameters:**
- `path`: Path

---

### `ensure_documentation_exists(project_root, prompt_user, auto_generate) -> tuple[bool, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/doc_helper.py:210`
⚠️ **Complexity:** 13 (High)

**Description:**
> Ensure codebase documentation exists, optionally generating it.

This is a high-level convenience function that combines:
- check_doc_query_available() - Check if docs exist
- should_generate_docs() - Determine if generation is needed
- Skill(sdd-toolkit:code-doc) invocation - Actually generate docs

Args:
    project_root: Root directory (default: auto-detect)
    prompt_user: If True, prompt user to generate missing docs
    auto_generate: If True, auto-generate without prompting

Returns:
    tuple[bool, str]: (success, message)
        - success: True if docs are available (existing or newly generated)
        - message: Path to docs OR error/info message

Example:
    >>> # In sdd-plan Phase 1.2
    >>> success, result = ensure_documentation_exists(prompt_user=True)
    >>> if success:
    ...     print(f"Using docs at: {result}")
    ...     # Proceed with doc-query analysis
    ... else:
    ...     print(f"No docs: {result}")
    ...     # Fall back to manual exploration

**Parameters:**
- `project_root`: Optional[str]
- `prompt_user`: bool
- `auto_generate`: bool

---

### `ensure_human_readable_directory(specs_dir) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:525`
**Complexity:** 5

**Description:**
> Ensure the .human-readable/ directory exists within the specs directory.

Creates specs/.human-readable/ and its README.md if they don't exist.
This is called defensively from multiple entry points to ensure
the directory structure is always available.

Args:
    specs_dir: Path to the specs directory (containing active/completed/archived)

Returns:
    Path to the .human-readable directory

Example:
    >>> specs_dir = Path("/project/specs")
    >>> hr_dir = ensure_human_readable_directory(specs_dir)
    >>> print(hr_dir)  # /project/specs/.human-readable

**Parameters:**
- `specs_dir`: Path

---

### `ensure_json_spec(specs_structure) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:254`
**Complexity:** 3

**Description:**
> Ensure a JSON spec file exists for the given spec_id.

**Parameters:**
- `specs_structure`: Path

---

### `ensure_json_spec_file(specs_structure, spec_data) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:279`
**Complexity:** 2

**Description:**
> Ensure matching JSON spec file is created for given spec data.

**Parameters:**
- `specs_structure`: Path
- `spec_data`: Dict[str, Any]

---

### `ensure_reports_directory(specs_dir) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:336`
**Complexity:** 5

**Description:**
> Ensure the .reports/ directory exists within the specs directory.

Creates specs/.reports/ and its README.md if they don't exist.
This is called defensively from multiple entry points to ensure
the directory structure is always available.

Args:
    specs_dir: Path to the specs directory (containing active/completed/archived)

Returns:
    Path to the .reports directory

Example:
    >>> specs_dir = Path("/project/specs")
    >>> reports_dir = ensure_reports_directory(specs_dir)
    >>> print(reports_dir)  # /project/specs/.reports

**Parameters:**
- `specs_dir`: Path

---

### `ensure_reviews_directory(specs_dir) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:399`
**Complexity:** 5

**Description:**
> Ensure the .reviews/ directory exists within the specs directory.

Creates specs/.reviews/ and its README.md if they don't exist.
This is called defensively from multiple entry points to ensure
the directory structure is always available.

Args:
    specs_dir: Path to the specs directory (containing active/completed/archived)

Returns:
    Path to the .reviews directory

Example:
    >>> specs_dir = Path("/project/specs")
    >>> reviews_dir = ensure_reviews_directory(specs_dir)
    >>> print(reviews_dir)  # /project/specs/.reviews

**Parameters:**
- `specs_dir`: Path

---

### `execute_verify_task(spec_data, task_id, spec_root, retry_count) -> dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/integrations.py:161`
⚠️ **Complexity:** 38 (High)

**Description:**
> Execute a verification task based on its metadata.

Args:
    spec_data: Loaded JSON spec data
    task_id: Task ID (e.g., "verify-1-1")
    spec_root: Root directory for the spec (default: current dir)
    retry_count: Current retry attempt number (internal use)

Returns:
    dict: {
        "success": bool,             # Overall success
        "output": str,               # Execution output
        "errors": list[str],         # Error messages
        "skill_used": str | None,    # Skill invoked (if any)
        "duration": float,           # Execution time in seconds
        "on_failure": dict | None,   # on_failure configuration used
        "retry_count": int,          # Number of retries attempted
        "actions_taken": list[str]   # Actions taken on failure
    }

Example:
    >>> spec_data = load_json_spec("auth-001", specs_dir)
    >>> result = execute_verify_task(spec_data, "verify-1-1")
    >>> if not result["success"]:
    ...     print(f"Verification failed: {result['errors']}")
    ...     print(f"Actions taken: {result['actions_taken']}")

**Parameters:**
- `spec_data`: dict
- `task_id`: str
- `spec_root`: str
- `retry_count`: int

---

### `extract_frontmatter(spec_file) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:16`
**Complexity:** 5

**Description:**
> Extract metadata/frontmatter information from a specification file.

Supports both JSON-based specs (current default) and legacy Markdown specs
that contain a YAML-style frontmatter block delimited by ``---`` markers.

Args:
    spec_file: Path to the specification file.

Returns:
    Dictionary containing extracted metadata. On failure, returns a
    dictionary with an ``"error"`` key describing the failure.

**Parameters:**
- `spec_file`: Union[str, Path]

---

### `extract_readme(project_root) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:359`
**Complexity:** 4

**Description:**
> Extract README content if it exists.

Args:
    project_root: Project root directory

Returns:
    README content or None

**Parameters:**
- `project_root`: Path

---

### `extract_subparsers(parser) -> Optional[Dict[str, argparse.ArgumentParser]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:148`
**Complexity:** 4

**Description:**
> Extract subparsers from an ArgumentParser.

**Parameters:**
- `parser`: argparse.ArgumentParser

---

### `find_active_work(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py:70`
**Complexity:** 9

**Description:**
> Find all active SDD specifications with resumable work.

**Parameters:**
- `project_root`: None

---

### `find_blocking_tasks(spec_data, task_id) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:345`
**Complexity:** 5

**Description:**
> Find all tasks that are blocked by the given task.

Args:
    spec_data: JSON spec file data dictionary
    task_id: Task ID to analyze

Returns:
    List of task IDs that are blocked by this task

Example:
    >>> blocked = find_blocking_tasks(spec_data, "task-1-1")
    >>> print(f"{task_id} blocks {len(blocked)} tasks")

**Parameters:**
- `spec_data`: Dict
- `task_id`: str

---

### `find_circular_dependencies(spec_data) -> Dict[str, object]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:161`
**Complexity:** 1

**Description:**
> Backward-compatible wrapper returning legacy dependency analysis format.

**Parameters:**
- `spec_data`: Dict

---

### `find_circular_dependencies(spec_data) -> Dict[str, object]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:176`
**Complexity:** 1

**Description:**
> Backward-compatible wrapper returning legacy dependency analysis format.

**Parameters:**
- `spec_data`: Dict

---

### `find_circular_deps(spec_data) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/validation.py:48`
**Complexity:** 1

**Description:**
> Detected circular dependencies wrapper (backwards compatible).

**Parameters:**
- `spec_data`: Dict

---

### `find_conftest_files(root_dir) -> List[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:41`
**Complexity:** 1

**Description:**
> Find all conftest.py files.

Args:
    root_dir: Root directory to search from

Returns:
    List of Path objects for conftest.py files

**Parameters:**
- `root_dir`: str

---

### `find_files_by_pattern(directory, pattern, recursive, max_depth) -> List[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:274`
**Complexity:** 5

**Description:**
> Find files matching a pattern in a directory.

Args:
    directory: Directory to search
    pattern: Glob pattern (e.g., "*.py", "test_*.py")
    recursive: Whether to search recursively
    max_depth: Maximum depth for recursive search (None = unlimited)

Returns:
    List of matching file paths

Example:
    >>> py_files = find_files_by_pattern(Path("src"), "*.py")
    >>> print(f"Found {len(py_files)} Python files")

**Parameters:**
- `directory`: Path
- `pattern`: str
- `recursive`: bool
- `max_depth`: Optional[int]

---

### `find_pattern(pattern, directory) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/workflow.py:57`
**Complexity:** 4

**Description:**
> Find files matching a pattern.

Args:
    pattern: Glob pattern (e.g., "*.ts", "src/**/*.spec.ts")
    directory: Directory to search (defaults to current directory)

Returns:
    List of matching file paths

**Parameters:**
- `pattern`: str
- `directory`: Optional[Path]

---

### `find_refactor_candidates(query, min_complexity, limit) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:14`
**Complexity:** 4

**Description:**
> Find high-priority refactoring candidates.

Identifies functions that would benefit most from refactoring by combining
complexity metrics with usage data. Priority score = complexity × dependents.

Args:
    query: DocumentationQuery instance
    min_complexity: Minimum complexity threshold (default: 10)
    limit: Maximum number of candidates to return (default: 20)

Returns:
    Dictionary with keys:
    - candidates: List of candidate dictionaries sorted by priority
    - quick_wins: Subset with high complexity, low dependents
    - major_refactors: Subset with high complexity, high dependents
    - summary: Statistics about the analysis

Example:
    >>> query = DocumentationQuery()
    >>> query.load()
    >>> result = find_refactor_candidates(query, min_complexity=15, limit=10)
    >>> print(f"Found {len(result['candidates'])} candidates")

**Parameters:**
- `query`: Any
- `min_complexity`: int
- `limit`: int

---

### `find_related_files(file_path, directory) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/project.py:303`
⚠️ **Complexity:** 12 (High)

**Description:**
> Find files related to a given file.

Args:
    file_path: Path to the source file
    directory: Project directory (defaults to current directory)

Returns:
    Dictionary with categorized related files

**Parameters:**
- `file_path`: str
- `directory`: Optional[Path]

---

### `find_session_by_pid(sessions_cache) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:178`
**Complexity:** 8

**Description:**
> Find which cached session matches the current process by walking the process tree.

Args:
    sessions_cache: The sessions cache dictionary for current directory
                   Format: {"sessions": {"session-id": {"ppid": 12345, ...}}, ...}

Returns:
    Session ID if found, None otherwise

**Parameters:**
- `sessions_cache`: Dict[str, Any]

---

### `find_similar_implementations(feature_name, docs_path) -> List[QueryResult]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:344`
**Complexity:** 1

**Description:**
> Find similar implementations (convenience function).

Args:
    feature_name: Feature name or pattern
    docs_path: Optional path to documentation

Returns:
    List of similar entities

**Parameters:**
- `feature_name`: str
- `docs_path`: Optional[str]

---

### `find_spec_file(spec_id, specs_dir) -> Optional[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:83`
**Complexity:** 3

**Description:**
> Find the spec file for a given spec ID.

Searches in pending/, active/, completed/, and archived/ subdirectories.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory (containing pending/active/completed/archived)

Returns:
    Absolute path to the spec file, or None if not found

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path

---

### `find_specs_directory(provided_path) -> Optional[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:10`
⚠️ **Complexity:** 17 (High)

**Description:**
> Discover the specs directory.

Args:
    provided_path: Optional explicit path to specs directory or file

Returns:
    Absolute Path to specs directory (containing active/completed/archived), or None if not found

**Parameters:**
- `provided_path`: Optional[str]

---

### `find_specs_directory() -> Optional[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:143`
**Complexity:** 4

**Description:**
> Find the specs directory in the project.

Returns:
    Path to specs directory or None if not found

---

### `find_stable_claude_process() -> Optional[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:223`
⚠️ **Complexity:** 15 (High)

**Description:**
> Find the stable 'claude' process PID by walking up the process tree.

This function walks up the process tree from the current process to find
the long-lived 'claude' binary, skipping short-lived subprocess wrappers.

This is critical for session detection when multiple concurrent Claude Code
sessions exist in the same directory. By caching the stable PID instead of
a short-lived subprocess PID, session detection remains accurate even as
subprocesses die.

Returns:
    The PID of the stable 'claude' process if found, otherwise None

---

### `find_test_coverage(query, entity_name, entity_type, entity_info) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:334`
**Complexity:** 5

**Description:**
> Find test files that cover the entity.

Uses heuristics to identify tests that exercise the code.

Args:
    query: DocumentationQuery instance
    entity_name: Name of the entity
    entity_type: 'function' or 'class'
    entity_info: Entity information dictionary

Returns:
    Dictionary with:
    - test_files: List of test files that reference the entity
    - estimated_coverage: Percentage estimate (0-100)

**Parameters:**
- `query`: Any
- `entity_name`: str
- `entity_type`: str
- `entity_info`: Dict[str, Any]

---

### `find_test_files(root_dir) -> List[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:18`
**Complexity:** 2

**Description:**
> Find all test files in the project.

Args:
    root_dir: Root directory to search from

Returns:
    List of Path objects for test files

**Parameters:**
- `root_dir`: str

---

### `find_tests(directory, source_file) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/project.py:118`
⚠️ **Complexity:** 17 (High)

**Description:**
> Discover test files and patterns in the project.

Args:
    directory: Directory to search (defaults to current directory)
    source_file: Optional source file to find corresponding test

Returns:
    Dictionary with test files, patterns, and framework detection

**Parameters:**
- `directory`: Optional[Path]
- `source_file`: Optional[str]

---

### `find_verify_tasks_for_task(spec_data, task_id) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/status.py:18`
**Complexity:** 5

**Description:**
> Find all verify tasks associated with a given task.

Verify tasks are identified by:
1. Having type="verify"
2. Being a sibling or child of the task (same parent or task is parent)
3. Having an ID pattern like verify-X-Y where X matches task-X-Y

Args:
    spec_data: Loaded JSON spec data
    task_id: Task ID to find verify tasks for (e.g., "task-1-1")

Returns:
    List of verify task IDs

**Parameters:**
- `spec_data`: dict
- `task_id`: str

---

### `flask_modules() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:133`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample Flask module data.

---

### `format_ai_context_research_prompt(context_summary, key_files, project_root) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:190`
**Complexity:** 2

**Description:**
> Format prompt for AI context research (read-only analysis).

Args:
    context_summary: Structured codebase context summary
    key_files: List of key file paths
    project_root: Project root directory

Returns:
    Formatted prompt string asking for research findings only

**Parameters:**
- `context_summary`: str
- `key_files`: List[str]
- `project_root`: Path

---

### `format_architecture_research_prompt(context_summary, key_files, project_root) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:104`
**Complexity:** 3

**Description:**
> Format prompt for architecture research (read-only analysis).

Args:
    context_summary: Structured codebase context summary
    key_files: List of key file paths to read
    project_root: Project root directory

Returns:
    Formatted prompt string asking for research findings only

**Parameters:**
- `context_summary`: str
- `key_files`: List[str]
- `project_root`: Path

---

### `format_argument(action) -> Tuple[str, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:105`
**Complexity:** 8

**Description:**
> Format a single argument for documentation.

**Parameters:**
- `action`: argparse.Action

---

### `format_call_graph_as_dot(graph) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:261`
**Complexity:** 6

**Description:**
> Format call graph as GraphViz DOT format.

**Parameters:**
- `graph`: Dict[str, Any]

---

### `format_candidate_entry(candidate, rank) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:289`
**Complexity:** 1

**Description:**
> Format a single candidate entry.

Args:
    candidate: Candidate dictionary
    rank: Overall rank (1-based)

Returns:
    Formatted string for one candidate

**Parameters:**
- `candidate`: Dict[str, Any]
- `rank`: int

---

### `format_candidates_list(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:228`
**Complexity:** 10

**Description:**
> Format candidates list organized by risk level.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with prioritized candidate list

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_completion_prompt(spec_data, phase_id, show_hours_input) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:325`
**Complexity:** 8

**Description:**
> Generate user-friendly completion prompt with optional hours input.

Creates a formatted prompt message to present to users when a spec or
phase is complete and ready to be marked as finalized. The prompt
includes progress summary and optionally asks for actual hours spent
if estimated hours were provided in the task metadata.

This function is designed to be called by sdd-update, sdd-next, and
status-report workflows when completion conditions are met (all tasks
completed, no blocked tasks).

Args:
    spec_data: JSON spec file data containing hierarchy and task information
    phase_id: Optional phase ID to format prompt for specific phase.
             If None, formats prompt for entire spec.
    show_hours_input: Whether to include actual hours input prompt.
                     Default True. Set False to skip hours input.

Returns:
    Dictionary with prompt information:
    {
        "prompt_text": str,           # Formatted completion message
        "requires_input": bool,        # True if hours input requested
        "completion_context": {        # Metadata about completion
            "node_id": str,            # Node that is complete
            "node_type": str,          # "spec" or "phase"
            "total_tasks": int,        # Total tasks in scope
            "completed_tasks": int,    # Number completed
            "estimated_hours": float,  # Estimated hours (if available)
            "has_hours_estimate": bool # Whether estimate exists
        },
        "error": Optional[str]         # Error message if prompt failed
    }

Example:
    >>> from claude_skills.common.spec import load_spec
    >>> from claude_skills.common.completion import format_completion_prompt
    >>>
    >>> spec_data = load_spec("specs/active/my-spec.json")
    >>> result = format_completion_prompt(spec_data)
    >>>
    >>> if result["error"]:
    ...     print(f"Error: {result['error']}")
    ... else:
    ...     print(result["prompt_text"])
    ...     if result["requires_input"]:
    ...         actual_hours = input("Enter actual hours: ")

    Example prompt output (spec-level with hours):
    '''
    All tasks complete!

    Spec: User Authentication System
    Progress: 23/23 tasks (100%)
    Estimated: 15.5 hours

    How many actual hours did this take? (Enter a number or press Enter to skip)
    '''

    Example prompt output (phase-level without hours):
    '''
    Phase complete!

    Phase: Database Schema Setup
    Progress: 7/7 tasks (100%)

    Mark this phase as complete?
    '''

**Parameters:**
- `spec_data`: Dict
- `phase_id`: Optional[str]
- `show_hours_input`: bool

---

### `format_dependency_tree(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:539`
⚠️ **Complexity:** 13 (High)

**Description:**
> Format dependency tree visualization.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with dependency tree

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_diff_json(report) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:234`
**Complexity:** 2

**Description:**
> Format diff report as JSON.

**Parameters:**
- `report`: DiffReport

---

### `format_diff_markdown(report, spec_id) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/diff.py:171`
⚠️ **Complexity:** 13 (High)

**Description:**
> Format diff report as markdown.

**Parameters:**
- `report`: DiffReport
- `spec_id`: str

---

### `format_execution_plan(spec_id, task_id, specs_dir) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:58`
⚠️ **Complexity:** 39 (High)

**Description:**
> Format an execution plan for a task with proper newlines and structure.

Args:
    spec_id: Specification ID
    task_id: Task ID to format
    specs_dir: Path to specs directory

Returns:
    Formatted execution plan string ready for display

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `specs_dir`: Path

---

### `format_hot_spots(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:365`
**Complexity:** 3

**Description:**
> Format hot spots table.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    Formatted string with hot spots table

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_json_output(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:756`
**Complexity:** 1

**Description:**
> Format impact result as JSON.

Args:
    impact_result: Output from analyze_impact()

Returns:
    JSON string

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_json_output(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:510`
**Complexity:** 1

**Description:**
> Format result as JSON.

Args:
    result: Output from find_refactor_candidates()

Returns:
    JSON string

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_json_output(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:593`
**Complexity:** 1

**Description:**
> Format trace result as JSON.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    JSON string

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_json_output(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:451`
**Complexity:** 1

**Description:**
> Format trace result as JSON.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    JSON string

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_layer_summary(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:339`
**Complexity:** 4

**Description:**
> Format layer breakdown summary.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    Formatted string with layer statistics

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_lifecycle_view(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:376`
⚠️ **Complexity:** 15 (High)

**Description:**
> Format lifecycle visualization showing CRUD flow.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    Formatted string with lifecycle stages

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_major_refactors(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:349`
**Complexity:** 4

**Description:**
> Format major refactors section.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with major refactors

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_metrics_human(metrics, max_context) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:271`
**Complexity:** 1

**Description:**
> Format token metrics for human-readable output.

**Parameters:**
- `metrics`: None
- `max_context`: int

---

### `format_metrics_json(metrics, max_context) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:292`
**Complexity:** 1

**Description:**
> Format token metrics as JSON.

**Parameters:**
- `metrics`: None
- `max_context`: int

---

### `format_number(n) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:266`
**Complexity:** 1

**Description:**
> Format a number with thousands separators.

**Parameters:**
- `n`: int

---

### `format_output(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py:154`
⚠️ **Complexity:** 18 (High)

**Description:**
> Format active work as human-readable text with last-accessed task info.

**Parameters:**
- `project_root`: None

---

### `format_prompt(failure_type, error_message, hypothesis, test_code, impl_code, context, question) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:363`
**Complexity:** 6

**Description:**
> Format a prompt for external tool consultation.

Args:
    failure_type: Type of test failure
    error_message: The full error message from pytest
    hypothesis: Your hypothesis about the root cause
    test_code: Test code snippet (optional)
    impl_code: Implementation code snippet (optional)
    context: Additional context (optional)
    question: Specific question to ask (optional)

Returns:
    Formatted prompt string

**Parameters:**
- `failure_type`: str
- `error_message`: str
- `hypothesis`: str
- `test_code`: Optional[str]
- `impl_code`: Optional[str]
- `context`: Optional[str]
- `question`: Optional[str]

---

### `format_property_analysis(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:490`
**Complexity:** 8

**Description:**
> Format property access analysis.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    Formatted string with property analysis

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_quick_wins(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:313`
**Complexity:** 4

**Description:**
> Format quick wins section.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with quick wins

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_recommendations(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:669`
**Complexity:** 3

**Description:**
> Format recommendations section.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with recommendations

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_recommendations(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:386`
**Complexity:** 4

**Description:**
> Format general recommendations section.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with recommendations

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_result(result, verbose) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:190`
⚠️ **Complexity:** 29 (High)

**Parameters:**
- `result`: QueryResult
- `verbose`: bool

---

### `format_risk_assessment(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:633`
**Complexity:** 2

**Description:**
> Format risk assessment display.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with risk assessment

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_summary(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:693`
**Complexity:** 1

**Description:**
> Format summary statistics.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with summary

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_summary(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:440`
**Complexity:** 1

**Description:**
> Format summary statistics.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with summary

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_summary(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:538`
**Complexity:** 1

**Description:**
> Format summary statistics.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    Formatted string with summary

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_summary(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:393`
**Complexity:** 2

**Description:**
> Format summary statistics.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    Formatted string with summary statistics

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_synthesis_output(synthesis, responses, printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:880`
⚠️ **Complexity:** 19 (High)

**Description:**
> Format and print the synthesis output in a structured way.

Args:
    synthesis: Synthesis dictionary from synthesize_responses()
    responses: List of all ConsultationResponse objects
    printer: PrettyPrinter instance (creates default if None)

**Parameters:**
- `synthesis`: Dict[str, any]
- `responses`: List[ConsultationResponse]
- `printer`: Optional[PrettyPrinter]

---

### `format_test_coverage(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:603`
**Complexity:** 4

**Description:**
> Format test coverage report.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with test coverage

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_text_output(impact_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:719`
**Complexity:** 2

**Description:**
> Format complete text output for impact command.

Args:
    impact_result: Output from analyze_impact()

Returns:
    Formatted string with all sections

**Parameters:**
- `impact_result`: Dict[str, Any]

---

### `format_text_output(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:472`
**Complexity:** 3

**Description:**
> Format complete text output for refactor-candidates command.

Args:
    result: Output from find_refactor_candidates()

Returns:
    Formatted string with all sections

**Parameters:**
- `result`: Dict[str, Any]

---

### `format_text_output(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:562`
**Complexity:** 2

**Description:**
> Format complete text output for trace-data command.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    Formatted string with all sections

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_text_output(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:417`
**Complexity:** 1

**Description:**
> Format complete text output for trace-entry command.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    Formatted string with all sections

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_tree_view(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:254`
**Complexity:** 8

**Description:**
> Format trace result as an ASCII tree visualization.

Creates a hierarchical tree showing the call chain from the entry function,
with layer annotations, complexity scores, and hot spot markers.

Args:
    trace_result: Output from trace_execution_flow()

Returns:
    Formatted tree string with Unicode box-drawing characters

Example Output:
    main [Presentation] (complexity: 8)
    ├─ process_data [Business Logic] (complexity: 15) 🔥
    │  ├─ validate [Utility] (complexity: 3)
    │  └─ save [Data] (complexity: 5)
    └─ format_output [Presentation] (complexity: 2)

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_usage_map(trace_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:450`
**Complexity:** 7

**Description:**
> Format usage map organized by architectural layer.

Args:
    trace_result: Output from trace_data_lifecycle()

Returns:
    Formatted string with layer breakdown

**Parameters:**
- `trace_result`: Dict[str, Any]

---

### `format_validation_summary(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:171`
**Complexity:** 7

**Description:**
> Render a human-readable summary of validation findings.

**Parameters:**
- `result`: NormalizedValidationResult

---

### `format_verification_summary(verification_results) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/verification.py:143`
**Complexity:** 6

**Description:**
> Format a summary of multiple verification results with proper newlines.

Args:
    verification_results: List of dicts with keys:
        - verify_id: str (e.g., 'verify-1-1')
        - title: str
        - status: str ('PASSED', 'FAILED', 'PARTIAL')
        - command: Optional[str]
        - result: Optional[str]
        - notes: Optional[str]

Returns:
    Formatted summary string ready for display

**Parameters:**
- `verification_results`: list[dict]

---

### `generate_ai_context_docs(context_summary, key_files, project_root, tool, use_multi_agent, dry_run, verbose, printer) -> Tuple[bool, Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:661`
**Complexity:** 4

**Description:**
> Get AI context research findings from AI consultation.

Args:
    context_summary: Codebase context summary
    key_files: List of key files
    project_root: Project root directory
    tool: Specific tool to use ("auto" for auto-selection)
    use_multi_agent: Use multiple agents if available
    dry_run: Show what would run without running
    verbose: Enable verbose output
    printer: Optional PrettyPrinter for consistent output

Returns:
    Tuple of (success: bool, result: Dict with responses_by_tool)

**Parameters:**
- `context_summary`: str
- `key_files`: List[str]
- `project_root`: Path
- `tool`: str
- `use_multi_agent`: bool
- `dry_run`: bool
- `verbose`: bool
- `printer`: Optional['PrettyPrinter']

---

### `generate_architecture_docs(context_summary, key_files, project_root, tool, use_multi_agent, dry_run, verbose, printer) -> Tuple[bool, Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:620`
**Complexity:** 4

**Description:**
> Get architecture research findings from AI consultation.

Args:
    context_summary: Codebase context summary
    key_files: List of key files
    project_root: Project root directory
    tool: Specific tool to use ("auto" for auto-selection)
    use_multi_agent: Use multiple agents if available
    dry_run: Show what would run without running
    verbose: Enable verbose output
    printer: Optional PrettyPrinter for consistent output

Returns:
    Tuple of (success: bool, result: Dict with responses_by_tool)

**Parameters:**
- `context_summary`: str
- `key_files`: List[str]
- `project_root`: Path
- `tool`: str
- `use_multi_agent`: bool
- `dry_run`: bool
- `verbose`: bool
- `printer`: Optional['PrettyPrinter']

---

### `generate_backups_readme_content() -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:442`
**Complexity:** 2

**Description:**
> Generate README content for the specs/.backups/ directory.

Reads from the template file in common/templates/backups_readme.md.

Returns:
    Markdown content for README.md explaining the backups directory

---

### `generate_combined_report(spec_result, json_spec_result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/reporting.py:149`
**Complexity:** 4

**Description:**
> Generate a combined validation report for markdown spec and JSON spec.

Args:
    spec_result: SpecValidationResult from markdown spec validation
    json_spec_result: JsonSpecValidationResult from JSON spec validation

Returns:
    Formatted combined report string

**Parameters:**
- `spec_result`: SpecValidationResult
- `json_spec_result`: JsonSpecValidationResult

---

### `generate_command_reference(subparsers, skill_name) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:160`
⚠️ **Complexity:** 17 (High)

**Description:**
> Generate markdown for the Command Reference section.

**Parameters:**
- `subparsers`: Dict[str, argparse.ArgumentParser]
- `skill_name`: str

---

### `generate_documentation(skill_name, sections) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:267`
**Complexity:** 9

**Description:**
> Generate complete documentation for a skill.

Args:
    skill_name: Name of the skill (e.g., 'sdd-validate')
    sections: List of sections to include. Options: 'global', 'commands', 'usage'
             If None, includes all applicable sections.

Returns:
    Generated markdown documentation

**Parameters:**
- `skill_name`: str
- `sections`: Optional[List[str]]

---

### `generate_global_options(parser, skill_name) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:128`
**Complexity:** 5

**Description:**
> Generate markdown for global options section.

**Parameters:**
- `parser`: argparse.ArgumentParser
- `skill_name`: str

---

### `generate_human_readable_readme_content() -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:505`
**Complexity:** 2

**Description:**
> Generate README content for the specs/.human-readable/ directory.

Reads from the template file in common/templates/human_readable_readme.md.

Returns:
    Markdown content for README.md explaining the human-readable directory

---

### `generate_json_report(consensus, spec_id, spec_title, review_type) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:221`
**Complexity:** 1

**Description:**
> Generate JSON format review report.

Args:
    consensus: Consensus data
    spec_id: Specification ID
    spec_title: Specification title
    review_type: Review type

Returns:
    JSON-serializable report dictionary

**Parameters:**
- `consensus`: Dict[str, Any]
- `spec_id`: str
- `spec_title`: str
- `review_type`: str

---

### `generate_json_spec_report(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/reporting.py:94`
**Complexity:** 9

**Description:**
> Generate a comprehensive JSON spec validation report.

Args:
    result: JsonSpecValidationResult from JSON spec validation

Returns:
    Formatted report string

**Parameters:**
- `result`: JsonSpecValidationResult

---

### `generate_markdown_report(consensus, spec_id, spec_title, review_type, parsed_responses) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reporting.py:12`
**Complexity:** 5

**Description:**
> Generate comprehensive markdown review report.

With AI synthesis, the consensus already contains structured markdown.
This function wraps it with header and model details.

Args:
    consensus: Consensus data from AI synthesis
    spec_id: Specification ID
    spec_title: Specification title
    review_type: Type of review performed
    parsed_responses: Individual model responses (optional)

Returns:
    Formatted markdown report

**Parameters:**
- `consensus`: Dict[str, Any]
- `spec_id`: str
- `spec_title`: str
- `review_type`: str
- `parsed_responses`: List[Dict[str, Any]]

---

### `generate_recommendations(entity_name, entity_type, blast_radius, test_coverage, risk_assessment) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py:456`
**Complexity:** 9

**Description:**
> Generate actionable refactoring recommendations.

Args:
    entity_name: Name of the entity
    entity_type: 'function' or 'class'
    blast_radius: Blast radius data
    test_coverage: Test coverage data
    risk_assessment: Risk assessment data

Returns:
    List of recommendation strings

**Parameters:**
- `entity_name`: str
- `entity_type`: str
- `blast_radius`: Dict[str, List[Dict[str, Any]]]
- `test_coverage`: Dict[str, Any]
- `risk_assessment`: Dict[str, Any]

---

### `generate_report(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/reporting.py:11`
⚠️ **Complexity:** 40 (High)

**Description:**
> Generate a validation report in the requested format.

**Parameters:**
- `result`: JsonSpecValidationResult

---

### `generate_reports_readme_content() -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:316`
**Complexity:** 2

**Description:**
> Generate README content for the specs/.reports/ directory.

Reads from the template file in common/templates/reports_readme.md.

Returns:
    Markdown content for README.md explaining the reports directory

---

### `generate_review_prompt(spec_content, review_type, spec_id, title) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:72`
**Complexity:** 4

**Description:**
> Generate an unbiased, critical review prompt.

Args:
    spec_content: Full specification content
    review_type: Type of review (quick, full, security, feasibility)
    spec_id: Specification ID
    title: Specification title

Returns:
    Formatted prompt string

**Parameters:**
- `spec_content`: str
- `review_type`: str
- `spec_id`: str
- `title`: str

---

### `generate_reviews_readme_content() -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:379`
**Complexity:** 2

**Description:**
> Generate README content for the specs/.reviews/ directory.

Reads from the template file in common/templates/reviews_readme.md.

Returns:
    Markdown content for README.md explaining the reviews directory

---

### `generate_simple_usage(parser, skill_name) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:220`
⚠️ **Complexity:** 14 (High)

**Description:**
> Generate usage section for CLIs without subcommands.

**Parameters:**
- `parser`: argparse.ArgumentParser
- `skill_name`: str

---

### `generate_spec_from_template(template_id, title, spec_id, default_category) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/templates.py:76`
**Complexity:** 5

**Description:**
> Generate a spec structure from a template.

Args:
    template_id: Template to use
    title: Specification title
    spec_id: Optional spec ID (auto-generated if not provided)
    default_category: Optional default task category (overrides automatic inference)
                     One of: investigation, implementation, refactoring, decision, research
    **kwargs: Additional metadata to override template defaults

Returns:
    Spec dictionary ready to be serialized to JSON

**Parameters:**
- `template_id`: str
- `title`: str
- `spec_id`: str
- `default_category`: str

---

### `generate_spec_report(result) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/reporting.py:18`
⚠️ **Complexity:** 22 (High)

**Description:**
> Generate a comprehensive spec validation report.

Args:
    result: SpecValidationResult from validation

Returns:
    Formatted report string

**Parameters:**
- `result`: SpecValidationResult

---

### `generate_time_report(spec_id, specs_dir, printer) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/time_tracking.py:180`
**Complexity:** 9

**Description:**
> Generate time variance report for a spec.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    printer: Optional printer for output

Returns:
    Dictionary with time analysis, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `get_all_tasks_in_subtree(hierarchy, node_id) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:133`
**Complexity:** 4

**Description:**
> Recursively collect all task IDs under a node.

Traverses the hierarchy tree starting from the given node and collects
all descendant nodes that are of type "task". This includes tasks at
any depth in the tree.

Args:
    hierarchy: The hierarchy dictionary from spec data
    node_id: Starting node ID to search from

Returns:
    List of task IDs found in the subtree (only nodes with type="task")

**Parameters:**
- `hierarchy`: Dict
- `node_id`: str

---

### `get_auto_trigger_failures() -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:358`
**Complexity:** 3

**Description:**
> Get list of failure types that auto-trigger consensus.

Returns:
    List of failure type names

---

### `get_available_tools() -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:49`
**Complexity:** 5

**Description:**
> Check which AI CLI tools are available.

Returns:
    List of available tool names

---

### `get_available_tools() -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:130`
**Complexity:** 1

**Description:**
> Get list of available external tools.

Returns:
    List of tool names that are installed

---

### `get_best_tool(doc_type, available_tools) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:74`
**Complexity:** 6

**Description:**
> Get the best available tool for a documentation type.

Args:
    doc_type: Type of documentation (architecture, ai_context, developer_guide)
    available_tools: List of available tools (auto-detected if None)

Returns:
    Tool name or None if no tools available

**Parameters:**
- `doc_type`: str
- `available_tools`: Optional[List[str]]

---

### `get_best_tool(failure_type, available_tools) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:330`
**Complexity:** 8

**Description:**
> Get the best available tool for a given failure type.

Args:
    failure_type: Type of test failure
    available_tools: List of available tool names (auto-detected if None)

Returns:
    Tool name to use, or None if no tools available

**Parameters:**
- `failure_type`: str
- `available_tools`: Optional[List[str]]

---

### `get_cached_transcript_path() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:82`
⚠️ **Complexity:** 36 (High)

**Description:**
> Load transcript path from cache for current working directory.

Uses multi-layered detection to identify which transcript belongs to the
current Claude Code session, enabling correct session detection even with
multiple concurrent sessions in the same directory.

Detection Strategy (in order of priority):
1. PID-based: Match current process tree to cached session PPIDs
2. TTY-based: Match current terminal to cached session TTY
3. Environment variable: Check CLAUDE_SESSION_ID
4. File writing detection: Check which transcript is open for writing (lsof)
5. Fallback: Most recently modified transcript (last resort)

Returns:
    Cached transcript path or None if not found

---

### `get_config_path() -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:37`
**Complexity:** 1

**Description:**
> Get the path to the config.yaml file.

Returns:
    Path to config.yaml in the skill root directory

---

### `get_consensus_info() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:378`
**Complexity:** 2

**Description:**
> Get consensus configuration info (for display/debugging).

Returns:
    Dict with consensus pairs and auto-trigger info

---

### `get_consensus_pair_for_failure(failure_type) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:177`
**Complexity:** 5

**Description:**
> Get the consensus pair to use for a specific failure type.

Checks in order:
1. Explicit entry for failure_type
2. Default setting for undefined types
3. Fallback to "default" pair

Args:
    failure_type: Type of test failure

Returns:
    Pair name (e.g., 'default', 'code-focus', 'discovery-focus')
    Returns 'default' if not configured

**Parameters:**
- `failure_type`: str

---

### `get_consensus_pairs() -> Dict[str, List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:214`
**Complexity:** 3

**Description:**
> Get defined consensus pairs from configuration.

Falls back to hardcoded MULTI_AGENT_PAIRS if not configured.

Returns:
    Dict mapping pair names to lists of tools

---

### `get_consultation_timeout() -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:232`
**Complexity:** 5

**Description:**
> Get consultation timeout from config (default: 90 seconds).

Returns:
    Timeout in seconds

---

### `get_current_ppid() -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:213`
**Complexity:** 1

**Description:**
> Get the parent process ID of the current process.

Returns:
    Parent PID

---

### `get_dependency_chain(spec_data, task_id) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:283`
**Complexity:** 7

**Description:**
> Get the full dependency chain for a task.

Returns list of task IDs that must be completed before the given task,
in order from immediate dependencies to transitive dependencies.

Args:
    spec_data: JSON spec file data dictionary
    task_id: Task ID to analyze

Returns:
    List of task IDs in dependency order

Example:
    >>> chain = get_dependency_chain(spec_data, "task-3-1")
    >>> print(chain)  # ["task-1-1", "task-2-1", "task-3-1"]

**Parameters:**
- `spec_data`: Dict
- `task_id`: str

---

### `get_directory_structure(test_files, root) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:179`
**Complexity:** 3

**Description:**
> Build a directory structure from test files.

Args:
    test_files: List of test file paths
    root: Root directory path

Returns:
    Dictionary mapping directory paths to lists of file names

**Parameters:**
- `test_files`: List[Path]
- `root`: Path

---

### `get_enabled_tools() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:96`
**Complexity:** 1

**Description:**
> Get only the enabled tools from configuration.

Returns:
    Dict with only enabled tools

---

### `get_flags_for_tool(tool) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:91`
**Complexity:** 3

**Description:**
> Get additional CLI flags for a tool from configuration.

Args:
    tool: Tool name

Returns:
    List of additional flags

**Parameters:**
- `tool`: str

---

### `get_impact_analysis(module_path, docs_path) -> Dict[str, any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:374`
**Complexity:** 1

**Description:**
> Get impact analysis for a module (convenience function).

Args:
    module_path: Path to the module
    docs_path: Optional path to documentation

Returns:
    Dict with impact analysis

**Parameters:**
- `module_path`: str
- `docs_path`: Optional[str]

---

### `get_journal_entries(spec_id, specs_dir, task_id, printer) -> Optional[List[Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:436`
⚠️ **Complexity:** 12 (High)

**Description:**
> Get journal entries for a spec, optionally filtered by task_id.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    task_id: Optional task ID to filter entries
    printer: Optional printer for output

Returns:
    List of journal entry dictionaries, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `task_id`: Optional[str]
- `printer`: Optional[PrettyPrinter]

---

### `get_json_spec_metadata(spec_data) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec_analysis.py:143`
**Complexity:** 3

**Description:**
> Extract metadata from JSON spec.

Args:
    spec_data: JSON spec file data dictionary

Returns:
    Dictionary with JSON spec metadata

Example:
    >>> with open("specs/active/my-spec.json") as f:
    ...     spec_data = json.load(f)
    >>> metadata = get_json_spec_metadata(spec_data)
    >>> print(f"Last updated: {metadata['last_updated']}")

**Parameters:**
- `spec_data`: Dict

---

### `get_language_for_extension(extension) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:90`
**Complexity:** 1

**Description:**
> Get language name for a file extension.

Args:
    extension: File extension (with or without dot)

Returns:
    Language name or 'unknown'

**Parameters:**
- `extension`: str

---

### `get_metrics_file_path() -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:213`
**Complexity:** 1

**Description:**
> Return the path to the metrics JSONL file.

---

### `get_missing_tools() -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:141`
**Complexity:** 1

**Description:**
> Get list of missing external tools.

Returns:
    List of tool names that are not installed

---

### `get_model_for_tool(tool, failure_type) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:53`
⚠️ **Complexity:** 11 (High)

**Description:**
> Get the best model for a tool, considering priority and failure-type overrides.

Falls back to hardcoded defaults if configuration not available.

Args:
    tool: Tool name (gemini, codex, cursor-agent)
    failure_type: Optional failure type for override lookup

Returns:
    Model name to use

**Parameters:**
- `tool`: str
- `failure_type`: Optional[str]

---

### `get_next_task(spec_data) -> Optional[Tuple[str, Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:103`
⚠️ **Complexity:** 15 (High)

**Description:**
> Find the next actionable task.

Args:
    spec_data: JSON spec file data

Returns:
    Tuple of (task_id, task_data) or None if no task available

**Parameters:**
- `spec_data`: Dict

---

### `get_node(spec_data, node_id) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:323`
**Complexity:** 1

**Description:**
> Get a specific node from the state hierarchy.

Args:
    spec_data: JSON spec file data
    node_id: Node identifier

Returns:
    Node data dictionary or None if not found

**Parameters:**
- `spec_data`: Dict
- `node_id`: str

---

### `get_parent_pids(pid, max_depth) -> List[int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:17`
**Complexity:** 8

**Description:**
> Get the chain of parent process IDs up the process tree.

Args:
    pid: Starting PID (defaults to current process)
    max_depth: Maximum depth to traverse (prevents infinite loops)

Returns:
    List of PIDs from current process up to init, excluding current PID

**Parameters:**
- `pid`: Optional[int]
- `max_depth`: int

---

### `get_parser_from_module(module_name) -> argparse.ArgumentParser`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:35`
**Complexity:** 10

**Description:**
> Import a CLI module and extract its ArgumentParser.

This function attempts to get the parser by:
1. Looking for a get_parser() function
2. Calling main() with --help and capturing the parser
3. Looking for a global 'parser' variable

**Parameters:**
- `module_name`: str

---

### `get_preset_description(preset) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:266`
**Complexity:** 2

**Description:**
> Get description for a preset.

Args:
    preset: Preset name

Returns:
    Description string or None if preset doesn't exist

**Parameters:**
- `preset`: str

---

### `get_preset_flags(preset) -> Optional[List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:281`
**Complexity:** 2

**Description:**
> Get flags for a preset.

Args:
    preset: Preset name

Returns:
    List of flag strings or None if preset doesn't exist

**Parameters:**
- `preset`: str

---

### `get_presets() -> Dict[str, Dict[str, str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:221`
**Complexity:** 1

**Description:**
> Get all available presets.

Returns:
    Dictionary of preset configurations

---

### `get_process_info(pid) -> Optional[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:300`
**Complexity:** 4

**Description:**
> Get information about a process.

Args:
    pid: Process ID

Returns:
    Dictionary with process info (name, cmdline, etc.) or None if not found

**Parameters:**
- `pid`: int

---

### `get_progress_summary(spec_data, node_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:151`
**Complexity:** 8

**Description:**
> Get progress summary for a node.

Args:
    spec_data: JSON spec file data
    node_id: Node to get progress for (default: spec-root)

Returns:
    Dictionary with progress information

**Parameters:**
- `spec_data`: Dict
- `node_id`: str

---

### `get_project_context(directory) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:183`
**Complexity:** 2

**Description:**
> Get context about the project for planning.

Args:
    directory: Project directory

Returns:
    Context dictionary with project info

**Parameters:**
- `directory`: Path

---

### `get_quick_routing(failure_type, available_tools) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:211`
**Complexity:** 7

**Description:**
> Get quick tool routing suggestion for a failure type.

Args:
    failure_type: Type of test failure (assertion, exception, etc.)
    available_tools: List of available tools (auto-detected if None)

Returns:
    Routing suggestion string

**Parameters:**
- `failure_type`: str
- `available_tools`: Optional[List[str]]

---

### `get_routing_suggestions(available_tools) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:152`
⚠️ **Complexity:** 14 (High)

**Description:**
> Provide routing suggestions based on available tools.

Args:
    available_tools: List of tool names that are available

Returns:
    List of suggestion strings

**Parameters:**
- `available_tools`: List[str]

---

### `get_session_info(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py:274`
**Complexity:** 6

**Description:**
> Get session state information as JSON.

**Parameters:**
- `project_root`: None

---

### `get_session_state(specs_dir) -> dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/integrations.py:391`
⚠️ **Complexity:** 11 (High)

**Description:**
> Get current session state for enhanced resumption.

Args:
    specs_dir: Path to specs directory (auto-detected if None)

Returns:
    dict: {
        "active_specs": list[dict],  # Active spec summaries
        "last_task": dict | None,    # Most recently modified task
        "timestamp": str,            # Last activity timestamp (ISO8601)
        "in_progress_count": int     # Number of in_progress tasks
    }

Example:
    >>> state = get_session_state()
    >>> if state["last_task"]:
    ...     spec_id = state["last_task"]["spec_id"]
    ...     task_id = state["last_task"]["task_id"]
    ...     print(f"Resume work on {spec_id}:{task_id}?")

**Parameters:**
- `specs_dir`: Optional[str]

---

### `get_spec_statistics(spec_file, json_spec_file) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec_analysis.py:19`
**Complexity:** 9

**Description:**
> Get comprehensive statistics about a spec file.

Analyzes the spec document and extracts:
- File size and line count
- Task/phase/verification counts
- Frontmatter metadata
- JSON spec file info (if available)

Args:
    spec_file: Path to spec markdown file
    json_spec_file: Optional path to JSON spec (auto-detected if not provided)

Returns:
    Dictionary with spec statistics and metrics

Example:
    >>> stats = get_spec_statistics(Path("specs/active/my-spec.md"))
    >>> print(f"Tasks: {stats['task_count']}, Phases: {stats['phase_count']}")

**Parameters:**
- `spec_file`: Path
- `json_spec_file`: Optional[Path]

---

### `get_stance_instruction(stance) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/prompts.py:307`
**Complexity:** 3

**Description:**
> Get stance-specific instruction for a model.

Args:
    stance: for, against, or neutral

Returns:
    Stance instruction string

**Parameters:**
- `stance`: str

---

### `get_status_report(spec_id, specs_dir, printer) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/validation.py:74`
**Complexity:** 9

**Description:**
> Generate comprehensive status report.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    printer: Optional printer for output

Returns:
    Dictionary with status information, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `get_summary_stats(test_files, conftest_files) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:225`
**Complexity:** 3

**Description:**
> Get summary statistics for all test files.

Args:
    test_files: List of test file paths
    conftest_files: List of conftest file paths

Returns:
    Dictionary with summary statistics

**Parameters:**
- `test_files`: List[Path]
- `conftest_files`: List[Path]

---

### `get_task(spec_id, task_id, specs_dir, printer, include_journal) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:120`
⚠️ **Complexity:** 19 (High)

**Description:**
> Get detailed information about a specific task.

Args:
    spec_id: Specification ID
    task_id: Task ID to retrieve
    specs_dir: Path to specs directory
    printer: Optional printer for output
    include_journal: If True, include journal entries for this task

Returns:
    Task data dictionary, or None if not found

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]
- `include_journal`: bool

---

### `get_task_context(task_description, docs_path) -> Dict[str, any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:314`
**Complexity:** 1

**Description:**
> Get context for a task (convenience function).

Args:
    task_description: Description of the task
    docs_path: Optional path to documentation

Returns:
    Dict with task context

**Parameters:**
- `task_description`: str
- `docs_path`: Optional[str]

---

### `get_task_context_from_docs(task_description, project_root) -> Optional[dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/doc_helper.py:104`
**Complexity:** 6

**Description:**
> Get task-relevant context from codebase documentation.

Args:
    task_description: Description of the task to find context for
    project_root: Root directory of the project (default: current dir)

Returns:
    dict | None: {
        "files": list[str],          # Suggested relevant files
        "dependencies": list[str],   # Related dependencies
        "similar": list[str],        # Similar implementations
        "complexity": dict           # Complexity insights
    } or None if unavailable

Example:
    >>> context = get_task_context_from_docs("implement JWT auth")
    >>> if context:
    ...     print(f"Check these files: {context['files']}")

**Parameters:**
- `task_description`: str
- `project_root`: str

---

### `get_task_counts_by_status(spec_data) -> Dict[str, int]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:252`
**Complexity:** 5

**Description:**
> Count tasks by their status.

Args:
    spec_data: JSON spec file data

Returns:
    Dictionary mapping status to count

**Parameters:**
- `spec_data`: Dict

---

### `get_task_info(spec_data, task_id) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:159`
**Complexity:** 1

**Description:**
> Get detailed information about a task.

Args:
    spec_data: JSON spec file data
    task_id: Task identifier

Returns:
    Task data dictionary or None

**Parameters:**
- `spec_data`: Dict
- `task_id`: str

---

### `get_task_journal(spec_id, task_id, specs_dir, printer) -> Optional[List[Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:520`
**Complexity:** 1

**Description:**
> Get journal entries specifically for a task.

This is a convenience wrapper around get_journal_entries.

Args:
    spec_id: Specification ID
    task_id: Task ID
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    List of journal entry dictionaries for the task, or None on error

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `get_template(template_id) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/templates.py:63`
**Complexity:** 1

**Description:**
> Get a specific template by ID.

Args:
    template_id: Template identifier (simple, medium, complex, security)

Returns:
    Template dictionary or None if not found

**Parameters:**
- `template_id`: str

---

### `get_template_description(template_id) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/templates.py:168`
**Complexity:** 3

**Description:**
> Get a human-readable description of a template.

Args:
    template_id: Template identifier

Returns:
    Formatted description string

**Parameters:**
- `template_id`: str

---

### `get_test_context(module_path, docs_path) -> Dict[str, any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:359`
**Complexity:** 1

**Description:**
> Get test context for a module (convenience function).

Args:
    module_path: Path to the module
    docs_path: Optional path to documentation

Returns:
    Dict with test context

**Parameters:**
- `module_path`: str
- `docs_path`: Optional[str]

---

### `get_tool_status_dict() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:303`
**Complexity:** 1

**Description:**
> Get tool status as a dictionary (for JSON output).

Returns:
    Dict with 'available' and 'missing' keys

---

### `has_dependency_cycle(graph, node) -> Tuple[bool, Optional[List[str]]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:191`
**Complexity:** 6

**Description:**
> Check if a specific node is part of a circular dependency.

Args:
    graph: Dependency graph mapping node IDs to their dependencies
    node: Node ID to check

Returns:
    Tuple of (has_cycle: bool, cycle_path: List[str] or None)

Example:
    >>> graph = {"task-1": ["task-2"], "task-2": ["task-1"]}
    >>> has_cycle, path = has_dependency_cycle(graph, "task-1")
    >>> print(has_cycle)  # True
    >>> print(path)  # ["task-1", "task-2", "task-1"]

**Parameters:**
- `graph`: Dict[str, List[str]]
- `node`: str

---

### `has_sdd_command() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:19`
**Complexity:** 1

**Description:**
> Check if sdd command is available on PATH.

---

### `identify_hot_spots(nodes) -> List[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:177`
⚠️ **Complexity:** 12 (High)

**Description:**
> Identify complexity hot spots in the call chain.

Hot spots are functions that exhibit concerning characteristics:
- High cyclomatic complexity (> 10)
- High fan-out (many direct calls, > 5)
- Both high complexity AND high fan-out (critical)

Args:
    nodes: Dictionary of function nodes with complexity and calls_count

Returns:
    List of hot spot dictionaries with:
    - function: Function name
    - reason: Why it's flagged
    - severity: 'high', 'medium', or 'low'
    - complexity: Complexity score
    - fan_out: Number of direct calls

**Parameters:**
- `nodes`: Dict[str, Dict[str, Any]]

---

### `identify_key_files(modules, project_root) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:183`
⚠️ **Complexity:** 15 (High)

**Description:**
> Identify key files that should be read for understanding the codebase.

Args:
    modules: List of module information
    project_root: Project root directory (optional)

Returns:
    List of file paths (relative) in suggested reading order

**Parameters:**
- `modules`: List[Dict[str, Any]]
- `project_root`: Path

---

### `identify_layers(nodes) -> Dict[str, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:123`
**Complexity:** 8

**Description:**
> Identify architectural layer for each function based on file path patterns.

Uses heuristic matching on file paths to classify functions into
architectural layers (Presentation, Business Logic, Data, Utility, Core).

Args:
    nodes: Dictionary of function nodes with 'file' attribute

Returns:
    Dictionary mapping function name to layer name

Layer Classification Rules:
    - Presentation: routes/, cli/, api/, handlers/, controllers/
    - Business Logic: services/, business/, workflows/, processors/
    - Data: models/, database/, repositories/, dao/, persistence/
    - Utility: utils/, helpers/, common/, lib/
    - Core: Everything else

**Parameters:**
- `nodes`: Dict[str, Dict[str, Any]]

---

### `identify_major_refactors(candidates) -> List[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:201`
**Complexity:** 4

**Description:**
> Identify major refactoring candidates.

Major refactors are functions with high complexity AND high dependent count,
meaning they require careful planning and coordination.

Criteria: complexity > 20 AND dependents > 10

Args:
    candidates: List of candidate dictionaries

Returns:
    Subset of candidates that are major refactors

**Parameters:**
- `candidates`: List[Dict[str, Any]]

---

### `identify_quick_wins(candidates) -> List[Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py:174`
**Complexity:** 4

**Description:**
> Identify quick win refactoring candidates.

Quick wins are functions with high complexity but low dependent count,
meaning they're isolated complexity that's safe to refactor.

Criteria: complexity > 15 AND dependents <= 3

Args:
    candidates: List of candidate dictionaries

Returns:
    Subset of candidates that are quick wins

**Parameters:**
- `candidates`: List[Dict[str, Any]]

---

### `infer_task_category(task_title, task_type) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/templates.py:198`
**Complexity:** 7

**Description:**
> Infer task_category based on keywords in the task title.

Analyzes the task title for category-specific keywords and returns
the most likely task category. Defaults to 'implementation' when
keywords are ambiguous or absent.

The function checks keywords in priority order:
1. investigation - exploring/analyzing existing code
2. refactoring - improving code structure
3. decision - architectural/design choices
4. research - gathering external information
5. implementation - creating new functionality (default)

Args:
    task_title: The task title to analyze
    task_type: Type of node (task, subtask, verify, etc.) - currently unused
               but reserved for future enhancements

Returns:
    One of: 'investigation', 'implementation', 'refactoring', 'decision', 'research'

Examples:
    >>> infer_task_category("Analyze current authentication flow")
    'investigation'

    >>> infer_task_category("Create user service")
    'implementation'

    >>> infer_task_category("Extract validation to utility")
    'refactoring'

    >>> infer_task_category("Choose between JWT vs sessions")
    'decision'

    >>> infer_task_category("Research OAuth 2.0 best practices")
    'research'

    >>> infer_task_category("")
    'implementation'

**Parameters:**
- `task_title`: str
- `task_type`: str

---

### `init_environment(spec_path) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/workflow.py:15`
**Complexity:** 3

**Description:**
> Initialize development environment with complete setup.

Args:
    spec_path: Optional path to spec file or directory

Returns:
    Dictionary with environment paths and validation status

**Parameters:**
- `spec_path`: Optional[str]

---

### `invalid_state_structure(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:747`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with nodes missing required fields.

**Parameters:**
- `specs_structure`: None

---

### `is_clear_command(entry) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/parser.py:25`
**Complexity:** 7

**Description:**
> Check if a transcript entry is a /clear command.

The /clear command resets the conversation context, so we should
reset token counters when we encounter it.

Args:
    entry: A parsed JSONL entry from the transcript

Returns:
    True if this entry represents a /clear command

**Parameters:**
- `entry`: dict

---

### `is_file_open_for_writing(filepath) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:23`
⚠️ **Complexity:** 11 (High)

**Description:**
> Check if a file is currently open for writing by any process.

Uses platform-specific tools:
- Linux/macOS: lsof
- Windows: fallback to modification time check

Returns:
    True if file is open for writing, False otherwise

**Parameters:**
- `filepath`: None

---

### `is_in_current_phase(spec_data, task_id, phase_id) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:74`
**Complexity:** 5

**Description:**
> Check if task belongs to current phase (including nested groups).

Args:
    spec_data: JSON spec file data
    task_id: Task identifier
    phase_id: Phase identifier to check against

Returns:
    True if task is within the phase hierarchy

**Parameters:**
- `spec_data`: Dict
- `task_id`: str
- `phase_id`: str

---

### `is_metrics_enabled() -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:218`
**Complexity:** 1

**Description:**
> Check if metrics collection is enabled (not in test environment).

---

### `is_pid_alive(pid) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/process_utils.py:140`
**Complexity:** 6

**Description:**
> Check if a process with the given PID is currently running.

Args:
    pid: Process ID to check

Returns:
    True if process exists, False otherwise

**Parameters:**
- `pid`: int

---

### `is_task_complete(task_node) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:166`
**Complexity:** 2

**Description:**
> Check if a single task is marked complete.

A task is considered complete if its status is explicitly set to "completed".
Tasks with status "in_progress", "pending", "blocked", or any other value
are not considered complete.

Args:
    task_node: Task node dictionary from hierarchy

Returns:
    True if task status is "completed", False otherwise

**Parameters:**
- `task_node`: Dict

---

### `is_unblocked(spec_data, task_id, task_data) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:19`
⚠️ **Complexity:** 13 (High)

**Description:**
> Check if all blocking dependencies are completed.

This checks both task-level dependencies and phase-level dependencies.
A task is blocked if:
1. Any of its direct task dependencies are not completed, OR
2. Its parent phase is blocked by an incomplete phase

Args:
    spec_data: JSON spec file data
    task_id: Task identifier
    task_data: Task data dictionary

Returns:
    True if task has no blockers or all blockers are completed

**Parameters:**
- `spec_data`: Dict
- `task_id`: str
- `task_data`: Dict

---

### `list_blockers(spec_id, specs_dir, printer) -> Optional[List[Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:373`
⚠️ **Complexity:** 11 (High)

**Description:**
> List all currently blocked tasks with their blocker details.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    List of blocked task dictionaries, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `list_phases(spec_data) -> List[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:215`
**Complexity:** 4

**Description:**
> List all phases with their status and progress.

Args:
    spec_data: JSON spec file data

Returns:
    List of phase dictionaries

**Parameters:**
- `spec_data`: Dict

---

### `list_phases(spec_id, specs_dir, printer) -> Optional[List[Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:215`
**Complexity:** 6

**Description:**
> List all phases with their progress.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    List of phase dictionaries, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `list_presets(printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:231`
**Complexity:** 3

**Description:**
> Display all available presets.

Args:
    printer: PrettyPrinter instance (creates default if None)

**Parameters:**
- `printer`: Optional[PrettyPrinter]

---

### `list_templates() -> Dict[str, Dict[str, Any]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/templates.py:53`
**Complexity:** 1

**Description:**
> Get all available templates.

Returns:
    Dictionary of template_id -> template_info

---

### `load_consensus_config() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:116`
**Complexity:** 5

**Description:**
> Load consensus configuration from config.yaml.

Returns:
    Dict with consensus configuration (pairs and auto_trigger)

---

### `load_consensus_config() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:333`
**Complexity:** 5

**Description:**
> Load consensus configuration from config.yaml.

Returns:
    Dict with consensus configuration

---

### `load_documentation(docs_path) -> DocumentationQuery`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/doc_query_lib.py:1711`
**Complexity:** 1

**Description:**
> Convenience function to load documentation.

Args:
    docs_path: Path to docs directory or documentation.json

Returns:
    Loaded DocumentationQuery object

**Parameters:**
- `docs_path`: Optional[str]

---

### `load_json_spec(spec_id, specs_dir) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:156`
**Complexity:** 4

**Description:**
> Load the JSON spec file for a given spec ID.

Searches for the spec file in active/, completed/, and archived/ directories.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory

Returns:
    Spec data dictionary, or None if not found

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path

---

### `load_model_config() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:24`
**Complexity:** 5

**Description:**
> Load model configuration from config.yaml.

Returns fallback to DEFAULT_MODELS if config not found or invalid.

Returns:
    Dict with model configuration including priorities and overrides

---

### `load_tool_config() -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:49`
**Complexity:** 7

**Description:**
> Load tool configuration from config.yaml with fallback to defaults.

Returns:
    Dict with tool configuration

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/__init__.py:123`
⚠️ **Complexity:** 13 (High)

**Decorators:** `@track_metrics('sdd')`

**Description:**
> Main entry point for unified SDD CLI.

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:383`
**Complexity:** 7

**Description:**
> Main CLI entry point.

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/generate_docs.py:316`
**Complexity:** 3

**Description:**
> Main entry point for the documentation generator.

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py:327`
**Complexity:** 5

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/setup_project_permissions.py:159`
**Complexity:** 3

---

### `main() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:389`
⚠️ **Complexity:** 17 (High)

**Description:**
> Main CLI entry point for sdd-integration commands.

---

### `mark_task_blocked(spec_id, task_id, reason, specs_dir, blocker_type, ticket, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/status.py:300`
**Complexity:** 10

**Description:**
> Mark a task as blocked with detailed blocker information.

Args:
    spec_id: Specification ID
    task_id: Task identifier
    reason: Description of why task is blocked
    specs_dir: Path to specs/active directory
    blocker_type: Type of blocker (dependency, technical, resource, decision)
    ticket: Optional ticket/issue reference
    dry_run: If True, don't save changes
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `reason`: str
- `specs_dir`: Path
- `blocker_type`: str
- `ticket`: Optional[str]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `mark_task_journaled(spec_id, task_id, specs_dir, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:24`
**Complexity:** 9

**Description:**
> Mark a task as journaled by clearing the needs_journaling flag.

Called automatically when add_journal_entry() includes a task_id.

Args:
    spec_id: Specification ID
    task_id: Task identifier
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `minimal_specs_dir(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:343`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a minimal specs directory structure for testing.

**Parameters:**
- `tmp_path`: None

---

### `mock_printer(mocker) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:995`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Mock PrettyPrinter for testing output.

**Parameters:**
- `mocker`: None

---

### `mock_subprocess_run(monkeypatch) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:214`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Mock subprocess.run for AI tool testing.

**Parameters:**
- `monkeypatch`: None

---

### `mock_subprocess_run_failure(monkeypatch) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:230`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Mock subprocess.run returning failure.

**Parameters:**
- `monkeypatch`: None

---

### `move_spec(spec_file, target_folder, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/lifecycle.py:22`
**Complexity:** 8

**Description:**
> Move a spec file between lifecycle folders.

Args:
    spec_file: Path to current spec file
    target_folder: Target folder name (active, completed, archived)
    dry_run: If True, show move without executing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_file`: Path
- `target_folder`: str
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `normalize_message_text(raw) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:226`
**Complexity:** 9

**Description:**
> Strip glyphs/severity prefixes from validation messages for consistent comparison.

**Parameters:**
- `raw`: str

---

### `normalize_path(path, base_directory) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:216`
**Complexity:** 3

**Description:**
> Normalize a single path (absolute or relative).

Args:
    path: Path string to normalize
    base_directory: Base directory for relative paths (defaults to cwd)

Returns:
    Normalized absolute Path object

Example:
    >>> normalized = normalize_path("../specs/active/my-spec.md")
    >>> print(normalized)  # /Users/user/project/specs/active/my-spec.md

**Parameters:**
- `path`: str
- `base_directory`: Optional[Path]

---

### `normalize_validation_result(result) -> NormalizedValidationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/formatting.py:133`
**Complexity:** 3

**Description:**
> Convert a raw validation result into aggregate counts and issue metadata.

**Parameters:**
- `result`: JsonSpecValidationResult

---

### `parse_doc_query_stats(output) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:59`
**Complexity:** 5

**Description:**
> Parse doc-query stats output.

Args:
    output: stdout from doc-query stats

Returns:
    Parsed statistics dictionary

**Parameters:**
- `output`: str

---

### `parse_response(tool_output, tool_name) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/synthesis.py:15`
**Complexity:** 8

**Description:**
> Extract raw response from tool output.

Handles wrapper formats (like gemini CLI) but returns raw markdown/text.
No parsing or structuring - that's done by AI synthesis.

Args:
    tool_output: Raw output from AI tool
    tool_name: Name of the tool for logging

Returns:
    Response dictionary with raw text

**Parameters:**
- `tool_output`: str
- `tool_name`: str

---

### `parse_transcript(transcript_path) -> Optional[TokenMetrics]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/parser.py:56`
**Complexity:** 10

**Description:**
> Parse a Claude Code transcript JSONL file and extract token metrics.

Args:
    transcript_path: Path to the transcript JSONL file

Returns:
    TokenMetrics object with aggregated token data, or None if parsing fails

**Parameters:**
- `transcript_path`: str | Path

---

### `phase_time(spec_id, phase_id, specs_dir, printer) -> Optional[Dict]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/query.py:35`
⚠️ **Complexity:** 14 (High)

**Description:**
> Calculate time spent on a specific phase.

This is a time-tracking specific operation that remains in sdd-update.

Args:
    spec_id: Specification ID
    phase_id: Phase ID to calculate time for
    specs_dir: Path to specs directory
    printer: Optional printer for output

Returns:
    Dictionary with time breakdown, or None on error

**Parameters:**
- `spec_id`: str
- `phase_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `plain_modules() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:149`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample plain Python library (no framework).

---

### `prepare_task(spec_id, specs_dir, task_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/discovery.py:239`
⚠️ **Complexity:** 14 (High)

**Description:**
> Prepare complete context for task implementation.

Combines task discovery, dependency checking, and detail extraction.
Includes automatic spec validation, doc-query context gathering, and
completion detection when no actionable tasks are found.

When no actionable tasks are found, checks if the spec is complete
(all tasks completed) vs. blocked (tasks waiting on dependencies).
Returns completion information for caller to handle.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    task_id: Optional task ID (auto-discovers if not provided)

Returns:
    Complete task preparation data with validation and context.

    When no tasks found:
    - If spec complete: success=True, spec_complete=True, completion_info set
    - If tasks blocked: success=False, spec_complete=False, completion_info set

    Fields:
        success (bool): True if task found or spec complete
        task_id (str|None): Next task ID if found
        task_data (dict|None): Task details if found
        spec_complete (bool): True if all tasks completed
        completion_info (dict|None): Completion check details
        error (str|None): Error message if applicable

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `task_id`: Optional[str]

---

### `print_context(context, verbose) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:296`
⚠️ **Complexity:** 17 (High)

**Parameters:**
- `context`: Dict[str, List[QueryResult]]
- `verbose`: bool

---

### `print_discovery_report(root_dir, show_summary, show_tree, show_fixtures, show_markers, show_detailed, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:303`
⚠️ **Complexity:** 35 (High)

**Description:**
> Print a comprehensive discovery report.

Args:
    root_dir: Root directory to analyze
    show_summary: Show summary statistics only
    show_tree: Show directory tree structure
    show_fixtures: Show all fixtures
    show_markers: Show all markers
    show_detailed: Show detailed analysis of each file
    printer: PrettyPrinter instance (creates default if None)

Returns:
    Exit code (0 for success, 1 for error)

**Parameters:**
- `root_dir`: str
- `show_summary`: bool
- `show_tree`: bool
- `show_fixtures`: bool
- `show_markers`: bool
- `show_detailed`: bool
- `printer`: Optional[PrettyPrinter]

---

### `print_module_summary(summary, verbose) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:357`
⚠️ **Complexity:** 18 (High)

**Parameters:**
- `summary`: Dict[str, Any]
- `verbose`: bool

---

### `print_routing_matrix(printer) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:568`
**Complexity:** 3

**Description:**
> Print the routing matrix showing which tools to use for each failure type.

Args:
    printer: PrettyPrinter instance (creates default if None)

**Parameters:**
- `printer`: Optional[PrettyPrinter]

---

### `print_tool_status(printer, include_routing) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/tool_checking.py:256`
**Complexity:** 6

**Description:**
> Print tool availability status to console.

Args:
    printer: PrettyPrinter instance (creates default if None)
    include_routing: If provided, also show routing for this failure type

Returns:
    Exit code: 0 if any tools available, 1 if none

**Parameters:**
- `printer`: Optional[PrettyPrinter]
- `include_routing`: Optional[str]

---

### `print_tree_structure(structure, indent) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/test_discovery.py:204`
**Complexity:** 4

**Description:**
> Print directory structure as a tree.

Args:
    structure: Directory structure dictionary
    indent: Indentation level

**Parameters:**
- `structure`: Dict
- `indent`: int

---

### `query_tasks(spec_id, specs_dir, status, task_type, parent, format_type, printer, limit) -> Optional[List[Dict]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/query_operations.py:15`
⚠️ **Complexity:** 26 (High)

**Description:**
> Query and filter tasks by various criteria.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    status: Filter by status (pending/in_progress/completed/blocked)
    task_type: Filter by type (task/verify/group/phase)
    parent: Filter by parent node ID
    format_type: Output format (table/json/simple)
    printer: Optional printer for output
    limit: Maximum number of results to return (default 20, use 0 for unlimited)

Returns:
    List of matching task dictionaries, or None on error

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `status`: Optional[str]
- `task_type`: Optional[str]
- `parent`: Optional[str]
- `format_type`: str
- `printer`: Optional[PrettyPrinter]
- `limit`: Optional[int]

---

### `read_code_file(file_path) -> Optional[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:451`
**Complexity:** 7

**Description:**
> Read code from a file path.

Args:
    file_path: Path to the file

Returns:
    File contents, or None if file doesn't exist or can't be read

**Parameters:**
- `file_path`: str

---

### `recalculate_progress(spec_data, node_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:9`
**Complexity:** 5

**Description:**
> Recursively recalculate progress for a node and all its parents.

Modifies spec_data in-place by updating completed_tasks, total_tasks,
and status fields for the node and all ancestors.

Args:
    spec_data: JSON spec file data dictionary
    node_id: Node to start recalculation from (default: spec-root)

Returns:
    The modified spec_data dictionary (for convenience/chaining)

**Parameters:**
- `spec_data`: Dict
- `node_id`: str

---

### `reconcile_state(spec_id, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/validation.py:247`
⚠️ **Complexity:** 15 (High)

**Description:**
> Reconcile JSON spec by fixing inconsistent task statuses.

Finds tasks where metadata.completed_at exists but status != "completed",
and updates their status to match the metadata. This fixes issues where
a task was marked complete but the status wasn't properly updated.

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    dry_run: If True, don't save changes
    printer: Optional printer for output

Returns:
    True if reconciliation successful, False otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `record_metric(skill, command, duration_ms, status, exit_code, error_message) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:74`
**Complexity:** 4

**Description:**
> Record a single metric entry to the JSONL file.

Args:
    skill: Name of the skill (e.g., 'sdd-next', 'doc-query')
    command: Command/subcommand executed (e.g., 'discover', 'search')
    duration_ms: Execution duration in milliseconds
    status: 'success' or 'failure'
    exit_code: Command exit code (0 for success, non-zero for failure)
    error_message: Optional error message if status is 'failure'

**Parameters:**
- `skill`: str
- `command`: str
- `duration_ms`: int
- `status`: str
- `exit_code`: int
- `error_message`: Optional[str]

---

### `register_all_subcommands(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/registry.py:7`
**Complexity:** 2

**Description:**
> Register all subcommands from skill modules.

Uses lazy imports to avoid loading unnecessary modules and handles
optional plugins gracefully (e.g., orchestration during Phase 1).

Args:
    subparsers: ArgumentParser subparsers object
    parent_parser: Parent parser with global options to inherit

Note:
    Handlers will receive printer when invoked, not during registration.
    This allows printer to be configured after parsing global flags.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_all_subcommands(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/registry.py:11`
**Complexity:** 2

**Description:**
> Register all skills-dev subcommands.

Provides development utilities for maintaining the claude_skills package.

**Parameters:**
- `subparsers`: Any
- `parent_parser`: argparse.ArgumentParser

---

### `register_code_doc(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/cli.py:437`
**Complexity:** 1

**Description:**
> Register documentation commands for the unified CLI.

**Parameters:**
- `subparsers`: argparse._SubParsersAction
- `parent_parser`: argparse.ArgumentParser

---

### `register_context(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/context_tracker/cli.py:350`
**Complexity:** 1

**Description:**
> Register 'context' subcommand for unified SDD CLI.

Args:
    subparsers: ArgumentParser subparsers object
    parent_parser: Parent parser with global options

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_doc_query(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/cli.py:987`
**Complexity:** 1

**Description:**
> Register documentation query commands for the unified doc CLI.

**Parameters:**
- `subparsers`: argparse._SubParsersAction
- `parent_parser`: argparse.ArgumentParser

---

### `register_gendocs(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/gendocs.py:39`
**Complexity:** 1

**Description:**
> Register gendocs command.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_migrate(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/migrate.py:71`
**Complexity:** 1

**Description:**
> Register migrate command.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_next(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/cli.py:1066`
**Complexity:** 1

**Description:**
> Register 'next' subcommands for unified CLI.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_plan(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/cli.py:161`
**Complexity:** 1

**Description:**
> Register plan subcommands for unified CLI.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_plan_review(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/cli.py:233`
**Complexity:** 1

**Description:**
> Register plan-review subcommands for unified CLI.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_render(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_render/cli.py:97`
**Complexity:** 1

**Description:**
> Register 'render' command for unified CLI.

Args:
    subparsers: Subparser object from argparse
    parent_parser: Parent parser with global options

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_run_tests(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/cli.py:172`
**Complexity:** 2

**Parameters:**
- `subparsers`: argparse._SubParsersAction
- `parent_parser`: argparse.ArgumentParser

---

### `register_setup_permissions(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/setup_permissions.py:172`
**Complexity:** 1

**Description:**
> Register setup-permissions subcommands.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_start_helper(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py:329`
**Complexity:** 1

**Description:**
> Register start-helper subcommands.

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_update(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/cli.py:796`
**Complexity:** 1

**Description:**
> Register 'update' subcommands for unified CLI.

Args:
    subparsers: The subparsers object to add commands to
    parent_parser: Parent parser with global options (--json, --quiet, --verbose, etc.)

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `register_validate(subparsers, parent_parser) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/cli.py:534`
**Complexity:** 1

**Description:**
> Register 'validate' subcommand for unified CLI.

Args:
    subparsers: ArgumentParser subparsers object
    parent_parser: Parent parser with global options

Note:
    Handlers receive (args, printer) when invoked from main().

**Parameters:**
- `subparsers`: None
- `parent_parser`: None

---

### `render_statistics(stats) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_validate/stats.py:104`
**Complexity:** 6

**Description:**
> Render statistics for display.

**Parameters:**
- `stats`: SpecStatistics

---

### `reorder_args_for_subcommand(cmd_line) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/cli/sdd/__init__.py:15`
⚠️ **Complexity:** 15 (High)

**Description:**
> Reorder command line arguments to support global options anywhere.

Uses argparse.parse_known_args() to robustly extract global options,
then reorders to place them after the subcommand.

Args:
    cmd_line: List of command line arguments

Returns:
    Reordered list of arguments

**Parameters:**
- `cmd_line`: None

---

### `review_with_tools(spec_content, tools, review_type, spec_id, spec_title, parallel) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/reviewer.py:202`
⚠️ **Complexity:** 12 (High)

**Description:**
> Review a spec using multiple AI tools with full synthesis.

Args:
    spec_content: Specification content to review
    tools: List of tool names to use
    review_type: Type of review (quick, full, security, feasibility)
    spec_id: Specification ID
    spec_title: Specification title
    parallel: Run tools in parallel (vs sequential)

Returns:
    Review results with parsed responses and consensus

**Parameters:**
- `spec_content`: str
- `tools`: List[str]
- `review_type`: str
- `spec_id`: str
- `spec_title`: str
- `parallel`: bool

---

### `run_cli() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py:20`
**Complexity:** 6

**Description:**
> Run sdd command with fallback to python -m if sdd not on PATH.

Automatically reorders arguments to put global flags before subcommands.
Global flags: --path, --specs-dir, --quiet, --json, --debug, --verbose, --no-color

---

### `run_cli() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py:20`
**Complexity:** 6

**Description:**
> Run sdd command with fallback to python -m if sdd not on PATH.

Automatically reorders arguments to put global flags before subcommands.
Global flags: --path, --specs-dir, --quiet, --json, --debug, --verbose, --no-color

---

### `run_cli() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py:24`
**Complexity:** 2

**Description:**
> Helper to run sdd CLI with unified command (sdd-validate commands).

---

### `run_cli() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_status_report.py:19`
**Complexity:** 7

**Description:**
> Run sdd command with fallback to python -m if sdd not on PATH.

Automatically reorders arguments to put global flags before subcommands.
Global flags: --path, --specs-dir, --quiet, --json, --debug, --verbose, --no-color

---

### `run_consultation(tool, prompt, dry_run, verbose, printer) -> Tuple[bool, str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/ai_consultation.py:374`
⚠️ **Complexity:** 14 (High)

**Description:**
> Run consultation with an AI tool.

Args:
    tool: Tool name (cursor-agent, gemini, codex)
    prompt: Formatted prompt
    dry_run: If True, show command without running
    verbose: Enable verbose output
    printer: Optional PrettyPrinter for consistent output (falls back to print if None)

Returns:
    Tuple of (success: bool, output: str)

**Parameters:**
- `tool`: str
- `prompt`: str
- `dry_run`: bool
- `verbose`: bool
- `printer`: Optional['PrettyPrinter']

---

### `run_consultation(tool, prompt, dry_run, printer, failure_type) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:489`
⚠️ **Complexity:** 14 (High)

**Description:**
> Run the external tool consultation.

Args:
    tool: Tool name (gemini, codex, cursor-agent)
    prompt: Formatted prompt
    dry_run: If True, just print the command without running
    printer: PrettyPrinter instance (creates default if None)
    failure_type: Optional failure type for model selection

Returns:
    Exit code from the tool

**Parameters:**
- `tool`: str
- `prompt`: str
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]
- `failure_type`: Optional[str]

---

### `run_doc_cli() -> subprocess.CompletedProcess[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_doc_cli.py:14`
**Complexity:** 1

**Description:**
> Run doc CLI via sdd.

---

### `run_pytest(preset, path, pattern, extra_args, printer) -> int`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:168`
**Complexity:** 8

**Description:**
> Run pytest with the specified configuration.

Args:
    preset: Name of the preset to use
    path: Specific test file or directory to run
    pattern: Pattern to match test names (used with -k)
    extra_args: Additional arguments to pass to pytest
    printer: PrettyPrinter instance (creates default if None)

Returns:
    Exit code from pytest

**Parameters:**
- `preset`: Optional[str]
- `path`: Optional[str]
- `pattern`: Optional[str]
- `extra_args`: Optional[List[str]]
- `printer`: Optional[PrettyPrinter]

---

### `run_sdd_command() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:24`
**Complexity:** 2

**Description:**
> Run sdd command with fallback to python -m if sdd not on PATH.

This ensures tests work in different environments.

---

### `run_skills_dev_cli() -> subprocess.CompletedProcess[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_skills_dev_cli.py:15`
**Complexity:** 1

**Description:**
> Run skills-dev CLI via sdd.

---

### `run_test_cli() -> subprocess.CompletedProcess[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_test_cli.py:15`
**Complexity:** 1

**Description:**
> Run test CLI via sdd.

---

### `run_tool_parallel(tool, prompt, failure_type) -> ConsultationResponse`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:688`
**Complexity:** 5

**Description:**
> Run a single tool consultation and capture output.

Args:
    tool: Tool name (gemini, codex, cursor-agent)
    prompt: Formatted prompt
    failure_type: Optional failure type for model selection

Returns:
    ConsultationResponse with results

**Parameters:**
- `tool`: str
- `prompt`: str
- `failure_type`: Optional[str]

---

### `sample_framework_info() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:188`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample framework detection result.

---

### `sample_frontmatter() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:956`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample frontmatter data.

---

### `sample_json_spec_circular_deps(specs_structure, sample_spec_simple) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:499`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with circular dependencies.

**Parameters:**
- `specs_structure`: None
- `sample_spec_simple`: None

---

### `sample_json_spec_completed(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:618`
**Complexity:** 5

**Decorators:** `@pytest.fixture`

**Description:**
> Create a fully completed JSON spec.

**Parameters:**
- `specs_structure`: None

---

### `sample_json_spec_complex(specs_structure, sample_spec_complex) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:455`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a complex JSON spec for the complex spec.

**Parameters:**
- `specs_structure`: None
- `sample_spec_complex`: None

---

### `sample_json_spec_simple(specs_structure, sample_spec_simple) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:435`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a simple JSON spec for testing basic operations.

**Parameters:**
- `specs_structure`: None
- `sample_spec_simple`: None

---

### `sample_json_spec_with_blockers(specs_structure, sample_spec_simple) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:534`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with some blocked tasks.

**Parameters:**
- `specs_structure`: None
- `sample_spec_simple`: None

---

### `sample_json_spec_with_deps(specs_structure, sample_spec_simple) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:471`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with task dependencies.

**Parameters:**
- `specs_structure`: None
- `sample_spec_simple`: None

---

### `sample_json_spec_with_time(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:578`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with time tracking data.

**Parameters:**
- `specs_structure`: None

---

### `sample_layers() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:199`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample layer detection result.

---

### `sample_modules() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:11`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample module data for testing framework and layer detection.

---

### `sample_node_project(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:889`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a sample Node.js project structure.

**Parameters:**
- `tmp_path`: None

---

### `sample_python_project(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:925`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a sample Python project structure.

**Parameters:**
- `tmp_path`: None

---

### `sample_spec_complex(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:355`
**Complexity:** 3

**Decorators:** `@pytest.fixture`

**Description:**
> Create a complex spec file with 3 phases, 3 tasks each.

**Parameters:**
- `specs_structure`: None

---

### `sample_spec_file(minimal_specs_dir) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py:355`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a minimal sample spec file for testing.

**Parameters:**
- `minimal_specs_dir`: None

---

### `sample_spec_invalid(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:415`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create an invalid spec file (missing frontmatter).

**Parameters:**
- `specs_structure`: None

---

### `sample_spec_invalid_frontmatter(create_temp_spec_file) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:1042`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a spec missing required top-level fields.

**Parameters:**
- `create_temp_spec_file`: None

---

### `sample_spec_invalid_phases(create_temp_spec_file) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:1054`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a spec with invalid phase structure.

**Parameters:**
- `create_temp_spec_file`: None

---

### `sample_spec_simple(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:342`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a simple spec file with 2 phases, 2 tasks each.

**Parameters:**
- `specs_structure`: None

---

### `sample_statistics() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:174`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample code statistics.

---

### `sample_task_data() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:969`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Sample task data.

---

### `save_json_spec(spec_id, specs_dir, spec_data, backup, validate) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:187`
**Complexity:** 8

**Description:**
> Save JSON spec file with atomic write and optional backup.

Updates the existing spec file in its current location (active/completed/archived).

Args:
    spec_id: Specification ID
    specs_dir: Path to specs directory
    spec_data: Spec data to write
    backup: Create backup before writing (default: True)
    validate: Validate JSON before writing (default: True)

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `spec_data`: Dict
- `backup`: bool
- `validate`: bool

---

### `should_auto_trigger_consensus(failure_type) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:143`
**Complexity:** 5

**Description:**
> Check if a failure type should automatically trigger multi-agent consensus.

Checks in order:
1. Explicit entry for failure_type
2. Default setting for undefined types
3. Fallback to False (single-agent)

Args:
    failure_type: Type of test failure

Returns:
    True if consensus should be auto-triggered, False otherwise

**Parameters:**
- `failure_type`: str

---

### `should_generate_docs(project_root, interactive) -> dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/doc_helper.py:161`
**Complexity:** 3

**Description:**
> Check if documentation should be generated.

Args:
    project_root: Root directory of the project
    interactive: If True, may prompt user for decision

Returns:
    dict: {
        "should_generate": bool,     # Recommendation
        "reason": str,               # Explanation
        "available": bool,           # Current doc availability
        "user_confirmed": bool | None # User response (if interactive)
    }

Example:
    >>> result = should_generate_docs()
    >>> if result["should_generate"] and result["user_confirmed"]:
    ...     # Run code-doc skill
    ...     print("Generating documentation...")

**Parameters:**
- `project_root`: str
- `interactive`: bool

---

### `should_prompt_completion(spec_data, phase_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/completion.py:186`
**Complexity:** 4

**Description:**
> Determine if completion prompt should be shown to user.

A completion prompt should only be shown if the spec/phase is fully
complete AND there are no blocked tasks. Blocked tasks indicate
unresolved dependencies or issues that prevent true completion.

This function prevents premature completion by checking both:
1. All tasks are completed (via check_spec_completion)
2. No tasks are currently blocked (blocked = incomplete dependencies)

Args:
    spec_data: JSON spec file data containing hierarchy and task information
    phase_id: Optional phase ID to check specific phase completion.
             If None, checks entire spec.

Returns:
    Dictionary with prompt decision and reasoning:
    {
        "should_prompt": bool,        # True if should show completion prompt
        "reason": str,                 # Explanation for the decision
        "is_complete": bool,           # Whether all tasks are complete
        "blocked_count": int,          # Number of blocked tasks
        "blocked_tasks": List[str],    # IDs of blocked tasks
        "node_id": str,                # Node that was checked
        "error": Optional[str]         # Error if check failed
    }

Example:
    >>> from claude_skills.common.spec import load_spec
    >>> from claude_skills.common.completion import should_prompt_completion
    >>>
    >>> spec_data = load_spec("specs/active/my-spec.json")
    >>> result = should_prompt_completion(spec_data)
    >>>
    >>> if result["should_prompt"]:
    ...     print("Ready to mark spec as complete!")
    ...     print(result["reason"])
    ... else:
    ...     print(f"Not ready: {result['reason']}")
    ...     if result["blocked_tasks"]:
    ...         print(f"Blocked tasks: {result['blocked_tasks']}")

**Parameters:**
- `spec_data`: Dict
- `phase_id`: Optional[str]

---

### `spec_stats(spec_file, json_spec_file) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/validation.py:58`
⚠️ **Complexity:** 15 (High)

**Description:**
> Return statistics and metadata about a JSON spec file.

**Parameters:**
- `spec_file`: Path
- `json_spec_file`: Optional[Path]

---

### `spec_with_all_categories() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:27`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a test spec with all five task_category types.

---

### `spec_with_issues() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:19`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a test spec with various fixable issues.

---

### `spec_with_mixed_categories() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:184`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a test spec with mix of categorized and uncategorized tasks.

---

### `spec_with_placeholder_paths() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:257`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create spec with placeholder file_path values that need migration.

---

### `spec_without_categories() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:126`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a test spec in old format (no task_category field).

---

### `specs_structure(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:311`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a complete specs directory structure.

Structure:
    tmp_path/
    └── specs/
        ├── active/      (JSON spec files)
        ├── completed/   (completed specs)
        └── archived/    (archived specs)

Returns:
    Path to the specs directory (containing active/completed/archived subdirectories)

**Parameters:**
- `tmp_path`: None

---

### `state_with_circular_deps_plan(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:797`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with circular dependencies.

**Parameters:**
- `specs_structure`: None

---

### `state_with_orphaned_nodes(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:675`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a JSON spec with orphaned nodes (missing parents/invalid dependencies).

**Parameters:**
- `specs_structure`: None

---

### `suggest_documentation_generation(directory) -> str`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan/planner.py:161`
**Complexity:** 1

**Description:**
> Suggest generating documentation if not available.

Args:
    directory: Project directory

Returns:
    Suggestion message

**Parameters:**
- `directory`: Path

---

### `suggest_files_for_task(task_description, docs_path) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/sdd_integration.py:329`
**Complexity:** 1

**Description:**
> Suggest files for a task (convenience function).

Args:
    task_description: Description of the task
    docs_path: Optional path to documentation

Returns:
    List of suggested file paths

**Parameters:**
- `task_description`: str
- `docs_path`: Optional[str]

---

### `suggest_reading_order(key_files, framework_info) -> List[str]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/code_doc/detectors.py:310`
**Complexity:** 7

**Description:**
> Suggest optimal reading order for key files.

Args:
    key_files: List of identified key files
    framework_info: Framework detection result

Returns:
    Ordered list of files to read

**Parameters:**
- `key_files`: List[str]
- `framework_info`: Dict[str, Any]

---

### `sync_metadata_from_state(spec_id, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:537`
⚠️ **Complexity:** 21 (High)

**Description:**
> Automatically synchronize JSON metadata with hierarchy data.

Updates:
- last_updated: Current timestamp
- progress_percentage: Calculated from hierarchy
- status: "completed" when all tasks done, otherwise "active"
- current_phase: ID of first in-progress phase

Args:
    spec_id: Specification ID
    specs_dir: Optional specs directory (auto-detected if not provided)
    dry_run: If True, show changes without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `specs_dir`: Optional[Path]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `synthesize_responses(responses) -> Dict[str, any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/consultation.py:811`
**Complexity:** 6

**Description:**
> Synthesize multiple consultation responses into unified insights.

Args:
    responses: List of ConsultationResponse objects

Returns:
    Dictionary with synthesis including consensus, unique insights, etc.

**Parameters:**
- `responses`: List[ConsultationResponse]

---

### `synthesize_with_ai(responses, spec_id, spec_title, working_dir) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_plan_review/synthesis.py:61`
⚠️ **Complexity:** 11 (High)

**Description:**
> Use AI to synthesize multiple model reviews into consensus.

Instead of fragile regex parsing, let AI read natural language reviews
and create structured synthesis.

Args:
    responses: List of response dicts with "tool" and "raw_review" keys
    spec_id: Specification ID
    spec_title: Specification title
    working_dir: Working directory for AI tool

Returns:
    Synthesized consensus dictionary

**Parameters:**
- `responses`: List[Dict[str, Any]]
- `spec_id`: str
- `spec_title`: str
- `working_dir`: str

---

### `temp_dir(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:304`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Provide a temporary directory that's cleaned up after test.

**Parameters:**
- `tmp_path`: None

---

### `temp_project_dir(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py:246`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a temporary project directory with README.

**Parameters:**
- `tmp_path`: None

---

### `test_apply_fix_actions_dry_run() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:374`
**Complexity:** 1

**Description:**
> Test applying actions in dry-run mode.

---

### `test_apply_fix_actions_handles_errors() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:450`
**Complexity:** 1

**Description:**
> Test that apply_fix_actions handles errors gracefully.

---

### `test_apply_fix_actions_real_apply(mock_backup, mock_save, mock_validate, mock_recalc) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:401`
**Complexity:** 1

**Decorators:** `@patch('claude_skills.sdd_validate.fix.recalculate_progress')`, `@patch('claude_skills.sdd_validate.fix.validate_spec_hierarchy')`, `@patch('claude_skills.sdd_validate.fix.save_json_spec')`, `@patch('claude_skills.sdd_validate.fix.backup_json_spec')`

**Description:**
> Test actually applying fix actions.

**Parameters:**
- `mock_backup`: None
- `mock_save`: None
- `mock_validate`: None
- `mock_recalc`: None

---

### `test_apply_fix_actions_with_diff(spec_with_issues, tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:88`
**Complexity:** 1

**Description:**
> Test apply_fix_actions with diff capture.

**Parameters:**
- `spec_with_issues`: None
- `tmp_path`: None

---

### `test_apply_pattern_filter_custom_key_exact_match() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:827`
**Complexity:** 1

**Description:**
> Test custom key function with exact matching.

---

### `test_apply_pattern_filter_custom_key_function() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:805`
**Complexity:** 1

**Description:**
> Test custom key function for nested fields.

---

### `test_apply_pattern_filter_empty_items() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:798`
**Complexity:** 1

**Description:**
> Test with empty items list.

---

### `test_apply_pattern_filter_empty_string_values() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:861`
**Complexity:** 1

**Description:**
> Test that empty string values are skipped.

---

### `test_apply_pattern_filter_exact_match() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:716`
**Complexity:** 1

**Description:**
> Test exact name matching.

---

### `test_apply_pattern_filter_exact_match_no_results() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:730`
**Complexity:** 1

**Description:**
> Test exact match returns empty list when no match found.

---

### `test_apply_pattern_filter_invalid_regex() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:788`
**Complexity:** 1

**Description:**
> Test that invalid regex raises re.error.

---

### `test_apply_pattern_filter_key_func_exception() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:889`
**Complexity:** 1

**Description:**
> Test that exceptions in key_func are handled gracefully.

---

### `test_apply_pattern_filter_missing_key() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:846`
**Complexity:** 1

**Description:**
> Test graceful handling when key is missing from some items.

---

### `test_apply_pattern_filter_multiple_matches() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:923`
**Complexity:** 1

**Description:**
> Test pattern that matches multiple items.

---

### `test_apply_pattern_filter_preserves_item_structure() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:910`
**Complexity:** 1

**Description:**
> Test that filtered items maintain their full structure.

---

### `test_apply_pattern_filter_regex_case_insensitive() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:756`
**Complexity:** 1

**Description:**
> Test that regex pattern matching is case-insensitive.

---

### `test_apply_pattern_filter_regex_complex_pattern() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:770`
**Complexity:** 1

**Description:**
> Test regex with more complex pattern.

---

### `test_apply_pattern_filter_regex_empty_string() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:875`
**Complexity:** 1

**Description:**
> Test regex pattern with empty string values.

---

### `test_apply_pattern_filter_regex_pattern() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:739`
**Complexity:** 1

**Description:**
> Test regex pattern matching (case-insensitive).

---

### `test_backward_compatibility_no_breaking_changes(spec_without_categories) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:508`
**Complexity:** 2

**Description:**
> Test that existing workflows work unchanged with old-format specs.

**Parameters:**
- `spec_without_categories`: None

---

### `test_build_call_graph_both_directions(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:440`
**Complexity:** 1

**Description:**
> Test build_call_graph() with direction='both'.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_callees_only(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:360`
**Complexity:** 1

**Description:**
> Test build_call_graph() with direction='callees'.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_callers_only(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:400`
**Complexity:** 1

**Description:**
> Test build_call_graph() with direction='callers'.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_depth_values(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:665`
**Complexity:** 1

**Description:**
> Test build_call_graph() assigns correct depth values.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_function_not_found(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:561`
**Complexity:** 1

**Description:**
> Test build_call_graph() with non-existent function.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_handles_cycles(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:521`
**Complexity:** 1

**Description:**
> Test build_call_graph() handles circular dependencies.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_include_metadata(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:599`
**Complexity:** 1

**Description:**
> Test build_call_graph() includes metadata when requested.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_invalid_direction(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:702`
**Complexity:** 1

**Description:**
> Test build_call_graph() raises error for invalid direction.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_isolated_function(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:577`
**Complexity:** 1

**Description:**
> Test build_call_graph() with function that has no callers or callees.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_max_depth(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:474`
**Complexity:** 1

**Description:**
> Test build_call_graph() respects max_depth.

**Parameters:**
- `tmp_path`: None

---

### `test_build_call_graph_without_metadata(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:634`
**Complexity:** 1

**Description:**
> Test build_call_graph() excludes metadata when not requested.

**Parameters:**
- `tmp_path`: None

---

### `test_build_counts_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:65`
**Complexity:** 1

**Description:**
> Test building counts fix action.

---

### `test_build_date_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:282`
**Complexity:** 1

**Description:**
> Test building date normalization action.

---

### `test_build_hierarchy_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:246`
**Complexity:** 1

**Description:**
> Test building hierarchy fix action.

---

### `test_build_metadata_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:91`
**Complexity:** 1

**Description:**
> Test building metadata fix action.

---

### `test_build_metadata_action_verify() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:123`
**Complexity:** 1

**Description:**
> Test building metadata fix action for verification nodes.

---

### `test_build_placeholder_file_path_action_all_placeholders() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:667`
**Complexity:** 2

**Description:**
> Test detection of all placeholder patterns.

---

### `test_build_placeholder_file_path_action_case_insensitive() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:620`
**Complexity:** 2

**Description:**
> Test that placeholder detection is case-insensitive.

---

### `test_build_placeholder_file_path_action_category_mapping() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:986`
**Complexity:** 2

**Description:**
> Test that category-name placeholders map directly to their category.

---

### `test_build_placeholder_file_path_action_category_name() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:522`
**Complexity:** 1

**Description:**
> Test detecting file_path with category name as placeholder.

---

### `test_build_placeholder_file_path_action_generic_placeholder_uses_title() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:1041`
**Complexity:** 1

**Description:**
> Test that generic placeholders (n/a, none, null) use title-based inference.

---

### `test_build_placeholder_file_path_action_no_file_path() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:743`
**Complexity:** 1

**Description:**
> Test that nodes without file_path are skipped.

---

### `test_build_placeholder_file_path_action_non_placeholder() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:707`
**Complexity:** 2

**Description:**
> Test that real file paths are not detected as placeholders.

---

### `test_build_placeholder_file_path_action_non_task_node() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:815`
**Complexity:** 2

**Description:**
> Test that placeholder detection only applies to task/subtask nodes.

---

### `test_build_placeholder_file_path_action_preserves_existing_category() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:845`
**Complexity:** 1

**Description:**
> Test that existing task_category is not overwritten.

---

### `test_build_placeholder_file_path_action_preview_shows_category() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:1087`
**Complexity:** 2

**Description:**
> Test that the preview message shows the inferred category.

---

### `test_build_placeholder_file_path_action_subtask() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:770`
**Complexity:** 1

**Description:**
> Test that placeholder detection works for subtasks.

---

### `test_build_placeholder_file_path_action_tbd() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:571`
**Complexity:** 1

**Description:**
> Test detecting file_path with TBD placeholder.

TBD (To Be Determined) maps to 'decision' category because it indicates
a decision needs to be made about what to implement.

---

### `test_build_placeholder_file_path_action_tbd_maps_to_decision() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:941`
**Complexity:** 1

**Description:**
> Test that 'tbd' placeholder maps to 'decision' category.

---

### `test_build_placeholder_file_path_action_whitespace() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:897`
**Complexity:** 1

**Description:**
> Test that placeholders with whitespace are detected.

---

### `test_build_status_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:309`
**Complexity:** 1

**Description:**
> Test building status normalization action.

---

### `test_build_task_category_action() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:154`
**Complexity:** 1

**Description:**
> Test building task_category fix action for implementation task.

---

### `test_build_task_category_action_investigation() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:201`
**Complexity:** 1

**Description:**
> Test building task_category fix action for investigation task.

---

### `test_calculate_statistics_basic() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:12`
**Complexity:** 1

**Description:**
> Test basic statistics calculation.

---

### `test_calculate_statistics_empty_hierarchy() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:104`
**Complexity:** 1

**Description:**
> Test statistics with empty hierarchy.

---

### `test_calculate_statistics_status_counts() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:122`
**Complexity:** 1

**Description:**
> Test status counting.

---

### `test_calculate_statistics_with_verifications() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:66`
**Complexity:** 1

**Description:**
> Test statistics with verification nodes.

---

### `test_case_sensitivity_of_categories() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:613`
**Complexity:** 1

**Description:**
> Test that task_category values are case-sensitive.

---

### `test_collect_fix_actions_deduplicates() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:483`
**Complexity:** 1

**Description:**
> Test that collect_fix_actions doesn't create duplicate actions.

---

### `test_collect_fix_actions_empty() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:26`
**Complexity:** 1

**Description:**
> Test collecting actions from a clean validation result.

---

### `test_collect_fix_actions_finds_multiple_issues(spec_with_issues) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:72`
**Complexity:** 1

**Description:**
> Test that collect_fix_actions finds all auto-fixable issues.

**Parameters:**
- `spec_with_issues`: None

---

### `test_collect_fix_actions_with_enhanced_errors() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:40`
**Complexity:** 1

**Description:**
> Test collecting actions from enhanced errors.

---

### `test_context_for_area_includes_docstrings_and_stats(doc_query_samples) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:52`
**Complexity:** 1

**Parameters:**
- `doc_query_samples`: None

---

### `test_describe_module_returns_summary(doc_query_samples) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:40`
**Complexity:** 1

**Parameters:**
- `doc_query_samples`: None

---

### `test_diff_computation() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:169`
**Complexity:** 1

**Description:**
> Test diff computation with before/after states.

---

### `test_doc_help_lists_key_subcommands() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_doc_cli.py:22`
**Complexity:** 2

---

### `test_doc_requires_subcommand() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_doc_cli.py:37`
**Complexity:** 2

---

### `test_empty_task_category_field() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:569`
**Complexity:** 1

**Description:**
> Test handling of empty/null task_category (should use default inference).

---

### `test_format_validation_summary_basic() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:71`
**Complexity:** 1

**Description:**
> Test basic summary formatting.

---

### `test_format_validation_summary_verbose() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:90`
**Complexity:** 1

**Description:**
> Test verbose summary formatting.

---

### `test_full_workflow_with_categories(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:475`
**Complexity:** 1

**Description:**
> Test complete workflow: generate -> validate -> use spec with task_category.

**Parameters:**
- `tmp_path`: None

---

### `test_generate_report_empty_dependency_analysis() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:348`
**Complexity:** 1

**Description:**
> Test report with empty dependency analysis.

---

### `test_generate_report_invalid_format() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:336`
**Complexity:** 1

**Description:**
> Test that invalid format raises ValueError.

---

### `test_generate_report_json_clean() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:63`
**Complexity:** 1

**Description:**
> Test generating JSON report for clean validation.

---

### `test_generate_report_json_with_errors() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:82`
**Complexity:** 1

**Description:**
> Test generating JSON report with errors.

---

### `test_generate_report_legacy_dependency_keys() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:286`
**Complexity:** 1

**Description:**
> Test report generation with legacy dependency key names.

---

### `test_generate_report_markdown_clean() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:10`
**Complexity:** 1

**Description:**
> Test generating markdown report for clean validation.

---

### `test_generate_report_markdown_with_errors() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:27`
**Complexity:** 1

**Description:**
> Test generating markdown report with errors.

---

### `test_generate_report_markdown_with_warnings() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:47`
**Complexity:** 1

**Description:**
> Test generating markdown report with warnings.

---

### `test_generate_report_mixed_dependency_keys() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:313`
**Complexity:** 1

**Description:**
> Test report generation with mixed new and legacy keys.

---

### `test_generate_report_with_dependencies_all_types() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:236`
**Complexity:** 1

**Description:**
> Test generating report with all dependency types.

---

### `test_generate_report_with_dependencies_bottlenecks() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:213`
**Complexity:** 1

**Description:**
> Test generating report with bottlenecks (CLI format).

---

### `test_generate_report_with_dependencies_cycles() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:144`
**Complexity:** 1

**Description:**
> Test generating report with dependency cycles (CLI format).

---

### `test_generate_report_with_dependencies_deadlocks() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:190`
**Complexity:** 1

**Description:**
> Test generating report with deadlocks (CLI format).

---

### `test_generate_report_with_dependencies_json() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:260`
**Complexity:** 1

**Description:**
> Test generating JSON report with dependencies.

---

### `test_generate_report_with_dependencies_orphaned() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:167`
**Complexity:** 1

**Description:**
> Test generating report with orphaned dependencies (CLI format).

---

### `test_generate_report_with_stats() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:100`
**Complexity:** 1

**Description:**
> Test generating report with statistics.

---

### `test_generate_report_with_stats_json() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py:123`
**Complexity:** 1

**Description:**
> Test generating JSON report with statistics.

---

### `test_get_call_count_function_not_found(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:299`
**Complexity:** 1

**Description:**
> Test get_call_count() returns None when function not found.

**Parameters:**
- `tmp_path`: None

---

### `test_get_call_count_none(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:281`
**Complexity:** 1

**Description:**
> Test get_call_count() returns None when not available.

**Parameters:**
- `tmp_path`: None

---

### `test_get_call_count_with_value(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:263`
**Complexity:** 1

**Description:**
> Test get_call_count() returns count when available.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callees_exclude_file(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:225`
**Complexity:** 1

**Description:**
> Test get_callees() with include_file=False.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callees_function_not_found(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:251`
**Complexity:** 1

**Description:**
> Test get_callees() returns empty list when function not found.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callees_with_v2_schema(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:192`
**Complexity:** 1

**Description:**
> Test get_callees() with schema v2.0 cross-reference data.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callers_exclude_file(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:106`
**Complexity:** 1

**Description:**
> Test get_callers() with include_file=False.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callers_exclude_line(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:134`
**Complexity:** 1

**Description:**
> Test get_callers() with include_line=False.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callers_function_not_found(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:162`
**Complexity:** 1

**Description:**
> Test get_callers() returns empty list when function not found.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callers_no_callers(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:174`
**Complexity:** 1

**Description:**
> Test get_callers() returns empty list when function has no callers.

**Parameters:**
- `tmp_path`: None

---

### `test_get_callers_with_v2_schema(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:72`
**Complexity:** 1

**Description:**
> Test get_callers() with schema v2.0 cross-reference data.

**Parameters:**
- `tmp_path`: None

---

### `test_gradual_migration_path(spec_with_mixed_categories, tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:533`
**Complexity:** 4

**Description:**
> Test that specs can be gradually migrated (some tasks categorized, some not).

**Parameters:**
- `spec_with_mixed_categories`: None
- `tmp_path`: None

---

### `test_migrate_old_spec_preserves_functionality(spec_without_categories, tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:413`
**Complexity:** 1

**Description:**
> Test that old specs can be migrated without breaking functionality.

**Parameters:**
- `spec_without_categories`: None
- `tmp_path`: None

---

### `test_migrate_placeholder_file_paths(spec_with_placeholder_paths, tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:439`
**Complexity:** 2

**Description:**
> Test that placeholder file_path values can be migrated with task_category.

**Parameters:**
- `spec_with_placeholder_paths`: None
- `tmp_path`: None

---

### `test_new_fix_builders_work(spec_with_issues) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:150`
**Complexity:** 2

**Description:**
> Test that the new fix builders are functional.

**Parameters:**
- `spec_with_issues`: None

---

### `test_normalize_status() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:354`
**Complexity:** 1

**Description:**
> Test status normalization.

---

### `test_normalize_timestamp() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py:343`
**Complexity:** 1

**Description:**
> Test timestamp normalization.

---

### `test_normalize_v2_schema_fields(tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:311`
**Complexity:** 1

**Description:**
> Test that v2.0 schema fields are properly normalized.

**Parameters:**
- `tmp_path`: None

---

### `test_normalize_validation_result_clean() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:12`
**Complexity:** 1

**Description:**
> Test normalization of a clean validation result.

---

### `test_normalize_validation_result_with_errors() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:32`
**Complexity:** 1

**Description:**
> Test normalization with errors.

---

### `test_normalize_validation_result_with_warnings() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:52`
**Complexity:** 1

**Description:**
> Test normalization with warnings only.

---

### `test_normalized_validation_result_properties() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py:128`
**Complexity:** 1

**Description:**
> Test NormalizedValidationResult computed properties.

---

### `test_normalizes_legacy_payload(doc_query_samples) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:25`
**Complexity:** 1

**Parameters:**
- `doc_query_samples`: None

---

### `test_normalizes_modern_payload(doc_query_samples) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py:6`
**Complexity:** 1

**Parameters:**
- `doc_query_samples`: None

---

### `test_render_statistics_json() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:197`
**Complexity:** 1

**Description:**
> Test JSON rendering of statistics.

---

### `test_render_statistics_text() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py:169`
**Complexity:** 1

**Description:**
> Test text rendering of statistics.

---

### `test_selective_fix_application(spec_with_issues, tmp_path) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py:125`
**Complexity:** 3

**Description:**
> Test that we can selectively apply only certain fixes.

**Parameters:**
- `spec_with_issues`: None
- `tmp_path`: None

---

### `test_skills_dev_help_lists_key_subcommands() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_skills_dev_cli.py:23`
**Complexity:** 2

---

### `test_skills_dev_migrate_shows_guidance() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_skills_dev_cli.py:43`
**Complexity:** 1

---

### `test_skills_dev_requires_subcommand() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_skills_dev_cli.py:36`
**Complexity:** 2

---

### `test_test_help_lists_key_subcommands() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_test_cli.py:23`
**Complexity:** 2

---

### `test_test_requires_subcommand() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_test_cli.py:36`
**Complexity:** 2

---

### `test_test_run_list_presets_success() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_test_cli.py:43`
**Complexity:** 2

---

### `test_validate_mixed_format_spec(spec_with_mixed_categories) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:399`
**Complexity:** 1

**Description:**
> Test that validation accepts spec with mix of categorized/uncategorized tasks.

**Parameters:**
- `spec_with_mixed_categories`: None

---

### `test_validate_spec_with_all_categories(spec_with_all_categories) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:318`
**Complexity:** 5

**Description:**
> Test that validation accepts spec with all valid task_category types.

**Parameters:**
- `spec_with_all_categories`: None

---

### `test_validate_spec_with_invalid_category() -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:351`
**Complexity:** 1

**Description:**
> Test that validation rejects invalid task_category values.

---

### `test_validate_spec_without_categories(spec_without_categories) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py:341`
**Complexity:** 1

**Description:**
> Test that validation accepts old-format spec without task_category (backward compat).

**Parameters:**
- `spec_without_categories`: None

---

### `trace_data_lifecycle(query, class_name, include_properties) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py:13`
**Complexity:** 3

**Description:**
> Trace the lifecycle of a data object (class) through the codebase.

Analyzes how instances of a class are created, used, modified, and destroyed,
providing insights into data flow patterns and usage across architectural layers.

Args:
    query: DocumentationQuery instance
    class_name: Name of the class to trace
    include_properties: Whether to include detailed property access analysis

Returns:
    Dictionary with keys:
    - class_name: Name of the traced class
    - class_info: Basic class information
    - lifecycle: Dict with creation, read, update, delete operations
    - data_flow: Flow organized by architectural layer
    - property_analysis: Property access patterns (if include_properties=True)
    - summary: Statistics about the lifecycle

Example:
    >>> query = DocumentationQuery()
    >>> query.load()
    >>> result = trace_data_lifecycle(query, "User", include_properties=True)
    >>> print(f"Found {result['summary']['total_operations']} operations")

**Parameters:**
- `query`: Any
- `class_name`: str
- `include_properties`: bool

---

### `trace_execution_flow(query, function_name, max_depth) -> Dict[str, Any]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py:13`
**Complexity:** 6

**Description:**
> Trace the execution flow starting from an entry function.

Builds a call chain showing all functions called (directly or indirectly)
from the specified entry function, with architectural layer detection
and complexity analysis.

Args:
    query: DocumentationQuery instance
    function_name: Name of the entry function to trace from
    max_depth: Maximum call chain depth to traverse (default: 5)

Returns:
    Dictionary with keys:
    - entry_function: Starting function name
    - max_depth: Maximum depth used
    - call_chain: Dict with nodes, edges, layers, hot_spots
    - summary: Statistics about the trace

Example:
    >>> query = DocumentationQuery()
    >>> query.load()
    >>> result = trace_execution_flow(query, "main", max_depth=3)
    >>> print(f"Traced {result['summary']['total_functions']} functions")

**Parameters:**
- `query`: Any
- `function_name`: str
- `max_depth`: int

---

### `track_metrics(skill_name) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/metrics.py:158`
**Complexity:** 8

**Description:**
> Decorator for tracking metrics on CLI main() functions.

Usage:
    @track_metrics('sdd-next')
    def main():
        # CLI logic
        return 0  # exit code

Args:
    skill_name: Name of the skill (e.g., 'sdd-next', 'doc-query')

**Parameters:**
- `skill_name`: str

---

### `track_time(spec_id, task_id, actual_hours, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/time_tracking.py:111`
**Complexity:** 9

**Description:**
> Record actual time spent on a task.

Args:
    spec_id: Specification ID
    task_id: Task identifier
    actual_hours: Actual hours spent on task
    specs_dir: Path to specs/active directory
    dry_run: If True, show change without saving
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `actual_hours`: float
- `specs_dir`: Path
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `unblock_task(spec_id, task_id, resolution, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/status.py:394`
⚠️ **Complexity:** 13 (High)

**Description:**
> Unblock a task and optionally set it to pending or in_progress.

Args:
    spec_id: Specification ID
    task_id: Task identifier
    resolution: Optional description of how blocker was resolved
    specs_dir: Path to specs/active directory
    dry_run: If True, don't save changes
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `resolution`: Optional[str]
- `specs_dir`: Path
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `update_metadata(spec_id, key, value, specs_dir, dry_run, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/journal.py:210`
**Complexity:** 9

**Description:**
> Update a single field in the JSON spec metadata.

Args:
    spec_id: Specification ID
    key: Metadata key to update
    value: New value (can be string, int, list, dict, etc.)
    specs_dir: Optional specs directory (auto-detected if not provided)
    dry_run: If True, show change without writing
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `key`: str
- `value`: Any
- `specs_dir`: Optional[Path]
- `dry_run`: bool
- `printer`: Optional[PrettyPrinter]

---

### `update_node(spec_data, node_id, updates) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/spec.py:338`
**Complexity:** 3

**Description:**
> Update a node in the state hierarchy.

Special handling for metadata: existing metadata fields are preserved
and merged with new metadata fields, rather than being replaced entirely.

Args:
    spec_data: JSON spec file data
    node_id: Node identifier
    updates: Dictionary of fields to update

Returns:
    True if node exists and was updated, False otherwise

**Parameters:**
- `spec_data`: Dict
- `node_id`: str
- `updates`: Dict

---

### `update_node_status(node, hierarchy) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:60`
⚠️ **Complexity:** 14 (High)

**Description:**
> Update a node's status based on its children's progress.

Modifies node in-place. Does not affect manually set statuses
for leaf nodes (tasks).

Args:
    node: Node dictionary from hierarchy
    hierarchy: Full hierarchy dictionary (needed to check child statuses)

**Parameters:**
- `node`: Dict
- `hierarchy`: Dict

---

### `update_parent_status(spec_data, node_id) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/progress.py:115`
**Complexity:** 5

**Description:**
> Update status and progress for a node's parent chain.

Use this after updating a task status to propagate changes up the hierarchy.

Args:
    spec_data: JSON spec file data dictionary
    node_id: Node whose parents should be updated

Returns:
    The modified spec_data dictionary (for convenience/chaining)

**Parameters:**
- `spec_data`: Dict
- `node_id`: str

---

### `update_permissions(project_root) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/dev_tools/setup_project_permissions.py:57`
**Complexity:** 7

**Description:**
> Update .claude/settings.json with SDD permissions.

**Parameters:**
- `project_root`: None

---

### `update_task_status(spec_id, task_id, new_status, specs_dir, note, dry_run, verify, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/status.py:53`
⚠️ **Complexity:** 42 (High)

**Description:**
> Update a task's status with automatic progress recalculation.

Args:
    spec_id: Specification ID
    task_id: Task identifier
    new_status: New status (pending, in_progress, completed, blocked)
    specs_dir: Path to specs/active directory
    note: Optional note about the status change
    dry_run: If True, don't save changes
    verify: If True and new_status is 'completed', run associated verify tasks
    printer: Optional printer for output

Returns:
    True if successful, False otherwise

**Parameters:**
- `spec_id`: str
- `task_id`: str
- `new_status`: str
- `specs_dir`: Path
- `note`: Optional[str]
- `dry_run`: bool
- `verify`: bool
- `printer`: Optional[PrettyPrinter]

---

### `valid_json_spec(specs_structure) -> None`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:650`
**Complexity:** 1

**Decorators:** `@pytest.fixture`

**Description:**
> Create a valid JSON spec with verification nodes for testing verification operations.

**Parameters:**
- `specs_structure`: None

---

### `validate_and_normalize_paths(paths, base_directory) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:145`
**Complexity:** 7

**Description:**
> Validate and normalize file paths.

Checks each path for existence, normalizes relative paths, and
categorizes them as valid or invalid.

Args:
    paths: List of paths to validate (can be relative or absolute)
    base_directory: Base directory for relative path resolution (defaults to cwd)

Returns:
    Dictionary with validation results:
    - valid_paths: list of valid path info dicts
    - invalid_paths: list of invalid path info dicts
    - normalized_paths: dict mapping original to normalized paths

Example:
    >>> result = validate_and_normalize_paths(["src/main.py", "/tmp/test.txt"])
    >>> print(f"Valid: {len(result['valid_paths'])}")
    >>> print(result['normalized_paths'])

**Parameters:**
- `paths`: List[str]
- `base_directory`: Optional[Path]

---

### `validate_dependencies(hierarchy) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:433`
⚠️ **Complexity:** 29 (High)

**Description:**
> Validate dependency graph: references exist, no circular dependencies.

Args:
    hierarchy: Hierarchy dictionary from JSON spec file

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `hierarchy`: Dict

---

### `validate_dependency_graph(spec_data) -> Tuple[bool, List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/dependency_analysis.py:233`
**Complexity:** 7

**Description:**
> Quick validation that dependency graph is valid.

Checks for:
- No circular dependencies
- No orphaned dependencies
- Valid dependency references

Args:
    spec_data: JSON spec file data dictionary

Returns:
    Tuple of (is_valid: bool, error_messages: List[str])

Example:
    >>> valid, errors = validate_dependency_graph(spec_data)
    >>> if not valid:
    ...     for error in errors:
    ...         print(f"Error: {error}")

**Parameters:**
- `spec_data`: Dict

---

### `validate_hierarchy(hierarchy) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:212`
⚠️ **Complexity:** 22 (High)

**Description:**
> Validate hierarchy integrity: parent/child references, no orphans, no cycles.

Args:
    hierarchy: Hierarchy dictionary from JSON spec file

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `hierarchy`: Dict

---

### `validate_iso8601_date(date_str) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:216`
**Complexity:** 1

**Description:**
> Validate ISO 8601 date format

**Parameters:**
- `date_str`: str

---

### `validate_metadata(hierarchy) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:546`
⚠️ **Complexity:** 15 (High)

**Description:**
> Validate type-specific metadata requirements.

Args:
    hierarchy: Hierarchy dictionary from JSON spec file

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `hierarchy`: Dict

---

### `validate_node_type(node_type) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:204`
**Complexity:** 1

**Description:**
> Validate node type field value

**Parameters:**
- `node_type`: str

---

### `validate_nodes(hierarchy) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:311`
⚠️ **Complexity:** 15 (High)

**Description:**
> Validate node structure and required fields for each node.

Args:
    hierarchy: Hierarchy dictionary from JSON spec file

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `hierarchy`: Dict

---

### `validate_path(path) -> Optional[Path]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/paths.py:109`
**Complexity:** 3

**Description:**
> Validate and normalize a file or directory path.

Args:
    path: Path string to validate

Returns:
    Absolute Path object if valid, None otherwise

**Parameters:**
- `path`: str

---

### `validate_paths(paths, base_directory) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/validation.py:53`
**Complexity:** 1

**Description:**
> Validate and normalize filesystem paths.

**Parameters:**
- `paths`: list
- `base_directory`: Optional[Path]

---

### `validate_preset(preset) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/run_tests/pytest_runner.py:253`
**Complexity:** 1

**Description:**
> Check if a preset name is valid.

Args:
    preset: Preset name to validate

Returns:
    True if valid, False otherwise

**Parameters:**
- `preset`: str

---

### `validate_spec(spec_file, specs_dir) -> Dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_next/validation.py:16`
**Complexity:** 5

**Description:**
> Validate a JSON spec file using the shared hierarchy validator.

**Parameters:**
- `spec_file`: Path
- `specs_dir`: Optional[Path]

---

### `validate_spec(spec_id, specs_dir, printer) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/validation.py:17`
**Complexity:** 6

**Description:**
> Validate JSON spec consistency using comprehensive hierarchy validator.

Checks for:
- Valid JSON structure
- Required fields present
- Parent-child relationships valid
- No orphaned nodes
- No circular dependencies
- Progress calculations correct

Args:
    spec_id: Specification ID
    specs_dir: Path to specs/active directory
    printer: Optional printer for output

Returns:
    True if valid, False if issues found

**Parameters:**
- `spec_id`: str
- `specs_dir`: Path
- `printer`: Optional[PrettyPrinter]

---

### `validate_spec_before_proceed(spec_path, quiet) -> dict`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/integrations.py:18`
⚠️ **Complexity:** 11 (High)

**Description:**
> Validate spec file before proceeding with task operations.

Args:
    spec_path: Path to spec JSON file
    quiet: If True, suppress verbose output

Returns:
    dict: {
        "valid": bool,               # Overall validation result
        "errors": list[dict],        # Critical errors
        "warnings": list[dict],      # Non-critical warnings
        "can_autofix": bool,         # Whether auto-fix is available
        "autofix_command": str       # Command to run for auto-fix
    }

Example:
    >>> result = validate_spec_before_proceed("specs/auth-001.json")
    >>> if not result["valid"]:
    ...     if result["can_autofix"]:
    ...         print(f"Run: {result['autofix_command']}")
    ...     else:
    ...         print(f"Errors: {result['errors']}")

**Parameters:**
- `spec_path`: str
- `quiet`: bool

---

### `validate_spec_hierarchy(spec_data) -> JsonSpecValidationResult`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:618`
**Complexity:** 3

**Description:**
> Validate JSON spec file hierarchy with all checks.

Args:
    spec_data: JSON spec file data dictionary

Returns:
    JsonSpecValidationResult with all validation findings

**Parameters:**
- `spec_data`: Dict

---

### `validate_spec_id_format(spec_id) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:210`
**Complexity:** 1

**Description:**
> Validate spec_id follows recommended format: {feature}-{YYYY-MM-DD}-{nnn}

**Parameters:**
- `spec_id`: str

---

### `validate_status(status) -> bool`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/validation.py:198`
**Complexity:** 1

**Description:**
> Validate status field value

**Parameters:**
- `status`: str

---

### `validate_structure(spec_data) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:154`
⚠️ **Complexity:** 16 (High)

**Description:**
> Validate top-level JSON structure and required fields.

Args:
    spec_data: JSON spec file data dictionary

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `spec_data`: Dict

---

### `validate_task_counts(hierarchy) -> Tuple[bool, List[str], List[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/common/hierarchy_validation.py:365`
⚠️ **Complexity:** 12 (High)

**Description:**
> Validate task count accuracy and propagation up the hierarchy.

Args:
    hierarchy: Hierarchy dictionary from JSON spec file

Returns:
    Tuple of (is_valid, list_of_errors, list_of_warnings)

**Parameters:**
- `hierarchy`: Dict

---

### `validate_timestamp_pair(start_timestamp, end_timestamp, allow_negative, printer) -> tuple[bool, Optional[str]]`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/sdd_update/time_tracking.py:16`
**Complexity:** 7

**Description:**
> Validate a pair of timestamps for time calculation.

Args:
    start_timestamp: Start timestamp string
    end_timestamp: End timestamp string
    allow_negative: If False, returns invalid for negative durations
    printer: Optional printer for error messages

Returns:
    Tuple of (is_valid, error_message)

**Parameters:**
- `start_timestamp`: Optional[str]
- `end_timestamp`: Optional[str]
- `allow_negative`: bool
- `printer`: Optional[PrettyPrinter]

---

### `write_spec_data(specs_structure, data) -> Path`

**Language:** python
**Defined in:** `src/claude_skills/claude_skills/tests/conftest.py:292`
**Complexity:** 1

**Description:**
> Write updated spec data to the active specs directory.

**Parameters:**
- `specs_structure`: Path
- `data`: Dict[str, Any]

---


## 📦 Dependencies

### `src/claude_skills/claude_skills/__init__.py`

- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.load_json_spec`

### `src/claude_skills/claude_skills/cli/sdd/__init__.py`

- `argparse`
- `claude_skills.cli.sdd.options.add_global_options`
- `claude_skills.cli.sdd.options.create_global_parent_parser`
- `claude_skills.cli.sdd.registry.register_all_subcommands`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.metrics.track_metrics`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/cli/sdd/options.py`

- `argparse`

### `src/claude_skills/claude_skills/cli/sdd/registry.py`

- `logging`

### `src/claude_skills/claude_skills/cli/skills_dev/gendocs.py`

- `claude_skills.common.PrettyPrinter`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/cli/skills_dev/migrate.py`

- `claude_skills.common.PrettyPrinter`

### `src/claude_skills/claude_skills/cli/skills_dev/registry.py`

- `__future__.annotations`
- `argparse`
- `claude_skills.common.PrettyPrinter`
- `typing.Any`

### `src/claude_skills/claude_skills/cli/skills_dev/setup_permissions.py`

- `claude_skills.common.PrettyPrinter`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/cli/skills_dev/start_helper.py`

- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.integrations.get_session_state`
- `datetime.datetime`
- `json`
- `pathlib.Path`
- `sys`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/__init__.py`

- `calculator.calculate_complexity`
- `calculator.calculate_statistics`
- `formatter.JSONGenerator`
- `formatter.MarkdownGenerator`
- `generator.DocumentationGenerator`
- `parser.CodebaseAnalyzer`

### `src/claude_skills/claude_skills/code_doc/ai_consultation.py`

- `concurrent.futures.ThreadPoolExecutor`
- `concurrent.futures.as_completed`
- `pathlib.Path`
- `subprocess`
- `sys`
- `time`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/code_doc/ast_analysis.py`

- `dataclasses.dataclass`
- `dataclasses.field`
- `enum.Enum`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`

### `src/claude_skills/claude_skills/code_doc/calculator.py`

- `ast`
- `collections.defaultdict`
- `typing.Any`
- `typing.Dict`
- `typing.List`

### `src/claude_skills/claude_skills/code_doc/cli.py`

- `__future__.annotations`
- `argparse`
- `claude_skills.code_doc.ai_consultation.compose_ai_context_doc`
- `claude_skills.code_doc.ai_consultation.compose_architecture_doc`
- `claude_skills.code_doc.ai_consultation.generate_ai_context_docs`
- `claude_skills.code_doc.ai_consultation.generate_architecture_docs`
- `claude_skills.code_doc.ai_consultation.get_available_tools`
- `claude_skills.code_doc.calculator.calculate_statistics`
- `claude_skills.code_doc.detectors.create_context_summary`
- `claude_skills.code_doc.detectors.detect_framework`
- `claude_skills.code_doc.detectors.detect_layers`
- `claude_skills.code_doc.detectors.extract_readme`
- `claude_skills.code_doc.detectors.identify_key_files`
- `claude_skills.code_doc.detectors.suggest_reading_order`
- `claude_skills.code_doc.generator.DocumentationGenerator`
- `claude_skills.code_doc.parsers.Language`
- `claude_skills.code_doc.parsers.create_parser_factory`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.metrics.track_metrics`
- `json`
- `pathlib.Path`
- `sys`
- `traceback`
- `typing.Iterable`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/detectors.py`

- `collections.defaultdict`
- `fnmatch`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`

### `src/claude_skills/claude_skills/code_doc/formatter.py`

- `collections.defaultdict`
- `datetime.datetime`
- `datetime.timezone`
- `typing.Any`
- `typing.Dict`
- `typing.List`

### `src/claude_skills/claude_skills/code_doc/generator.py`

- `json`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parser.py`

- `ast`
- `collections.defaultdict`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`

### `src/claude_skills/claude_skills/code_doc/parsers/__init__.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedClass`
- `base.ParsedFunction`
- `base.ParsedModule`
- `base.ParsedParameter`
- `factory.ParserFactory`
- `factory.create_parser_factory`
- `python.PythonParser`

### `src/claude_skills/claude_skills/code_doc/parsers/base.py`

- `abc.ABC`
- `abc.abstractmethod`
- `dataclasses.dataclass`
- `dataclasses.field`
- `enum.Enum`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parsers/css.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedFunction`
- `base.ParsedModule`
- `pathlib.Path`
- `sys`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parsers/factory.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `collections.defaultdict`
- `pathlib.Path`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Type`

### `src/claude_skills/claude_skills/code_doc/parsers/go.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedClass`
- `base.ParsedFunction`
- `base.ParsedModule`
- `base.ParsedParameter`
- `pathlib.Path`
- `sys`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parsers/html.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedFunction`
- `base.ParsedModule`
- `pathlib.Path`
- `sys`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parsers/javascript.py`

- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedClass`
- `base.ParsedFunction`
- `base.ParsedModule`
- `base.ParsedParameter`
- `pathlib.Path`
- `sys`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/code_doc/parsers/python.py`

- `ast`
- `ast_analysis.CallSite`
- `ast_analysis.CrossReferenceGraph`
- `ast_analysis.DynamicPattern`
- `ast_analysis.DynamicPatternWarning`
- `ast_analysis.InstantiationSite`
- `ast_analysis.ReferenceType`
- `ast_analysis.create_cross_reference_graph`
- `base.BaseParser`
- `base.Language`
- `base.ParseResult`
- `base.ParsedClass`
- `base.ParsedFunction`
- `base.ParsedModule`
- `base.ParsedParameter`
- `collections.defaultdict`
- `pathlib.Path`
- `sys`
- `typing.List`

### `src/claude_skills/claude_skills/code_doc/schema.py`

- `dataclasses.dataclass`
- `dataclasses.field`
- `parsers.base.ParsedClass`
- `parsers.base.ParsedFunction`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/__init__.py`

- `completion.check_spec_completion`
- `completion.format_completion_prompt`
- `completion.should_prompt_completion`
- `dependency_analysis.DEFAULT_BOTTLENECK_THRESHOLD`
- `dependency_analysis.analyze_dependencies`
- `dependency_analysis.find_blocking_tasks`
- `dependency_analysis.find_circular_dependencies`
- `dependency_analysis.get_dependency_chain`
- `dependency_analysis.has_dependency_cycle`
- `dependency_analysis.validate_dependency_graph`
- `doc_helper.check_doc_query_available`
- `doc_helper.check_sdd_integration_available`
- `doc_helper.ensure_documentation_exists`
- `doc_helper.get_task_context_from_docs`
- `doc_helper.should_generate_docs`
- `hierarchy_validation.validate_dependencies`
- `hierarchy_validation.validate_hierarchy`
- `hierarchy_validation.validate_metadata`
- `hierarchy_validation.validate_nodes`
- `hierarchy_validation.validate_spec_hierarchy`
- `hierarchy_validation.validate_structure`
- `hierarchy_validation.validate_task_counts`
- `integrations.execute_verify_task`
- `integrations.get_session_state`
- `integrations.validate_spec_before_proceed`
- `metrics.capture_metrics`
- `metrics.get_metrics_file_path`
- `metrics.is_metrics_enabled`
- `metrics.record_metric`
- `metrics.track_metrics`
- `paths.batch_check_paths_exist`
- `paths.ensure_backups_directory`
- `paths.ensure_directory`
- `paths.ensure_human_readable_directory`
- `paths.ensure_reports_directory`
- `paths.ensure_reviews_directory`
- `paths.find_files_by_pattern`
- `paths.find_spec_file`
- `paths.find_specs_directory`
- `paths.generate_backups_readme_content`
- `paths.generate_human_readable_readme_content`
- `paths.generate_reports_readme_content`
- `paths.generate_reviews_readme_content`
- `paths.normalize_path`
- `paths.validate_and_normalize_paths`
- `paths.validate_path`
- `printer.PrettyPrinter`
- `progress.get_progress_summary`
- `progress.list_phases`
- `progress.recalculate_progress`
- `progress.update_parent_status`
- `query_operations.check_complete`
- `query_operations.get_task`
- `query_operations.list_blockers`
- `query_operations.list_phases`
- `query_operations.query_tasks`
- `reporting.generate_combined_report`
- `reporting.generate_json_spec_report`
- `reporting.generate_spec_report`
- `spec.backup_json_spec`
- `spec.extract_frontmatter`
- `spec.get_node`
- `spec.load_json_spec`
- `spec.save_json_spec`
- `spec.update_node`
- `validation.EnhancedError`
- `validation.JsonSpecValidationResult`
- `validation.SpecValidationResult`
- `validation.normalize_message_text`
- `validation.validate_iso8601_date`
- `validation.validate_node_type`
- `validation.validate_spec_id_format`
- `validation.validate_status`

### `src/claude_skills/claude_skills/common/completion.py`

- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/dependency_analysis.py`

- `dataclasses.dataclass`
- `typing.Dict`
- `typing.Iterable`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/common/doc_helper.py`

- `json`
- `pathlib.Path`
- `shutil`
- `subprocess`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/hierarchy_validation.py`

- `claude_skills.common.EnhancedError`
- `claude_skills.common.JsonSpecValidationResult`
- `claude_skills.common.normalize_message_text`
- `claude_skills.common.validate_iso8601_date`
- `claude_skills.common.validate_node_type`
- `claude_skills.common.validate_spec_id_format`
- `claude_skills.common.validate_status`
- `pathlib.Path`
- `re`
- `typing.Dict`
- `typing.Iterable`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/common/integrations.py`

- `datetime.datetime`
- `hierarchy_validation.validate_spec_hierarchy`
- `json`
- `pathlib.Path`
- `subprocess`
- `time`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/metrics.py`

- `contextlib.contextmanager`
- `datetime.datetime`
- `functools`
- `json`
- `os`
- `pathlib.Path`
- `shlex`
- `sys`
- `time`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/paths.py`

- `pathlib.Path`
- `sys`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/printer.py`

- `sys`

### `src/claude_skills/claude_skills/common/progress.py`

- `typing.Dict`
- `typing.List`

### `src/claude_skills/claude_skills/common/query_operations.py`

- `pathlib.Path`
- `printer.PrettyPrinter`
- `progress.list_phases`
- `spec.get_node`
- `spec.load_json_spec`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/reporting.py`

- `claude_skills.common.JsonSpecValidationResult`
- `claude_skills.common.SpecValidationResult`
- `datetime.datetime`
- `pathlib.Path`
- `typing.List`

### `src/claude_skills/claude_skills/common/spec.py`

- `datetime.datetime`
- `datetime.timezone`
- `json`
- `pathlib.Path`
- `paths.ensure_backups_directory`
- `paths.find_spec_file`
- `shutil`
- `sys`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`
- `typing.Union`

### `src/claude_skills/claude_skills/common/spec_analysis.py`

- `json`
- `pathlib.Path`
- `re`
- `spec.extract_frontmatter`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/common/validation.py`

- `dataclasses.dataclass`
- `dataclasses.field`
- `re`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/context_tracker/__init__.py`

- `parser.TokenMetrics`
- `parser.parse_transcript`

### `src/claude_skills/claude_skills/context_tracker/cli.py`

- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.context_tracker.parser.parse_transcript`
- `claude_skills.context_tracker.process_utils.find_session_by_pid`
- `claude_skills.context_tracker.process_utils.get_parent_pids`
- `claude_skills.context_tracker.process_utils.is_pid_alive`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/context_tracker/parser.py`

- `dataclasses.dataclass`
- `json`
- `pathlib.Path`
- `typing.Optional`

### `src/claude_skills/claude_skills/context_tracker/process_utils.py`

- `os`
- `pathlib.Path`
- `platform`
- `subprocess`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/dev_tools/generate_docs.py`

- `argparse`
- `contextlib.redirect_stderr`
- `contextlib.redirect_stdout`
- `importlib`
- `io`
- `pathlib.Path`
- `sys`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/dev_tools/sdd_start_helper.py`

- `argparse`
- `common.integrations.get_session_state`
- `datetime.datetime`
- `json`
- `os`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/dev_tools/setup_project_permissions.py`

- `argparse`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/doc_query/cli.py`

- `__future__.annotations`
- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.metrics.track_metrics`
- `claude_skills.doc_query.doc_query_lib.DocumentationQuery`
- `claude_skills.doc_query.doc_query_lib.QueryResult`
- `claude_skills.doc_query.doc_query_lib.check_docs_exist`
- `claude_skills.doc_query.doc_query_lib.check_documentation_staleness`
- `claude_skills.doc_query.workflows.impact_analysis.analyze_impact`
- `claude_skills.doc_query.workflows.impact_analysis.format_json_output`
- `claude_skills.doc_query.workflows.impact_analysis.format_text_output`
- `claude_skills.doc_query.workflows.refactor_candidates.find_refactor_candidates`
- `claude_skills.doc_query.workflows.refactor_candidates.format_json_output`
- `claude_skills.doc_query.workflows.refactor_candidates.format_text_output`
- `claude_skills.doc_query.workflows.trace_data.format_json_output`
- `claude_skills.doc_query.workflows.trace_data.format_text_output`
- `claude_skills.doc_query.workflows.trace_data.trace_data_lifecycle`
- `claude_skills.doc_query.workflows.trace_entry.format_json_output`
- `claude_skills.doc_query.workflows.trace_entry.format_text_output`
- `claude_skills.doc_query.workflows.trace_entry.trace_execution_flow`
- `json`
- `sys`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/doc_query/doc_query_lib.py`

- `dataclasses.dataclass`
- `json`
- `pathlib.Path`
- `re`
- `textwrap`
- `typing.Any`
- `typing.Dict`
- `typing.Iterable`
- `typing.List`
- `typing.Optional`
- `typing.Union`

### `src/claude_skills/claude_skills/doc_query/sdd_integration.py`

- `doc_query_lib.DocumentationQuery`
- `doc_query_lib.QueryResult`
- `pathlib.Path`
- `re`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`

### `src/claude_skills/claude_skills/doc_query/workflows/__init__.py`

- `impact_analysis.analyze_impact`
- `refactor_candidates.find_refactor_candidates`
- `trace_data.trace_data_lifecycle`
- `trace_entry.trace_execution_flow`

### `src/claude_skills/claude_skills/doc_query/workflows/impact_analysis.py`

- `json`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/doc_query/workflows/refactor_candidates.py`

- `json`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/doc_query/workflows/trace_data.py`

- `json`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/doc_query/workflows/trace_entry.py`

- `json`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/run_tests/cli.py`

- `__future__.annotations`
- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.metrics.track_metrics`
- `claude_skills.run_tests.consultation.FAILURE_TYPES`
- `claude_skills.run_tests.consultation.MULTI_AGENT_PAIRS`
- `claude_skills.run_tests.consultation.consult_multi_agent`
- `claude_skills.run_tests.consultation.consult_with_auto_routing`
- `claude_skills.run_tests.consultation.get_available_tools`
- `claude_skills.run_tests.consultation.get_consensus_pair_for_failure`
- `claude_skills.run_tests.consultation.print_routing_matrix`
- `claude_skills.run_tests.consultation.run_consultation`
- `claude_skills.run_tests.consultation.should_auto_trigger_consensus`
- `claude_skills.run_tests.pytest_runner.get_presets`
- `claude_skills.run_tests.pytest_runner.list_presets`
- `claude_skills.run_tests.pytest_runner.run_pytest`
- `claude_skills.run_tests.pytest_runner.validate_preset`
- `claude_skills.run_tests.test_discovery.print_discovery_report`
- `claude_skills.run_tests.tool_checking.FAILURE_TYPES`
- `claude_skills.run_tests.tool_checking.get_tool_status_dict`
- `claude_skills.run_tests.tool_checking.print_tool_status`
- `json`
- `sys`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/run_tests/consultation.py`

- `claude_skills.common.PrettyPrinter`
- `claude_skills.run_tests.tool_checking.check_tool_availability`
- `claude_skills.run_tests.tool_checking.get_available_tools`
- `claude_skills.run_tests.tool_checking.get_config_path`
- `concurrent.futures.ThreadPoolExecutor`
- `concurrent.futures.as_completed`
- `pathlib.Path`
- `subprocess`
- `time`
- `typing.Dict`
- `typing.List`
- `typing.NamedTuple`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/run_tests/pytest_runner.py`

- `claude_skills.common.PrettyPrinter`
- `pathlib.Path`
- `subprocess`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/run_tests/test_discovery.py`

- `claude_skills.common.PrettyPrinter`
- `collections.defaultdict`
- `pathlib.Path`
- `re`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Set`
- `typing.Tuple`

### `src/claude_skills/claude_skills/run_tests/tool_checking.py`

- `claude_skills.common.PrettyPrinter`
- `pathlib.Path`
- `shutil`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `yaml`

### `src/claude_skills/claude_skills/sdd_next/__init__.py`

- `discovery.check_dependencies`
- `discovery.get_next_task`
- `discovery.get_task_info`
- `discovery.prepare_task`
- `project.check_environment`
- `project.detect_project`
- `project.find_related_files`
- `project.find_tests`
- `validation.find_circular_deps`
- `validation.spec_stats`
- `validation.validate_paths`
- `validation.validate_spec`
- `workflow.find_pattern`
- `workflow.init_environment`

### `src/claude_skills/claude_skills/sdd_next/cli.py`

- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.check_complete`
- `claude_skills.common.completion.format_completion_prompt`
- `claude_skills.common.ensure_reports_directory`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.get_progress_summary`
- `claude_skills.common.list_blockers`
- `claude_skills.common.list_phases`
- `claude_skills.common.load_json_spec`
- `claude_skills.common.query_tasks`
- `claude_skills.sdd_next.discovery.check_dependencies`
- `claude_skills.sdd_next.discovery.get_next_task`
- `claude_skills.sdd_next.discovery.get_task_info`
- `claude_skills.sdd_next.discovery.prepare_task`
- `claude_skills.sdd_next.project.check_environment`
- `claude_skills.sdd_next.project.detect_project`
- `claude_skills.sdd_next.project.find_related_files`
- `claude_skills.sdd_next.project.find_tests`
- `claude_skills.sdd_next.validation.find_circular_deps`
- `claude_skills.sdd_next.validation.spec_stats`
- `claude_skills.sdd_next.validation.validate_paths`
- `claude_skills.sdd_next.validation.validate_spec`
- `claude_skills.sdd_next.workflow.find_pattern`
- `claude_skills.sdd_next.workflow.init_environment`
- `json`
- `os`
- `pathlib.Path`
- `sys`
- `typing.List`

### `src/claude_skills/claude_skills/sdd_next/discovery.py`

- `claude_skills.common.check_doc_query_available`
- `claude_skills.common.completion.check_spec_completion`
- `claude_skills.common.completion.should_prompt_completion`
- `claude_skills.common.get_node`
- `claude_skills.common.get_task_context_from_docs`
- `claude_skills.common.load_json_spec`
- `claude_skills.common.paths.find_spec_file`
- `claude_skills.common.validate_spec_before_proceed`
- `pathlib.Path`
- `typing.Dict`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_next/project.py`

- `json`
- `pathlib.Path`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_next/validation.py`

- `claude_skills.common.find_circular_dependencies`
- `claude_skills.common.load_json_spec`
- `claude_skills.common.spec_analysis.get_json_spec_metadata`
- `claude_skills.common.validate_and_normalize_paths`
- `claude_skills.common.validate_spec_hierarchy`
- `json`
- `pathlib.Path`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_next/workflow.py`

- `claude_skills.common.ensure_directory`
- `claude_skills.common.find_specs_directory`
- `pathlib.Path`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_plan/__init__.py`

- `claude_skills.sdd_plan.planner.analyze_codebase`
- `claude_skills.sdd_plan.planner.create_spec_interactive`
- `claude_skills.sdd_plan.planner.find_specs_directory`
- `claude_skills.sdd_plan.planner.get_project_context`
- `claude_skills.sdd_plan.templates.generate_spec_from_template`
- `claude_skills.sdd_plan.templates.get_template`
- `claude_skills.sdd_plan.templates.get_template_description`
- `claude_skills.sdd_plan.templates.infer_task_category`
- `claude_skills.sdd_plan.templates.list_templates`

### `src/claude_skills/claude_skills/sdd_plan/cli.py`

- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.ensure_reports_directory`
- `claude_skills.common.find_specs_directory`
- `claude_skills.sdd_plan.analyze_codebase`
- `claude_skills.sdd_plan.create_spec_interactive`
- `claude_skills.sdd_plan.get_project_context`
- `claude_skills.sdd_plan.get_template_description`
- `claude_skills.sdd_plan.list_templates`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/sdd_plan/planner.py`

- `datetime.datetime`
- `json`
- `pathlib.Path`
- `subprocess`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_plan/templates.py`

- `datetime.datetime`
- `datetime.timezone`
- `typing.Any`
- `typing.Dict`

### `src/claude_skills/claude_skills/sdd_plan_review/__init__.py`

- `claude_skills.sdd_plan_review.prompts.generate_review_prompt`
- `claude_skills.sdd_plan_review.reporting.generate_json_report`
- `claude_skills.sdd_plan_review.reporting.generate_markdown_report`
- `claude_skills.sdd_plan_review.reviewer.check_tool_available`
- `claude_skills.sdd_plan_review.reviewer.detect_available_tools`
- `claude_skills.sdd_plan_review.reviewer.review_with_tools`
- `claude_skills.sdd_plan_review.synthesis.build_consensus`
- `claude_skills.sdd_plan_review.synthesis.parse_response`

### `src/claude_skills/claude_skills/sdd_plan_review/cli.py`

- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.ensure_reviews_directory`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.load_json_spec`
- `claude_skills.sdd_plan_review.check_tool_available`
- `claude_skills.sdd_plan_review.detect_available_tools`
- `claude_skills.sdd_plan_review.reporting.generate_json_report`
- `claude_skills.sdd_plan_review.reporting.generate_markdown_report`
- `claude_skills.sdd_plan_review.review_with_tools`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/sdd_plan_review/prompts.py`

- `typing.Any`
- `typing.Dict`

### `src/claude_skills/claude_skills/sdd_plan_review/reporting.py`

- `datetime.datetime`
- `datetime.timezone`
- `typing.Any`
- `typing.Dict`
- `typing.List`

### `src/claude_skills/claude_skills/sdd_plan_review/reviewer.py`

- `claude_skills.sdd_plan_review.prompts.generate_review_prompt`
- `claude_skills.sdd_plan_review.synthesis.build_consensus`
- `claude_skills.sdd_plan_review.synthesis.parse_response`
- `concurrent.futures.ThreadPoolExecutor`
- `concurrent.futures.as_completed`
- `concurrent.futures.wait`
- `json`
- `pathlib.Path`
- `subprocess`
- `tempfile`
- `time`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_plan_review/synthesis.py`

- `json`
- `re`
- `statistics.mean`
- `statistics.median`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_render/__init__.py`

- `renderer.SpecRenderer`

### `src/claude_skills/claude_skills/sdd_render/cli.py`

- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.ensure_human_readable_directory`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.load_json_spec`
- `json`
- `pathlib.Path`
- `renderer.SpecRenderer`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_render/renderer.py`

- `pathlib.Path`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/__init__.py`

- `journal.add_journal_entry`
- `journal.update_metadata`
- `lifecycle.complete_spec`
- `lifecycle.move_spec`
- `query.check_complete`
- `query.get_task`
- `query.list_blockers`
- `query.list_phases`
- `query.phase_time`
- `query.query_tasks`
- `status.mark_task_blocked`
- `status.unblock_task`
- `status.update_task_status`
- `time_tracking.generate_time_report`
- `time_tracking.track_time`
- `validation.audit_spec`
- `validation.get_status_report`
- `validation.validate_spec`
- `verification.add_verification_result`

### `src/claude_skills/claude_skills/sdd_update/cli.py`

- `argparse`
- `claude_skills.common.PrettyPrinter`
- `claude_skills.common.execute_verify_task`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.load_json_spec`
- `claude_skills.sdd_update.journal.add_journal_entry`
- `claude_skills.sdd_update.journal.add_revision_entry`
- `claude_skills.sdd_update.journal.bulk_journal_tasks`
- `claude_skills.sdd_update.journal.sync_metadata_from_state`
- `claude_skills.sdd_update.journal.update_metadata`
- `claude_skills.sdd_update.lifecycle.activate_spec`
- `claude_skills.sdd_update.lifecycle.complete_spec`
- `claude_skills.sdd_update.lifecycle.move_spec`
- `claude_skills.sdd_update.query.check_complete`
- `claude_skills.sdd_update.query.get_task`
- `claude_skills.sdd_update.query.list_blockers`
- `claude_skills.sdd_update.query.list_phases`
- `claude_skills.sdd_update.query.phase_time`
- `claude_skills.sdd_update.query.query_tasks`
- `claude_skills.sdd_update.status.mark_task_blocked`
- `claude_skills.sdd_update.status.unblock_task`
- `claude_skills.sdd_update.status.update_task_status`
- `claude_skills.sdd_update.time_tracking.generate_time_report`
- `claude_skills.sdd_update.time_tracking.track_time`
- `claude_skills.sdd_update.validation.audit_spec`
- `claude_skills.sdd_update.validation.detect_unjournaled_tasks`
- `claude_skills.sdd_update.validation.get_status_report`
- `claude_skills.sdd_update.validation.reconcile_state`
- `claude_skills.sdd_update.validation.validate_spec`
- `claude_skills.sdd_update.verification.add_verification_result`
- `claude_skills.sdd_update.verification.format_verification_summary`
- `claude_skills.sdd_update.workflow.complete_task_workflow`
- `json`
- `pathlib.Path`
- `sys`

### `src/claude_skills/claude_skills/sdd_update/journal.py`

- `claude_skills.common.paths.find_specs_directory`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.common.spec.update_node`
- `datetime.datetime`
- `datetime.timezone`
- `pathlib.Path`
- `string.Template`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_update/lifecycle.py`

- `claude_skills.common.paths.ensure_directory`
- `claude_skills.common.paths.find_spec_file`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.sdd_update.time_tracking.aggregate_task_times`
- `datetime.datetime`
- `datetime.timezone`
- `pathlib.Path`
- `shutil`
- `subprocess`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/query.py`

- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.query_operations.check_complete`
- `claude_skills.common.query_operations.get_task`
- `claude_skills.common.query_operations.list_blockers`
- `claude_skills.common.query_operations.list_phases`
- `claude_skills.common.query_operations.query_tasks`
- `claude_skills.common.spec.load_json_spec`
- `pathlib.Path`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/status.py`

- `claude_skills.common.completion.check_spec_completion`
- `claude_skills.common.execute_verify_task`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.progress.recalculate_progress`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.common.spec.update_node`
- `datetime.datetime`
- `datetime.timezone`
- `pathlib.Path`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/time_tracking.py`

- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.common.spec.update_node`
- `datetime.datetime`
- `pathlib.Path`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/validation.py`

- `claude_skills.common.completion.check_spec_completion`
- `claude_skills.common.dependency_analysis.find_circular_dependencies`
- `claude_skills.common.hierarchy_validation.validate_spec_hierarchy`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.progress.get_progress_summary`
- `claude_skills.common.progress.get_task_counts_by_status`
- `claude_skills.common.progress.list_phases`
- `claude_skills.common.spec.load_json_spec`
- `pathlib.Path`
- `typing.Dict`
- `typing.List`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/verification.py`

- `claude_skills.common.paths.find_specs_directory`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.common.spec.update_node`
- `datetime.datetime`
- `datetime.timezone`
- `pathlib.Path`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_update/workflow.py`

- `__future__.annotations`
- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `copy`
- `datetime.datetime`
- `datetime.timezone`
- `journal._build_journal_entry`
- `journal._ensure_journal_container`
- `journal.add_journal_entry`
- `journal.add_revision_entry`
- `journal.mark_task_journaled`
- `journal.sync_metadata_from_state`
- `json`
- `pathlib.Path`
- `status.update_task_status`
- `time_tracking.calculate_time_from_timestamps`
- `time_tracking.track_time`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_validate/__init__.py`

- `diff.DiffReport`
- `diff.compute_diff`
- `diff.format_diff_json`
- `diff.format_diff_markdown`
- `fix.FixAction`
- `fix.FixReport`
- `fix.apply_fix_actions`
- `fix.collect_fix_actions`
- `formatting.NormalizedValidationResult`
- `formatting.format_validation_summary`
- `formatting.normalize_validation_result`
- `reporting.generate_report`
- `stats.SpecStatistics`
- `stats.calculate_statistics`
- `stats.render_statistics`

### `src/claude_skills/claude_skills/sdd_validate/cli.py`

- `argparse`
- `dataclasses.asdict`
- `json`
- `pathlib.Path`
- `sys`
- `typing.Any`
- `typing.Dict`

### `src/claude_skills/claude_skills/sdd_validate/diff.py`

- `__future__.annotations`
- `copy`
- `dataclasses.dataclass`
- `dataclasses.field`
- `json`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_validate/fix.py`

- `__future__.annotations`
- `claude_skills.common.backup_json_spec`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.recalculate_progress`
- `claude_skills.common.save_json_spec`
- `claude_skills.common.validate_spec_hierarchy`
- `claude_skills.common.validate_status`
- `claude_skills.common.validation.EnhancedError`
- `claude_skills.common.validation.JsonSpecValidationResult`
- `claude_skills.sdd_plan.templates.infer_task_category`
- `claude_skills.sdd_validate.formatting.normalize_validation_result`
- `copy`
- `dataclasses.asdict`
- `dataclasses.dataclass`
- `dataclasses.field`
- `datetime.datetime`
- `datetime.timezone`
- `json`
- `pathlib.Path`
- `re`
- `typing.Any`
- `typing.Callable`
- `typing.Dict`
- `typing.Iterable`
- `typing.List`
- `typing.Optional`
- `typing.Sequence`
- `typing.Set`

### `src/claude_skills/claude_skills/sdd_validate/formatting.py`

- `__future__.annotations`
- `claude_skills.common.validation.EnhancedError`
- `claude_skills.common.validation.JsonSpecValidationResult`
- `dataclasses.dataclass`
- `dataclasses.field`
- `typing.Any`
- `typing.Dict`
- `typing.Iterable`
- `typing.List`
- `typing.Optional`
- `typing.Sequence`
- `typing.Tuple`

### `src/claude_skills/claude_skills/sdd_validate/reporting.py`

- `__future__.annotations`
- `claude_skills.common.JsonSpecValidationResult`
- `claude_skills.sdd_validate.formatting.NormalizedValidationResult`
- `claude_skills.sdd_validate.formatting.normalize_validation_result`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/sdd_validate/stats.py`

- `__future__.annotations`
- `dataclasses.dataclass`
- `pathlib.Path`
- `typing.Any`
- `typing.Dict`

### `src/claude_skills/claude_skills/tests/conftest.py`

- `copy`
- `datetime.datetime`
- `json`
- `pathlib.Path`
- `pytest`
- `shutil`
- `tempfile`
- `typing.Any`
- `typing.Dict`
- `typing.Optional`

### `src/claude_skills/claude_skills/tests/integration/test_doc_cli.py`

- `__future__.annotations`
- `os`
- `pathlib.Path`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_sdd_next_cli.py`

- `json`
- `pathlib.Path`
- `pytest`
- `shutil`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_sdd_update_cli.py`

- `json`
- `pathlib.Path`
- `pytest`
- `shutil`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_cli.py`

- `json`
- `pathlib.Path`
- `pytest`
- `shutil`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_sdd_validate_new_features.py`

- `claude_skills.common.validate_spec_hierarchy`
- `claude_skills.sdd_validate.apply_fix_actions`
- `claude_skills.sdd_validate.collect_fix_actions`
- `claude_skills.sdd_validate.compute_diff`
- `claude_skills.sdd_validate.format_diff_markdown`
- `json`
- `pathlib.Path`
- `pytest`
- `tempfile`

### `src/claude_skills/claude_skills/tests/integration/test_skills_dev_cli.py`

- `__future__.annotations`
- `os`
- `pathlib.Path`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_status_report.py`

- `json`
- `pathlib.Path`
- `pytest`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_task_category_workflow.py`

- `claude_skills.common.hierarchy_validation.validate_spec_hierarchy`
- `claude_skills.sdd_plan.templates.generate_spec_from_template`
- `claude_skills.sdd_validate.fix.apply_fix_actions`
- `claude_skills.sdd_validate.fix.collect_fix_actions`
- `json`
- `pathlib.Path`
- `pytest`
- `tempfile`

### `src/claude_skills/claude_skills/tests/integration/test_test_cli.py`

- `__future__.annotations`
- `os`
- `pathlib.Path`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/integration/test_unified_cli.py`

- `json`
- `pathlib.Path`
- `pytest`
- `shutil`
- `subprocess`
- `sys`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/conftest.py`

- `pathlib.Path`
- `pytest`
- `unittest.mock.MagicMock`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_ai_consultation.py`

- `claude_skills.code_doc.ai_consultation.DOC_TYPE_ROUTING`
- `claude_skills.code_doc.ai_consultation.format_ai_context_research_prompt`
- `claude_skills.code_doc.ai_consultation.format_architecture_research_prompt`
- `claude_skills.code_doc.ai_consultation.get_best_tool`
- `claude_skills.code_doc.ai_consultation.run_consultation`
- `pathlib.Path`
- `pytest`
- `unittest.mock.MagicMock`
- `unittest.mock.patch`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_detectors.py`

- `claude_skills.code_doc.detectors.create_context_summary`
- `claude_skills.code_doc.detectors.detect_framework`
- `claude_skills.code_doc.detectors.detect_layers`
- `claude_skills.code_doc.detectors.extract_readme`
- `claude_skills.code_doc.detectors.identify_key_files`
- `claude_skills.code_doc.detectors.suggest_reading_order`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_base.py`

- `claude_skills.code_doc.parsers.base.BaseParser`
- `claude_skills.code_doc.parsers.base.Language`
- `claude_skills.code_doc.parsers.base.ParseResult`
- `claude_skills.code_doc.parsers.base.ParsedClass`
- `claude_skills.code_doc.parsers.base.ParsedFunction`
- `claude_skills.code_doc.parsers.base.ParsedModule`
- `claude_skills.code_doc.parsers.base.ParsedParameter`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_css.py`

- `claude_skills.code_doc.parsers.base.Language`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_factory.py`

- `claude_skills.code_doc.parsers.base.Language`
- `claude_skills.code_doc.parsers.factory.ParserFactory`
- `claude_skills.code_doc.parsers.factory.create_parser_factory`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_go.py`

- `claude_skills.code_doc.parsers.base.Language`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_html.py`

- `claude_skills.code_doc.parsers.base.Language`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_javascript.py`

- `claude_skills.code_doc.parsers.base.Language`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_code_doc/test_parsers_python.py`

- `claude_skills.code_doc.parsers.base.Language`
- `claude_skills.code_doc.parsers.python.PythonParser`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_dev_tools/test_sdd_start_helper.py`

- `io.StringIO`
- `json`
- `pathlib.Path`
- `pytest`
- `sdd_start_helper`
- `sys`
- `unittest.mock.MagicMock`
- `unittest.mock.patch`

### `src/claude_skills/claude_skills/tests/unit/test_doc_query/conftest.py`

- `json`
- `pathlib.Path`
- `pytest`
- `typing.Dict`

### `src/claude_skills/claude_skills/tests/unit/test_doc_query/test_lib.py`

- `claude_skills.doc_query.doc_query_lib.DocumentationQuery`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_completion.py`

- `claude_skills.common.completion.check_spec_completion`
- `claude_skills.common.completion.count_blocked_tasks`
- `claude_skills.common.completion.format_completion_prompt`
- `claude_skills.common.completion.get_all_tasks_in_subtree`
- `claude_skills.common.completion.is_task_complete`
- `claude_skills.common.completion.should_prompt_completion`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_doc_helper.py`

- `claude_skills.common.doc_helper.check_doc_query_available`
- `claude_skills.common.doc_helper.check_sdd_integration_available`
- `claude_skills.common.doc_helper.ensure_documentation_exists`
- `claude_skills.common.doc_helper.get_task_context_from_docs`
- `claude_skills.common.doc_helper.should_generate_docs`
- `pytest`
- `subprocess`
- `unittest.mock.MagicMock`
- `unittest.mock.Mock`
- `unittest.mock.patch`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_integrations.py`

- `claude_skills.common.integrations.execute_verify_task`
- `claude_skills.common.integrations.get_session_state`
- `claude_skills.common.integrations.validate_spec_before_proceed`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.validation.EnhancedError`
- `claude_skills.common.validation.JsonSpecValidationResult`
- `json`
- `pathlib.Path`
- `pytest`
- `subprocess`
- `unittest.mock.MagicMock`
- `unittest.mock.Mock`
- `unittest.mock.patch`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_paths.py`

- `claude_skills.common.find_spec_file`
- `claude_skills.common.find_specs_directory`
- `claude_skills.common.validate_path`
- `json`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_printer.py`

- `claude_skills.common.PrettyPrinter`
- `io.StringIO`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_progress.py`

- `claude_skills.common.get_progress_summary`
- `claude_skills.common.list_phases`
- `claude_skills.common.load_json_spec`
- `claude_skills.common.recalculate_progress`
- `claude_skills.common.update_parent_status`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_common/test_spec.py`

- `claude_skills.common.backup_json_spec`
- `claude_skills.common.extract_frontmatter`
- `claude_skills.common.get_node`
- `claude_skills.common.load_json_spec`
- `claude_skills.common.save_json_spec`
- `json`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_next/conftest.py`

- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_discovery.py`

- `claude_skills.common.load_json_spec`
- `claude_skills.sdd_next.discovery.check_dependencies`
- `claude_skills.sdd_next.discovery.get_next_task`
- `claude_skills.sdd_next.discovery.get_task_info`
- `claude_skills.sdd_next.discovery.prepare_task`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_project.py`

- `claude_skills.sdd_next.project.check_environment`
- `claude_skills.sdd_next.project.detect_project`
- `claude_skills.sdd_next.project.find_related_files`
- `claude_skills.sdd_next.project.find_tests`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_validation.py`

- `claude_skills.common.load_json_spec`
- `claude_skills.sdd_next.validation.find_circular_deps`
- `claude_skills.sdd_next.validation.spec_stats`
- `claude_skills.sdd_next.validation.validate_paths`
- `claude_skills.sdd_next.validation.validate_spec`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_next/test_workflow.py`

- `claude_skills.sdd_next.workflow.find_pattern`
- `claude_skills.sdd_next.workflow.init_environment`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/conftest.py`

- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_hierarchy_validation.py`

- `claude_skills.common.hierarchy_validation.validate_dependencies`
- `claude_skills.common.hierarchy_validation.validate_hierarchy`
- `claude_skills.common.hierarchy_validation.validate_metadata`
- `claude_skills.common.hierarchy_validation.validate_nodes`
- `claude_skills.common.hierarchy_validation.validate_spec_hierarchy`
- `claude_skills.common.hierarchy_validation.validate_structure`
- `claude_skills.common.hierarchy_validation.validate_task_counts`
- `json`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_plan/test_templates.py`

- `claude_skills.sdd_plan.templates.get_template`
- `claude_skills.sdd_plan.templates.infer_task_category`
- `claude_skills.sdd_plan.templates.list_templates`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/conftest.py`

- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_journal.py`

- `claude_skills.common.spec.load_json_spec`
- `claude_skills.sdd_update.journal.add_journal_entry`
- `claude_skills.sdd_update.journal.add_revision_entry`
- `claude_skills.sdd_update.journal.bulk_journal_tasks`
- `claude_skills.sdd_update.journal.sync_metadata_from_state`
- `claude_skills.sdd_update.journal.update_metadata`
- `datetime.datetime`
- `json`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_lifecycle.py`

- `claude_skills.common.spec.load_json_spec`
- `claude_skills.common.spec.save_json_spec`
- `claude_skills.sdd_update.lifecycle.activate_spec`
- `claude_skills.sdd_update.lifecycle.complete_spec`
- `claude_skills.sdd_update.lifecycle.move_spec`
- `json`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_query_operations.py`

- `claude_skills.common.query_operations.get_journal_entries`
- `claude_skills.common.query_operations.get_task_journal`
- `claude_skills.sdd_update.query.check_complete`
- `claude_skills.sdd_update.query.get_task`
- `claude_skills.sdd_update.query.list_blockers`
- `claude_skills.sdd_update.query.list_phases`
- `claude_skills.sdd_update.query.phase_time`
- `claude_skills.sdd_update.query.query_tasks`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_status.py`

- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.sdd_update.status.update_task_status`
- `datetime.datetime`
- `json`
- `pathlib.Path`
- `pytest`
- `tempfile`
- `time`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_time_tracking.py`

- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.sdd_update.time_tracking.aggregate_task_times`
- `claude_skills.sdd_update.time_tracking.calculate_time_from_timestamps`
- `claude_skills.sdd_update.time_tracking.validate_timestamp_pair`
- `json`
- `pathlib.Path`
- `pytest`
- `tempfile`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_verification.py`

- `claude_skills.common.spec.load_json_spec`
- `claude_skills.sdd_update.verification.add_verification_result`
- `claude_skills.sdd_update.verification.format_verification_summary`
- `pathlib.Path`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_update/test_workflow.py`

- `claude_skills.common.printer.PrettyPrinter`
- `claude_skills.common.spec.load_json_spec`
- `claude_skills.sdd_update.workflow.complete_task_workflow`
- `datetime.datetime`
- `datetime.timedelta`
- `datetime.timezone`
- `json`
- `pathlib.Path`
- `pytest`
- `tempfile`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_fix.py`

- `claude_skills.common.validation.EnhancedError`
- `claude_skills.common.validation.JsonSpecValidationResult`
- `claude_skills.sdd_validate.fix.FixAction`
- `claude_skills.sdd_validate.fix.FixReport`
- `claude_skills.sdd_validate.fix._build_counts_action`
- `claude_skills.sdd_validate.fix._build_date_action`
- `claude_skills.sdd_validate.fix._build_hierarchy_action`
- `claude_skills.sdd_validate.fix._build_metadata_action`
- `claude_skills.sdd_validate.fix._build_placeholder_file_path_action`
- `claude_skills.sdd_validate.fix._build_status_action`
- `claude_skills.sdd_validate.fix._build_task_category_action`
- `claude_skills.sdd_validate.fix._normalize_status`
- `claude_skills.sdd_validate.fix._normalize_timestamp`
- `claude_skills.sdd_validate.fix.apply_fix_actions`
- `claude_skills.sdd_validate.fix.collect_fix_actions`
- `json`
- `pathlib.Path`
- `pytest`
- `unittest.mock.mock_open`
- `unittest.mock.patch`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_formatting.py`

- `claude_skills.common.validation.JsonSpecValidationResult`
- `claude_skills.sdd_validate.formatting.NormalizedValidationResult`
- `claude_skills.sdd_validate.formatting.format_validation_summary`
- `claude_skills.sdd_validate.formatting.normalize_validation_result`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_reporting.py`

- `claude_skills.common.validation.JsonSpecValidationResult`
- `claude_skills.sdd_validate.reporting.generate_report`
- `json`
- `pytest`

### `src/claude_skills/claude_skills/tests/unit/test_sdd_validate/test_stats.py`

- `claude_skills.sdd_validate.stats.SpecStatistics`
- `claude_skills.sdd_validate.stats.calculate_statistics`
- `claude_skills.sdd_validate.stats.render_statistics`
- `json`
- `pytest`
