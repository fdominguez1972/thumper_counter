# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT: Thumper Counter (Deer Tracking System Rebuild)

**Rebuild using:** spec-kit + claude-cli  
**Original project:** I:\deer_tracker  
**Purpose:** Learn spec-kit workflow while rebuilding the deer tracking ML pipeline  

## CRITICAL: User Preferences & Working Style

### ASCII-ONLY OUTPUT (HIGHEST PRIORITY)
**ALL output must use ASCII characters only - NO Unicode, emojis, or special characters**

- NO Unicode characters (checkmarks, crosses, arrows, etc.)
- NO Emojis (deer, party, checkmark, etc.)  
- NO Smart quotes (use straight quotes: ' and ")
- NO Special dashes (use regular hyphen: -)
- NO Box-drawing characters

**Allowed for emphasis:**
- Use [OK], [FAIL], [WARN], [INFO] for status indicators
- Use ASCII art with dashes, equals, asterisks for borders
- Use ALL CAPS for important headers

### User Technical Profile
- **Level**: Advanced (independently catches bugs, reviews code)
- **Preferences**: Comprehensive documentation, understands WHY not just WHAT
- **Platform**: Windows 10/11 with Docker Desktop + WSL2
- **Editor**: vi (not nano)
- **Style**: Prefers "turbo mode" (multithreaded operations when possible)
- **Approach**: One-step-at-a-time with approval
- **Learning Goal**: Gain proficiency with spec-kit methodology

### IMPORTANT LESSONS FROM PAST SESSIONS

**Filesystem Issues to Avoid:**
- Always use Filesystem MCP for file creation (not Python pathlib)
- Files created in Docker/WSL may not sync to Windows filesystem
- Always verify file creation with `ls` or `dir` commands
- Use explicit paths with Windows drive letters (I:\) when needed

**Known Issues from deer_tracker build:**
- Filesystem naming conflicts (files getting stuck in virtual filesystem)
- Token waste from trying multiple approaches to file operations
- Use Filesystem:write_file FIRST TIME instead of trying alternatives

## Project Structure (spec-kit driven)

```
thumper_counter/
├── specs/              # spec-kit specifications
│   ├── system.spec     # Overall system architecture
│   ├── ml.spec         # ML pipeline specification
│   ├── api.spec        # Backend API specification
│   └── ui.spec         # Frontend specification
├── src/
│   ├── backend/        # FastAPI application
│   ├── worker/         # Celery + ML processing
│   ├── frontend/       # React dashboard
│   └── models/         # ML model storage
├── docker/
│   ├── docker-compose.yml
│   └── dockerfiles/
├── tests/
├── docs/
├── .env
├── .gitignore
├── README.md
└── CLAUDE.md
```

## Spec-Kit Workflow

### WHY spec-kit?
- **Separation of concerns**: Design decisions separate from implementation
- **Documentation-driven**: Specs become living documentation
- **Iterative refinement**: Easy to modify specs before coding
- **Team collaboration**: Clear contracts between components
- **Testing foundation**: Specs drive test creation

### Our Approach
1. **Define specs first** - Clear understanding before coding
2. **Validate specs** - Ensure completeness and consistency  
3. **Generate scaffolding** - Use claude-cli to create boilerplate
4. **Implement incrementally** - One component at a time
5. **Test against specs** - Verify implementation matches design

## Original System Components

### ML Pipeline (to rebuild)
- **Detection**: YOLOv8 for deer detection
- **Classification**: CNN for buck/doe/fawn classification  
- **Re-identification**: ResNet50 for individual tracking
- **GPU acceleration**: NVIDIA CUDA support

### Infrastructure (to rebuild)
- **Backend**: FastAPI (port 8000)
- **Database**: PostgreSQL 15
- **Queue**: Redis + Celery
- **Frontend**: React (port 3000)
- **Monitoring**: Flower (port 5555)

### Data
- **Images**: 40,617 trail camera photos
- **Locations**: 7 camera sites
- **Database**: Deer profiles, detections, sightings

## Commands & Conventions

### Git
```bash
git init
git add .
git commit -m "Initial commit with spec-kit structure"
```

### Docker
```bash
# Use docker-compose (not docker compose)
docker-compose up -d
docker-compose logs -f
docker-compose exec <service> <command>
```

### Python in containers
```bash
# ALWAYS use python3 (not python)
docker exec <container> python3 script.py
```

### File operations
```bash
# Use Filesystem MCP for reliability
# Avoid Python file operations that may not sync
```

## Development Standards

### Status Indicators
- [OK] - Success
- [FAIL] - Error  
- [WARN] - Warning
- [INFO] - Information
- [TODO] - Pending task

### Error Handling
Always include try-catch with clear ASCII messages:
```python
try:
    # operation
except Exception as e:
    print(f"[FAIL] Operation failed: {e}")
```

### Multi-threading
Use parallel processing when appropriate:
```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_function, items)
```

## Session Goals

1. **Learn spec-kit workflow** - Understanding the methodology
2. **Create cleaner architecture** - Modular, maintainable design
3. **Document for GitHub** - Publication-ready documentation
4. **Avoid past issues** - No filesystem sync problems
5. **Build proficiency** - Master claude-cli integration

## Notes

- Always explain WHY we're doing something, not just what
- One step at a time with user approval
- Use ASCII-only output (critical requirement)
- Be aware of filesystem sync issues from past sessions
- Multi-threaded operations when beneficial
