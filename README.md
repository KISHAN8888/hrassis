## BE-Chatur


## update UV
  ## 'uv sync'

## go to the Virtual environment
  ## comman for windows
  ```.venv\Scripts\activate```
  ## for mac/linux
  ```source .venv/bin/activate```

## run fastApi Server
  ## 'uv run uvicorn main:app --reload '

## Project Overview
BE-Chatur is a backend application designed to handle various tasks such as job description management, resume parsing, and chatbot interactions. It is built using FastAPI and integrates with several services and libraries to provide a robust solution for managing and processing data.

## Directory Structure
**Project Folder Structure Overview**

  The project is structured in a way that ensures clean code organization, modularity, and maintainability. Below is a brief explanation of the main directories and their responsibilities inside the `app/` folder.

  ### 1. `routers/`
    - This directory contains all the route definitions for the application.
    - Each route is structured to call the respective controllers.
    - Ensures clean separation between route handling and business logic.

  ### 2. `controllers/`
    - Contains the core business logic of the application.
    - Handles requests from `routers` and interacts with the `Repository` layer for data operations.
    - Returns appropriate responses to clients.

  ### 3. `Repository/` (DB Service)
    - Responsible for database interactions and queries.
    - Provides a structured way to handle CRUD operations.
    - Abstracts direct database queries away from controllers.

  ### 4. `Tasks/` (AI Functions)
    - Houses AI-related functionalities and processing.
    - Used for handling machine learning models, automation, or data processing tasks.

  ### 5. `Services/`
    - Contains all minor services required for the project.
    - Examples include authentication, external API integrations, background jobs, and utility services.

  ### 6. `helpers/`
    - Includes helper functions used across the project.
    - May include utility functions for formatting, validation, or common reusable logic.

  ### 7. Other Essential Directories
    - **`models/`**: Defines database schemas and ORM models.
    - **`utils/`**: Stores various utility functions that assist in different parts of the application.
    - **`validators/`**: Contains validation logic for input data and request payloads.

  This folder structure ensures separation of concerns, making the project scalable and easy to maintain.
- **main.py**: The entry point of the FastAPI application.
- **pyproject.toml**: Lists the project dependencies and metadata.

## Directory and File Descriptions

### `src/` Directory
- **emailCoordination/**: Contains modules related to coordinating email communications. -- Incomplete
- **jobDescription/**: Manages job description functionalities, including routes and logic for handling job descriptions.
- **databaseQuery/**: Handles database queries and interactions. -- Incomplete
- **auth/**: Manages authentication processes and user management. -- Unchecked
- **resumeParsing/**: Contains logic and routes for parsing and handling resumes.
- **chatbot/**: Manages chatbot interactions and related functionalities.
- **helper.py**: A utility file that provides helper functions used across various modules.
- **__init__.py**: An empty file, typically used to mark a directory as a Python package.

### `tasks/` Directory
- **resume_parsing_worker.py**: A Celery worker script for handling resume parsing tasks asynchronously.
- **database_worker.py**: Manages database-related tasks using Celery. -- Incomplete
- **celery_app.py**: Configures the Celery application, including broker and backend settings.
- **job_description_worker.py**: Handles job description-related tasks asynchronously using Celery.
- **__init__.py**: An empty file, marking the directory as a Python package.

## Installation Instructions
1. **Install Python**: Ensure you have Python installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/).

2. **Install Dependencies**: Use the following command to install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```
   Alternatively, you can use the `pyproject.toml` file with a tool like `poetry` or `pipenv`.

3. **Install UV**: Follow the installation guide provided in the [UV documentation](https://docs.astral.sh/uv/#installation).

4. **Sync UV**: Run the following command to sync UV:
   ```sh
   uv sync
   ```

## Running the Project
To run the FastAPI application, execute the following command:
```sh
uv run fastapi run main.py
```
```sh
uv run uvicorn main:app --reload
```

## Docker Setup
To run the project using Docker, follow these steps:
1. **Build the Docker Image**: Create a `Dockerfile` in the project root and define the necessary instructions to build the image.
2. **Run the Docker Container**: Use the `docker run` command to start the container.

## Future Implementations
- **Empty Files**: Some files are currently placeholders and are intended for future development. These include `__init__.py` files in various directories, which will be implemented as the project evolves.

## Additional Notes
- **RabbitMQ Setup**: Set up RabbitMQ either locally or using Docker to handle message brokering for Celery tasks.
If running locally, run the following command:
for installation of rabbitmq:
```sh
brew install rabbitmq
```
for running the server:
```sh
rabbitmq-server
```

## Running the Scripts
- **FastAPI Application**: Run the main application using the command:
  ```sh
  uv run fastapi run main.py
  ```
- **Celery Workers**: Start the Celery workers for handling asynchronous tasks. For example, to start the resume parsing worker, use:
  **For Linux**
  ```sh
  celery -A app.tasks.celery_app worker --loglevel=info -Q job_description,resumes,assessments
  ```
  #### setting autoreloader- 
  ```sh
  watchmedo auto-restart --directory=./ --pattern="*.py" --recursive -- celery -A app.tasks.
celery_app worker --loglevel=info -Q job_description,resumes
  ```
  **For Windows**
  ```sh
  celery -A app.tasks.celery_app worker --pool=solo -l info -Q job_description,resumes
  ```
  Repeat similar commands for other workers like `database_worker` and `email_worker`.

## Project Key Mappings
- **FastAPI Routers**: The `main.py` file includes routers for different modules, mapping URLs to specific functionalities like job descriptions, resumes, and chatbots.
- **Celery Tasks**: Each worker script in the `tasks` directory maps specific tasks to be executed asynchronously, allowing for efficient background processing.
