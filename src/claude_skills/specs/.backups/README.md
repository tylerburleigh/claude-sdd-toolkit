# Spec Backups Directory

This directory stores backup copies of specification files created before modifications.

## Purpose

The `.backups/` directory is a hidden directory used to store:
- Automatic backups created before spec file modifications
- Safety copies created by `sdd-validate fix` before applying fixes
- Historical snapshots of spec files before updates
- Recovery points for spec file restoration

## Why a Hidden Directory?

This directory is prefixed with a dot (`.`) to indicate it contains tool-generated content that is:
- Not part of the primary specification content
- Generated automatically before modifications
- Should not clutter the main specs directory structure
- Can be safely cleaned up periodically

## Usage

### Automatic Creation

Backups are automatically created when:

```bash
# Before applying validation fixes
sdd validate <spec-file> --fix

# Before any spec file modifications (handled internally)
```

The toolkit automatically creates this directory and README when needed - no manual setup required.

### Backup Naming

Backups follow this naming convention:
```
specs/.backups/
├── README.md                          # This file
├── <spec-id>.backup                   # Default backup
├── <spec-id>.backup2                  # Additional backup with custom suffix
└── <spec-id>-YYYY-MM-DD-HH-MM.backup  # Timestamped backup
```

## Managing Backups

### Cleaning Old Backups

Backups can accumulate over time. To clean old backups:

```bash
# Remove backups older than 30 days
find specs/.backups -name "*.backup*" -mtime +30 -delete

# Or keep only the most recent 5 backups per spec
# (implement custom cleanup script as needed)
```

### Gitignore Consideration

Consider adding this directory to `.gitignore` if you don't want to track backups in version control:

```
# In .gitignore
specs/.backups/
```

Backups are safety nets for local modifications and typically don't need to be shared via version control.

## Restoring from Backup

If you need to restore a spec from backup:

```bash
# Copy backup back to active directory
cp specs/.backups/<spec-id>.backup specs/active/<spec-id>.json

# Or use version control if backups are tracked
git checkout HEAD -- specs/active/<spec-id>.json
```

## Directory Structure

```
specs/.backups/
├── README.md                                    # This file
├── <spec-id>.backup                            # Most recent backup
├── <spec-id>.backup2                           # Additional backup copy
└── <spec-id>-YYYY-MM-DD-HH-MM-SS.backup       # Timestamped backup
```

## Related Tools

- **sdd-validate** - Creates backups before applying fixes
- **sdd-update** - May create backups before updates
- **sdd-plan** - Creates new specs (no backup needed)
- **sdd-next** - Reads specs (no backup created)

## Best Practices

1. **Automatic Safety** - Backups are created automatically, no action needed
2. **Periodic Cleanup** - Clean old backups to save disk space
3. **Version Control** - Use git as primary backup, this is for recent safety
4. **Check Before Delete** - Verify spec is correct before deleting backups
5. **Recovery Window** - Keep at least 7 days of backups for safety

## Notes

- This directory is automatically created by the SDD toolkit
- It centralizes backup files in a dedicated location
- Backups are created before any destructive spec modifications
- Manual backups can also be created using `backup_json_spec()` utility
- Old backups can be safely deleted once you're confident in changes
