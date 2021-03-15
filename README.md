# api_demo

This API is the result of a hiring exercise.

The purpose of this API is to handle files from the users. Allowing uploads and downloads.

## API constraints

- Limited to 99 files per user

## API routes

The API has 6 routes:

- POST /auth - To obtain a token for interacting with the API.
- GET /me - Returns all files on the user space.
- POST /me - Receives a file and stores in the user space.
- GET /f/:file_id - Returns the file.
- GET /f/:file_id/share - Returns a short URL to download the file.
- GET /s/:share_url - Returns the file

For more documentation, read the OpenAPI spec at http://localhost:8000/docs

## Run tests

Tests for this project are defined in the tests/ folder.
TODO:

## Project structure

Files related to application are in the ``app`` directory.
Application parts are:

```txt
api
├── auth              - auth related deps and routes.
│   ├── deps          - dependencies for routes with auth.
│   └── auth          - auth related routes.
├── schemas           - pydantic models for this api.
├── tests             - unit tests for this api.
├── routes            - web routes
│   └── files         - files related routes.
├── database.py       - in memory db .
├── config.py         - settings for this api.
└── main.py           - FastAPI application creation.
```

## TODO

- Add locks to the database, filesystem on reorganizations of duplicates / overwrites
