# Advanced Topics

Advanced concepts, architecture patterns, and extension points for the SDD Toolkit. This guide is for developers who want to extend the toolkit or understand its internals.

## Table of Contents

- [Design Patterns](#design-patterns)
- [Technology Stack](#technology-stack)
- [Architecture Overview](#architecture-overview)
- [Extension Points](#extension-points)
- [Performance Optimization](#performance-optimization)
- [Provider Abstraction Layer](#provider-abstraction-layer)
- [Testing Strategy](#testing-strategy)
- [Contributing](#contributing)

---

## Design Patterns

The SDD Toolkit leverages several design patterns for maintainability and extensibility.

### Command Pattern

**Used in:** CLI command structure

**Purpose:** Encapsulate operations as objects

**Implementation:**
```python
class Command:
    def execute(self, args):
        raise NotImplementedError

class ProgressCommand(Command):
    def execute(self, args):
        spec = load_spec(args.spec_id)
        return calculate_progress(spec)

# Dispatch
commands = {
    'progress': ProgressCommand(),
    'validate': ValidateCommand(),
}
commands[args.command].execute(args)
```

**Benefits:**
- Easy to add new commands
- Consistent command interface
- Testable in isolation

---

### Factory Pattern

**Used in:** Language parser creation

**Purpose:** Create parser instances without specifying exact class

**Implementation:**
```python
class ParserFactory:
    parsers = {
        'python': PythonParser,
        'javascript': JavaScriptParser,
        'typescript': TypeScriptParser,
    }

    @classmethod
    def create(cls, language):
        parser_class = cls.parsers.get(language)
        if parser_class:
            return parser_class()
        return GenericParser()
```

**Benefits:**
- Easy to add language support
- Centralized parser registration
- Runtime language detection

---

### Strategy Pattern

**Used in:** AI tool selection and execution

**Purpose:** Define family of algorithms, make them interchangeable

**Implementation:**
```python
class ProviderStrategy:
    def execute(self, prompt):
        raise NotImplementedError

class GeminiStrategy(ProviderStrategy):
    def execute(self, prompt):
        return call_gemini_api(prompt)

class CursorStrategy(ProviderStrategy):
    def execute(self, prompt):
        return call_cursor_agent(prompt)

# Runtime selection
provider = get_strategy(config.tool_priority[0])
result = provider.execute(prompt)
```

**Benefits:**
- Swap providers at runtime
- Add new providers easily
- Consistent interface

---

### Facade Pattern

**Used in:** Documentation query interface

**Purpose:** Provide unified interface to complex subsystem

**Implementation:**
```python
class DocQuery:
    """Facade for complex doc operations"""

    def __init__(self):
        self.loader = DocLoader()
        self.parser = ASTParser()
        self.analyzer = CodeAnalyzer()

    def search(self, query):
        doc = self.loader.load()
        parsed = self.parser.parse(doc)
        return self.analyzer.search(parsed, query)
```

**Benefits:**
- Simplified API
- Hides complexity
- Easier to refactor internals

---

### Provider Pattern

**Used in:** AI tool abstraction

**Purpose:** Abstract over multiple implementations

**Implementation:**
```python
class ProviderContext:
    def __init__(self, name, model):
        self.name = name
        self.model = model

    def execute(self, prompt, tools=None):
        raise NotImplementedError

    def supports_tools(self):
        return False
```

**Benefits:**
- Uniform interface for all AI tools
- Easy to add new providers
- Tool-agnostic skill code

---

### Repository Pattern

**Used in:** Spec file operations

**Purpose:** Abstract data persistence

**Implementation:**
```python
class SpecRepository:
    def __init__(self, base_path):
        self.base_path = base_path

    def find_by_id(self, spec_id):
        for folder in ['active', 'pending', 'completed']:
            path = self.base_path / folder / f"{spec_id}.json"
            if path.exists():
                return self.load(path)
        return None

    def save(self, spec):
        path = self._get_path(spec)
        write_json(path, spec)
```

**Benefits:**
- Centralized file I/O
- Easy to change storage (could use DB)
- Testable with mocks

---

### Mediator Pattern

**Used in:** Output formatting

**Purpose:** Reduce coupling between formatter classes

**Implementation:**
```python
class OutputMediator:
    def __init__(self):
        self.formatters = {
            'json': JSONFormatter(),
            'rich': RichFormatter(),
            'plain': PlainFormatter(),
        }

    def format(self, data, mode):
        formatter = self.formatters[mode]
        return formatter.format(data)
```

**Benefits:**
- Formatters don't know about each other
- Easy to add new formats
- Central configuration point

---

## Technology Stack

### Core Components

**Language:** Python 3.9+
- Modern async/await support
- Type hints for better IDE support
- Standard library utilities

**Project Statistics:**
- 183 Python modules
- 154 classes
- 915 functions
- 72,268 lines of code
- Average complexity: 6.93

---

### Key Libraries

#### Rich (Terminal UI)

**Purpose:** Enhanced terminal output

**Usage:**
```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Spec Progress")
table.add_column("Task", style="cyan")
table.add_column("Status", style="green")
console.print(table)
```

**Features:**
- Colored output
- Tables and trees
- Progress bars
- Markdown rendering

---

#### tree-sitter (AST Parsing)

**Purpose:** Parse source code into AST

**Usage:**
```python
from tree_sitter import Language, Parser

PY_LANGUAGE = Language('build/languages.so', 'python')
parser = Parser()
parser.set_language(PY_LANGUAGE)

tree = parser.parse(source_code.encode())
```

**Supported Languages:**
- Python (built-in)
- JavaScript/TypeScript (built-in)
- Rust, Go, Java (via extensions)

**Adding Language:**
```bash
pip install tree-sitter-{language}
```

---

#### JSON Schema (Validation)

**Purpose:** Validate spec files

**Usage:**
```python
from jsonschema import validate, ValidationError

schema = load_json('specification-schema.json')
spec = load_json('my-spec.json')

try:
    validate(spec, schema)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
```

---

### AI Integration

**External CLI Tools:**
- `gemini` - Google Gemini CLI
- `cursor-agent` - Cursor Composer
- `codex` - Anthropic Codex CLI
- `claude` - Claude via Anthropic API
- `opencode` - OpenCode AI SDK (Node.js)

**Integration Method:**
```python
import subprocess

def call_provider(provider, prompt):
    result = subprocess.run(
        [provider, prompt],
        capture_output=True,
        text=True
    )
    return result.stdout
```

---

### Testing

**Framework:** pytest

**Coverage:**
- Unit tests for core logic
- Integration tests for workflows
- Fixture-based test data

**Example:**
```python
def test_spec_validation():
    spec = load_fixture('valid-spec.json')
    errors = validate_spec(spec)
    assert len(errors) == 0
```

---

## Architecture Overview

### Modular Skill-Based Design

Each major capability is an independent skill module:

```
skills/
├── sdd-plan/           # Spec creation
├── sdd-next/           # Task orchestration
├── sdd-update/         # Progress tracking
├── doc-query/          # Code analysis
├── llm-doc-gen/        # AI documentation
├── run-tests/          # Test execution
├── sdd-plan-review/    # Multi-model review
├── sdd-fidelity-review/# Implementation verification
└── common/             # Shared utilities
```

**Benefits:**
- Independent development
- Clear separation of concerns
- Easy testing
- Extensible

---

### Data Flow Architecture

**Primary State:** JSON Specifications

```
specs/
├── pending/      # Planned work
├── active/       # Current implementation
├── completed/    # Finished features
└── archived/     # Cancelled work
```

**Lifecycle:**
```
Plan → Validate → Activate → Implement → Track → Review → Complete
  ↓        ↓          ↓           ↓         ↓        ↓         ↓
sdd-plan  validate  activate  sdd-next  update  fidelity    PR/archive
```

All state is Git-trackable JSON files.

---

### Provider Abstraction Layer

Unified interface for multiple AI tools:

```python
# All providers implement ProviderContext
providers = ["gemini", "cursor-agent", "codex", "claude"]

# Parallel consultation
results = consult_multi_agent(
    prompt=prompt,
    providers=["gemini", "cursor-agent"],
    mode="parallel"
)
```

**Read-Only Mode:**

Some providers (claude, opencode) enforce read-only restrictions:
- ✅ Can: Read files, Search code, Web search
- ❌ Cannot: Write files, Edit files, Run bash

---

## Extension Points

### Add a New Skill

**Steps:**

1. **Create skill directory:**
   ```bash
   mkdir -p skills/my-skill
   cd skills/my-skill
   ```

2. **Create SKILL.md:**
   ```markdown
   # My Skill

   [Skill description and instructions]
   ```

3. **Create CLI implementation:**
   ```bash
   mkdir -p src/claude_skills/my_skill
   touch src/claude_skills/my_skill/cli.py
   ```

4. **Implement CLI:**
   ```python
   import click
   from claude_skills.common.utils import load_spec

   @click.command()
   @click.argument('spec_id')
   def my_command(spec_id):
       """My custom skill"""
       spec = load_spec(spec_id)
       # Implementation
       click.echo("Done!")
   ```

5. **Register in main CLI:**
   ```python
   # In src/claude_skills/cli.py
   from .my_skill.cli import my_command

   cli.add_command(my_command, name='my-skill')
   ```

6. **Add tests:**
   ```python
   # tests/test_my_skill.py
   def test_my_skill():
       result = run_cli(['my-skill', 'test-spec'])
       assert result.exit_code == 0
   ```

---

### Add a Language Parser

**Steps:**

1. **Install tree-sitter grammar:**
   ```bash
   pip install tree-sitter-rust  # Example for Rust
   ```

2. **Create parser class:**
   ```python
   # src/claude_skills/code_doc/parsers/rust_parser.py
   from .base_parser import BaseParser

   class RustParser(BaseParser):
       language_name = 'rust'

       def parse_function(self, node):
           # Extract function info
           return {
               'name': self.get_name(node),
               'signature': self.get_signature(node),
               'complexity': self.calculate_complexity(node)
           }
   ```

3. **Register parser:**
   ```python
   # In parsers/factory.py
   from .rust_parser import RustParser

   PARSERS = {
       'python': PythonParser,
       'javascript': JavaScriptParser,
       'rust': RustParser,  # Add here
   }
   ```

4. **Add file detection:**
   ```python
   # In parsers/detection.py
   EXTENSIONS = {
       '.py': 'python',
       '.js': 'javascript',
       '.rs': 'rust',  # Add here
   }
   ```

5. **Test:**
   ```python
   def test_rust_parser():
       parser = RustParser()
       code = 'fn main() { println!("Hello"); }'
       result = parser.parse(code)
       assert len(result['functions']) == 1
   ```

---

### Add an AI Provider

**Steps:**

1. **Extend ProviderContext:**
   ```python
   # src/claude_skills/common/providers/my_provider.py
   from .base import ProviderContext

   class MyProvider(ProviderContext):
       def __init__(self, model):
           super().__init__('my-provider', model)

       def execute(self, prompt, tools=None):
           # Call your AI service
           result = my_api_call(prompt, self.model)
           return result

       def supports_tools(self):
           return False  # Or True if supports function calling
   ```

2. **Register provider:**
   ```python
   # In providers/registry.py
   from .my_provider import MyProvider

   PROVIDERS = {
       'gemini': GeminiProvider,
       'my-provider': MyProvider,  # Add here
   }
   ```

3. **Add detection logic:**
   ```python
   # In providers/detection.py
   def detect_provider(name):
       if name == 'my-provider':
           # Check if CLI available
           return shutil.which('my-provider-cli') is not None
       # ...
   ```

4. **Update config templates:**
   ```yaml
   # In templates/setup/ai_config.yaml
   tool_priority:
     default:
       - gemini
       - my-provider  # Add here
   ```

5. **Test:**
   ```python
   def test_my_provider():
       provider = MyProvider('default-model')
       result = provider.execute("test prompt")
       assert result is not None
   ```

---

## Performance Optimization

### Scalability Characteristics

**Documentation Generation:**
- **Complexity:** O(n) where n = files
- **Performance:** ~0.1-0.5s per file
- **Bottleneck:** Tree-sitter parsing

**Spec Validation:**
- **Complexity:** O(n) where n = tasks
- **Performance:** <100ms for typical spec
- **Bottleneck:** Dependency graph analysis

**Doc Queries:**
- **Complexity:** O(log n) with indexes
- **Performance:** <50ms for typical query
- **Bottleneck:** JSON deserialization

**AI Calls:**
- **Complexity:** Independent per call
- **Performance:** 10-60s per call
- **Bottleneck:** API latency

---

### Optimization Strategies

#### 1. Parallel AI Consultation

```python
import concurrent.futures

def consult_parallel(prompt, providers):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(call_provider, p, prompt): p
            for p in providers
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            provider = futures[future]
            results[provider] = future.result()
    return results
```

**Impact:** 2x speedup for 2 providers

---

#### 2. Performance Benchmarking

Benchmark prepare-task latency to ensure enhancements don't add overhead:

```bash
# Benchmark specific spec
python scripts/benchmark_prepare_task_latency.py my-spec-001

# Benchmark with specific task
python scripts/benchmark_prepare_task_latency.py my-spec-001 task-2-1

# More iterations for statistical significance
python scripts/benchmark_prepare_task_latency.py my-spec-001 --iterations 100

# JSON output for CI integration
python scripts/benchmark_prepare_task_latency.py my-spec-001 --json
```

**Performance Target:**
- Delta between minimal and enhanced context: <30ms (99th percentile)
- Absolute latency: <100ms (median)

**Example Output:**
```
Benchmark Results:
==================
Baseline Context:
  Median: 45ms | p95: 67ms | p99: 89ms

Enhanced Context (new default):
  Median: 52ms | p95: 74ms | p99: 92ms

Delta (enhanced - baseline):
  Median: +7ms | p95: +7ms | p99: +3ms ✓

✓ PASS: p99 delta (3ms) < 30ms threshold
```

**Use Cases:**
- Validate performance impact of context enhancements
- Establish baseline metrics before refactoring
- CI/CD performance regression testing
- Compare performance across different specs

---

#### 3. TTL-Based Caching

```python
import time
from functools import lru_cache

class TTLCache:
    def __init__(self, ttl=900):  # 15 minutes
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())
```

**Impact:** Avoid redundant API calls

---

#### 3. Lazy Loading

```python
class Spec:
    def __init__(self, spec_id):
        self.spec_id = spec_id
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = load_json(self.path)
        return self._data
```

**Impact:** Faster initialization

---

#### 4. Progressive Rendering

```python
def render_spec_streaming(spec):
    yield "# Spec: {}\n\n".format(spec.title)
    for phase in spec.phases:
        yield f"## Phase: {phase.title}\n"
        for task in phase.tasks:
            yield f"- {task.title}\n"
```

**Impact:** Perceived performance improvement

---

### Memory Management

**Large Spec Files:**
```python
import json

def load_spec_streaming(path):
    """Stream large JSON files"""
    with open(path) as f:
        return json.load(f)  # Still loads fully, but could use ijson
```

**Better approach with ijson:**
```python
import ijson

def iterate_tasks(path):
    """Stream tasks from large spec"""
    with open(path, 'rb') as f:
        tasks = ijson.items(f, 'tasks.item')
        for task in tasks:
            yield task
```

---

## Provider Abstraction Layer

### Architecture

```
Skills
  ↓
ProviderContext (Abstract)
  ↓
├── GeminiProvider
├── CursorProvider
├── CodexProvider
├── ClaudeProvider
└── OpenCodeProvider
```

### Security Model

**Read-Only Providers:**

```python
class ReadOnlyProvider(ProviderContext):
    """Enforce read-only tool access"""

    ALLOWED_TOOLS = ['Read', 'Grep', 'Glob', 'WebSearch']

    def execute(self, prompt, tools=None):
        if tools:
            tools = [t for t in tools if t in self.ALLOWED_TOOLS]
        return super().execute(prompt, tools)
```

**Use cases:**
- Untrusted prompts
- Experimental features
- Safety guarantees

---

### Provider Configuration

**YAML Structure:**
```yaml
# Global fallback
tool_priority:
  default:
    - gemini
    - cursor-agent

# Per-skill override
sdd-plan-review:
  tool_priority:
    - cursor-agent
    - gemini
  models:
    gemini: gemini-2.5-pro
    cursor-agent: composer-1
```

**Loading:**
```python
import yaml

config = yaml.safe_load(open('.claude/ai_config.yaml'))
tools = config['tool_priority']['default']
```

---

## Testing Strategy

### Test Categories

**Unit Tests:**
```python
def test_calculate_progress():
    spec = {
        'tasks': [
            {'status': 'completed'},
            {'status': 'completed'},
            {'status': 'pending'},
        ]
    }
    progress = calculate_progress(spec)
    assert progress['percentage'] == 66
```

**Integration Tests:**
```python
def test_full_workflow(tmp_path):
    # Create spec
    spec_id = create_spec(tmp_path, "Test Feature")

    # Activate
    activate_spec(tmp_path, spec_id)

    # Complete task
    complete_task(tmp_path, spec_id, 'task-1-1')

    # Verify
    progress = get_progress(tmp_path, spec_id)
    assert progress['completed'] == 1
```

**Fixture-Based Testing:**
```python
@pytest.fixture
def sample_spec():
    return load_json('tests/fixtures/sample-spec.json')

def test_validation(sample_spec):
    errors = validate_spec(sample_spec)
    assert len(errors) == 0
```

---

### Test Organization

```
tests/
├── unit/
│   ├── test_validation.py
│   ├── test_progress.py
│   └── test_dependencies.py
├── integration/
│   ├── test_workflow.py
│   └── test_cli.py
├── fixtures/
│   ├── valid-spec.json
│   └── invalid-spec.json
└── conftest.py
```

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/tylerburleigh/claude-sdd-toolkit
cd claude-sdd-toolkit

# Install in development mode
cd src/claude_skills
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=claude_skills
```

---

### Code Style

**Follow PEP 8:**
```bash
# Format code
black claude_skills/

# Check style
flake8 claude_skills/

# Type checking
mypy claude_skills/
```

---

### Pull Request Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes with tests:**
   ```python
   # Add feature
   # Add tests
   pytest tests/test_my_feature.py
   ```

3. **Update documentation:**
   - Update CHANGELOG.md
   - Update relevant docs
   - Add examples if needed

4. **Submit PR:**
   - Clear description
   - Link to issue if applicable
   - Pass CI checks

---

### Architecture Decisions

**When adding features, consider:**

1. **Modularity:** Can this be a separate skill?
2. **Dependencies:** Minimize external dependencies
3. **Backwards compatibility:** Don't break existing specs
4. **Performance:** Profile before optimizing
5. **Testing:** Add tests for new code
6. **Documentation:** Update docs

---

## Next Steps

Now that you understand advanced topics:

- **Extend the toolkit:** Add a custom skill or provider
- **Contribute:** Submit PRs for improvements
- **Optimize:** Profile and improve performance
- **Integrate:** Use toolkit in your CI/CD pipeline

---

**Related Documentation:**
- [Core Concepts](core-concepts.md) - Fundamental concepts
- [Skills Reference](skills-reference.md) - Skill usage
- [CLI Reference](cli-reference.md) - Command-line interface
- [Configuration](configuration.md) - Configuration options
- [GitHub Repository](https://github.com/tylerburleigh/claude-sdd-toolkit) - Source code and issues
