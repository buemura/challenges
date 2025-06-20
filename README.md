# memory-efficient-data-pipeline

Memory-Efficient Data Pipeline Design a data processing pipeline that:

- Processes a stream of incoming JSON data from a webhook.
- Transforms and aggregates the data using generators and iterators.
- Outputs results to both a database and a message queue.

  Constraints:

- Must handle variable-rate data influx efficiently.
- Should maintain constant memory usage regardless of input volume.

## Setup

1. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

Start the API server using Uvicorn:

```bash
uvicorn main:app --reload
```

You can customize parameters such as host and port:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
