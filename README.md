# 🐳 Production-Ready Containerized Web Application

An end-to-end project demonstrating a production-ready containerized Python web application using FastAPI, PostgreSQL database, Redis caching, and Nginx reverse proxy, orchestrated with Docker Compose.

## ✨ Project Goal

The main objective of this project is to build and deploy a multi-service web application within Docker containers, focusing on industry best practices such as:
- Using **FastAPI** for the web API development.
- Integrating with a **PostgreSQL** database for persistent data storage.
- Implementing **Redis** as a caching layer to improve performance.
- Utilizing **Nginx** as a reverse proxy for routing and potentially serving static files.
- Orchestrating all services using **Docker Compose**.
- Implementing a **multi-stage Dockerfile** to optimize the build process and minimize the final image size.
- Leveraging **Alpine-based images** where suitable for smaller container footprints.

## 🏗️ Architecture Overview

The application architecture is designed as follows:
+--------------+ +------------------+ +---------------------+ +--------------+
| Client | <---> | Nginx | <---> | FastAPI | <---> | PostgreSQL |
| (Browser/App)| | (Reverse Proxy) | | (Python/Uvicorn) | | (Database) |
+--------------+ +------------------+ +---------------------+ +--------------+
^ ^
| |
+-------------------------+
|
| (Caching)
|
+--------------+
| Redis |
| (Caching) |
+--------------+


-   Client requests hit the Nginx reverse proxy.
-   Nginx forwards API requests to the FastAPI application.
-   FastAPI interacts with PostgreSQL for data persistence and Redis for caching.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually comes bundled with Docker Desktop)

## 🚀 Getting Started

Follow these steps to get the project up and running on your local machine using Docker Compose.

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Review Configuration:**
    - Database and Redis connection URLs are set as environment variables directly in `docker-compose.yml`. In a real production scenario, consider using a `.env` file and ignoring it in `.gitignore` for secrets.
    - The `nginx.conf` is set up to proxy requests to the `fastapi` service.

3.  **Build and Run the Containers:**
    Navigate to the root directory of the cloned repository (where `docker-compose.yml` is located) and run:

    ```bash
    docker-compose up -d --build
    ```
    - `--build`: Forces Docker Compose to rebuild the images. This is important the first time or after changes to the Dockerfile or app code.
    - `-d`: Runs the services in detached mode (in the background).

4.  **Wait for Services:**
    Allow a minute or two for the services (PostgreSQL, Redis, FastAPI) to start up completely. You can check their status using `docker-compose ps` and view logs using `docker-compose logs <service_name>`.

5.  **Seed the Database (Optional but Recommended):**
    The project includes a `seed_db.py` script to populate the `employees` table with some initial data. You can run this script inside the running FastAPI container:

    ```bash
    docker exec -it <fastapi-container-name> python /app/seed_db.py
    ```
    Replace `<fastapi-container-name>` with the actual name of your FastAPI container (e.g., `solution-fastapi-1`), which you can find using `docker ps`.

6.  **Access the Application:**
    The application should now be accessible via Nginx on `localhost` on port 80.

    Open your web browser or use `curl` to access the endpoints listed below.

## 🌍 API Endpoints

The FastAPI application exposes the following endpoints:

*   **`GET /`**
    -   **Description:** Root endpoint, returns a basic welcome message and app status.
    -   **Example:** `http://localhost:80/`
    -   **Response:** `{"Hello": "World", "app_status": "running", "message": "Connected to FastAPI app."}`

*   **`GET /status`**
    -   **Description:** Provides the application's status and database configuration information. Does NOT connect to the database or Redis for this status.
    -   **Example:** `http://localhost:80/status`
    -   **Response:** `{"app_status": "running", "database_connection_status": "Configured via DATABASE_URL", "message": "Basic FastAPI app with DB and Redis setup."}`

*   **`GET /users/`**
    -   **Description:** Lists all users from the database. This endpoint utilizes Redis caching: it tries to fetch data from the cache first, and if not found, it queries the database and stores the result in the cache.
    -   **Example:** `http://localhost:80/users/`
    -   **Response:** A JSON array of user objects (e.g., `[{"id": 1, "name": "...", "email": "..."}]`).

*   **`POST /users/`**
    -   **Description:** Creates a new user in the database. Requires `name` and `email` as form data or request body parameters. Invalidates the `/users/` cache after successful creation.
    -   **Example (using curl):**
        ```bash
        curl -X POST http://localhost:80/users/ -d "name=Test User&email=test@example.com"
        ```
    -   **Response:** The details of the newly created user (e.g., `{"id": 5, "name": "Test User", "email": "test@example.com"}`).

*   **`GET /employees/`**
    -   **Description:** Lists all employees from the database. This is the endpoint added as part of the task extension. (Note: Caching is NOT implemented for this endpoint in this example).
    -   **Example:** `http://localhost:80/employees/`
    -   **Response:** A JSON array of employee objects (e.g., `[{"id": 1, "name": "Alice Smith"}, {"id": 2, "name": "Bob Johnson"}]`).

## 🛠️ Project Implementation Details

*   **Multi-Stage Dockerfile:** The `Dockerfile` uses a two-stage approach (`builder` and `runtime`). The `builder` stage installs dependencies using a more complete Python image, while the `runtime` stage copies only the necessary installed packages and application code onto a lighter `slim` Python image. This significantly reduces the final image size compared to a single-stage build. Crucially, both stages use the *same minor Python version* (`3.9.22`) to ensure binary compatibility of installed packages. Necessary system libraries (`libpq5`, `libssl1.1`) are installed in the `runtime` stage to support Python packages with C extensions.
*   **Alpine/Slim Images:** Using `python:3.9.22-bullseye` for the builder and `python:3.9.22-slim-bullseye` for the runtime helps keep the resulting image size down while still being based on the robust Debian Bullseye distribution.
*   **Database & Caching:** SQLAlchemy with AsyncIO is used for asynchronous database interactions with PostgreSQL, and `redis-py` (async version) is used for connecting to Redis. Basic read-through caching and cache invalidation are demonstrated for the `/users/` endpoint.
*   **Nginx:** Acts as the entry point, forwarding all incoming HTTP requests on port 80 to the FastAPI service.

## 🛑 Stopping the Services

To gracefully stop and clean up all Docker Compose resources, use:

```bash
docker-compose down
