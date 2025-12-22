# Action Item Extractor

A FastAPI-based web application that extracts actionable items from free-form notes using either heuristic-based pattern matching or LLM-powered extraction via RunPod API.

## Overview

This application provides two methods for extracting action items from text:
1. **Heuristic-based extraction**: Uses pattern matching to identify action items (bullet points, checkboxes, keywords)
2. **LLM-powered extraction**: Uses a large language model hosted on RunPod to intelligently extract action items from unstructured text

The application stores notes and extracted action items in a SQLite database, allowing users to track and manage their tasks.

## Features

- Extract action items from free-form text using pattern matching
- Extract action items using LLM-powered analysis via RunPod API
- Save notes to the database
- List and view all saved notes
- Mark action items as complete
- Filter action items by note ID
- Simple, clean web interface

## Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- RunPod API key (for LLM extraction feature)

## Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd modern-software-dev-assignments
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   Create a `.env` file in the `week2` directory (or project root) with your RunPod API key:
   ```
   RUNPOD_API_KEY=your_runpod_api_key_here
   ```

4. **Activate your conda environment** (if using conda):
   ```bash
   conda activate cs146s
   ```

## Running the Application

From the project root directory, start the FastAPI server:

```bash
poetry run uvicorn week2.app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000/`

### Accessing the Web Interface

Open your web browser and navigate to:
```
http://127.0.0.1:8000/
```

### API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### Notes Endpoints

#### Create a Note
- **POST** `/notes`
- **Request Body**:
  ```json
  {
    "content": "Your note content here"
  }
  ```
- **Response**: Note object with id, content, and created_at timestamp

#### List All Notes
- **GET** `/notes`
- **Response**: Array of note objects

#### Get a Single Note
- **GET** `/notes/{note_id}`
- **Response**: Note object with id, content, and created_at timestamp

### Action Items Endpoints

#### Extract Action Items (Heuristic)
- **POST** `/action-items/extract`
- **Request Body**:
  ```json
  {
    "text": "Your notes text here",
    "save_note": true
  }
  ```
- **Response**: Object containing note_id (if saved) and array of extracted action items

#### Extract Action Items (LLM)
- **POST** `/action-items/extract-llm`
- **Request Body**:
  ```json
  {
    "text": "Your notes text here",
    "save_note": true
  }
  ```
- **Response**: Object containing note_id (if saved) and array of extracted action items
- **Note**: Requires `RUNPOD_API_KEY` environment variable to be set

#### List Action Items
- **GET** `/action-items?note_id={optional_note_id}`
- **Query Parameters**:
  - `note_id` (optional): Filter action items by note ID
- **Response**: Array of action item objects

#### Mark Action Item as Done
- **POST** `/action-items/{action_item_id}/done`
- **Request Body**:
  ```json
  {
    "done": true
  }
  ```
- **Response**: Object with action item id and updated done status

## Running Tests

The test suite uses pytest. To run all tests:

```bash
poetry run pytest week2/tests/
```

To run tests with verbose output:

```bash
poetry run pytest week2/tests/ -v
```

To run a specific test file:

```bash
poetry run pytest week2/tests/test_extract.py
```

### Test Coverage

The test suite includes:
- Tests for heuristic-based extraction (`extract_action_items`)
- Tests for LLM-based extraction (`extract_action_items_llm`)
- Tests for various input formats (bullet lists, checkboxes, keywords, empty input)

## Project Structure

```
week2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application setup
│   ├── db.py                # Database operations
│   ├── schemas.py           # Pydantic models for API contracts
│   ├── routers/
│   │   ├── action_items.py  # Action items endpoints
│   │   └── notes.py         # Notes endpoints
│   └── services/
│       └── extract.py       # Extraction logic (heuristic + LLM)
├── frontend/
│   └── index.html          # Web interface
├── tests/
│   └── test_extract.py     # Unit tests
├── data/
│   └── app.db              # SQLite database (created on first run)
├── assignment.md           # Assignment instructions
├── writeup.md              # Assignment writeup template
└── README.md               # This file
```

## Database Schema

The application uses SQLite with two main tables:

### Notes Table
- `id`: INTEGER PRIMARY KEY
- `content`: TEXT NOT NULL
- `created_at`: TEXT (ISO timestamp)

### Action Items Table
- `id`: INTEGER PRIMARY KEY
- `note_id`: INTEGER (foreign key to notes.id, nullable)
- `text`: TEXT NOT NULL
- `done`: INTEGER DEFAULT 0 (0 = not done, 1 = done)
- `created_at`: TEXT (ISO timestamp)

## Extraction Methods

### Heuristic-Based Extraction

The `extract_action_items()` function identifies action items by:
- Bullet points (`-`, `*`, `•`, numbered lists)
- Checkbox markers (`[ ]`, `[todo]`)
- Keyword prefixes (`todo:`, `action:`, `next:`)
- Imperative sentence starters (e.g., "add", "create", "implement")

### LLM-Based Extraction

The `extract_action_items_llm()` function:
- Sends the text to a RunPod-hosted LLM endpoint
- Uses a carefully crafted prompt to extract action items
- Parses JSON array response from the LLM
- Falls back to heuristic extraction if LLM call fails

## Error Handling

The application includes comprehensive error handling:
- **400 Bad Request**: Invalid input (e.g., empty text)
- **404 Not Found**: Resource not found (e.g., note or action item ID)
- **500 Internal Server Error**: Server-side errors during processing
- **503 Service Unavailable**: LLM service unavailable (missing API key or service error)

## Development

### Code Style

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **Pydantic** for data validation
- Type hints throughout

### Adding New Features

1. Define schemas in `app/schemas.py` for new endpoints
2. Add router endpoints in `app/routers/`
3. Implement business logic in `app/services/`
4. Add database functions in `app/db.py` if needed
5. Write tests in `tests/`
6. Update frontend in `frontend/index.html` if UI changes are needed

## License

This project is part of a course assignment.

## Author

Generated documentation for Week 2 Assignment - Action Item Extractor

