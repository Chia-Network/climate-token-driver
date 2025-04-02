## 1.1.3 (2025-04-02)

## 1.1.3-rc18 (2025-04-01)

## 1.1.3-rc17 (2025-04-01)

## 1.1.3-rc16 (2025-04-01)

## 1.1.3-rc15 (2025-04-01)

## 1.1.3-rc14 (2025-04-01)

## 1.1.3-rc13 (2025-04-01)

## 1.1.3-rc12 (2025-04-01)

## 1.1.3-rc11 (2025-04-01)

## 1.1.3-rc10 (2025-03-12)

## 1.1.3-rc9 (2025-03-11)

## 1.1.3-rc8 (2025-03-11)

## 1.1.3-rc7 (2025-03-11)

## 1.1.3-rc6 (2025-03-11)

## 1.1.3-rc5 (2025-03-11)

## 1.1.3-rc4 (2025-03-11)

## 1.1.3-rc3 (2025-03-11)

## 1.1.3-rc2 (2025-03-11)

## 1.1.3-rc1 (2025-03-07)

## 1.1.2-rc12 (2025-02-07)

## 1.1.2-rc11 (2025-02-07)

## 1.1.2-rc10 (2025-01-15)

## 1.1.2-rc9 (2025-01-13)

### Feat

- allow for connections to different hosts for wallet and full node

### Fix

- use ternary instead

## 1.1.2-rc8 (2025-01-08)

## 1.1.2-rc7 (2025-01-08)

## 1.1.2-rc6 (2025-01-08)

## 1.1.2-rc5 (2025-01-07)

## 1.1.2-rc4 (2025-01-07)

## 1.1.2-rc3 (2024-12-19)

### Refactor

- add disallow_route and disallow_startup decorators and tests

## 1.1.2 (2024-12-16)

## 1.1.2-rc2 (2024-12-13)

## 1.1.1 (2024-12-12)

## 1.1.0 (2024-11-12)

## 1.0.40 (2024-11-04)

## 1.0.39 (2024-04-05)

## 1.0.38 (2024-02-01)

## 1.0.37 (2023-12-12)

## 1.0.36 (2023-11-13)

## 1.0.35 (2023-11-02)

## 1.1.2-rc1 (2024-12-13)

### Feat

- added organizations passthrough resource feat: added org_uid query param to /activities
- swapped asset id for coin_id in activities/activity-record feat: added coin id to activity class
- swapped asset id for coin_id in activities/activity-record feat: added coin id to activity class
- revised by-cw-unit-id endpoint to select by warehouseUnitId, activity mode, and asset id feat: renamed /activities/by-cw-unit-id to /activities/activity-record
- revised by-cw-unit-id endpoint to select by warehouseUnitId, activity mode, and asset id feat: renamed /activities/by-cw-unit-id to /activities/activity-record
- get activity by warehouseUnitId working
- revised /by-cw-unit-id resource response fix: None type error when not climate data returned by CADT
- added /activities/by-cw-unit-id resource
- paginate cadt request
- add version to log output
- add version to log output
- optimized sub-optimal scan_token_activity cron
- support logging to log file or stdout

### Fix

- failing linter
- linter errors
- linter errors
- merge inconsistencies
- fixes needed for compatibility with chia-blockchain 2.4.4
- issues with token pydantic classes and forward refs
- issues with reading from DBs due to bad context manager code
- activities scan
- activities scan

### Refactor

- consolidate common functionality

## 1.0.34 (2023-10-24)

## 1.0.33 (2023-10-12)

## 1.0.32 (2023-10-11)

## 1.0.31 (2023-10-11)

## 1.0.30 (2023-10-11)

## 1.0.29 (2023-10-05)

## 1.0.28 (2023-10-03)

### Feat

- dont use meta_ prefix for cadt metadata

### Fix

- Update code to interface with Chia 2.0.1+
- meta_ prefix in tests
- add missing max coin amount in select coin call
- derivation roots
- update the default cadt api host
- rework wallet indexes
- update default CADT API in config

## 1.0.27 (2023-09-29)

### Fix

- break out server host

## 1.0.26 (2023-09-20)

### Feat

- change transaction type from 2050 to 1

## 1.0.25 (2023-09-19)

## 1.0.24 (2023-09-19)

## 1.0.23 (2023-09-11)

## 1.0.22 (2023-09-08)

### Feat

- use settings in module
- make ports confirgurable

### Fix

- configre_ports
- instance
- cast to none
- cast as it
- add fields to settings class

## 1.0.21 (2023-07-19)

## 1.0.20 (2023-07-18)

## 1.0.19 (2023-07-18)

## 1.0.18 (2023-07-18)

## 1.0.17 (2023-07-18)

## 1.0.16 (2023-07-18)

## 1.0.15 (2023-07-18)

## 1.0.14 (2023-07-17)

## 1.0.13 (2023-07-17)

## 1.0.12 (2023-07-17)

## 1.0.11 (2023-07-17)

## 1.0.10 (2023-07-17)

### Feat

- add sort query

## 1.0.9 (2023-07-12)

## 1.0.8 (2023-07-12)

### Feat

- add height range filter to activity controller

## 1.0.7 (2023-06-29)

## 1.0.6 (2023-06-10)

## 1.0.5 (2023-06-09)

## 1.0.4 (2023-06-09)

### Fix

- update climate warehouse and ui  parameter names
- add exit code for incorrect host configuration
- format host conditional
- require localhost unless running in explorer mode
- prevent infinite loop of activity scanning
