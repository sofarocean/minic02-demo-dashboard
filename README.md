# MiniCO2 Demo Dashboard

Python Streamlit app for viewing CO2 sensor data on a simple map dashboard.

## Setup

### Create and Activate a Virtual Environment

Create the virtual environment:

    python -m venv venv

Activate it (macOS/Linux):

    source venv/bin/activate

### Install Dependencies

    pip install -r requirements.txt

### Environment Configuration (Optional)

To pre-fill the dashboard form fields during development, copy the example environment file:

    cp .env.example .env

Then edit `.env` with your preferred defaults:

```bash
DEFAULT_SPOTTER_ID=SPOT-31299C
DEFAULT_API_TOKEN=your_api_token_here
DEFAULT_START_DATE=2025-01-01T00:00Z
```

### Deactivate the Virtual Environment

When you're done working on the project:

    deactivate

## How to Use

Run locally with:

    streamlit run app.py

## Dev Notes
