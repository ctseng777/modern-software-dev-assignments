# API

Base: OpenAPI 3.0.3
Title: Modern Software Dev Starter (Week 4)
Version: 1.0.0

## Endpoints

### GET /
Serve frontend.

Response 200
- Content-Type: text/html
- Body: string (HTML)

### GET /notes/
List notes.

Response 200
- Content-Type: application/json
- Body: array of NoteRead

### POST /notes/
Create note.

Request body (required)
- Content-Type: application/json
- Schema: NoteCreate

Response 201
- Content-Type: application/json
- Body: NoteRead

### GET /notes/search/
Search notes.

Query parameters
- q (string, optional): search query

Response 200
- Content-Type: application/json
- Body: array of NoteRead

### GET /notes/{note_id}
Get note.

Path parameters
- note_id (integer, required)

Responses
- 200: NoteRead
- 404: HTTPError

### GET /action-items/
List action items.

Response 200
- Content-Type: application/json
- Body: array of ActionItemRead

### POST /action-items/
Create action item.

Request body (required)
- Content-Type: application/json
- Schema: ActionItemCreate

Response 201
- Content-Type: application/json
- Body: ActionItemRead

### PUT /action-items/{item_id}/complete
Complete action item.

Path parameters
- item_id (integer, required)

Responses
- 200: ActionItemRead
- 404: HTTPError

## Schemas

### NoteCreate
- title: string, required
- content: string, required
- additionalProperties: false

### NoteRead
- id: integer, required
- title: string, required
- content: string, required
- additionalProperties: false

### ActionItemCreate
- description: string, required
- additionalProperties: false

### ActionItemRead
- id: integer, required
- description: string, required
- completed: boolean, required
- additionalProperties: false

### HTTPError
- detail: string, required
- additionalProperties: false
