# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WIKISOFT3 is an AI-powered HR/Finance data validation system that automatically validates and maps employee roster Excel files. It uses a ReACT (Reasoning + Acting) AI Agent pattern with multiple validation layers.

## Build & Run Commands

### Backend (FastAPI on port 8003)
```bash
cd WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003
```

### Frontend (React/Vite on port 3004)
```bash
cd WIKISOFT3/frontend
npm install  # first time only
npm run dev -- --port 3004
```

### Tests
```bash
cd WIKISOFT3
source ../.venv/bin/activate
pytest tests/ -v                    # all tests
pytest tests/test_matcher.py -v     # single test file
```

### Learning Scripts
```bash
python scripts/learn_from_file.py /path/to/file.xls  # learn from single file
python scripts/learn_from_data.py                     # batch learning
```

## Architecture

```
Frontend (React) → /api/auto-validate → Parser → Matcher → Validators → Report
                                           ↓
                                   Few-shot + AI Matching (GPT-4o)
```

### Key Directories
- `WIKISOFT3/external/api/` - FastAPI routes and middleware
- `WIKISOFT3/internal/ai/` - AI/ML components (matcher.py is core)
- `WIKISOFT3/internal/agent/` - ReACT agent implementation
- `WIKISOFT3/internal/validators/` - 3-layer validation (format → cross → AI-assisted)
- `WIKISOFT3/internal/parsers/` - Excel parsing and standard schema
- `WIKISOFT3/training_data/` - Learned patterns and cases
- `WIKISOFT3/frontend/src/` - React TypeScript UI

### Primary API Endpoints
- `POST /api/auto-validate` - Main file validation
- `POST /api/react-agent/validate` - ReACT agent validation
- `GET /api/diagnostic-questions` - Get diagnostic questions
- `POST /api/learn/correction` - Record user corrections

## Key Patterns

### ReACT Agent Loop
Think → Act (Tool Call) → Observe → Loop until complete. Implementation in `internal/agent/react_agent.py`.

### Three Validation Layers
1. **L1** (`validation_layer1.py`): Format validation (dates, types, ranges)
2. **L2** (`validation_layer2.py`): Cross-validation (duplicates, logic)
3. **L3** (`validation_layer_ai.py`): AI-assisted with domain context

### Graceful Degradation
System works without OpenAI API by falling back to rule-based matching.

## Environment

Python virtual environment is at `../.venv` (one level up from WIKISOFT3).

Key env vars in `WIKISOFT3/.env`:
- `OPENAI_API_KEY` - Required for AI matching
- `API_TOKEN` - API authentication

## Git

- Development branch: `kangjun`
- Main branch: `main`
