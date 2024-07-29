# HES-IE-Master-Group- MALTESERS

# Electricity Price Predictor

## Description

This web application provides future predictions of electricity prices based on a time series model trained on variables such as temperature, electricity demand, and other relevant factors. It features a React-based frontend and a Flask backend, with the backend containerized using Docker and deployed on Google Cloud Run.

## Technology Stack

-   **Frontend**: React.js
-   **Backend**: Flask
-   **Deployment**: Docker, Google Cloud Run

## Installation and Setup

Ensure you have Docker installed on your system to run the containerized application.

```bash
git clone https://github.com/Haya-dmarroquin/HES-IE-Master-Group-Project-MALTESERS
cd HES-IE-Master-Group-Project-MALTESERS
cd application_code
```

### Backend Setup

1. Navigate to the backend directory:

```bash
cd application_code/backend
```

2. Build the Docker container:

```bash
docker build -t electricity-price-predictor .
```

3. Alternatively, pull the pre-built Docker image from Docker Hub:

```bash
docker pull tkeereweer/flask-backend:v3
```

4. Run the container:

```bash
docker run -d -p 5000:5000 --name electricity-price-predictor
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd application_code/frontend
```

2. Install Required dependencies: `npm install`

3. Start the development server: `npm start`

## API Endpoints

-   `/get-graph` (GET): Returns historical data for the last year of electricity prices.
-   `/predict` (POST): Accepts an `end_date` and returns predictions from the current date up to the specified `end_date`.

## Environment Variables

Make sure to set up the necessary environment variables, particularly for deployment configurations:

-   `PORT`: The port on which the server runs (default is 5000).

## Deployment

This application is containerized with Docker and ready for deployment on Google Cloud Run. Detailed deployment instructions will be specific to your Google Cloud configuration.

## Additional Notes

-   Ensure that the `models` and `data` directories are correctly set up as per the Flask application's requirements.
-   Update paths and configurations as necessary depending on your specific environment and deployment needs.
