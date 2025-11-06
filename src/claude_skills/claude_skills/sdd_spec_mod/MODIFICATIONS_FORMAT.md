# SDD Spec Modifications File Format

This document describes the JSON format for batch modification files used with the `apply_modifications()` function.

## Overview

Modification files contain an array of operations that are applied sequentially to an SDD specification. Each operation is self-contained and can succeed or fail independently.

## File Structure

```json
{
  "modifications": [
    { "operation": "...", /* operation-specific fields */ },
    { "operation": "...", /* operation-specific fields */ },
    ...
  ]
}
```

## Supported Operations

### 1. add_node

Add a new task, phase, or other node to the spec hierarchy.

**Required fields:**
- `operation`: Must be `"add_node"`
- `parent_id`: ID of the parent node
- `node_data`: Object containing node information
  - `node_id`: Unique identifier for the new node
  - `type`: One of `"phase"`, `"task"`, `"subtask"`, `"verify"`, `"group"`
  - `title`: Non-empty human-readable title

**Optional fields:**
- `node_data.description`: Detailed description (default: `""`)
- `node_data.status`: Initial status - `"pending"`, `"in_progress"`, `"completed"`, or `"blocked"` (default: `"pending"`)
- `node_data.metadata`: Additional metadata object (default: `{}`)
- `node_data.dependencies`: Dependency lists with `blocks`, `blocked_by`, `depends` arrays (default: empty arrays)
- `position`: Position in parent's children list, 0-indexed (default: append to end)

**Example:**
```json
{
  "operation": "add_node",
  "parent_id": "phase-2",
  "node_data": {
    "node_id": "task-2-5",
    "type": "task",
    "title": "Implement caching layer",
    "description": "Add Redis-based caching for API responses",
    "status": "pending",
    "metadata": {
      "estimated_hours": 4,
      "priority": "high"
    },
    "dependencies": {
      "blocks": [],
      "blocked_by": ["task-2-3"],
      "depends": ["task-2-3"]
    }
  },
  "position": 2
}
```

### 2. remove_node

Remove a node from the spec hierarchy.

**Required fields:**
- `operation`: Must be `"remove_node"`
- `node_id`: ID of the node to remove

**Optional fields:**
- `cascade`: Boolean. If `true`, recursively removes all descendants. If `false` and node has children, operation fails. (default: `false`)

**Example:**
```json
{
  "operation": "remove_node",
  "node_id": "task-obsolete-1",
  "cascade": true
}
```

### 3. update_node_field

Update a specific field on an existing node.

**Required fields:**
- `operation`: Must be `"update_node_field"`
- `node_id`: ID of the node to update
- `field`: Name of the field to update
- `value`: New value for the field

**Updatable fields:**
- `title`: String (non-empty)
- `description`: String
- `status`: One of `"pending"`, `"in_progress"`, `"completed"`, `"blocked"`
- `type`: One of `"phase"`, `"task"`, `"subtask"`, `"verify"`, `"group"`, `"spec"`
- `metadata`: Object (merged with existing metadata)
- `dependencies`: Object with `blocks`, `blocked_by`, `depends` arrays

**Protected fields** (cannot be updated):
- `parent`
- `children`
- `total_tasks`
- `completed_tasks`

**Example:**
```json
{
  "operation": "update_node_field",
  "node_id": "task-1-3",
  "field": "description",
  "value": "Updated description with more detail about implementation approach"
}
```

**Metadata update example:**
```json
{
  "operation": "update_node_field",
  "node_id": "task-2-1",
  "field": "metadata",
  "value": {
    "estimated_hours": 6,
    "actual_hours": 4.5,
    "complexity": "medium"
  }
}
```

### 4. move_node

Move a node to a different parent in the hierarchy.

**Required fields:**
- `operation`: Must be `"move_node"`
- `node_id`: ID of the node to move
- `new_parent_id`: ID of the new parent node

**Optional fields:**
- `position`: Position in new parent's children list, 0-indexed (default: append to end)

**Example:**
```json
{
  "operation": "move_node",
  "node_id": "task-1-5",
  "new_parent_id": "phase-2",
  "position": 0
}
```

## Complete Example

Here's a complete modifications file demonstrating all operation types:

```json
{
  "modifications": [
    {
      "operation": "add_node",
      "parent_id": "phase-1",
      "node_data": {
        "node_id": "task-1-6",
        "type": "task",
        "title": "Write integration tests",
        "description": "Add integration tests for authentication flow",
        "status": "pending",
        "metadata": {
          "estimated_hours": 3
        }
      }
    },
    {
      "operation": "update_node_field",
      "node_id": "task-1-2",
      "field": "status",
      "value": "in_progress"
    },
    {
      "operation": "move_node",
      "node_id": "task-2-7",
      "new_parent_id": "phase-3",
      "position": 1
    },
    {
      "operation": "remove_node",
      "node_id": "task-deprecated",
      "cascade": false
    },
    {
      "operation": "update_node_field",
      "node_id": "phase-2",
      "field": "title",
      "value": "Phase 2: Enhanced Implementation"
    }
  ]
}
```

## Return Value

The `apply_modifications()` function returns a detailed result object:

```json
{
  "success": true,
  "message": "Applied 5/5 modifications successfully",
  "total_operations": 5,
  "successful": 5,
  "failed": 0,
  "results": [
    {
      "operation": { /* original operation object */ },
      "success": true,
      "message": "Successfully added node 'task-1-6' as child of 'phase-1'",
      "node_id": "task-1-6"
    },
    {
      "operation": { /* original operation object */ },
      "success": true,
      "message": "Successfully updated field 'status' for node 'task-1-2'",
      "old_value": "pending"
    },
    ...
  ]
}
```

## Error Handling

### File-level Errors

These errors prevent any modifications from being applied:

- **FileNotFoundError**: Modifications file doesn't exist
- **JSONDecodeError**: File contains invalid JSON
- **ValueError**: File structure is invalid (missing `modifications` key, etc.)

### Operation-level Errors

These errors affect only the specific operation:

- Missing required fields
- Invalid field values (e.g., invalid status, empty title)
- Non-existent node IDs
- Protected field updates
- Circular dependencies (for move operations)
- Node has children (for remove without cascade)

When an operation fails, previous successful operations are kept, but remaining operations are still attempted.

## Best Practices

1. **Order matters**: Operations are applied sequentially. If task-2 depends on task-1 being added first, ensure task-1 is earlier in the modifications array.

2. **Use unique node IDs**: When adding nodes, ensure `node_id` doesn't already exist in the spec.

3. **Validate before applying**: Consider validating the spec after applying modifications to ensure integrity.

4. **Handle failures gracefully**: Check the `results` array to identify which operations failed and why.

5. **Backup specs**: Create a revision before applying bulk modifications:
   ```python
   from claude_skills.sdd_spec_mod import create_revision, apply_modifications

   # Create revision first
   create_revision(spec_data, "Before bulk modifications")

   # Then apply modifications
   result = apply_modifications(spec_data, "modifications.json")
   ```

6. **Test with small batches**: When creating complex modifications, test with a subset first to ensure the format is correct.

## Schema Validation

A JSON Schema file is available at `modifications_schema.json` for validating modification files. Use it with any JSON schema validator to catch errors before applying modifications.

## See Also

- `modification.py` - Implementation of modification operations
- `modifications_schema.json` - JSON Schema for validation
- `revision.py` - Revision tracking and rollback functionality
