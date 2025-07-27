# TakNews

## Introduction and System Architecture

### Project Abstract:
The TakNews project is a backend system that gathers news articles from Zoomit.ir, stores them in a database, and makes them available through a flexible REST API. Built to be reliable and scalable, it was developed in three steps: designing the API and database, creating a web scraper, and automating everything with Celery and Docker. 


### Technology Stack:
TakNews uses a set of carefully selected technologies, each chosen to address specific functional and operational needs of the system. This includes efficient tools for web scraping and background task processing, as well as containerization solutions for simplified deployment and improved scalability. The table below provides an overview of the core technologies and their roles within the system.

|         Technology          |               Role               |                                                   	Rationale                                                   |
|:---------------------------:|:--------------------------------:|:--------------------------------------------------------------------------------------------------------------:|
| Django REST Framework (DRF) |            API Layer             |        Simplifies building RESTful endpoints, with support for serialization, authentication, and docs.        |
|           MariaDB           |             Database             |    MySQL‑compatible, production‑ready relational database offering high performance and easy maintenance..     |
|           Scrapy            |      Web Scraping Framework      |      Asynchronous processing and extensibility for efficient, large‑scale data extraction from web pages.      |
|         Playwright          |      Dynamic Page Rendering      |            Executes JavaScript in pages headlessly, ensuring accurate crawling of dynamic content.             |
|           Celery            |     Asynchronous Task Queue      |         Offloads long‑running jobs (like scraping) to background workers, keeping the API responsive.          |
|         Celery Beat         |          Task Scheduler          |         Automates periodic execution of tasks (e.g., scheduled crawling) without manual intervention.          |
|            Redis            |  Message Broker & Task Backend   |                 In‑memory data store for fast communication between Django and Celery workers.                 |
|           Flower            |       Celery Monitoring UI       |                   Live dashboard for tracking task execution and worker health in real time.                   |
|   Docker & Docker Compose   | Containerization & Orchestration | Packages each service into isolated containers, guaranteeing identical dev, test, and production environments. |


### Architectural Blueprint:
TakNews breaks the system into independent parts, each handling its own task. This makes the whole setup more scalable and reliable.

1. **Scheduled Trigger**

   Celery Beat runs every minute and enqueues a “scrape news” task.

2. **Task Queuing**

   The task lands in Redis (message broker) and waits in the queue.

3. **Task Consumption**

   A Celery worker watches Redis, picks up the task immediately, and runs it.

4. **Data Aggregation**

   The worker launches the Scrapy + Playwright spider against Zoomit.ir, extracts titles, content, tags, and cleans the results.

5. **Data Persistence**

   Cleaned articles are saved in the MySQL database.

6. **API Request**

   Clients send GET /api/news/ (or with filters) to the Django/DRF endpoint.
 
7. **API Response**

   Django queries MySQL (applying filters/pagination), serializes the results to JSON, and returns them.

8. **Orchestration**
   
   All services (Django, MySQL, Redis, Celery workers, Celery Beat) run in Docker Compose containers, communicating over a private network.

##  The Core API Engine 

This part explains the API that lets users access the collected news data. It was built using Django and Django REST Framework.

### Database Schema and Data Models

The API is based on a clear and simple database structure created using Django. It is designed to store news articles and their related information. The main parts of the database are:

* The Tag model stores categories or tags for news articles.

* The News model holds a news article with its title, content, source, publish date, active status, and related tags.

**Each news article can have multiple tags, and each tag can be associated with multiple news articles.**

### RESTful API Endpoints
The primary access point to the news data is a single list endpoint.

**Endpoint:** ``` GET /api/news/ ```

**Method:** ``` GET ```

Retrieves a paginated list of all news articles stored in the system.

Each article includes key fields such as id, title, content, source, published_at, and related tags_info.

**Endpoint:** ``` POST /api/news/ ```

**Method:** ``` POST ```

Creates a new news article.


The request should include title, content, source, published_at, and a list of tags.

On success, it returns the created article with its details.


### Advanced Filtering and Search Logic
The API supports advanced filtering via query parameters. To handle OR conditions in filters, the system uses Django Q objects to build dynamic queries. This allows combining multiple filters effectively. The table below shows available query parameters for /api/news/.

|    Parameter     |                  Description                  |        Example Usage        |
|:----------------:|:---------------------------------------------:|:---------------------------:|
|     tags         |           filters articles by tags            |     ?tags=ai,technology     |
| include_keyword  | includes only articles with the exact keyword |     ?include_keyword=ai     |
| exclude_keyword  |       removes articles with the keyword       | ?exclude_keyword=technology |


**These filters can be applied simultaneously to refine the search results more effectively.**

## Automated Data Aggregation
This section describes the web scraping part that gathers news content from the Zoomit website to populate the database.

### Scrapy
Scrapy is a Python framework used for web scraping. It helps extract data from websites efficiently and cleanly for further processing or storage. Its key advantages for this project include:   

* Asynchronous by Default: Scrapy is built on Twisted, an asynchronous networking library. This allows it to handle multiple requests concurrently, leading to significantly faster crawling speeds compared to sequential request libraries.

* Robust Selectors: It provides powerful and convenient mechanisms (CSS selectors and XPath) for extracting data from HTML/XML documents.

* Extensible Pipeline: Scrapy features an item processing pipeline, which allows for modular and reusable post-processing of scraped data, such as cleaning, validation, and storing it in a database.

### Spider Implementation: The "Zoomit" Scraper
A web scraper was developed using Scrapy to collect news articles from the Zoomit website and save them into the database. The spider starts by visiting Zoomit's archive pages and navigates through multiple pages (up to 10) to find new articles. If there are no news articles in the database, the spider crawls news from pages 1 to 10. Otherwise, it crawls only the new articles published after the latest one already stored in the database. The last saved article URL in the database is tracked to avoid duplicate scraping.

For each archive page, the spider extracts links matching a specific pattern that identifies news articles. It then requests each article page, extracts the title, full content, publication date (converting Jalali to Gregorian calendar), source URL, and associated tags. The content is cleaned by removing unnecessary characters and joining text fragments.

The scraper uses a delay and limits concurrent requests to avoid overloading the server. It also integrates with Playwright to handle dynamic web content. The collected data is sent to a custom Django pipeline for saving into the database.


## Asynchronous Operations and Automation
This section explains the parts that make the project an automated and production-ready system. It includes adding a task queue for asynchronous processing and containerizing the whole application stack.

### Celery Integration for Asynchronous Tasks
To keep the news data continuously updated, the Celery library was used to run the scraping function asynchronously and on a regular schedule. This ensures that new articles are fetched and saved to the database without interrupting the main application. Celery Beat was integrated to handle task scheduling. The entire system was also containerized using Docker to simplify deployment and management.

The Celery setup is defined in a dedicated celery.py file, linking the Celery app to Django settings. Redis acts as the message broker between Django and Celery workers. The scraping function was turned into a Celery task using @shared_task for asynchronous execution. Celery Beat handles periodic scheduling, ensuring the task runs regularly without manual triggers. Docker containerizes the whole application to ease deployment and management.

### Periodic Data Fetching with Celery Beat
To automate data collection, Celery Beat was used as a scheduler that runs tasks at regular times. This helps keep the news database updated by automatically running the scraping function without manual work.

A schedule was set up in Django settings to run the scraping task every few hours (for example, every 1 minute). When it’s time, Celery Beat adds the task to the Redis queue, and a worker runs it. This way, the data collection happens automatically and continuously.

### Task Monitoring with Flower
Celery Flower is a web-based monitoring tool for Celery that shows the real-time status of workers and tasks. It helps improve management and track the performance of the asynchronous task system.

## Environment Configuration and Deployment
This section provides a comprehensive guide to setting up and running the TakNews project, covering both local development and containerized deployment using Docker.

### Local Development Environment Setup
To run the project locally without Docker, follow these steps:

* Clone the project repository using Git.

* Create and activate a Python virtual environment.

* Install all required packages with ``` pip install -r requirements.txt. ```

* Create a .env file in the project folder and add the needed settings like SECRET_KEY, DEBUG mode, database URL, and Redis URL for Celery.

* Apply database migrations by running ``` python manage.py migrate. ```

* Start the services in separate terminals:

  * Run the Django server with ``` python manage.py runserver. ```

  * Start a Celery worker using ``` celery -A taknews worker -l info. ```

  * Start Celery Beat scheduler with ``` celery -A taknews beat -l info. ```

These steps prepare the environment to develop and test the application locally.

### Containerized Deployment with Docker
Docker and Docker Compose are used to create an isolated, repeatable, and easy-to-manage environment for the entire project. This approach is recommended for both development and production.

**Dockerfile**

A single Dockerfile builds the container image for the Django app, Celery worker, and Celery Beat services. It:

* Starts from a lightweight Python base image (like python:3.9-slim)

* Installs dependencies from requirements.txt

* Copies the project code into the container

* Sets the default command to run the app, usually using Gunicorn

**docker-compose.yml**
This file defines and connects all project services:

* db: MySQL database with persistent storage

* redis: Redis service acting as the Celery broker

* web: Main Django app, exposing port 8000, dependent on db and redis

* worker: Celery worker using the same image but a different command

* beat: Celery Beat scheduler, also using the same image with a different command

* flower: A monitoring tool for Celery, providing a web dashboard to track tasks and worker status.

* nginx: A reverse proxy server that routes incoming requests to the Django web app and serves static files.

**Running Commands**
To build and run all containers:

* Run ``` docker-compose build ``` to build the images

* Run ``` docker-compose up -d ``` to start all services in the background




