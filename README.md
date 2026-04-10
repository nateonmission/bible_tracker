# Bible Tracker

A personal Bible reading tracker that runs locally on your computer. Log what you read, see your progress across the entire canon, and visualize your reading habit with a year-long heatmap.

## Features

- **Reading log** — record any passage by book, chapter, and verse with exact per-chapter verse limits enforced in the UI
- **Reading history** — view all past readings sorted chronologically or in biblical order; delete entries with confirmation
- **Heatmap** — GitHub-style activity grid showing daily verse counts over the past 365 days
- **Canon support** — switch between Protestant (66 books), Catholic (73 books), and Jewish/Tanakh (24 books); optionally include the Apocrypha when using the Protestant canon
- **Settings** — canon preference is persisted locally in the browser

## Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy, SQLite
- **Frontend:** Vanilla HTML/CSS/JavaScript (no build step)

## Installation

### Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/nateonmission/bible_tracker.git
   cd bible_tracker
   ```

2. **Create a virtual environment and install dependencies**

   With uv (recommended):
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install fastapi sqlalchemy uvicorn
   ```

3. **Seed the database**

   This creates `bible_tracker.db` and loads all book data for all canons:
   ```bash
   python seed_db.py
   ```

4. **Start the server**

   ```bash
   uvicorn main:app --reload
   ```

5. **Open the app**

   Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

## Running Tests

```bash
pytest test_main_routes.py
```

## Project Structure

```
bible_tracker/
├── data/               # CSV files with book data for each canon (P, C, J)
├── models/             # SQLAlchemy ORM models
├── routes/             # FastAPI route handlers
├── schemas/            # Pydantic request/response schemas
├── static/             # Frontend (index.html, js.js, styles.css)
├── database.py         # Database engine and session setup
├── main.py             # FastAPI app entry point
└── seed_db.py          # Database initialization and book seeding
```
