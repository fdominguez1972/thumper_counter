# Thumper Counter - Deer Tracking System

**A spec-driven rebuild of the Hopkins Ranch deer tracking system using spec-kit and claude-cli**

## Project Status

[INFO] Project initialization in progress  
[TODO] Create spec-kit specifications  
[TODO] Implement ML pipeline  
[TODO] Build API and frontend  

## Overview

This is a complete rebuild of the deer tracking system originally in `I:\deer_tracker`. The rebuild focuses on:

1. **Learning spec-kit workflow** - Documentation-driven development
2. **Cleaner architecture** - Modular, testable components  
3. **Better documentation** - GitHub-ready with clear explanations
4. **Avoiding past issues** - Proper filesystem handling from the start

## Technology Stack

- **Specifications**: spec-kit (github.com/github/spec-kit)
- **CLI Tool**: claude-cli for code generation
- **Backend**: FastAPI + PostgreSQL + Redis
- **ML Pipeline**: YOLOv8 + ResNet50 + Custom CNN
- **Frontend**: React  
- **Infrastructure**: Docker Compose with GPU support

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd thumper_counter

# Initialize with claude-cli
claude init

# Review specifications
cat specs/system.spec

# Build and run
docker-compose up -d
```

## Project Structure

```
thumper_counter/
├── specs/           # spec-kit specifications
├── src/             # Source code
├── docker/          # Docker configuration
├── tests/           # Test suites
├── docs/            # Documentation
└── CLAUDE.md        # AI assistant context
```

## Development Workflow

1. **Write specs** - Define what we're building
2. **Validate** - Ensure specs are complete
3. **Generate code** - Use claude-cli for scaffolding
4. **Implement** - Fill in the logic
5. **Test** - Verify against specs
6. **Document** - Keep docs in sync

## Original System Capabilities

The system processes trail camera images to:
- Detect deer using computer vision
- Classify by sex (buck/doe/fawn)
- Track individuals across photos
- Generate population statistics
- Visualize movement patterns

**Dataset**: 40,617 images from 7 camera locations

## Why spec-kit?

spec-kit provides:
- **Clear contracts** between components
- **Living documentation** that stays current
- **Test generation** from specifications
- **Iterative refinement** before coding
- **Team collaboration** through shared understanding

## License

[TODO: Add license]

## Contributors

- Original system built over Sessions 1-28
- Rebuild using spec-kit methodology
- Guided by claude-cli integration
