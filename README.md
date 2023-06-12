# Climate Token Driver Suite

This application can run in 4 modes, each providing a separate application with a distinct use case:

* **Chia Climate Tokenization**:
  * Mode: Registry
  * Use case: A registry would use this to tokenize carbon credits onto the Chia blockchain
  * Port: 31312
  * Application Name: climate-tokenization-chia
  * *Only listens on localhost for connections from the [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine)*
* **Climate Explorer**:
  * Mode: Explorer
  * Use case: A registry (or interested observer) would use this to track all on-chain activity related to tokenized carbon credits
  * Port: 31313
  * Application Name: climate-explorer
* **Climate Token Driver**:
  * Mode: Client
  * Use case: A carbon token holder could use this in conjunction with the [Climate Wallet](https://github.com/Chia-Network/Climate-Wallet) to manage their tokenized carbon credits
  * Port: 31314
  * Application Name: climate-tokenization-chia
* **Dev Mode (for developers only!)**:
  * Mode: Dev
  * Use case: Developers are able to test the software without having to communicate with the blockchain
  * Port: 31999
  * Application Name: Only available from source builds

When compiling from source, the "mode" is controlled by the `.env` file.  Each application, or mode, is offered as precompiled binaries, appropriate for most users.

## Related Projects

* [Chia Blockchain](https://github.com/Chia-Network/chia-blockchain)
* [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine)
* [Climate Tokenization Engine User Interface](https://github.com/Chia-Network/Climate-Tokenization-Engine-UI)
* [Climate Explorer UI](https://github.com/Chia-Network/climate-explorer-ui)
* [Climate Wallet](https://github.com/Chia-Network/Climate-Wallet)
* [Climate Action Data Trust](https://github.com/Chia-Network/cadt)
* [Climate Action Data Trust UI](https://github.com/Chia-Network/cadt-ui)

## Hierarchy

- `app`:
    - `api`: API layer implementations
    - `core`: service layer implementations
    - `crud`: repository layer implementations
    - `db`: database utilities
    - `models`: database models
    - `schemas`: schemas shared by all the layers
- `tests`: pytest suites

## Installation and configuration

Precompiled executables are available for Mac, Windows, and Linux (both ARM and x86) on the [releases](https://github.com/Chia-Network/climate-token-driver/releases) page.

### Debian-based Linux Distros

For users of Debian, Ubuntu, Mint, PopOS, and other Debian-based distributions, a .deb file is provided on the [releases](https://github.com/Chia-Network/climate-token-driver/releases) page.  This can be installed with

```sh
dpkg -i package-filename.deb
```

### From Source

- Clone this repo.

  ```sh
  git clone --recurse-submodules https://github.com/Chia-Network/climate-token-driver.git
  ```

  or, using SSH...

  ```sh
  git clone --recurse-submodules git@github.com:Chia-Network/climate-token-driver.git
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

## Configurations

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
- `SERVER_HOST`: the network IP address this application binds to.  Setting to `0.0.0.0` listens on all interfaces, which is appropriate when running the Climate Explorer.  When running Chia Climate Tokenization, the `SERVER_HOST` must be `localhost` or `127.0.0.1` as this prevents the registry from accidentally being available on the public web, which would be a severe security issue.  When in Chia Climate Tokenization mode, the application should only be receiving requests from the [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine) which is expected to be run on the same host as Chia Climate Tokenization.
- `SERVER_PORT`: you can leave this blank and the port will be automatically assigned based on `MODE`:
  - `dev`: 31999
  - `registry`: 31312
  - `explorer`: 31313
  - `client`: 31314

- `LOG_PATH`: the path this application write logs to, relative to `${CHIA_ROOT}`.
- `CADT_API_SERVER_HOST`: the climate warehouse API URL.
- `CADT_API_KEY`: the climate warehouse API key.

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

## For Developers

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
### Commiting

​This repo uses a [commit convention](https://www.conventionalcommits.org/en/v1.0.0/). A typical commit message might read:
​
```
    fix: correct home screen layout
```
​
The first part of this is the commit "type". The most common types are "feat" for new features, and "fix" for bugfixes. Using these commit types helps us correctly manage our version numbers and changelogs. Since our release process calculates new version numbers from our commits it is very important to get this right.
​

- `feat` is for introducing a new feature
- `fix` is for bug fixes
- `docs` for documentation only changes
- `style` is for code formatting only
- `refactor` is for changes to code which should not be detectable by users or testers
- `perf` is for a code change that improves performance
- `test` is for changes which only touch test files or related tooling
- `build` is for changes which only touch our develop/release tools
- `ci` is for changes to the continuous integration files and scripts
- `chore` is for changes that don't modify code, like a version bump
- `revert` is for reverting a previous commit

After the type and scope there should be a colon.

 ​
The "subject" of the commit follows. It should be a short indication of the change. The commit convention prefers that this is written in the present-imperative tense.


#### Branch Layout

All pull requests should be made against the `develop` branch.  Commits to the `main` branch will trigger a release, so the `main` branch is always the code in the latest release.
