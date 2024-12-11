# Climate Token Driver Suite

![Minimum Chia Version](https://raw.githubusercontent.com/Chia-Network/core-registry-api/main/minimumChiaVersion.svg)
![Tested Up to Chia Version](https://raw.githubusercontent.com/Chia-Network/core-registry-api/main/testedChiaVersion.svg)

This application can run in 4 modes, each providing a separate application with a distinct use case:

- **Chia Climate Tokenization**:
  - Mode: Registry
  - Use case: A registry would use this to tokenize carbon credits onto the Chia blockchain
  - Port: 31312
  - Application Name: climate-tokenization-chia
  - Only listens on localhost for connections from the [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine)
- **Climate Explorer**:
  - Mode: Explorer
  - Use case: A registry (or interested observer) would use this to track all on-chain activity related to tokenized carbon credits
  - Port: 31313
  - Application Name: climate-explorer
- **Climate Token Driver**:
  - Mode: Client
  - Use case: A carbon token holder could use this in conjunction with the [Climate Wallet](https://github.com/Chia-Network/Climate-Wallet) to manage their tokenized carbon credits
  - Port: 31314
  - Application Name: climate-token-driver
- **Dev Mode (for developers only!)**:
  - Mode: Dev
  - Use case: Developers are able to test the software without having to communicate with the blockchain
  - Port: 31999
  - Application Name: Only available from source builds

When compiling from source, the "mode" is controlled by the `.env` file. Each application, or mode, is offered as precompiled binaries, appropriate for most users.

## Related Projects

- [Chia Blockchain](https://github.com/Chia-Network/chia-blockchain)
- [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine)
- [Climate Tokenization Engine User Interface](https://github.com/Chia-Network/Climate-Tokenization-Engine-UI)
- [Climate Explorer UI](https://github.com/Chia-Network/climate-explorer-ui)
- [Climate Wallet](https://github.com/Chia-Network/Climate-Wallet)
- [Climate Action Data Trust](https://github.com/Chia-Network/cadt)
- [Climate Action Data Trust UI](https://github.com/Chia-Network/cadt-ui)

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

For users of Debian, Ubuntu, Mint, PopOS, and other Debian-based distributions, a .deb file is provided on the [releases](https://github.com/Chia-Network/climate-token-driver/releases) page. This can be installed with

```sh
dpkg -i package-filename.deb
```

The Chia Climate Tokenization and Climate Explorer applications are also available via apt:

1. Start by updating apt and allowing repository download over HTTPS:

```
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
```

2.  Add Chia's official GPG Key (if you have installed Chia with `apt`, you'll have this key already and will get a message about overwriting the existing key, which is safe to do):

```
curl -sL https://repo.chia.net/FD39E6D3.pubkey.asc | sudo gpg --dearmor -o /usr/share/keyrings/chia.gpg
```

3. Use the following command to setup the repository.

```
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/chia.gpg] https://repo.chia.net/climate-tokenization/debian/ stable main" | sudo tee /etc/apt/sources.list.d/climate-tokenization.list > /dev/null
```

4.  Install Chia Clmate Tokenization and Climate Explorer

```
sudo apt-get update
sudo apt-get install climate-tokenization-chia
sudo apt-get install climate-explorer-chia
```

5.  Start Chia Climate Tokenization and Climate Explorer with systemd

```
sudo systemctl start climate-tokenization-chia@<USERNAME>
sudo systemctl start climate-explorer-chia@<USERNAME>
```

For `<USERNAME>`, enter the user that Chia runs as (the user with the `.chia` directory in their home directory). For example, if the `ubuntu` is where Chia runs, start Chia Climate Tokenization with `systemctl start climate-tokenization-chia@ubuntu`.

6.  Set the Chia Climate Tokenization and Climate Explorer to run at boot

```
sudo systemctl enable climate-tokenization-chia@<USERNAME>
sudo systemctl enable climate-explorer-chia@<USERNAME>
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

1. The application will first look for any environment variables set on the host machine for `MODE`, `CHIA_ROOT`, and `CONFIG_PATH`. Any variables not set on the host system will be loaded from the `.env` environment file, which is opened via `python-dotenv`, where `${CHIA_ROOT}` and `${CONFIG_PATH}` are pre-loaded. This file is not visible to end users in packaged binaries, and are suitable for binary builders to change the default _flavor_ for the binary (though it is overridden by system environment variables).

1. Then, a `config.yaml` file located at `${CHIA_ROOT}/${CONFIG_PATH}` is loaded, which adds to the configurations after `.env`.
   This part of the configuration is free to change by end binary users.
   When the application is closed and reopened, the new configurable would automatically apply.

The whole list of configurable variables are detailed in [config.py](app/config.py), and below we provide brief explanations:

- `MODE (environment variable)`: one of `dev`, `registry`, `client`, and `explorer`. In `dev` mode, the application essentially enables all functionalities (endpoints), while in the rest, some select endpoints will be allowed. Each mode has installers and executable binaries built and available on the [releases](https://github.com/Chia-Network/climate-token-driver/releases) page.
- `CHIA_ROOT (environment variable)`: the root of Chia wallets on the local machine, typically `~/.chia/mainnet`.
- `CONFIG_PATH (environment variable)`: the path of the `config.yaml` file, relative to `${CHIA_ROOT}`. Rarely needs to be changed.
- `LOG_PATH`: the path this application write logs to, relative to `${CHIA_ROOT}`. Can also be set to `stdout`. 
- `CADT_API_SERVER_HOST`: the CADT API URL in the format of `scheme://domain:port/path`.
- `CADT_API_KEY`: the CADT API key.

Only when in `registry` (Chia Climate Tokenization) and `client` (Climate Token Driver) modes, the following configurations are relevant:

- `DEFAULT_FEE`: the fee, in mojos, for token-related transactions.
- `CHIA_HOSTNAME`: the Chia service to connect to.
- `CHIA_FULL_NODE_RPC_PORT`: the Chia full node RPC port.
- `CHIA_WALLET_RPC_PORT`: the Chia wallet RPC port.

Only in `registry` mode (Chia Climate Tokenization), the following configurations are relevant:

- `CLIMATE_TOKEN_REGISTRY_PORT`: 31312 by default.

There is no option to set the `SERVER_HOST` in registry mode as this is designed to only integrate with the [Climate Tokenization Engine](https://github.com/Chia-Network/Climate-Tokenization-Engine) or other tokenization engines on localhost and will therefore only listen on 127.0.0.1.

Only in `client` mode (Climate Token Driver) are the following configurations relevant:

- `CLIMATE_TOKEN_CLIENT_PORT`: 31314 by default.

As with `registry` mode, `client` mode is only designed to integrate with other tools (such as the [Climate Wallet](https://github.com/Chia-Network/Climate-Wallet)) on localhost and therefore only listens on 127.0.0.1.

Only when in `explorer` mode, the following configurations are relevant:

- `CLIMATE_EXPLORER_SERVER_HOST`: Network interface to bind the climate explorer to. Default is `0.0.0.0` as the Climate Explorer is intended to be a publicly available interface. Can be set to `127.0.0.1` to be privately available only on localhost.
- `CLIMATE_EXPLORER_PORT`: 31313 by default.
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

- Install node.js for linter using [nvm](https://github.com/nvm-sh/nvm)

  ```sh
  nvm install
  nvm use
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

[Signed commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits) are required.

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

All pull requests should be made against the `develop` branch. Commits to the `main` branch will trigger a release, so the `main` branch is always the code in the latest release.
