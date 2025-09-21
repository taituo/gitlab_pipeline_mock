# Build and Test Guide

These commands wrap the project workflow. All tasks run inside the local virtual environment created under `.venv`.

## Install dependencies

```sh
make install
```

- Creates `.venv` if needed using `python3 -m venv` (override with `PYTHON=python3.11` etc.).
- Installs the project in editable mode with dev dependencies (`pip install -e .[dev]`).

## Run the test suite

```sh
make test
```

- Ensures dependencies are present (`make install`).
- Executes `pytest` which covers trigger/poll flows and scenario CRUD (see `tests/test_pipelines.py`).

## Launch the API locally

```sh
make run
```

- Starts `uvicorn app.main:app --reload` using the virtualenv binary.
- Export `MOCK_TOKEN` before running to match your client expectations.

## Clean the environment

```sh
make clean
```

- Removes the `.venv` directory to reset the toolchain.

## Manual workflow (if required)

If Make is unavailable, replicate the steps manually:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn app.main:app --reload
```

The automated tests mirror the `curl` flows in `EXAMPLE.md`, so running them ensures the documented scenarios remain valid.
