---
name: thor-crud-base
description: Build or refactor full-stack CRUD modules using the Thor base CRUD pattern for future projects, independent of any existing entity code. Use when Codex is asked to create backend models, migrations, schemas, repositories, services, API routes, frontend listing, create, edit, view, delete, simple search, advanced filtering, pagination, lazy-loaded data, required fields, or navigation flows for a CRUD feature.
---

# Thor CRUD Base

## Workflow

Use this skill as a generic full-stack CRUD standard. Do not assume access to an existing CRUD implementation. If the project already has backend layers, UI components, routing conventions, API clients, or state libraries, adapt the examples to those local patterns while preserving the behavioral contract.

Read `references/crud-base-pattern.md` when implementing or reviewing a CRUD. It contains copyable backend and frontend examples for persistence, API contracts, pagination, filters, navigation, list pages, table filters, forms, required fields, lazy loading, mutations, and verification.

## Core Contract

Build each CRUD as a backend contract plus frontend surfaces.

Backend layers should include, adapting names to the stack:

- persistence model/entity
- migration or schema change
- request/response schemas or DTOs
- repository/query layer
- service/business layer
- API router/controller with list, get, create, update, and delete endpoints
- tests for validation, filters, pagination, and mutations when the project has tests

Frontend surfaces should include:

- list route: `/entities`
- create route: `/entities/new` or the project-local equivalent such as `/entidades/nova`
- reusable table component for list, search, advanced filters, pagination, and row actions
- reusable form component for create and edit
- optional details component or route for read-only view

Keep the backend and frontend contracts aligned: field names, enum values, required fields, nullable fields, filter names, date formats, pagination parameters, and error behavior must match.

Use a full page for create flows, not a popup. The list's primary action navigates to the create route. The create screen includes a `Voltar`/Back button. After successful create, navigate back to the list unless the user asks for another destination.

View and edit may be routes or dialogs depending on the project. Prefer routes for complex forms and dialogs for compact read/edit flows. Delete must require explicit confirmation before mutation.

## Backend API Behavior

Expose predictable REST-style endpoints unless the project uses another API style:

- `GET /entities` returns `{ items, total }`
- `GET /entities/{id}` returns one record or `404`
- `POST /entities` validates and creates
- `PUT` or `PATCH /entities/{id}` validates and updates
- `DELETE /entities/{id}` deletes, soft-deletes, or deactivates according to business rules

List endpoints must support server-side pagination. Prefer `limit` and `offset`, or map to the project's existing `page` and `pageSize` convention. Apply filters in the backend query, not after loading all rows into memory.

Search endpoints should support:

- simple text query such as `q`
- advanced filters for exact fields, enums, booleans, numeric ranges, and date ranges
- deterministic ordering, usually newest first or by stable identifier
- explicit max page size to protect the API

Backend required fields and enum values are the source of truth. Mirror them in frontend validation, but never rely on frontend-only validation.

## List Behavior

Fetch only the current page from the API. Do not load all records just to paginate locally when the dataset can grow.

Keep list state explicit:

- `filters`
- `pageIndex`
- `pageSize`

Use a stable query/cache key containing the entity name, filters, page index, and page size. Expected paginated API shape is `{ items, total }`, or adapt the mapper if the backend uses different names.

## Search, Filters, And Pagination

Provide simple search:

- search input in the table toolbar
- search icon when icon library exists
- Enter key submits
- Search button submits
- every new search resets the page to the first page

Provide advanced search:

- collapsed by default behind a toggle button
- responsive grid of metadata fields
- text, enum, boolean, numeric, and date-range controls as appropriate
- clear filters action that resets the draft and submits an empty filter object

Render pagination above and below the table for long result sets. Include displayed count, total count, current page, total pages, page-size selector, first/previous/numbered/next/last controls, and disabled states during fetch.

## Forms

Use a schema validator when the stack supports one, such as Zod. Keep defaults explicit. Required fields must be represented in both the validation schema and UI.

Use a visible required marker beside labels. Show field errors directly below fields. Show mutation errors near submit. Disable submit while saving and use saving text such as `Salvando...` or `Saving...`.

Use responsive layout:

- two-column grids for short fields on larger screens
- full-width fields for long descriptions
- bordered conditional sections when a field reveals dependent data

For edit mode, reset form values from the loaded entity. For create mode, reset to defaults after success only if staying on the form; otherwise navigate away.

## Lazy Loading

Use lazy loading intentionally:

- paginate list data server-side with `limit`/`offset` or `page`/`pageSize`
- fetch option lists only when the form or field is visible
- use `enabled` or equivalent guards for queries that depend on IDs, selected modes, or open dialogs
- fetch heavy row details only when the user opens details
- keep background fetch state separate from empty/error states

## Mutations

Use create, update, and delete mutations. On success:

- invalidate or refresh the list query
- invalidate related lookup/detail queries when needed
- call an `onSaved` or equivalent callback so the parent controls navigation/closing
- keep delete confirmation close to the destructive action

Convert optional numeric fields and empty strings before sending payloads. Prefer `null` for intentionally empty optional backend fields when the API expects nullable values.

## Backend Data Integrity

Keep business rules in the backend service layer even when the frontend also validates them. Use database constraints for unique fields, required columns, foreign keys, indexes for searched fields, and timestamp columns when the project supports them.

For filters and pagination, add indexes that match likely queries. At minimum, consider indexes for stable identifiers, status fields, parent/foreign keys, and creation/update timestamps. For broad text search, use the project's established full-text mechanism when available; otherwise use conservative `contains`/`ilike` filters appropriate to the database.

Return consistent errors:

- `400` or `422` for validation errors
- `404` for missing records
- `409` for uniqueness or state conflicts
- `500` only for unexpected failures

## Visual Standard

CRUD screens are operational tools. Keep them dense, scannable, and predictable. Avoid landing pages, decorative backgrounds, nested cards, oversized hero layouts, and purely ornamental UI. Use familiar icons for add, search, filter, view, edit, delete, and back actions when available.
