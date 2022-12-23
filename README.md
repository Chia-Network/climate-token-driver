# Climate Token Driver Suite

This repository is intended to be used in multiple components in the Climate Portal system, including

- Climate Portal (as token driver)
- Climate Wallet (as token driver)
- Climate Explorer (as token driver and backend)

## Hierarchy

- `app`:
    - `api`: API layer implementations
    - `core`: service layer implementations
    - `crud`: repository layer implementations
    - `db`: database utilities
    - `models`: database models
    - `schemas`: schemas shared by all the layers
- `tests`: pytest suites

## Usage

### Installation and configuration

- Clone this repo.

  ```sh
  git clone --recurse-submodules https://github.com/Chia-Network/climate-token-driver.git
  ```

- Note that `chia-blockchain` is used as a submodule of this repo to involve its test suites from the source file.
  Include `chia-blockchain` in python search path with:

  ```sh
  export PYTHONPATH=.:./chia-blockchain:$PYTHONPATH
  ```

- Make a `.env` file for your environment variables.
  See the section below for setting up a correct `.env` file.

  ```sh
  cp .env.example .env
  # then change variable in .env
  ```

### Configurations

Note there are two steps the application loads the configurations:
1. The application will first look for any environment variables set on the host machine for `MODE`, `CHIA_ROOT`, `CONFIG_PATH`, and `SERVER_PORT`.
   Any variables not set on the host system will be loaded from the `.env` environment file, which is opened via `python-dotenv`, where `${CHIA_ROOT}` 
   and `${CONFIG_PATH}` are pre-loaded. This file is not visible to end users in packaged binaries, and are suitable for binary builders to change the 
   default *flavor* for the binary (though it is overridden by system environment variables).

1. Then, a `config.yaml` file located at `${CHIA_ROOT}/${CONFIG_PATH}` is loaded, which adds to the configurations after `.env`.
   This part of the configuration is free to change by end binary users.
   When the application is closed and reopened, the new configurable would automatically apply.

The whole list of configurable variables are detailed in [config.py](app/config.py), and below we provide brief explanations:

- `MODE`: one of `dev`, `registry`, `client`, and `explorer`.
          In the first mode, the application essentially enables all functionalities (endpoints), while in the rest, some select endpoints will be allowed.
          Make sure the binaries are built with `MODE` not equal to `dev`.

- `CHIA_ROOT`: the root of Chia wallets on the local machine, typically `~/.chia/mainnet`.
- `CONFIG_PATH`: the path of the `config.yaml` file, relative to `${CHIA_ROOT}`.
- `SERVER_HOST`: the host this application runs on.
- `SERVER_PORT`: you can leave this blank and the port will be automatically assigned based on `MODE`:
  - `dev`: 31999
  - `registry`: 31312
  - `explorer`: 31313
  - `client`: 31314

- `LOG_PATH`: the path this application write logs to, relative to `${CHIA_ROOT}`.
- `CLIMATE_API_URL`: the climate warehouse API URL.

Only when in `registry` and `client` modes, the following configurations are relevant:

- `DEFAULT_FEE`: the fee, in mojos, for token-related transactions.
- `CHIA_HOSTNAME`: the Chia service to connect to.
- `CHIA_FULL_NODE_RPC_PORT`: the Chia full node RPC port.
- `CHIA_WALLET_RPC_PORT`: the Chia wallet RPC port.

Only when in `explorer` mode, the following configurations are relevant:

- `DB_PATH`: the database this application writes to, relative to `${CHIA_ROOT}`.
- `BLOCK_START`: the block to start scanning for climate token activities.
- `BLOCK_RANGE`: the number of blocks to scan for climate token activities at a time.
- `MIN_DEPTH`: the minimum number of blocks an activity needs to be on chain to be recorded.
- `LOOKBACK_DEPTH`: this number of latest blocks are always rescanned to ensure all latest token activities are picked up for newly created tokens.

### Run from source for development

- [Install Poetry](https://python-poetry.org/docs/)

- Optionally create virtual environment, and install dependencies.

  ```sh
  python -m virtualenv venv && source venv/bin/activate
  poetry install
  ```

- Run the main script for development.

  ```sh
  python app/main.py
  ```

### Package app

- Package the app.
  ```sh
  # first ensure the `MODE` is set to the intended mode, then
  python -m PyInstaller --clean pyinstaller.spec
  ```

- Run the binary.
  ```sh
  ./dist/main
  ```

### Run test cases
- Invoke `pytest` with:
  ```sh
  # first ensure the `MODE` is set to the `dev` for all tests to be discoverable, then
  python -m pytest ./tests
  ```
