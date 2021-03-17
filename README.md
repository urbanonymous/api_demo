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

## Start the API

To start the API you need to execute the following command:
`make`

That will build the docker image and start the container at the port `8080`

The default user_id is `username`
The default password is `password`

## Run tests

Unit tests for this project are defined in the app/api/tests folder.
End to end tests for this project are defined in the app/tests folder.

Warning: *You first need to start the api with docker*

To run the unit tests, run the following command:
`make test-local`

To run the e2e tests, run the following command:
`make test-e2e`

## Clean environment

To remove the container and images of this API, run the following commands:  

`make stop`

`make clean`

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
