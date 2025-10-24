# Spec-Driven Development: sdd-next Package

Complete documentation for the `sdd-next` skill - task preparation for spec-driven workflows.

## 📦 Package Contents

This skill package includes:

- **[SKILL.md](./SKILL.md)** - Complete skill documentation (main reference)
- **[quick-start.md](./references/quick-start.md)** - Get started in 5 minutes
- **[examples.md](./references/examples.md)** - Real-world usage examples
- **[patterns.md](./references/patterns.md)** - Best practices and anti-patterns
- **README.md** - This file (overview and navigation)

## 🎯 What This Skill Does

The **sdd-next** skill bridges specifications to implementation by:

1. **Finding next tasks** - Identifies what to work on based on dependencies and progress
2. **Gathering context** - Collects all relevant information before coding
3. **Creating execution plans** - Generates detailed, step-by-step implementation guides
4. **Managing workflow** - Coordinates the "what's next" development cycle

**Core Philosophy:** Context-driven execution - every task implementation begins with full understanding of the spec's intent, the task's role in the larger plan, and all relevant codebase context. This prevents scope creep and ensures clean integration.

## 🔧 How It Fits In

### Complete Skill Ecosystem

```
┌─────────────────────────────────────────┐
│ sdd-plan                 │
│ Creates specifications and task lists   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ sdd-next      ← THIS   │
│ Finds tasks and creates execution plans │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ sdd-update                 │
│ Tracks progress and updates status      │
└─────────────────────────────────────────┘
```

### Typical Workflow

1. **Plan** (sdd-plan) → Create specification with phases and tasks
2. **Execute** (sdd-next) → Find next task, create execution plan
3. **Track** (sdd-update) → Mark complete, update progress
4. **Repeat** → Back to step 2 until spec complete

## 🚀 Quick Start

### First Time Using This Skill?

1. **Read**: [quick-start.md](./references/quick-start.md) (5 minutes)
2. **Try**: "What's next?" command on your spec
3. **Practice**: Create a plan for the recommended task
4. **Refer**: [examples.md](./references/examples.md) for common scenarios

### Already Familiar?

Jump to:
- [Complete Documentation](./SKILL.md) - Deep dive into all features
- [Patterns Guide](./references/patterns.md) - Best practices and pitfalls
- [Examples](./references/examples.md) - Real-world usage scenarios

## 📚 Documentation Guide

### For Different User Types

#### 👤 New to Spec-Driven Development
**Start here:**
1. Read the overview in this README
2. Follow [quick-start.md](./references/quick-start.md)
3. Try on a simple spec
4. Reference [patterns.md](./references/patterns.md) for dos/don'ts

#### 👥 Experienced with Specs, New to sdd-next
**Start here:**
1. Skim [quick-start.md](./references/quick-start.md) for syntax
2. Review [examples.md](./references/examples.md) for workflows
3. Use [SKILL.md](./SKILL.md) as reference

#### 🔧 Power User / Skill Developer
**Start here:**
1. Read [SKILL.md](./SKILL.md) completely
2. Study [patterns.md](./references/patterns.md) for edge cases
3. Examine [examples.md](./references/examples.md) for implementation details
4. Adapt patterns to your workflow

### By Task Type

#### "I need to start implementing a spec"
→ [Quick Start - Basic Usage](./references/quick-start.md#basic-usage)

#### "I'm blocked and need alternatives"
→ [Examples - Handling Blocked Tasks](./references/examples.md#example-3-handling-blocked-task)

#### "Multiple people working on same spec"
→ [Examples - Cross-Phase Work](./references/examples.md#example-4-cross-phase-work)

#### "Returning after break"
→ [Examples - Resuming After Break](./references/examples.md#example-5-resuming-after-break)

#### "What's the best way to work?"
→ [Patterns - Effective Patterns](./references/patterns.md#effective-patterns)

#### "What mistakes should I avoid?"
→ [Patterns - Anti-Patterns](./references/patterns.md#anti-patterns)

## 💡 Core Concepts

### 1. Task Identification
The skill analyzes specifications and JSON spec files to identify:
- **Next logical task** - Follows spec order
- **Available tasks** - Not blocked by dependencies
- **Parallel-safe tasks** - Can work on anytime
- **Blocked tasks** - What's waiting and why

### 2. Context Gathering
Before creating a plan, the skill gathers:
- **Spec details** - What the task should accomplish
- **Dependencies** - What files/tasks this relies on
- **Integration points** - How this connects to other code
- **Patterns** - Existing conventions to follow
- **Risks** - Potential issues to watch for

### 3. Execution Planning
Plans include:
- **Step-by-step instructions** - Clear, ordered actions
- **Code examples** - Show what to implement
- **Time estimates** - Realistic duration per step
- **Testing strategy** - How to verify correctness
- **Success criteria** - Definition of "done"

### 4. Workflow Management
The skill manages:
- **Status tracking** - Marks tasks in_progress
- **Progress awareness** - Shows overall completion
- **Team coordination** - Prevents duplicate work
- **Deviation handling** - Documents changes from plan

## 🎨 Usage Patterns

### Pattern 1: Sequential Development
```
┌─────────────────────┐
│ What's next?        │
├─────────────────────┤
│ Create plan         │
├─────────────────────┤
│ Approve & start     │
├─────────────────────┤
│ Implement code      │
├─────────────────────┤
│ Mark complete       │
└─────────────────────┘
        ↓ Repeat
```

### Pattern 2: Exploratory Development
```
┌─────────────────────┐
│ What's next?        │
├─────────────────────┤
│ Tell me more        │
├─────────────────────┤
│ How does this fit?  │
├─────────────────────┤
│ What are risks?     │
├─────────────────────┤
│ Create plan         │
├─────────────────────┤
│ Implement           │
└─────────────────────┘
```

### Pattern 3: Blocked Adaptation
```
┌─────────────────────┐
│ What's next?        │
├─────────────────────┤
│ [Task is blocked]   │
├─────────────────────┤
│ Show alternatives   │
├─────────────────────┤
│ Pick alternative    │
├─────────────────────┤
│ Create plan         │
└─────────────────────┘
```

## 🛠️ Common Commands

### Discovery
- `"What's next?"` - Find recommended task
- `"Show me progress"` - Overall status
- `"What else can I work on?"` - See alternatives
- `"Show me all active specs"` - List all specs

### Planning
- `"Create a plan for task-X-Y"` - Detailed execution plan
- `"Tell me about task-X-Y"` - Get task context
- `"How does this fit in?"` - Architecture explanation
- `"What are the dependencies?"` - Dependency analysis

### Execution
- `"Looks good, let's start"` - Approve plan, mark in_progress
- `"Show me more about step X"` - Deep dive into step
- `"Change step Y to use Z"` - Adjust plan before starting

### Coordination
- `"What is Alice working on?"` - Check team status
- `"Can I work on X while Bob does Y?"` - Parallel feasibility
- `"Mark task complete"` - Update status (uses sdd-update)

## ⚙️ Configuration

### Prerequisites

**System Requirements:**
- **Python 3** - Required for all task operations (JSON parsing, JSON spec file queries)
- **sdd-next-tools.py** - Included in `scripts/` subdirectory

**Project Requirements:**
- Specification created by `sdd-plan`
- Files in `specs/active/` directory
- JSON spec file in `specs/active/` directory
- Understanding of project structure

### File Locations
```
project/
├── specs/
│   ├── active/
│   │   └── feature-id.json   ← JSON spec file
│   ├── completed/
│   └── archived/
├── src/
│   └── [your code]
└── tests/
    └── [your tests]
```

### Integration Points
- **Reads**: Specifications, JSON spec files, source code
- **Writes**: Nothing directly (uses sdd-update for state updates)
- **Coordinates**: With sdd-update for status changes

### Required Tools

**Python Script: sdd-next-tools.py**

This skill uses `scripts/sdd-next-tools.py` for all JSON parsing and task management operations.

**Key Commands:**
```bash
# Task discovery
python3 sdd-next-tools.py next-task <spec-id>
python3 sdd-next-tools.py task-info <spec-id> <task-id>
python3 sdd-next-tools.py progress <spec-id>

# Spec extraction
python3 sdd-next-tools.py frontmatter <spec-file>
python3 sdd-next-tools.py extract-task <spec-file> <task-id>

# Project analysis
python3 sdd-next-tools.py detect-project
python3 sdd-next-tools.py find-tests
```

**Verify Installation:**
```bash
python3 scripts/sdd-next-tools.py verify-tools
```

**Why Python?** JSON JSON spec files require reliable parsing. Python 3 is standard on most systems and provides built-in JSON support with no external dependencies.

For complete command reference, see [SKILL.md - Required Tools](./SKILL.md#required-tools).

## 📊 Success Metrics

### You're Using It Well If:
- ✅ Clear understanding of next task before starting
- ✅ Detailed plans created before coding
- ✅ Progress tracked accurately in JSON spec file
- ✅ Rare surprises during implementation
- ✅ Team coordination smooth (if applicable)
- ✅ Can resume work easily after breaks

### Red Flags:
- ❌ Frequently hitting unexpected blockers
- ❌ Reworking code after initial implementation
- ❌ JSON spec file out of sync with reality
- ❌ Unclear what to work on next
- ❌ Team members duplicating work

## 🔍 Troubleshooting

### Issue: Can't find specifications
**Solution:** Check `specs/active/` directory exists and contains `.md` files

### Issue: Recommended task doesn't feel right
**Solution:** Ask "What else can I work on?" for alternatives

### Issue: Plan too vague
**Solution:** Request more details: "Show me code examples for step X"

### Issue: Dependencies unclear
**Solution:** Ask: "What files does this depend on?"

### Issue: JSON spec file out of sync
**Solution:** Use sdd-update to update status

**More troubleshooting:** See [SKILL.md - Troubleshooting](./SKILL.md#troubleshooting)

## 🎓 Learning Path

### Week 1: Basics
1. ✅ Read quick-start guide
2. ✅ Use skill to find next task
3. ✅ Create first execution plan
4. ✅ Complete one task following plan

### Week 2: Patterns
1. ✅ Study effective patterns
2. ✅ Recognize anti-patterns in own work
3. ✅ Practice adaptive task selection
4. ✅ Handle first blocker gracefully

### Week 3: Advanced
1. ✅ Coordinate with team members
2. ✅ Work on parallel-safe tasks
3. ✅ Document deviations properly
4. ✅ Resume work smoothly after breaks

### Mastery
1. ✅ Create custom workflows
2. ✅ Mentor others on skill usage
3. ✅ Identify when NOT to use skill
4. ✅ Contribute patterns back to team

## 📖 Related Documentation

### This Skill Package
- **[SKILL.md](./SKILL.md)** - Complete reference
- **[quick-start.md](./references/quick-start.md)** - Fast onboarding
- **[examples.md](./references/examples.md)** - Real scenarios
- **[patterns.md](./references/patterns.md)** - Best practices

### Other Skills
- **sdd-plan** - Creates specifications
- **sdd-update** - Tracks progress

### External Resources
- Spec-Driven Development methodology
- Task dependency management
- Team coordination patterns

## 🤝 Contributing

### Found a Useful Pattern?
Document it and share with team:
1. Describe the pattern
2. Explain why it works
3. Show example usage
4. Note when to use it

### Discovered an Anti-Pattern?
Help others avoid it:
1. Describe what went wrong
2. Explain why it fails
3. Show better approach
4. Add to patterns.md

### Have Questions?
- Check [examples.md](./references/examples.md) for similar scenarios
- Review [patterns.md](./references/patterns.md) for guidance
- Consult [SKILL.md](./SKILL.md) for details

## 📝 Version History

**v1.0** (2025-10-18)
- Initial release
- Core task identification
- Execution plan generation
- Context gathering
- Complete documentation package

## 🔗 Quick Links

| Need | Document | Section |
|------|----------|---------|
| Get started fast | [quick-start.md](./references/quick-start.md) | Basic Usage |
| Understand features | [SKILL.md](./SKILL.md) | Core Philosophy |
| See real examples | [examples.md](./references/examples.md) | All examples |
| Learn best practices | [patterns.md](./references/patterns.md) | Effective Patterns |
| Avoid mistakes | [patterns.md](./references/patterns.md) | Anti-Patterns |
| Troubleshoot issues | [SKILL.md](./SKILL.md) | Troubleshooting |

## 💬 Common Questions

**Q: When should I use this skill?**  
A: When you have a spec and need to know what to implement next.

**Q: Can I use it without the sdd-plan?**  
A: No, you need a spec created by the sdd-plan first.

**Q: What if I want to work on a specific task?**  
A: Just say "Create a plan for task-X-Y" instead of asking "What's next?"

**Q: Does it work with multiple developers?**  
A: Yes! It uses the JSON spec file to coordinate and prevent duplicate work.

**Q: Can I customize the execution plans?**  
A: Yes, request changes before approving: "Change step 3 to use async/await"

**Q: What if the recommended task is blocked?**  
A: It will suggest alternatives you can work on instead.

## 🎯 Next Steps

1. **New User?** → Start with [quick-start.md](./references/quick-start.md)
2. **Want Examples?** → Read [examples.md](./references/examples.md)
3. **Need Details?** → Reference [SKILL.md](./SKILL.md)
4. **Improve Skills?** → Study [patterns.md](./references/patterns.md)

---

**Remember:** This skill is designed to make spec-driven development smooth and efficient. Use it to bridge the gap between planning and implementation, and you'll write better code faster.

Happy developing! 🚀
