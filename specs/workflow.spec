# Development Workflow Specification
# Version: 1.0.0
# Date: 2025-11-05

## Git Branching Strategy

### Branch Structure
```
main (production-ready)
├── development (active development)
│   ├── feature/ml-pipeline
│   ├── feature/api-endpoints
│   └── feature/frontend-dashboard
└── hotfix/* (emergency fixes)
```

### Branching Rules

1. **Main Branch**
   - Protected branch - no direct commits
   - Only accepts merges from development
   - Always deployable
   - Tagged for releases (v1.0.0, v1.1.0, etc.)

2. **Development Branch**
   - Primary working branch
   - All features merge here first
   - Tested before merging to main
   - CI/CD runs on this branch

3. **Feature Branches**
   - Branch from: development
   - Merge to: development
   - Naming: feature/description
   - Delete after merge

4. **Hotfix Branches**
   - Branch from: main
   - Merge to: main AND development
   - Naming: hotfix/issue-description
   - For critical production fixes only

## Commit Message Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding tests
- **chore**: Maintenance tasks

### Examples
```
feat(api): add image upload endpoint

- Support multiple file uploads
- Validate image formats
- Add location selection
- Queue for ML processing

Refs: specs/api.spec
```

## Push Strategy

### Multiple Remotes
```bash
# Production server
git remote add ubuntu ssh://user@10.0.6.206/path/to/repo.git

# Backup server  
git remote add synology ssh://user@10.0.4.82/path/to/repo.git

# Push to all remotes
git push ubuntu development
git push synology development
```

### Automated Push Script
```bash
#!/bin/bash
# push-all.sh
for remote in ubuntu synology; do
    echo "Pushing to $remote..."
    git push $remote development
done
```

## Code Review Process

1. **Before Committing**
   - Run tests: `pytest tests/`
   - Check linting: `ruff check .`
   - Verify specs compliance

2. **Commit Checklist**
   - [ ] Tests pass
   - [ ] Code follows specs
   - [ ] Documentation updated
   - [ ] No sensitive data (API keys, passwords)

3. **Merge Requirements**
   - All tests pass
   - Code review completed
   - Documentation updated
   - No merge conflicts

## Release Process

1. **Version Numbering**
   - MAJOR.MINOR.PATCH (1.0.0)
   - MAJOR: Breaking changes
   - MINOR: New features
   - PATCH: Bug fixes

2. **Release Steps**
   ```bash
   # 1. Merge development to main
   git checkout main
   git merge development
   
   # 2. Tag release
   git tag -a v1.0.0 -m "Release v1.0.0: Initial release"
   
   # 3. Push with tags
   git push ubuntu main --tags
   git push synology main --tags
   ```

## Backup Strategy

### Automatic Backups
- Ubuntu server: Primary development
- Synology NAS: Backup and archive
- Both updated with every push

### Recovery
```bash
# If primary fails, pull from backup
git remote add backup ssh://user@10.0.4.82/path/to/repo.git
git fetch backup
git checkout -b recovery backup/development
```

---

**Specification Status**: ACTIVE
**Next Review**: After first release
**Compliance**: Required for all commits
