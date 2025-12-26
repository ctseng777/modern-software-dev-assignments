# API

Base: OpenAPI 3.1.0
Title: Modern Software Dev Starter (Week 4)
Version: 0.1.0

## Endpoints

### GET /
Root

Responses
- 200 (application/json): object


### GET /action-items/
List Items

Responses
- 200 (application/json): array of ActionItemRead


### POST /action-items/
Create Item

Request body
- Required
- Content-Type: application/json
- Schema: ActionItemCreate

Responses
- 201 (application/json): ActionItemRead
- 422 (application/json): HTTPValidationError


### PUT /action-items/{item_id}/complete
Complete Item

Parameters
- item_id (integer, required, path)

Responses
- 200 (application/json): ActionItemRead
- 422 (application/json): HTTPValidationError


### GET /notes/
List Notes

Responses
- 200 (application/json): array of NoteRead


### POST /notes/
Create Note

Request body
- Required
- Content-Type: application/json
- Schema: NoteCreate

Responses
- 201 (application/json): NoteRead
- 422 (application/json): HTTPValidationError


### GET /notes/search/
Search Notes

Parameters
- q (object, optional, query)

Responses
- 200 (application/json): array of NoteRead
- 422 (application/json): HTTPValidationError


### GET /notes/{note_id}
Get Note

Parameters
- note_id (integer, required, path)

Responses
- 200 (application/json): NoteRead
- 422 (application/json): HTTPValidationError


### DELETE /notes/{note_id}
Delete Note

Parameters
- note_id (integer, required, path)

Responses
- 204: no body
- 422 (application/json): HTTPValidationError

## Schemas

### ActionItemCreate
- description: string, required

### ActionItemRead
- completed: boolean, required
- description: string, required
- id: integer, required

### HTTPValidationError
- detail: array of ValidationError, optional

### NoteCreate
- content: string, required
- title: string, required

### NoteRead
- content: string, required
- id: integer, required
- title: string, required

### ValidationError
- loc: array of object, required
- msg: string, required
- type: string, required
