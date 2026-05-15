# Oura Personal Health Dashboard & ML Analytics

A self-hosted project to collect, visualize, and analyze biometric data from the Oura API, with a focus on personal experimentation and machine learning.

---

## Important Disclaimer

This repository contains source code only.

* This is not a hosted service
* The developer does not run any servers or backend for users
* The developer does not receive, store, or process any user data

If you clone or use this repository:

> You are fully responsible for your deployment, your data, and how the software is used.

- [Terms of Service](./TERMS_OF_SERVICE.md)
- [Privacy Policy](./PRIVACY_POLICY.md)

---

## Overview

This project enables individuals to build their own private health dashboard and analytics pipeline using data from the Oura API.

All data flows directly between:

* Your environment
* The Oura API

The developer is not involved in this process.

---

## Features

### Data Ingestion

* Fetch data from Oura API v2
* Supported endpoints:

  * Personal info
  * Sleep
  * Activity
  * Readiness
  * Heart rate

### Dashboard

* Readiness score, HRV balance, resting-heart-rate contributor, temperature deviation
* Sleep score, total sleep duration, sleep efficiency, restless periods
* Activity score, steps, active calories, walking distance
* Heart-rate latest sample, average BPM, sample count
* 7-180 day selectable data window
* Raw data previews for validation and debugging

### Authentication Harness

* Personal Access Token support via `OURA_ACCESS_TOKEN`
* Sidebar status check without revealing the token
* Tokens stay in your shell, service manager, or local secret manager
* `.env` and Streamlit secrets are ignored by Git

---

## Architecture

```text
Your Oura Account -> Your App Instance -> Oura API -> Local Dashboard
```

Core files:

* `dashboard.py` - Streamlit UI
* `oura_project/auth.py` - local token/auth status harness
* `oura_project/client.py` - Oura API v2 client
* `oura_project/metrics.py` - summary helpers for dashboard cards
* `tests/test_metrics.py` - standard-library tests for auth, date ranges, and metrics

---

## Setup

### Prerequisites

* Oura account with active membership
* Python 3.11+
* Oura Personal Access Token

Create a personal access token in your Oura developer settings, then keep it outside the repository.

### Environment Variables

```bash
cp .env.example .env
export OURA_ACCESS_TOKEN=your_personal_access_token
export OURA_DAYS_BACK=30
```

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run dashboard.py
```

### Run Tests

```bash
python3 -m unittest discover -s tests -v
```

---

## Example API Call

```http
GET https://api.ouraring.com/v2/usercollection/daily_sleep
Authorization: Bearer <access_token>
```

The app performs live API calls through `oura_project/client.py` and never commits tokens or response data.

---

## Data & Privacy

* The developer does not collect or access any user data
* All data remains within your own environment
* You are responsible for:

  * Data storage
  * Security
  * Compliance with applicable laws

---

## No Medical Advice

This project is for informational and experimental purposes only.

* It does not provide medical advice
* It is not a medical device
* Do not use it for diagnosis or treatment

---

## Responsibility

By using this project, you acknowledge:

* You run and manage the software independently
* You are solely responsible for your data and usage
* The developer is not liable for any outcomes, including:

  * Data issues
  * Incorrect analysis
  * Health-related decisions

---

## ML Ideas

* Predict readiness from sleep/activity
* Detect overtraining or fatigue
* Identify optimal sleep patterns
* Build personalized health scoring

---

## Future Improvements

* OAuth 2.0 callback flow for multi-user deployment
* Local encrypted token storage
* Webhook-based updates
* Multi-source integrations such as Apple Health or Garmin
* Advanced ML models
* Automated insights

---

## License

See LICENSE file (MIT License).

---

## Motivation

A personal exploration of turning raw health data into meaningful insights through:

> tracking -> understanding -> modeling -> experimentation

---

## Contact

[Thomas Kirisits](https://github.com/ThomasKirisits)
