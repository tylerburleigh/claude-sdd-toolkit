# LLM-Based Documentation Generation

> AI-powered documentation generation for codebases of any size

## Overview

The `llm-doc-gen` feature generates comprehensive, high-quality documentation for your codebase using Large Language Models. It intelligently analyzes your project structure, code files, and generates multiple documentation shards covering architecture, components, and overview.

### Key Features

- **Multi-LLM Support**: Works with Gemini, Codex, Cursor Agent, Claude, and OpenCode
- **Smart Batching**: Processes documentation shards in configurable batches for better LLM context utilization
- **Write-as-you-go**: Generates and writes documentation incrementally to handle large projects
- **Structured Output**: Creates organized documentation with index, overview, architecture, and component inventory
- **Automatic Project Detection**: Identifies project type, languages, and tech stack automatically

## Quick Start

### Basic Usage

Generate documentation for your project:

```bash
sdd llm-doc-gen generate ./src
```

This will:
1. Scan your project structure
2. Analyze key files and source code
3. Generate documentation shards using AI
4. Write organized markdown files to `./docs/llm-generated/`

### Common Options

```bash
# Specify output directory
sdd llm-doc-gen generate ./src --output-dir ./docs/ai

# Provide project details
sdd llm-doc-gen generate ./src --name "MyProject" --description "A web application"

# Enable verbose output
sdd llm-doc-gen generate ./src --verbose

# Disable batching (process all shards at once)
sdd llm-doc-gen generate ./src --no-batching

# Configure batch size
sdd llm-doc-gen generate ./src --batch-size 5
```

## Command Reference

### `sdd llm-doc-gen generate`

Generate comprehensive documentation using LLMs.

```bash
sdd llm-doc-gen generate <directory> [options]
```

#### Arguments

- `directory`: Project directory to document (required)

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir DIR` | Output directory for documentation | `./docs/llm-generated` |
| `--name NAME` | Project name | Directory name |
| `--description DESC` | Project description | Auto-generated |
| `--batch-size N` | Number of shards per batch | 3 |
| `--no-batching` | Disable batched generation | Batching enabled |
| `--verbose, -v` | Verbose output | Disabled |

## How It Works

### 1. Project Scanning

The tool scans your project to identify:

- **Project structure**: Monolith, monorepo, or multi-part
- **Primary languages**: Python, JavaScript/TypeScript, Go, etc.
- **Tech stack**: Frameworks, libraries, and tools
- **Key files**: README, package.json, requirements.txt, etc.
- **Source files**: Code files for analysis

### 2. Documentation Generation

Four documentation shards are generated:

1. **Project Overview** (`project-overview.md`)
   - High-level project description
   - Purpose and goals
   - Key features
   - Technology summary

2. **Architecture** (`architecture.md`)
   - System architecture
   - Component relationships
   - Design patterns
   - Technology decisions

3. **Component Inventory** (`component-inventory.md`)
   - Detailed component catalog
   - File structure analysis
   - Module descriptions
   - API surfaces

4. **Index** (`index.md`)
   - Navigation hub
   - Links to all documentation
   - Quick reference
   - Project metadata

### 3. Batched Processing

Documentation shards can be generated in batches to:

- **Improve quality**: Smaller batches allow LLMs to focus better
- **Manage context**: Avoid hitting token limits on large projects
- **Enable progress tracking**: See documentation being generated incrementally

## Examples

### Example 1: Document a Python Project

```bash
cd /path/to/my-python-app
sdd llm-doc-gen generate . --name "MyPythonApp" --description "A FastAPI web application"
```

**Output:**

```
[INFO] Generating LLM-based documentation for: MyPythonApp
[INFO] Project root: /path/to/my-python-app
[INFO] Output directory: /path/to/my-python-app/docs/llm-generated
[INFO] Scanning project...
[INFO] Generating documentation shards...
Consulting gemini for documentation generation...
[SUCCESS] ✓ Documentation generated successfully!
[INFO]   Shards generated: 4
[INFO]     - project_overview
[INFO]     - architecture
[INFO]     - component_inventory
[INFO]     - index
[INFO]
Documentation written to: /path/to/my-python-app/docs/llm-generated
[INFO]
Generated files:
[INFO]   - architecture.md (5.2 KB)
[INFO]   - component-inventory.md (12.4 KB)
[INFO]   - index.md (2.1 KB)
[INFO]   - project-overview.md (3.7 KB)
```

### Example 2: Document with Custom Output Directory

```bash
sdd llm-doc-gen generate ./backend \
  --output-dir ./documentation/backend \
  --name "Backend API" \
  --description "RESTful API server for the platform" \
  --verbose
```

### Example 3: Large Project with Batching

```bash
sdd llm-doc-gen generate ./large-monorepo \
  --batch-size 2 \
  --output-dir ./docs/auto-generated \
  --verbose
```

This processes 2 shards at a time, providing better control over LLM context and resource usage.

### Example 4: Quick Documentation without Batching

```bash
sdd llm-doc-gen generate ./simple-utility --no-batching
```

For small projects, disabling batching generates all shards in a single pass.

## Generated Documentation Structure

```
docs/llm-generated/
├── index.md                    # Navigation hub
├── project-overview.md         # High-level overview
├── architecture.md             # System architecture
├── component-inventory.md      # Component catalog
└── doc-generation-state.json   # Generation metadata
```

### Sample Output

#### index.md

```markdown
# MyProject Documentation Index

**Type:** monolith
**Primary Language:** Python
**Architecture:** Modular
**Last Updated:** 2025-11-19

## Project Overview

A web application for managing tasks

## Quick Reference

- **Tech Stack:** Python, FastAPI, PostgreSQL
- **Entry Point:** main.py
- **Architecture Pattern:** Layered

## Generated Documentation

### Core Documentation
- [Project Overview](project-overview.md)
- [Architecture](architecture.md)
- [Component Inventory](component-inventory.md)
```

## AI Provider Configuration

The tool automatically detects available AI providers:

1. **OpenCode** (recommended)
2. **Gemini**
3. **Cursor Agent**
4. **Codex**
5. **Claude**

To configure specific providers, see [docs/providers/](../providers/).

## Best Practices

### 1. Provide Project Context

```bash
sdd llm-doc-gen generate ./src \
  --name "Meaningful Project Name" \
  --description "Clear, concise description of what the project does"
```

Better context leads to better documentation.

### 2. Use Appropriate Batch Sizes

- **Small projects (<50 files)**: `--no-batching` or `--batch-size 4`
- **Medium projects (50-200 files)**: `--batch-size 3` (default)
- **Large projects (>200 files)**: `--batch-size 2`

### 3. Review and Refine

AI-generated documentation is a starting point. Review and refine it for accuracy and completeness.

### 4. Regenerate Periodically

As your codebase evolves, regenerate documentation to keep it current:

```bash
sdd llm-doc-gen generate ./src  # Overwrites existing docs
```

## Troubleshooting

### No AI Providers Available

**Error:**
```
No AI providers available. Install cursor-agent, gemini, codex, or opencode.
```

**Solution:**
```bash
# Install OpenCode (recommended)
npm install -g @opencode/cli

# Or install Gemini
npm install -g @google/gemini-cli

# Verify installation
sdd llm-doc-gen generate ./test-project
```

### Generation Fails for Specific Shards

**Error:**
```
[ERROR] ✗ Documentation generation failed
[ERROR]   Failed shards: 1
[ERROR]     - architecture: LLM consultation timeout
```

**Solutions:**
1. Reduce batch size: `--batch-size 1`
2. Simplify project (temporarily remove large files)
3. Try a different AI provider
4. Increase timeout (requires code modification)

### Output Directory Permission Issues

**Error:**
```
Permission denied: /docs/llm-generated
```

**Solution:**
```bash
# Create directory with proper permissions
mkdir -p ./docs/llm-generated
chmod 755 ./docs/llm-generated

# Or specify a writable directory
sdd llm-doc-gen generate ./src --output-dir ~/my-docs
```

## Integration with SDD Workflow

You can incorporate documentation generation into your SDD workflow:

```bash
# After completing a major feature
sdd llm-doc-gen generate ./src --output-dir ./docs/current

# Add to git
git add docs/current
git commit -m "docs: Regenerate documentation for v2.0 features"
```

## Advanced Usage

### Custom Documentation for Specific Modules

```bash
# Document just the backend module
sdd llm-doc-gen generate ./backend --name "Backend Services"

# Document just the frontend
sdd llm-doc-gen generate ./frontend --name "Frontend Application"
```

### Combining with Code Documentation

```bash
# Generate API docs with code-doc
sdd code-doc ./src --output ./docs/api.json

# Generate narrative docs with llm-doc-gen
sdd llm-doc-gen generate ./src --output-dir ./docs/guide
```

## Performance Considerations

- **Batch size**: Smaller batches are slower but higher quality
- **Project size**: Large projects (>500 files) may take 5-10 minutes
- **AI provider**: Different providers have different speeds and quality
- **Network latency**: Cloud-based providers depend on connection speed

## Future Enhancements

Planned features for upcoming releases:

- **Incremental updates**: Update only changed documentation
- **Custom templates**: Define your own documentation structure
- **Multi-language support**: Documentation in multiple languages
- **Interactive mode**: Ask questions during generation
- **Integration testing**: Verify documentation accuracy against code

## See Also

- [Code Documentation Tool](./code-doc.md) - AST-based code analysis
- [Documentation Query Tool](./doc-query.md) - Query generated documentation
- [SDD Planning](./sdd-plan.md) - Spec-driven development planning
- [AI Provider Configuration](./providers/) - Configure AI tools

## Support

For issues or feature requests:

- GitHub Issues: [https://github.com/tylerburleigh/claude-sdd-toolkit/issues](https://github.com/tylerburleigh/claude-sdd-toolkit/issues)
- Documentation: [https://github.com/tylerburleigh/claude-sdd-toolkit/docs](https://github.com/tylerburleigh/claude-sdd-toolkit/docs)
