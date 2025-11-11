# Using Claude CLI with Spec-Kit

## Quick Start Guide

This guide explains how to use claude-cli to implement the thumper_counter project based on our specifications.

## Prerequisites

1. **Install claude-cli**
```bash
# Install globally
npm install -g claude-cli

# Or use with npx
npx claude-cli
```

2. **Configure API Key**
```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"

# Or create .env file in project root
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## Step 1: Initialize Claude CLI

From the project root (`I:\projects\thumper_counter`):

```bash
# Initialize claude in the project
claude init

# This creates:
# - .claude/config.json (configuration)
# - .claude/context.md (project context)
```

## Step 2: Configure Project Context

Edit `.claude/context.md` to include our specifications:

```markdown
# Project: Thumper Counter

## Specifications
- System Architecture: specs/system.spec
- ML Pipeline: specs/ml.spec  
- API Design: specs/api.spec
- UI Design: specs/ui.spec

## Current Task
Implement the deer tracking system following spec-kit methodology.

## Important Notes
- Use ASCII-only output (no emojis/unicode)
- Backend uses python3 (not python)
- One step at a time with explanations
```

## Step 3: Generate Code with Claude CLI

### Generate Backend Structure
```bash
# Generate FastAPI backend
claude generate --spec specs/api.spec --output src/backend \
  "Create FastAPI backend structure with all endpoints from the API specification"

# Generate database models
claude generate --spec specs/system.spec --output src/backend/models \
  "Create SQLAlchemy models for Image, Deer, Detection, and Location"

# Generate ML pipeline
claude generate --spec specs/ml.spec --output src/worker \
  "Create Celery tasks for the ML processing pipeline"
```

### Generate Frontend Structure  
```bash
# Generate React app structure
claude generate --spec specs/ui.spec --output src/frontend \
  "Create React app with routing and component structure"

# Generate Redux store
claude generate --spec specs/ui.spec --output src/frontend/store \
  "Create Redux store with slices for images, deer, and processing"
```

### Generate Docker Configuration
```bash
# Generate docker-compose.yml
claude generate --spec specs/system.spec --output docker \
  "Create docker-compose.yml with all 7 services"

# Generate Dockerfiles
claude generate --spec specs/system.spec --output docker/dockerfiles \
  "Create Dockerfiles for backend, worker, and frontend services"
```

## Step 4: Interactive Development

Use claude-cli in interactive mode for iterative development:

```bash
# Start interactive session
claude chat

# Example prompts:
> Implement the image upload endpoint following the API spec
> Add YOLOv8 detection to the ML pipeline worker
> Create the deer profile grid component
> Add WebSocket support for real-time updates
```

## Step 5: Generate Tests

```bash
# Generate API tests
claude generate --spec specs/api.spec --output tests/api \
  "Create pytest tests for all API endpoints"

# Generate ML pipeline tests
claude generate --spec specs/ml.spec --output tests/ml \
  "Create tests for detection, classification, and re-identification"

# Generate frontend tests
claude generate --spec specs/ui.spec --output tests/frontend \
  "Create Jest tests for React components"
```

## Step 6: Documentation Generation

```bash
# Generate API documentation
claude generate --spec specs/api.spec --output docs/api \
  "Create OpenAPI documentation and usage examples"

# Generate deployment guide
claude generate --spec specs/system.spec --output docs/deployment \
  "Create deployment guide with step-by-step instructions"
```

## Claude CLI Commands Reference

### Basic Commands
```bash
claude init                    # Initialize project
claude chat                    # Start interactive session
claude generate                # Generate code from prompt
claude review <file>           # Review and improve code
claude explain <file>          # Explain code functionality
claude test <file>            # Generate tests for code
```

### Useful Flags
```bash
--spec <file>      # Use specification file as context
--output <dir>     # Output directory for generated code
--model <name>     # Use specific model (default: claude-3-opus)
--max-tokens <n>   # Set max response tokens
--temperature <n>  # Set creativity (0.0-1.0)
```

### Context Management
```bash
# Add files to context
claude context add src/backend/main.py

# Remove files from context  
claude context remove src/old_file.py

# List current context
claude context list

# Clear all context
claude context clear
```

## Best Practices

### 1. Incremental Generation
Don't try to generate everything at once. Build incrementally:
```bash
# Good: Specific, focused requests
claude generate "Create the Image SQLAlchemy model with all fields from the spec"

# Bad: Too broad
claude generate "Create the entire backend"
```

### 2. Use Specifications as Context
Always reference specs when generating code:
```bash
claude generate --spec specs/api.spec \
  "Implement the GET /api/v1/images endpoint with all query parameters"
```

### 3. Review Generated Code
```bash
# Generate first version
claude generate --output src/backend/api/images.py \
  "Create images API endpoints"

# Review and improve
claude review src/backend/api/images.py \
  "Add error handling and logging"
```

### 4. Maintain Consistency
Create templates for consistent code style:
```bash
# Create a template
claude generate --output templates/endpoint.py \
  "Create a template for FastAPI endpoints with error handling"

# Use template for new endpoints
claude generate --spec templates/endpoint.py \
  "Create deer endpoints following this template"
```

## Workflow Example

Here's a complete workflow for implementing a feature:

```bash
# 1. Generate the model
claude generate --spec specs/system.spec --output src/backend/models/deer.py \
  "Create Deer SQLAlchemy model"

# 2. Generate the API endpoint
claude generate --spec specs/api.spec --output src/backend/api/deer.py \
  "Create deer API endpoints"

# 3. Generate the service layer
claude generate --output src/backend/services/deer_service.py \
  "Create service layer for deer business logic"

# 4. Generate tests
claude generate --output tests/api/test_deer.py \
  "Create comprehensive tests for deer endpoints"

# 5. Review the implementation
claude review src/backend/api/deer.py \
  "Check for security issues and optimization opportunities"

# 6. Generate documentation
claude generate --output docs/api/deer.md \
  "Create API documentation for deer endpoints"
```

## Troubleshooting

### Issue: Claude doesn't understand the project structure
**Solution:** Update `.claude/context.md` with more details

### Issue: Generated code doesn't match specifications
**Solution:** Use `--spec` flag to provide specification file

### Issue: Code is too generic
**Solution:** Provide specific examples in your prompts

### Issue: Inconsistent code style
**Solution:** Create and reference template files

## Tips for Success

1. **Start with data models** - They're the foundation
2. **Test as you go** - Generate tests alongside code
3. **Keep specs updated** - Modify specs as you learn
4. **Use interactive mode** - For complex problem-solving
5. **Version control everything** - Commit working versions

## Next Steps

1. Run `claude init` in the project directory
2. Start with backend models: `claude generate --spec specs/system.spec`
3. Move to API endpoints: `claude generate --spec specs/api.spec`
4. Implement ML pipeline: `claude generate --spec specs/ml.spec`
5. Build frontend: `claude generate --spec specs/ui.spec`

---

**Remember:** Claude CLI is a tool to accelerate development, not replace thinking. Always review and understand the generated code!
