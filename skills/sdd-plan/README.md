# Spec-Driven Development Skill

A comprehensive skill for Claude that implements plan-first, verify-always development methodology.

## What is Spec-Driven Development?

Spec-Driven Development is a methodology that prioritizes creating detailed specifications before writing code. This approach:

- **Reduces drift**: Prevents AI from hallucinating APIs or misunderstanding requirements
- **Increases confidence**: Every change is planned, verified, and documented
- **Enables iteration**: Clear specifications make it easy to refine and adjust
- **Improves collaboration**: Specifications serve as contracts between team members
- **Catches issues early**: Problems surface during planning, not deployment

## How It Works

```
1. Understand Intent → What are we trying to accomplish?
2. Explore Codebase → What already exists? What patterns should we follow?
3. Create Specification → Detailed plan with phases, files, and verification
4. Review & Refine → Collaborate on the spec before implementing
5. Implement Phase-by-Phase → Execute against the plan systematically
6. Verify Each Phase → Test thoroughly at every step
7. Iterate if Needed → Update spec and re-verify if issues arise
```

## When to Use This Skill

✅ **Use Spec-Driven Development for:**
- New features or significant functionality additions
- Complex refactoring across multiple files
- API integrations or external service connections
- Architecture changes or system redesigns
- Large codebases where context drift is a risk
- Any task where precision and reliability are critical

❌ **Don't use for:**
- Simple one-file changes
- Trivial bug fixes
- Formatting or style changes only
- Quick prototypes or proof-of-concepts
- Exploratory code

## What's Included

### Core Documentation
- **SKILL.md** - Complete methodology guide for Claude
- **LICENSE.txt** - MIT license

### Reference Materials
- **examples.md** - Detailed real-world specification examples
  - REST API endpoint addition
  - Database schema migration
  - UI component refactoring
- **anti-patterns.md** - Common mistakes and how to avoid them
- **quick-reference.md** - One-page cheat sheet

### Tooling
- **sdd-validate** - Standalone validator, report generator, and auto-fix utility for JSON specs
- **sdd-next / sdd-update** - Companion skills for execution planning and progress tracking
- **code-doc (optional parsers)** - Multi-language source parsing that relies on [tree-sitter](https://tree-sitter.github.io/tree-sitter/) bindings. Install the language packages you need (for example `pip install tree-sitter tree-sitter-javascript tree-sitter-typescript tree-sitter-go tree-sitter-html tree-sitter-css`). Modules fall back gracefully when bindings are absent.

### Assets
- **spec-template.md** - Ready-to-use specification template (use as a scratch pad before producing JSON)

## Quick Start

### Using with Claude

1. **Install the skill** in Claude (upload the skill folder)

2. **Trigger the skill** by asking Claude to help with development tasks:
   ```
   "Help me build a new user authentication system using spec-driven development"
   "I need to refactor our payment processing - create a specification first"
   "Let's add a new API endpoint for activity logs"
   ```

3. **Claude will:**
   - Explore your codebase to understand existing patterns
   - Create a detailed specification with phases
   - Present the spec for your review
   - Implement phase-by-phase with verification
   - Generate verification reports

### Working Locally

**Author the JSON spec manually (recommended):**
```bash
# Create initial skeleton (example)
cat <<'JSON' > specs/active/my-feature.json
{
  "spec_id": "my-feature-2025-10-22-001",
  "generated": "2025-10-22T10:00:00Z",
  "last_updated": "2025-10-22T10:00:00Z",
  "hierarchy": {}
}
JSON
```

**Use the markdown template as a scratch pad if helpful:**
```bash
cp assets/spec-template.md notes/my-feature.md
# Draft details here, then translate into JSON
```

**Validate specification quality with sdd-validate:**
```bash
# Validate JSON spec file (single source of truth)
sdd-validate validate specs/active/my-feature.json

# Generate stakeholder-friendly report
sdd-validate report specs/active/my-feature.json --output specs/reports/my-feature.md

# Preview fixes without modifying the file
sdd-validate fix specs/active/my-feature.json --preview
```

## Example Workflow

### 1. Request a Feature
```
You: "I need to add pagination to our user list API endpoint"
```

### 2. Claude Explores and Specifies
Claude will:
- Explore your codebase for existing patterns
- Identify files that need modification
- Create a phased specification
- Present it for review

### 3. Review the Specification
```
You: "Looks good, but can we add filtering by user status too?"
```

Claude updates the specification to include filtering.

### 4. Implementation
Claude implements phase-by-phase:
- Phase 1: Database query layer
- Phase 2: Service layer logic
- Phase 3: API controller and route
- Phase 4: Tests and documentation

After each phase, Claude verifies the changes work correctly.

### 5. Final Verification
Claude generates a comprehensive verification report showing:
- All planned changes completed
- No regressions introduced
- All tests passing
- Ready for deployment

## File Structure

```
sdd-plan/
├── SKILL.md                      # Main skill documentation for Claude
├── LICENSE.txt                   # MIT License
├── references/
│   ├── examples.md              # Real-world examples
│   ├── anti-patterns.md         # What to avoid
│   └── quick-reference.md       # One-page guide
└── assets/
    └── spec-template.md         # Blank template
```

## Key Principles

1. **Plan First, Code Second**: Always create specifications before implementation
2. **File-Level Specificity**: Know exactly which files will be modified and why
3. **Explicit Reasoning**: Every change must have clear justification
4. **Phase-by-Phase Execution**: Complete and verify each phase independently
5. **Comprehensive Verification**: Test everything at every step
6. **Document Deviations**: If implementation diverges from spec, explain why
7. **Stay On Spec**: Only implement what's in the specification
8. **Living Documents**: Update specifications as understanding evolves

## Benefits

### For Developers
- **Confidence**: Know exactly what you're building and why
- **Speed**: Less time debugging, more time building
- **Clarity**: Clear roadmap from intent to implementation
- **Quality**: Built-in verification catches issues early

### For Teams
- **Alignment**: Everyone understands the plan
- **Reviewability**: Specifications are easier to review than code diffs
- **Knowledge Sharing**: Specifications serve as documentation
- **Reduced Rework**: Catch misunderstandings before implementation

### For AI-Assisted Development
- **Reduced Hallucinations**: Specifications keep AI grounded
- **Better Context**: Clear plans help AI maintain focus
- **Verifiable Output**: Easy to check if AI implemented correctly
- **Iterative Improvement**: Specifications make refinement straightforward

## Inspired By

This skill implements Spec-Driven Development methodology, which brings engineering discipline to AI-assisted coding through:

- Planning before execution
- Structured, phase-based specifications
- Implementation verification
- Iterative refinement

## Best Practices

### Specification Quality
- Be specific enough that two people would implement identically
- Include examples and code snippets where helpful
- Base specifications on actual codebase exploration
- Document all assumptions and verify them

### Phase Design
- Keep phases to manageable scope (1-2 hours each)
- Ensure each phase is independently testable
- Define clear dependencies between phases
- Include verification steps for each phase

### Verification
- Test both happy paths and edge cases
- Include regression testing
- Document all verification results
- Don't skip verification steps

### Communication
- Share specifications before implementation
- Invite feedback and refinement
- Document decisions and trade-offs
- Keep specifications updated

## Tips for Success

1. **Start Simple**: Begin with smaller features to learn the methodology
2. **Iterate on Specs**: First pass doesn't need to be perfect
3. **Verify Often**: Better to catch issues early than late
4. **Document Learnings**: Note what worked and what didn't
5. **Collaborate**: Specifications benefit from multiple perspectives
6. **Trust the Process**: The upfront planning pays dividends

## Resources

- **Quick Reference**: See `references/quick-reference.md` for a one-page guide
- **Examples**: Check `references/examples.md` for detailed specifications
- **Anti-Patterns**: Read `references/anti-patterns.md` to avoid common mistakes
- **Template**: Use `assets/spec-template.md` to start new specifications

## Contributing

Found a great pattern or improvement? This skill can be extended with:
- Additional examples for different types of projects
- Domain-specific specification templates
- Enhanced verification scripts
- Integration with development tools

## Support

For questions or issues with this skill:
1. Check the quick reference guide
2. Review the examples
3. Read the anti-patterns document
4. Consult Claude using the skill

## License

MIT License - See LICENSE.txt for full details.

---

**Remember**: The best code is code that works correctly the first time. Spec-Driven Development gets you there by planning thoroughly and verifying constantly.

Happy building! 🚀
