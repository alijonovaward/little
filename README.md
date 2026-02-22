# Chatbot Service
[![Deploy to server](https://github.com/karimoff96/DjangoTemplate.git/actions/workflows/deploy.yml/badge.svg?branch=master)](https://github.com/karimoff96/Million-halal-mart.git/actions/workflows/deploy.yml)

Welcome to Django+Docker initial template repository. This is dockerized django project for easy setup and deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Running the Service](#running-the-service)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed:
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Setup and Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/karimoff96/Million-halal-mart.git
   cd 

## Environment Configuration:

Copy the provided `.env.example` file to a new file named `.env` in the root directory. Adjust the variables in `.env` as necessary for your setup.

```bash
cp .env.example .env

docker-compose build

docker-compose up
```
In order to create django app the docker containers should be running then first create `apps` folder and inside apps folder create an empty folder with your app name. (apps/myapp) then run following command:
```bash
docker-compose exec web bash #for entering inside the web container
python manage.py startapp folder /apps/myapp
```

This will start the Django application and its associated services. Once running, you can access the application at [http://localhost:8000](http://localhost:8000).
## Production :
```bash
cp .env.example .env

docker-compose -f docker-compose.prod.yml build

docker-compose -f docker-compose.prod.yml up
```

This will start the Django application and its associated services. Once running, you can access the application at [http://domain](http://domain).

## Features

- **RESTful API**: Interact with the template using a simple REST API.
- **Docker Support**: Easily deploy and scale the service using Docker.

## Contributing

We welcome contributions! If you'd like to contribute, please fork the repository, make your changes, and submit a pull request. Ensure your changes are well-documented.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.


