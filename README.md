# Personal Expenditure Manager

INF1103 Team Project, LAB-P11 Group 5.

Young adults often have to read through bank statements line by line to
understand where their money goes. This app takes uploaded statements, uses
Gemini to turn each raw line into a standardised, categorised transaction, and
then applies business rules to produce a spending assessment with
recommendations.

## Team

| Name | Student ID |
|---|---|
| Loh Cheng Hong Ashton | 2601559 |
| Darryl Lim Hui Yang | 2601735 |
| Samuel Lim En Yao | 2601923 |
| Lim Choi Hwee | 2603613 |
| Edmund Chan Yi Siong | 2604454 | 


## Run the tests

The test script needs no API key and no internet connection.

```bash
docker run --rm expense-manager python -m pytest tests -v
```

## Run without Docker

Requires Python 3.14.

```bash
pip install -r requirements.txt
python -m streamlit run io_manager.py
python -m pytest tests -v
```

The first start downloads the WordNet word data used for category
suggestions, so it needs internet once. The Docker image has it built in.

## Using the app

1. **Upload** tab: upload a statement (PDF, CSV, JSON, PNG or JPG). Gemini
   extracts and categorises each transaction, and valid records are saved.
2. **Recommendation** tab:
   - view the transactions as a table and as charts, filtered by month
   - add, edit or archive a transaction; every edit and archive is recorded
     in the audit trail
   - review transactions the AI filed as "Misc" and recategorise them from a
     typed description
   - select a month, enter a current balance and monthly income, and generate
     the assessment

## Structure

Data moves through four layers:

`user / file -> io_manager -> ai_manager -> logic_manager -> data_manager`

| File | Layer | Responsibility |
|---|---|---|
| `io_manager.py` | Input/output | Streamlit page: uploads, forms, tables, charts and all user-facing messages |
| `ai_manager.py` | AI | Builds prompts, calls Gemini, validates the JSON response schema, retries and falls back to other models on failure |
| `logic_manager.py` | Logic | Business rules applied to the AI-categorised records |
| `data_manager.py` | Data | Loads and saves the CSV files, audit trail, filters, and recovery from a missing or corrupt file |
| `InputDescription.py` | Helper | Suggests a category from a typed description using WordNet |
| `tests/` | Tests | Automated tests for the logic and data managers |

The code is fully procedural: functions only, no classes.

## Business rules

| Rule | Flags when |
|---|---|
| Cash-flow risk | Net cash flow over the latest 30 days, less planned expenses, is below S$0 |
| High bills burden | Bills exceed 5% of monthly income |
| Excessive discretionary spending | Entertainment and Shopping (optionally Misc) exceed 50% of monthly income |
| Excessive non-essential spending | Spending outside Food, Groceries, Transport and Bills exceeds 50% of monthly income |
| Emergency fund inadequacy | Current balance is below 3 months of average essential expenses |
| Irregular income | Income over the latest 3 months varies by more than 20% of its average |
| Subscription creep | Subscriptions over the latest 30 days exceed 5% of monthly income |
| High savings (stagnant) | Current balance exceeds 80% of monthly income |

## Data

All data is stored in flat CSV files in the `data` folder.

| File | Contents |
|---|---|
| `data/collated_data.csv` | Every transaction: `transaction_id`, `date_and_time`, `retailer`, `category`, `transaction_amount`, `transaction_type`, `description` |
| `data/audit_trail.csv` | Log of edits and archives with the old and new values. Created on first use |

Sample transactions are included so the app has records on first run. Saves
are written to a temporary file first, and an unreadable data file is renamed
to `*.corrupt-<timestamp>.csv` instead of being overwritten.

## CI/CD

The project uses one GitHub Actions workflow, `.github/workflows/tests.yml`,
with three jobs.

| Job | Stage | Runs on | What it does |
|---|---|---|---|
| Run test script | CI | Every push and every pull request to `main` | Installs `requirements.txt` on a clean machine and runs the automated tests |
| Build image and test inside container | CI | Every push and every pull request to `main` | Builds the Docker image from the `Dockerfile` and runs the tests inside the container |
| Package Docker image | CD | Pushes to `main` only, after both CI jobs pass | Rebuilds the image, re-runs the tests inside it, and publishes it as a downloadable artifact |

### Continuous integration

Every change is tested automatically before it can be merged. The result
appears as a tick or a cross next to the commit and on the pull request. The
tests use hardcoded sample records, so the workflow needs no API key.

### Continuous delivery

Each merge to `main` produces a ready-to-run Docker image built from exactly
what is on `main`. If either CI job fails, no image is published.

To use a delivered image:

1. On GitHub, open the **Actions** tab and select the latest run on `main`.
2. Under **Artifacts**, download `expense-manager-image` and unzip it to get
   `expense-manager.tar.gz`.
3. Load and run it:

```bash
docker load -i expense-manager.tar.gz
docker run --rm -p 8501:8501 expense-manager
```

Open http://localhost:8501 and enter a Gemini API key in the sidebar.
Artifacts are kept for 14 days.
