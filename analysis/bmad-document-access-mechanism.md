# How BMAD Makes Document-Project Documentation Accessible to AI Coding Assistants

## Overview

BMAD-METHOD uses a sophisticated **content discovery and loading system** that automatically makes `document-project` output available to AI coding assistants through workflow context variables. The system is designed to be intelligent, efficient, and context-aware.

---

## Core Mechanism: The Discovery Protocol

### 1. Workflow Configuration (`workflow.yaml`)

Each workflow that needs access to documentation declares its requirements in `input_file_patterns`:

```yaml
input_file_patterns:
  document_project:
    description: "Brownfield project documentation (optional)"
    sharded: "{output_folder}/index.md"
    load_strategy: "INDEX_GUIDED"
```

**Key Points:**
- `sharded: "{output_folder}/index.md"` - Points to the master index file
- `load_strategy: "INDEX_GUIDED"` - Uses intelligent loading strategy
- No `whole:` pattern - document-project always uses sharded structure

### 2. The Discovery Protocol (`workflow.xml`)

The `discover_inputs` protocol in `src/core/tasks/workflow.xml` handles automatic content loading:

**Step 1: Parse Input File Patterns**
- Reads `input_file_patterns` from workflow.yaml
- Identifies load strategies for each pattern

**Step 2: Smart File Loading**
- **First:** Tries whole document pattern (if exists)
- **Then:** Falls back to sharded pattern
- **Strategy Selection:** Uses specified `load_strategy` or defaults to `FULL_LOAD`

**Step 3: Content Variable Creation**
- Stores loaded content in variables like `{document_project_content}`
- Reports what was loaded (file counts, paths)

---

## Loading Strategies

BMAD supports three loading strategies:

### 1. FULL_LOAD
**Use Case:** Load all files in a sharded directory
**Example:** Loading all architecture files

```yaml
load_strategy: "FULL_LOAD"
```

**Behavior:**
- Finds ALL `.md` files matching the pattern
- Loads every file completely
- Concatenates in logical order (index.md first, then alphabetical)
- Stores in `{pattern_name_content}` variable

### 2. SELECTIVE_LOAD
**Use Case:** Load specific shard using template variables
**Example:** Loading only epic-3.md for a specific epic

```yaml
load_strategy: "SELECTIVE_LOAD"
sharded_single: "{output_folder}/*epic*/epic-{{epic_num}}.md"
```

**Behavior:**
- Resolves template variables (e.g., `{{epic_num}}`)
- Loads only the specific file
- Stores in `{pattern_name_content}` variable

### 3. INDEX_GUIDED (Used for document-project)
**Use Case:** Intelligent loading based on index.md structure
**Example:** Loading document-project documentation

```yaml
load_strategy: "INDEX_GUIDED"
sharded: "{output_folder}/index.md"
```

**Behavior:**
1. **Loads `index.md`** from the sharded directory
2. **Parses structure:**
   - Table of contents
   - Links to other documents
   - Section headers
   - Document descriptions
3. **Analyzes workflow purpose:**
   - Understands what the workflow is trying to do
   - Identifies which documents are relevant
4. **Intelligently loads relevant docs:**
   - Example: If workflow is about authentication and index shows "Auth Overview", "Payment Setup", "Deployment"
     → Loads auth docs, considers deployment docs, skips payment
5. **Stores combined content** in `{document_project_content}` variable

**Key Principle:** "When in doubt, LOAD IT - context is valuable, being thorough is better than missing critical info"

---

## How INDEX_GUIDED Works for Document-Project

### The Index.md Structure

`document-project` generates `index.md` with:
- **Project Overview** - High-level summary
- **Quick Reference** - Tech stack, entry points, architecture patterns
- **Generated Documentation** - Links to all generated docs:
  - `project-overview.md`
  - `architecture.md`
  - `source-tree-analysis.md`
  - `component-inventory.md`
  - `development-guide.md`
  - `api-contracts.md` (conditional)
  - `data-models.md` (conditional)
  - `deep-dive-{area}.md` (if deep-dives exist)
- **For AI-Assisted Development** section - Guidance on which docs to reference for different feature types

### INDEX_GUIDED Loading Process

When a workflow requests `document_project` content:

1. **Loads `index.md`** from `{output_folder}/index.md`
2. **Analyzes the index structure:**
   - Reads all document links
   - Understands document purposes from descriptions
   - Notes the "For AI-Assisted Development" guidance section
3. **Determines relevance based on workflow:**
   - **PRD workflow:** Needs architecture, tech stack, existing patterns → Loads architecture.md, project-overview.md
   - **Story context workflow:** Needs specific area details → Loads relevant architecture sections, component inventory
   - **Code review workflow:** Needs full context → Loads all architecture and component docs
4. **Loads identified documents:**
   - Reads the actual content from linked files
   - Combines into single content variable
5. **Stores in `{document_project_content}`:**
   - All loaded documentation is concatenated
   - Available as a single context variable

---

## Workflow Integration Examples

### Example 1: PRD Workflow

**Configuration (`prd/workflow.yaml`):**
```yaml
input_file_patterns:
  document_project:
    description: "Brownfield project documentation (optional)"
    sharded: "{output_folder}/index.md"
    load_strategy: "INDEX_GUIDED"
```

**Usage (`prd/instructions.md`):**
```xml
<step n="0.5" goal="Discover and load input documents">
  <invoke-protocol name="discover_inputs" />
  <note>After discovery, these content variables are available: 
    {product_brief_content}, {research_content}, {document_project_content}
  </note>
</step>

<step n="1" goal="Discovery - Project, Domain, and Vision">
  <action>Review loaded content: 
    {product_brief_content}, {research_content}, 
    {document_project_content} (auto-loaded in Step 0.5)
  </action>
</action>
```

**What Happens:**
1. Workflow invokes `discover_inputs` protocol
2. Protocol finds `{output_folder}/index.md`
3. INDEX_GUIDED strategy loads index.md and analyzes it
4. Determines PRD needs: architecture, tech stack, existing patterns
5. Loads: `index.md`, `project-overview.md`, `architecture.md`, `source-tree-analysis.md`
6. Combines into `{document_project_content}`
7. AI assistant can now reference `{document_project_content}` throughout the workflow

### Example 2: Story Context Workflow

**Configuration (`story-context/workflow.yaml`):**
```yaml
input_file_patterns:
  document_project:
    sharded: "{output_folder}/index.md"
    load_strategy: "INDEX_GUIDED"
```

**Usage (`story-context/instructions.md`):**
```xml
<step n="1.5" goal="Discover and load project documents">
  <invoke-protocol name="discover_inputs" />
  <note>After discovery, these content variables are available: 
    {prd_content}, {tech_spec_content}, {architecture_content}, 
    {ux_design_content}, {epics_content}, {document_project_content}
  </note>
</step>

<step n="2" goal="Collect relevant documentation">
  <action>Extract relevant sections from: 
    {prd_content}, {tech_spec_content}, {architecture_content}, 
    {ux_design_content}, {document_project_content}
  </action>
</step>
```

**What Happens:**
1. Story context workflow needs to understand existing codebase
2. INDEX_GUIDED loads index.md
3. Analyzes story domain/keywords
4. Loads relevant architecture sections, component inventory, API contracts
5. AI assistant uses `{document_project_content}` to understand:
   - Existing components to reuse
   - API patterns to follow
   - Architecture constraints
   - Integration points

### Example 3: Code Review Workflow

**Configuration (`code-review/workflow.yaml`):**
```yaml
input_file_patterns:
  document_project:
    sharded: "{output_folder}/index.md"
    load_strategy: "INDEX_GUIDED"
```

**Usage (`code-review/instructions.md`):**
```xml
<step n="1.5" goal="Pre-load architecture and brownfield docs">
  <invoke-protocol name="discover_inputs" />
  <note>Architecture and brownfield docs were pre-loaded in Step 1.5 
    as {architecture_content} and {document_project_content}
  </note>
</step>
```

**What Happens:**
1. Code review needs comprehensive context
2. INDEX_GUIDED loads full documentation set
3. AI assistant uses `{document_project_content}` to:
   - Verify code follows architecture patterns
   - Check component usage matches inventory
   - Validate API contracts
   - Ensure integration patterns are correct

---

## Content Variable Usage in Instructions

Once loaded, workflows use `{document_project_content}` directly in their instructions:

### Direct Reference
```xml
<action>Review {document_project_content} for existing authentication patterns</action>
```

### Extraction
```xml
<action>Extract relevant sections from: 
  {prd_content}, {architecture_content}, {document_project_content}
</action>
```

### Cross-Reference
```xml
<action>Cross-reference story requirements with 
  {document_project_content} to identify reusable components
</action>
```

### Conditional Logic
```xml
<check if="field_type == brownfield OR document-project output found">
  <action>Use {document_project_content} for brownfield analysis</action>
</check>
```

---

## Benefits of This Approach

### 1. **Automatic Context Loading**
- No manual file reading required
- AI assistants get context automatically
- Reduces errors from missing context

### 2. **Intelligent Loading**
- INDEX_GUIDED only loads relevant docs
- Prevents context exhaustion
- Optimizes token usage

### 3. **Consistent Interface**
- All workflows use same `{document_project_content}` variable
- Standardized access pattern
- Easy to understand and maintain

### 4. **Flexible Strategy**
- Different workflows can use different strategies
- FULL_LOAD for comprehensive needs
- INDEX_GUIDED for intelligent loading
- SELECTIVE_LOAD for specific files

### 5. **Workflow Transparency**
- Discovery protocol reports what was loaded
- Example: "✓ Loaded {document_project_content} from 5 files: index.md, architecture.md, ..."
- AI assistants know what context they have

---

## The Index.md as AI Entry Point

The `index.md` file serves as the **master AI entry point**:

### Structure Optimized for AI

1. **Quick Reference Section:**
   - Tech stack summary
   - Entry points
   - Architecture patterns
   - Database info
   - Deployment platform

2. **Documentation Links:**
   - Clear descriptions of each document
   - Purpose of each file
   - When to reference each doc

3. **AI-Assisted Development Guidance:**
   - "For AI-Assisted Development" section
   - Guidance on which docs to reference for:
     - UI-only features
     - API/Backend features
     - Full-stack features
     - Deployment changes

### Example from index.md:
```markdown
## For AI-Assisted Development

This documentation was generated specifically to enable AI agents 
to understand and extend this codebase.

### When Planning New Features:

**UI-only features:**
→ Reference: `architecture.md`, `component-inventory.md`

**API/Backend features:**
→ Reference: `architecture.md`, `api-contracts.md`, `data-models.md`

**Full-stack features:**
→ Reference: All architecture docs
```

---

## Multi-Part Project Support

For multi-part projects (client/server monorepos):

### Index.md Structure:
```markdown
## Project Structure

This project consists of 2 parts:

### Client (client)
- **Type:** web/React
- **Location:** `client/`
- **Tech Stack:** React, TypeScript, Vite

### Server (server)
- **Type:** backend/Express
- **Location:** `server/`
- **Tech Stack:** Node.js, Express, PostgreSQL
```

### INDEX_GUIDED Loading:
- Loads `index.md` with part structure
- Identifies which parts are relevant to workflow
- Loads part-specific documentation:
  - `architecture-client.md`
  - `architecture-server.md`
  - `component-inventory-client.md`
  - `api-contracts-server.md`
- Includes `integration-architecture.md` for cross-part communication

---

## Comparison with Direct File Reading

### Without Discovery Protocol (Manual):
```xml
<action>Read {output_folder}/index.md</action>
<action>Read {output_folder}/architecture.md</action>
<action>Read {output_folder}/component-inventory.md</action>
<action>Combine into context</action>
```

**Problems:**
- Manual file management
- No intelligent selection
- Risk of missing files
- No sharding support
- Context exhaustion risk

### With Discovery Protocol (Automatic):
```xml
<step n="0.5" goal="Discover and load input documents">
  <invoke-protocol name="discover_inputs" />
</step>

<step n="1" goal="Use context">
  <action>Review {document_project_content}</action>
</step>
```

**Benefits:**
- Automatic discovery
- Intelligent loading
- Sharding support
- Context management
- Consistent interface

---

## Technical Implementation Details

### Protocol Execution Flow

1. **Workflow starts** → Loads `workflow.yaml`
2. **Finds `input_file_patterns`** → Parses patterns
3. **Invokes `discover_inputs` protocol** → Executes discovery
4. **For each pattern:**
   - Tries whole document pattern
   - Falls back to sharded pattern
   - Applies load strategy
   - Loads files
   - Creates content variable
5. **Reports results** → Lists loaded files
6. **Makes variables available** → `{document_project_content}` ready

### Content Variable Format

The `{document_project_content}` variable contains:
- **Concatenated Markdown content** from all loaded files
- **File separators** (if multiple files loaded)
- **Complete documentation** ready for AI consumption

### Error Handling

- **File not found:** Sets variable to empty string, notes in session
- **Sharded directory empty:** Reports no files found
- **Index.md missing:** Falls back gracefully, reports issue

---

## Best Practices

### For Workflow Authors:

1. **Always use INDEX_GUIDED for document-project:**
   ```yaml
   document_project:
     sharded: "{output_folder}/index.md"
     load_strategy: "INDEX_GUIDED"
   ```

2. **Invoke discovery early:**
   ```xml
   <step n="0.5" goal="Discover and load input documents">
     <invoke-protocol name="discover_inputs" />
   </step>
   ```

3. **Document available variables:**
   ```xml
   <note>After discovery, these content variables are available: 
     {document_project_content}
   </note>
   ```

4. **Use content variables in instructions:**
   ```xml
   <action>Review {document_project_content} for existing patterns</action>
   ```

### For Document-Project Output:

1. **Always generate `index.md`** - Required for INDEX_GUIDED
2. **Structure index.md clearly** - Helps intelligent loading
3. **Include AI guidance** - "For AI-Assisted Development" section
4. **Link all documents** - INDEX_GUIDED follows links
5. **Use descriptive names** - Helps relevance detection

---

## Summary

BMAD-METHOD makes `document-project` documentation accessible to AI coding assistants through:

1. **Workflow Configuration:** Declares documentation needs in `input_file_patterns`
2. **Discovery Protocol:** Automatically loads files using smart strategies
3. **INDEX_GUIDED Strategy:** Intelligently loads relevant docs based on index.md
4. **Content Variables:** Makes loaded content available as `{document_project_content}`
5. **Workflow Integration:** Workflows reference variables directly in instructions

**Key Innovation:** The INDEX_GUIDED strategy transforms `index.md` from a simple table of contents into an **intelligent AI entry point** that enables context-aware documentation loading, preventing context exhaustion while ensuring AI assistants have the information they need.

This system ensures that AI coding assistants always have access to comprehensive project context without manual file management, making brownfield development significantly more efficient and accurate.
