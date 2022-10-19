# Climate Token Driver Suite

This repository is intended to be used in multiple components in the Climate Portal system, including

- Climate Portal
- Climate Wallet
- Climate Explorer

## Hierarchy

- `app`:
    - `api`: API layer implementations
    - `core`: service layer implementations
    - `crud`: repository layer implementations
    - `db`: database utilities
    - `models`: database models
    - `schemas`: schemas shared by all the layers


## Usage

### Run from source for developement

- [Install Poetry](https://python-poetry.org/docs/)

- Optionally create virtual environment, and install dependencies
  ```sh
  python -m virtualenv venv && source venv/bin/activate
  poetry install
  ```

- Run the main script
  ```sh
  MODE=dev CHIA_ROOT=~/.chia/testnet10 python app/main.py
  ```

### Package and run app

- Make a `.env` file for your enviroment variables
  ```sh
  cp .env.example .env
  # change variable in .env
  ```

- Package the app
  ```sh
  make package-app
  ```

- Run the binary/executable
  ```sh
  MODE=dev CHIA_ROOT=~/.chia/testnet10 ./dist/main
  ```
