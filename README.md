# Car Catalog API

Welcome to the Car Catalog API! This Django project serves as a comprehensive API for managing vehicles, tags, and specifications, providing a robust car catalog system.

## Table of Contents
- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Running the Server](#running-server)

## Overview

The Car Catalog API is designed to be a central hub for managing information related to vehicles, including details about specifications, tags, and user authentication. The API follows RESTful principles and is built using Django.

## API Endpoints

The Car Catalog API provides the following endpoints:

### Health Check

- **Endpoint**: `/api/health-check/`
- **Method**: `GET`
- **Description**: Returns a successful response.

### Schema

- **Endpoint**: `/api/schema/`
- **Method**: `GET`
- **Description**: Retrieve the OpenAPI3 schema for this API.

### User

#### Create User

- **Endpoint**: `/api/user/create/`
- **Method**: `POST`
- **Description**: Create a new user in the system.

#### Retrieve Authenticated User

- **Endpoint**: `/api/user/me/`
- **Method**: `GET`
- **Description**: Retrieve information about the authenticated user.

#### Update Authenticated User

- **Endpoint**: `/api/user/me/`
- **Method**: `PUT`
- **Description**: Update information for the authenticated user.

#### Partially Update Authenticated User

- **Endpoint**: `/api/user/me/`
- **Method**: `PATCH`
- **Description**: Partially update information for the authenticated user.

#### Create Auth Token

- **Endpoint**: `/api/user/token/`
- **Method**: `POST`
- **Description**: Create a new auth token for the user.

### Vehicle

#### Manage Specifications

- **Endpoint**: `/api/vehicle/specifications/`
- **Method**: `GET`
- **Description**: Manage specifications in the database.

#### Manage Tags

- **Endpoint**: `/api/vehicle/tags/`
- **Method**: `GET`
- **Description**: Manage tags in the database.

#### Manage Vehicles

- **Endpoint**: `/api/vehicle/vehicles/`
- **Method**: `GET`
- **Description**: View for managing vehicle APIs.

### Upload Vehicle Image

- **Endpoint**: `/api/vehicle/vehicles/{id}/upload_image/`
- **Method**: `POST`
- **Description**: Upload an image to a vehicle.

## Running server

### Local Development
- **Build and run the Docker containers locally:**: `docker-compose -f docker-compose.yml up -d`

### Dev Server Development
- **Build and run the Docker containers on a server:**: `docker-compose -f docker-compose-deploy.yml up -d`
