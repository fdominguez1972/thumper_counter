# Safe Spec-Kit Installation Guide
**Purpose:** Explore spec-kit without risking current project
**Date:** November 8, 2025

---

## SAFEST APPROACH: Test in Separate Directory First

### Option 1: Test Repository (RECOMMENDED)

```bash
# Create test directory outside project
cd /mnt/i/projects
mkdir thumper_spec_test
cd thumper_spec_test

# Initialize git (spec-kit requires git)
git init

# Install spec-kit locally (won't affect global system)
npm init -y
npm install --save-dev @github/specify

# Run spec-kit init
npx specify init

# Explore what it created
ls -la
tree .specify/
cat .specify/config.yml

# Try creating a test spec
npx specify create system

# Review generated files
ls specs/
cat specs/system.spec
```

**Advantages:**
- Zero risk to main project
- Learn the tool first
- See what files it creates
- Understand the workflow
- Delete when done

**When comfortable, apply to real project.**

---

## Option 2: New Git Branch (SAFE)

```bash
# In your project
cd /mnt/i/projects/thumper_counter

# Create experimental branch
git checkout -b 998-spec-kit-experiment

# Now safe to test spec-kit
npm install --save-dev @github/specify

# Initialize (creates .specify/ and config)
npx specify init

# Review what changed
git status
git diff

# If you like it:
git add .
git commit -m "experiment: Add spec-kit initialization"

# If you don't like it:
git checkout 007-data-quality  # Go back
git branch -D 998-spec-kit-experiment  # Delete branch
```

**Advantages:**
- Test in real project
- Easy to undo (delete branch)
- Can compare before/after
- Safe to experiment

---

## Option 3: Dry-Run Install (SAFEST FOR GLOBAL)

```bash
# Check what would be installed globally
npm install -g @github/specify --dry-run

# If looks good, actually install
npm install -g @github/specify

# Verify installation
specify --version
which specify

# Test with --help (doesn't modify anything)
specify --help
specify init --help
```

**Note:** Global install won't modify your project until you run `specify init`.

---

## What Spec-Kit Init Actually Creates

When you run `specify init`, it creates:

```
your-project/
├── .specify/
│   ├── config.yml          # Configuration file
│   ├── constitution.md     # Project principles (optional)
│   └── memory/             # AI context directory (initially empty)
├── specs/                  # Specifications directory
│   └── (empty initially)
├── .gitignore              # Updated to include .specify/ patterns
└── package.json            # If using npm install (local)
```

**Files it DOES NOT touch:**
- Your existing source code (src/)
- Your existing docs (docs/)
- Your existing configs (docker-compose.yml, etc.)
- Your database or data files

**Safe because:**
- Only creates NEW directories
- Adds to .gitignore (doesn't replace)
- You control when to create specs
- No automatic changes to existing files

---

## Recommended Safe Workflow

### Step 1: Global Install (Minimal Risk)
```bash
# Install CLI globally (doesn't modify project)
npm install -g @github/specify

# Verify it works
specify --version
# Expected: @github/specify version X.X.X
```

### Step 2: Test in Dummy Project
```bash
# Create test project
mkdir /tmp/spec_test
cd /tmp/spec_test
git init

# Initialize spec-kit
specify init

# Explore
ls -la .specify/
cat .specify/config.yml

# Create test spec
specify create test

# See what happens
ls specs/
cat specs/test.spec
```

### Step 3: Read Generated Files
```bash
# Check the config format
cat .specify/config.yml

# Example output:
# version: 1
# project:
#   name: spec_test
#   description: ""
# specs:
#   directory: specs
#   extensions: [.spec, .md]
```

### Step 4: Apply to Real Project (When Ready)
```bash
cd /mnt/i/projects/thumper_counter

# Create safety branch
git checkout -b 998-spec-kit-init

# Run init
specify init

# Review changes
git status
# Expected:
#   new file: .specify/config.yml
#   modified: .gitignore (if exists)

# Check what was added to .gitignore
git diff .gitignore

# If happy with it
git add .specify/ .gitignore
git commit -m "chore: Initialize spec-kit"

# If not happy
git checkout 007-data-quality
git branch -D 998-spec-kit-init
```

---

## What to Check Before Running Init

### 1. Git Status Should Be Clean
```bash
git status
# Should show: "nothing to commit, working tree clean"
```

**Why:** So you can easily see what spec-kit changes.

### 2. Backup Current State (Paranoid Option)
```bash
# Create backup branch
git branch backup-pre-spec-kit

# Or copy entire directory
cp -r /mnt/i/projects/thumper_counter /mnt/i/projects/thumper_counter.backup
```

### 3. Check npm/node Versions
```bash
node --version
# Should be: v18+ recommended

npm --version
# Should be: v9+ recommended
```

---

## Undo Commands (If Needed)

### If You Don't Like What Init Created

**Option A: Manual Removal**
```bash
# Remove spec-kit files
rm -rf .specify/
rm -rf specs/  # Only if empty

# Restore .gitignore if modified
git checkout .gitignore

# Remove from package.json if installed locally
npm uninstall @github/specify
```

**Option B: Git Reset (If Committed)**
```bash
# See recent commits
git log --oneline -5

# Reset to before spec-kit
git reset --hard HEAD~1

# Or reset to specific commit
git reset --hard a0b5130  # Your pre-spec-kit commit
```

**Option C: Delete Branch**
```bash
# Switch to safe branch
git checkout 007-data-quality

# Delete experimental branch
git branch -D 998-spec-kit-init
```

---

## My Recommendation

**SAFEST PATH:**

1. **Test in separate directory first** (Option 1)
   ```bash
   cd /mnt/i/projects
   mkdir spec_test && cd spec_test
   git init
   npm install --save-dev @github/specify
   npx specify init
   # Explore, learn, understand
   ```

2. **Create experimental branch** (Option 2)
   ```bash
   cd /mnt/i/projects/thumper_counter
   git checkout -b 998-spec-kit-experiment
   npm install --save-dev @github/specify
   npx specify init
   git status  # Review changes
   ```

3. **Review generated files carefully**
   ```bash
   cat .specify/config.yml
   git diff .gitignore
   ```

4. **If satisfied, commit**
   ```bash
   git add .specify/ .gitignore package.json
   git commit -m "chore: Initialize spec-kit"
   ```

5. **Merge to main branch when ready**
   ```bash
   git checkout 007-data-quality
   git merge 998-spec-kit-experiment
   ```

---

## What Spec-Kit Won't Do

**Won't change:**
- Source code (src/)
- Documentation (docs/)
- Docker configs
- Database schema
- Environment variables
- Git history

**Won't install:**
- New dependencies in your project (unless you choose local install)
- Database migrations
- Docker images

**Won't break:**
- Your existing workflow
- Git remotes
- Running services
- Processed data

---

## Red Flags to Watch For

**STOP if you see:**
- Errors about missing dependencies
- Warnings about overwriting files
- Prompts to delete existing directories
- Changes to src/ or other code directories

**Normal to see:**
- Creation of .specify/ directory
- Creation of specs/ directory
- Updates to .gitignore
- Addition to package.json (if local install)

---

## Quick Safety Checklist

Before running `specify init`:
- [ ] Git status is clean
- [ ] Current branch is experimental (not main)
- [ ] Have backup (branch or copy)
- [ ] Read `specify init --help`
- [ ] Tested in dummy directory first
- [ ] Know how to undo (git reset or branch delete)

After running `specify init`:
- [ ] Review `git status`
- [ ] Check `.specify/config.yml` contents
- [ ] Verify `.gitignore` changes
- [ ] Ensure no unexpected file modifications
- [ ] Test that existing services still work

---

## Example: Complete Safe Test

```bash
# 1. Test in isolated directory
cd /tmp
mkdir spec_kit_test && cd spec_kit_test
git init
echo "# Test" > README.md
git add . && git commit -m "init"

# 2. Install and init spec-kit
npm install --save-dev @github/specify
npx specify init

# 3. See what it created
tree -a -L 2
cat .specify/config.yml

# 4. Create a test spec
npx specify create example

# 5. Review the spec
cat specs/example.spec

# 6. If happy, try in real project with branch
cd /mnt/i/projects/thumper_counter
git checkout -b 998-spec-kit-test
npm install --save-dev @github/specify
npx specify init
git status
git diff

# 7. If not happy, abort
git checkout 007-data-quality
git branch -D 998-spec-kit-test
```

---

## When to Contact Spec-Kit Support

**Before modifying your real project**, try:
- Reading: https://github.com/github/spec-kit/blob/main/README.md
- Checking: https://github.com/github/spec-kit/issues
- Searching: Existing issues for similar questions

**Safe to proceed when:**
- You've tested in dummy directory
- You understand what files are created
- You've read the generated config.yml
- You have a backup/branch strategy
- You're comfortable with git reset if needed

---

## Final Recommendation

**Command to start:**
```bash
# Safest first step (no changes to your project)
npm install -g @github/specify
specify --version

# Second safest step (test in dummy directory)
cd /tmp
mkdir spec_test && cd spec_test
git init
specify init
tree -a

# When confident (create experimental branch)
cd /mnt/i/projects/thumper_counter
git checkout -b 998-spec-kit-init
specify init
git status
```

**You can always:**
- Delete the branch if you don't like it
- Keep experimenting on the branch
- Merge when you're confident

**Remember:** Spec-kit is just adding files, not modifying existing code. The risk is very low, especially with a git branch!

---

Good luck! Start with the dummy directory, then move to a branch. You'll be fine!
