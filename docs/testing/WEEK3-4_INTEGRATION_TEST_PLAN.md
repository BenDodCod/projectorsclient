# Week 3-4 Integration Test Plan
## Enhanced Projector Control Application

**Document Version:** 1.0
**Date:** 2026-01-11
**Phase:** Week 3-4 Core Development - T-003 Preparation
**Work Order:** WO-20260111-001-T003-PREP
**Author:** Test Engineer & QA Automation Specialist
**Status:** READY FOR IMPLEMENTATION (starts Day 3)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Current Testing State](#2-current-testing-state)
3. [Integration Test Scenarios](#3-integration-test-scenarios)
4. [Test Scenario Matrix](#4-test-scenario-matrix)
5. [Performance Benchmarks](#5-performance-benchmarks)
6. [Mock Server Enhancements](#6-mock-server-enhancements)
7. [Test Data Fixtures](#7-test-data-fixtures)
8. [Implementation Timeline](#8-implementation-timeline)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Overview

### 1.1 Goals

**Primary Objectives:**
- Add 50+ integration tests to validate multi-component workflows
- Reach 750+ total tests (currently 578 passing)
- Maintain 85%+ code coverage (current: 85.52%, stretch target: 90%)
- Establish performance benchmarks for critical operations
- Enhance mock PJLink server for comprehensive Class 2 testing

**Strategic Importance:**
- Integration tests validate that components work together correctly
- Performance benchmarks establish baseline for future optimization
- Enhanced mock server enables testing of Class 2 features without physical hardware
- Comprehensive coverage ensures production-ready quality

### 1.2 Timeline

**Start Date:** Day 3 (January 13, 2026)
**End Date:** Day 14 (January 25, 2026)
**Duration:** 12 days
**Dependencies:** T-001.1 (Database Indexes), T-002.1 (Authentication Enhancements)

### 1.3 Success Criteria

**Must Have (Blocking):**
- [ ] 750+ total tests passing (current: 578)
- [x] 85%+ code coverage (ACHIEVED: 85.52%)
- [ ] All 15 priority integration scenarios tested
- [ ] Performance benchmarks documented
- [ ] 0 failed tests, ≤5 skipped tests

**Should Have (Important):**
- [ ] 90% code coverage (stretch target)
- [ ] All Class 2 commands supported in mock server
- [ ] Error injection framework operational
- [ ] Benchmark report generated

**Could Have (Nice to Have):**
- [ ] Advanced mock server features (latency simulation)
- [ ] Accessibility test framework foundation
- [ ] Real-time test monitoring dashboard

---

## 2. Current Testing State

### 2.1 Test Metrics (as of January 11, 2026)

**Test Count:**
- **Total Tests:** 578 passing
- **Unit Tests:** 538 tests (93.1%)
- **Integration Tests:** 40 tests (6.9%)
- **Skipped Tests:** 0
- **Failed Tests:** 0
- **Success Rate:** 100%

**Coverage:**
- **Overall Coverage:** 85.52%
- **Target:** 85% (ACHIEVED ✅)
- **Stretch Target:** 90%
- **Total Statements:** 2,225
- **Missed Statements:** 322

**Coverage by Module (Key Areas):**
| Module | Coverage | Statements | Missed | Priority |
|--------|----------|-----------|--------|----------|
| `pjlink_protocol.py` | 93.94% | 289 | 17 | LOW (excellent) |
| `connection.py` | 88.21% | 195 | 20 | MEDIUM |
| `logging_config.py` | 86.11% | 114 | 13 | MEDIUM |
| `validators.py` | 85.57% | 259 | 32 | MEDIUM |
| `settings.py` | 85.67% | 266 | 35 | MEDIUM |
| `rate_limiter.py` | 84.12% | 219 | 34 | HIGH (security) |
| `projector_controller.py` | 83.29% | 337 | 47 | HIGH (core) |
| `security.py` | 81.21% | 236 | 43 | HIGH (security) |
| `file_security.py` | 79.70% | 217 | 42 | HIGH (security) |

### 2.2 Existing Integration Tests

**File:** `tests/integration/test_settings_security_integration.py`
- **Tests:** 22 integration tests
- **Coverage Focus:** Settings + Security + Database
- **Key Scenarios:**
  - Credential encryption roundtrip
  - Settings cache invalidation
  - Database integrity checks
  - Admin password verification
  - Entropy file handling

**File:** `tests/integration/test_concurrent_connections.py`
- **Tests:** 18 integration tests
- **Coverage Focus:** PJLink + Rate Limiter + Concurrent Operations
- **Key Scenarios:**
  - Multiple concurrent connections
  - Rate limiting under load
  - Circuit breaker basic behavior
  - Connection timeout handling

**Total Integration Tests:** 40 tests (6.9% of total)

### 2.3 Current Test Infrastructure

**Fixtures Available (conftest.py):**
- `temp_dir`: Temporary directory for test files
- `temp_db_path`: Temporary database path
- `mock_pjlink_server`: Mock PJLink Class 1 server
- `mock_pjlink_server_with_auth`: Mock server with authentication
- `mock_pjlink_server_class2`: Mock PJLink Class 2 server
- `projector_configs`: Sample projector configurations (4 projectors)
- `in_memory_sqlite_db`: In-memory SQLite database
- `initialized_test_db`: Database with schema and sample data

**Mock Server Capabilities:**
- Class 1 commands: power, input, mute, lamp hours, errors, info
- Class 2 commands: freeze (implemented), volume/resolution (pending)
- MD5 authentication support
- Multi-threaded request handling
- Configurable PJLink class

**Test Markers:**
- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (with databases, mocked projectors)
- `@pytest.mark.e2e`: End-to-end tests (full workflow)
- `@pytest.mark.slow`: Slow tests (>1s)
- `@pytest.mark.performance`: Performance benchmarks (new)

---

## 3. Integration Test Scenarios

This section defines the 15 priority integration test scenarios for Week 3-4, organized by category.

### 3.1 Category 1: Multi-Component Workflows (30 tests total)

#### Scenario 1: Database Integrity Check on Startup
**File:** `tests/integration/test_database_integrity.py` (NEW)
**Tests:** 6 tests
**Components:** DatabaseManager, DatabaseIntegrityManager, SettingsManager

**Test Cases:**
1. `test_integrity_check_detects_missing_tables`
   - **Setup:** Delete critical table (app_settings)
   - **Action:** Initialize DatabaseManager with verify_integrity=True
   - **Expected:** Raise DatabaseError with "missing table" message

2. `test_integrity_check_detects_corrupted_encryption`
   - **Setup:** Manually corrupt encrypted credential in database
   - **Action:** Run integrity check
   - **Expected:** Detect corruption, log warning, return EncryptionCheckResult.failed

3. `test_integrity_check_detects_admin_password_tampering`
   - **Setup:** Modify admin_password_hash directly in database
   - **Action:** Run integrity check
   - **Expected:** Detect tampering, raise critical security alert

4. `test_integrity_check_detects_foreign_key_violations`
   - **Setup:** Create orphaned projector_credentials record
   - **Action:** Run foreign key check
   - **Expected:** Detect orphaned record, return ForeignKeyCheckResult.failed

5. `test_integrity_check_passes_on_healthy_database`
   - **Setup:** Fresh database with valid data
   - **Action:** Run full integrity check
   - **Expected:** All checks pass, return IntegrityCheckResult.success

6. `test_integrity_check_performance_under_500ms`
   - **Setup:** Database with 100 projectors and 500 settings
   - **Action:** Run full integrity check, measure time
   - **Expected:** Complete in <500ms

**Dependencies:** T-001.4 (Database Integrity Utilities)
**Performance Target:** <500ms for full check
**Test Data:** Corrupted databases in `tests/fixtures/corrupted_data/`

---

#### Scenario 2: Settings Import/Export with Encryption
**File:** `tests/integration/test_settings_import_export.py` (NEW)
**Tests:** 7 tests
**Components:** BackupManager, SettingsManager, CredentialManager, DatabaseManager

**Test Cases:**
1. `test_export_creates_encrypted_backup_file`
   - **Setup:** Settings with 50 entries, 5 projectors with credentials
   - **Action:** Call settings.export_settings(path, password)
   - **Expected:** Encrypted JSON file created with AES-256-GCM

2. `test_import_restores_all_settings`
   - **Setup:** Backup file from export, fresh database
   - **Action:** Call settings.import_settings(backup_path, password)
   - **Expected:** All 50 settings restored, verified by reading from database

3. `test_import_restores_projector_credentials`
   - **Setup:** Backup with 5 projector credentials, fresh database
   - **Action:** Import backup, decrypt credentials
   - **Expected:** Credentials decrypted successfully, match original values

4. `test_import_with_wrong_password_fails`
   - **Setup:** Valid backup file
   - **Action:** Call import_settings with incorrect password
   - **Expected:** Raise BackupError("Authentication failed")

5. `test_import_detects_corrupted_backup_file`
   - **Setup:** Backup file with modified ciphertext (corrupt auth_tag)
   - **Action:** Attempt import
   - **Expected:** Raise BackupError("Integrity check failed - file corrupted")

6. `test_export_import_preserves_admin_password`
   - **Setup:** Set admin password, create backup, fresh database
   - **Action:** Import backup, verify admin password
   - **Expected:** Admin password hash restored, password verification works

7. `test_export_backup_password_different_from_admin_password`
   - **Setup:** Admin password "Admin123!", backup password "Admin123!"
   - **Action:** Attempt export with same password
   - **Expected:** Raise ValidationError("Backup password must differ from admin password")

**Dependencies:** T-001.2 (Backup/Restore Functionality)
**Performance Target:** Backup 100 settings in <1 second
**Test Data:** Sample backup files in `tests/fixtures/backups/`

---

#### Scenario 3: Authentication Flow (Admin + Lockout + Audit)
**File:** `tests/integration/test_authentication_flow.py` (EXPAND EXISTING)
**Tests:** 8 tests (add 5 new to existing 3)
**Components:** PasswordHasher, RateLimiter, DatabaseManager, AuditLogger

**Test Cases (new tests):**
1. `test_admin_authentication_class1_projector`
   - **Setup:** Mock PJLink Class 1 server with password "admin"
   - **Action:** Connect with ProjectorController, authenticate
   - **Expected:** Authentication succeeds, command executes

2. `test_admin_authentication_class2_projector`
   - **Setup:** Mock PJLink Class 2 server with password "admin"
   - **Action:** Connect with ProjectorController, authenticate
   - **Expected:** Authentication succeeds, %2 prefix in commands

3. `test_failed_authentication_triggers_rate_limiter`
   - **Setup:** Mock server with password, 3 failed auth attempts
   - **Action:** Attempt authentication with wrong password 3 times
   - **Expected:** RateLimiter lockout triggered, 4th attempt blocked

4. `test_locked_account_prevents_further_attempts`
   - **Setup:** Account locked (3 failed attempts)
   - **Action:** Attempt authentication with correct password
   - **Expected:** Blocked with "Account locked until {timestamp}"

5. `test_lockout_expires_after_configured_duration`
   - **Setup:** Account locked, wait for lockout expiration (use mock time)
   - **Action:** Attempt authentication after expiration
   - **Expected:** Lockout cleared, authentication succeeds

**Dependencies:** T-002.1 (Authentication Details Handling)
**Performance Target:** <100ms per authentication attempt
**Test Data:** Mock projectors with various authentication configurations

---

#### Scenario 4: Network Timeout Recovery
**File:** `tests/integration/test_network_timeout_recovery.py` (NEW)
**Tests:** 5 tests
**Components:** ProjectorController, RetryableOperation, CircuitBreaker

**Test Cases:**
1. `test_transient_timeout_retried_successfully`
   - **Setup:** Mock server with 50% timeout rate (error injection)
   - **Action:** Send power_on command with retry enabled
   - **Expected:** Retried up to 3 times, eventually succeeds

2. `test_persistent_timeout_opens_circuit_breaker`
   - **Setup:** Mock server that always times out
   - **Action:** Send 3 consecutive commands
   - **Expected:** Circuit breaker opens after 3 failures

3. `test_circuit_breaker_prevents_repeated_timeout_attempts`
   - **Setup:** Circuit breaker in OPEN state
   - **Action:** Attempt to send command
   - **Expected:** Immediately rejected with "Circuit breaker OPEN"

4. `test_circuit_breaker_half_open_recovery`
   - **Setup:** Circuit breaker OPEN, wait for timeout expiration
   - **Action:** Send probe command (should transition to HALF_OPEN)
   - **Expected:** Probe sent, success transitions to CLOSED

5. `test_exponential_backoff_increases_retry_delay`
   - **Setup:** Mock server with transient failures
   - **Action:** Send command with retry, measure delay between retries
   - **Expected:** Delays increase exponentially (100ms, 200ms, 400ms)

**Dependencies:** T-002.3 (Circuit Breaker), T-002.4 (Retry Logic)
**Performance Target:** Max 3 retries, total <10 seconds
**Test Data:** Error injection configurations

---

#### Scenario 5: Cache Invalidation Scenarios
**File:** `tests/integration/test_cache_invalidation.py` (NEW)
**Tests:** 4 tests
**Components:** SettingsManager, DatabaseManager

**Test Cases:**
1. `test_cache_invalidates_on_database_update`
   - **Setup:** SettingsManager with cached value
   - **Action:** Update setting directly in database (bypass cache)
   - **Expected:** Cache detects change, re-reads from database

2. `test_cache_invalidates_on_setting_update`
   - **Setup:** SettingsManager with cached value
   - **Action:** Call settings.set("key", "new_value")
   - **Expected:** Cache updated immediately, database updated

3. `test_cache_invalidates_on_settings_import`
   - **Setup:** SettingsManager with cached values, import backup file
   - **Action:** Call settings.import_settings(backup_path, password)
   - **Expected:** Entire cache cleared, values re-read from database

4. `test_cache_ttl_expiration`
   - **Setup:** SettingsManager with TTL=5 seconds
   - **Action:** Read setting, wait 6 seconds, read again
   - **Expected:** First read from cache, second read from database (cache expired)

**Dependencies:** None (existing SettingsManager functionality)
**Performance Target:** Cache hit <1ms, cache miss <5ms
**Test Data:** Settings with various TTL configurations

---

### 3.2 Category 2: Performance Benchmarks (10 tests total)

#### Scenario 6: Database Performance with Indexes
**File:** `tests/integration/test_database_performance.py` (NEW)
**Tests:** 4 tests
**Components:** DatabaseManager with indexes from T-001.1

**Test Cases:**
1. `test_settings_lookup_with_index_under_5ms`
   - **Setup:** Database with 1000 settings, index on setting_key
   - **Action:** Lookup setting by key 100 times, measure average time
   - **Expected:** Average query time <5ms

2. `test_projector_list_query_with_index_under_10ms`
   - **Setup:** Database with 100 projectors, index on room_name + active
   - **Action:** Query active projectors by room 50 times, measure average time
   - **Expected:** Average query time <10ms

3. `test_audit_log_recent_events_with_index_under_20ms`
   - **Setup:** Database with 10,000 audit log entries, index on timestamp
   - **Action:** Query last 100 events 50 times, measure average time
   - **Expected:** Average query time <20ms

4. `test_database_initialization_under_100ms`
   - **Setup:** Fresh database (file-based, not in-memory)
   - **Action:** Initialize DatabaseManager, create schema, add indexes
   - **Expected:** Complete in <100ms

**Dependencies:** T-001.1 (Database Indexes)
**Performance Targets:** Settings <5ms, Projectors <10ms, Audit <20ms, Init <100ms
**Test Data:** Large datasets (1000 settings, 100 projectors, 10,000 audit entries)

---

#### Scenario 7: PJLink Command Latency
**File:** `tests/integration/test_performance_benchmarks.py` (NEW)
**Tests:** 3 tests
**Components:** ProjectorController, PJLink Protocol

**Test Cases:**
1. `test_power_on_command_under_5_seconds`
   - **Setup:** Mock PJLink server with realistic 200ms latency
   - **Action:** Send power_on command 20 times, measure average time
   - **Expected:** Average time <5 seconds (including network + processing)

2. `test_status_check_under_3_seconds`
   - **Setup:** Mock PJLink server
   - **Action:** Send get_power, get_input, get_errors commands, measure time
   - **Expected:** All 3 queries complete in <3 seconds total

3. `test_concurrent_10_projectors_under_10_seconds`
   - **Setup:** 10 mock PJLink servers on different ports
   - **Action:** Send power_on to all 10 simultaneously (ThreadPoolExecutor)
   - **Expected:** All 10 commands complete in <10 seconds total

**Dependencies:** None (existing PJLink functionality)
**Performance Targets:** Power on <5s, Status <3s, 10 concurrent <10s
**Test Data:** Mock servers with configurable latency

---

#### Scenario 8: Backup/Restore Performance
**File:** `tests/integration/test_backup_restore_performance.py` (NEW)
**Tests:** 3 tests
**Components:** BackupManager, SettingsManager

**Test Cases:**
1. `test_backup_100_settings_under_1_second`
   - **Setup:** Database with 100 settings
   - **Action:** Create backup, measure time
   - **Expected:** Backup created in <1 second

2. `test_restore_100_settings_under_1_second`
   - **Setup:** Backup file with 100 settings, fresh database
   - **Action:** Restore backup, measure time
   - **Expected:** Restore completes in <1 second

3. `test_backup_500_settings_with_credentials_under_5_seconds`
   - **Setup:** Database with 500 settings, 50 projector credentials
   - **Action:** Create backup (encrypt credentials), measure time
   - **Expected:** Backup created in <5 seconds

**Dependencies:** T-001.2 (Backup/Restore Functionality)
**Performance Targets:** 100 settings <1s, 500 settings <5s
**Test Data:** Large datasets with credentials

---

### 3.3 Category 3: Failure Scenarios (15 tests total)

#### Scenario 9: File Permission Failures (Graceful Degradation)
**File:** `tests/integration/test_file_permission_failures.py` (NEW)
**Tests:** 4 tests
**Components:** FileSecurity, DatabaseManager, BackupManager

**Test Cases:**
1. `test_database_file_read_only_prevents_writes`
   - **Setup:** Create database file, set to read-only
   - **Action:** Attempt to insert setting
   - **Expected:** Raise PermissionError, log error, database unchanged

2. `test_backup_directory_no_write_permission`
   - **Setup:** Backup directory with no write permission
   - **Action:** Attempt to create backup
   - **Expected:** Raise BackupError("Cannot write to backup directory")

3. `test_entropy_file_missing_creates_new`
   - **Setup:** Delete entropy.bin file
   - **Action:** Initialize CredentialManager
   - **Expected:** New entropy file created with 32 secure random bytes

4. `test_database_file_locked_by_another_process`
   - **Setup:** Open database connection in separate process (simulate lock)
   - **Action:** Attempt to open database
   - **Expected:** Retry with timeout, raise DatabaseError if timeout exceeded

**Dependencies:** None (existing file security functionality)
**Performance Target:** Graceful failure within 1 second
**Test Data:** Various file permission scenarios

---

#### Scenario 10: Entropy File Corruption Recovery
**File:** `tests/integration/test_entropy_corruption_recovery.py` (NEW)
**Tests:** 3 tests
**Components:** CredentialManager, FileSecurity

**Test Cases:**
1. `test_corrupted_entropy_file_regenerates`
   - **Setup:** Write invalid data to entropy.bin (wrong size)
   - **Action:** Initialize CredentialManager
   - **Expected:** Detect corruption, regenerate entropy file, log warning

2. `test_entropy_file_tampered_recreates_and_decrypts_fail`
   - **Setup:** Valid encrypted credentials, then modify entropy.bin
   - **Action:** Attempt to decrypt credentials
   - **Expected:** Decryption fails, credentials unrecoverable (expected behavior)

3. `test_entropy_file_permissions_restored_on_corruption`
   - **Setup:** Corrupt entropy file with wrong permissions
   - **Action:** Initialize CredentialManager
   - **Expected:** New entropy file created with correct ACL (user-only read/write)

**Dependencies:** None (existing CredentialManager functionality)
**Performance Target:** Recovery within 500ms
**Test Data:** Corrupted entropy files in `tests/fixtures/corrupted_data/`

---

#### Scenario 11: PJLink Class 2 → Class 1 Fallback
**File:** `tests/integration/test_pjlink_class_fallback.py` (NEW)
**Tests:** 4 tests
**Components:** ProjectorController, PJLink Protocol

**Test Cases:**
1. `test_class2_command_falls_back_to_class1_on_unsupported`
   - **Setup:** Mock server supports Class 1 only, controller sends Class 2 command
   - **Action:** Send freeze command (Class 2 specific)
   - **Expected:** Command fails with Class 2, retried as Class 1 (unsupported), logged

2. `test_class_detection_from_response_prefix`
   - **Setup:** Mock server responds with %1 or %2 prefix
   - **Action:** Send command, detect class from response
   - **Expected:** PJLinkClass enum set correctly (CLASS_1 or CLASS_2)

3. `test_fallback_persists_for_subsequent_commands`
   - **Setup:** First command triggers fallback to Class 1
   - **Action:** Send second command to same projector
   - **Expected:** Second command sent as Class 1 (no retry needed)

4. `test_class2_projector_maintains_class2_commands`
   - **Setup:** Mock Class 2 server
   - **Action:** Send freeze command
   - **Expected:** Command sent with %2 prefix, no fallback

**Dependencies:** T-002.1 (Authentication Details Handling)
**Performance Target:** Fallback detection <100ms
**Test Data:** Mock servers with Class 1 and Class 2 configurations

---

#### Scenario 12: Database Migration with Existing Data
**File:** `tests/integration/test_database_migration_flow.py` (NEW)
**Tests:** 4 tests
**Components:** MigrationManager, DatabaseManager

**Test Cases:**
1. `test_v1_database_upgrades_to_v2_with_indexes`
   - **Setup:** Create v1 database (no indexes, no schema_migrations table)
   - **Action:** Initialize DatabaseManager (auto_migrate=True)
   - **Expected:** Migration v1→v2 runs, indexes created, schema_migrations table created

2. `test_existing_data_preserved_during_migration`
   - **Setup:** v1 database with 50 settings, 10 projectors
   - **Action:** Run migration to v2
   - **Expected:** All 50 settings and 10 projectors still present, indexes added

3. `test_migration_checksum_verification_detects_tampering`
   - **Setup:** Migration file with modified checksum
   - **Action:** Attempt migration
   - **Expected:** Raise SchemaError("Migration checksum mismatch - file tampered")

4. `test_failed_migration_rolls_back_transaction`
   - **Setup:** Migration script with intentional SQL error (invalid syntax)
   - **Action:** Attempt migration
   - **Expected:** Transaction rolled back, database unchanged, error logged

**Dependencies:** T-001.3 (Schema Migration System)
**Performance Target:** Migration completes in <500ms
**Test Data:** v1 databases in `tests/fixtures/databases/v1/`

---

### 3.4 Category 4: Security Workflows (10 tests total)

#### Scenario 13: Backup/Restore with Credential Preservation
**File:** `tests/integration/test_backup_restore_workflow.py` (already planned in Section 3.1, Scenario 2)
**Tests:** 7 tests (see Scenario 2 above)

#### Scenario 14: SQL Injection Prevention
**File:** `tests/integration/test_sql_injection_prevention.py` (NEW)
**Tests:** 3 tests
**Components:** DatabaseManager, SettingsManager, InputValidator

**Test Cases:**
1. `test_sql_injection_in_setting_key_prevented`
   - **Setup:** Malicious setting key: `"key'; DROP TABLE app_settings; --"`
   - **Action:** Call settings.set(malicious_key, "value")
   - **Expected:** Parameterized query prevents injection, setting stored safely

2. `test_sql_injection_in_projector_name_prevented`
   - **Setup:** Malicious projector name: `"Projector'; UPDATE projector_config SET active=0; --"`
   - **Action:** Insert projector with malicious name
   - **Expected:** Parameterized query prevents injection, projector created safely

3. `test_sql_injection_in_search_query_prevented`
   - **Setup:** Search query: `"Room%' OR '1'='1"`
   - **Action:** Search projectors by room name
   - **Expected:** Parameterized query prevents injection, returns correct results only

**Dependencies:** None (existing database security)
**Performance Target:** No impact on query performance
**Test Data:** OWASP SQL injection payloads

---

---

## 4. Test Scenario Matrix

| Scenario # | Scenario Name | Components | Test Data | Performance Target | Dependencies | Test Count |
|-----------|--------------|-----------|-----------|-------------------|--------------|-----------|
| 1 | Database Integrity Check | DatabaseManager, IntegrityManager, SettingsManager | Corrupted databases | <500ms full check | T-001.4 | 6 |
| 2 | Settings Import/Export | BackupManager, SettingsManager, CredentialManager | Sample backups | 100 settings <1s | T-001.2 | 7 |
| 3 | Authentication Flow | PasswordHasher, RateLimiter, AuditLogger | Mock projectors | <100ms per attempt | T-002.1 | 8 |
| 4 | Network Timeout Recovery | ProjectorController, RetryableOperation, CircuitBreaker | Error injection configs | Max 3 retries <10s | T-002.3, T-002.4 | 5 |
| 5 | Cache Invalidation | SettingsManager, DatabaseManager | Settings with TTL | Cache hit <1ms | None | 4 |
| 6 | Database Performance | DatabaseManager + Indexes | 1000 settings, 100 projectors | <5ms queries | T-001.1 | 4 |
| 7 | PJLink Command Latency | ProjectorController, PJLink Protocol | Mock servers with latency | Power on <5s | None | 3 |
| 8 | Backup/Restore Performance | BackupManager, SettingsManager | 100-500 settings | 100 settings <1s | T-001.2 | 3 |
| 9 | File Permission Failures | FileSecurity, DatabaseManager, BackupManager | Various permissions | Graceful fail <1s | None | 4 |
| 10 | Entropy Corruption Recovery | CredentialManager, FileSecurity | Corrupted entropy files | Recovery <500ms | None | 3 |
| 11 | PJLink Class Fallback | ProjectorController, PJLink Protocol | Class 1 & 2 servers | Fallback <100ms | T-002.1 | 4 |
| 12 | Database Migration | MigrationManager, DatabaseManager | v1 databases | Migration <500ms | T-001.3 | 4 |
| 13 | Backup Credential Preservation | BackupManager, CredentialManager | Backup files | (see Scenario 2) | T-001.2 | (included in #2) |
| 14 | SQL Injection Prevention | DatabaseManager, InputValidator | OWASP payloads | No perf impact | None | 3 |
| **TOTAL** | **14 unique scenarios** | **All components** | **Various fixtures** | **Multi-target** | **4 dependencies** | **58 tests** |

**Summary:**
- **Total New Integration Tests:** 58 tests (exceeds 50 target)
- **Current Integration Tests:** 40 tests
- **Total After Implementation:** 98 integration tests
- **Total Test Count:** 578 + 58 = 636 tests (working toward 750 target)

**Note:** An additional 114 tests will come from:
- Unit tests for new components (T-001, T-002): ~100 tests
- Mock server enhancements: ~10 tests
- Accessibility framework stubs: ~4 tests

---

## 5. Performance Benchmarks

### 5.1 Benchmark Requirements

**What to Measure:**
1. **Database Operations:**
   - Query time for settings lookup (with indexes)
   - Query time for projector list (with indexes)
   - Query time for audit log recent events (with indexes)
   - Database initialization time (schema + indexes)

2. **PJLink Commands:**
   - Power on/off command response time
   - Status check command response time
   - Concurrent operations (10 projectors simultaneously)

3. **Backup/Restore:**
   - Backup creation time (100 settings, 500 settings)
   - Restore time (100 settings, 500 settings)
   - Backup with credential encryption overhead

4. **Application Startup:**
   - Cold start time (initialize database, load settings)
   - Warm start time (database already exists)

### 5.2 How to Measure

**Tools:**
- **pytest-benchmark:** Integrated with pytest for performance testing
- **Custom timing decorators:** For specific component timing
- **Profiling:** cProfile for identifying bottlenecks (if needed)

**Benchmark Test Structure:**
```python
import pytest
import time

@pytest.mark.performance
def test_settings_lookup_benchmark(benchmark, initialized_test_db):
    """Benchmark settings lookup with index."""
    db = DatabaseManager(initialized_test_db)
    settings = SettingsManager(db)

    # Insert 1000 settings for realistic test
    for i in range(1000):
        settings.set(f"key_{i}", f"value_{i}")

    # Benchmark the lookup operation
    def lookup():
        return settings.get("key_500")

    result = benchmark(lookup)

    # Assert performance target
    assert benchmark.stats['mean'] < 0.005  # <5ms average
```

**Running Benchmarks:**
```bash
# Run performance tests only
pytest tests/integration/test_performance_benchmarks.py -m performance -v

# Generate benchmark report
pytest tests/integration/test_performance_benchmarks.py --benchmark-only --benchmark-save=week3

# Compare benchmarks
pytest-benchmark compare week3 week2
```

### 5.3 Performance Targets

| Operation | Target | Acceptable | Unacceptable | Measurement |
|-----------|--------|-----------|--------------|-------------|
| Settings lookup (with index) | <5ms | 5-10ms | >10ms | Average of 100 lookups |
| Projector list query (with index) | <10ms | 10-20ms | >20ms | Average of 50 queries |
| Audit log recent events (with index) | <20ms | 20-50ms | >50ms | Average of 50 queries |
| Database initialization | <100ms | 100-200ms | >200ms | Fresh database creation |
| PJLink power on command | <5s | 5-7s | >7s | Single command |
| PJLink status check | <3s | 3-5s | >5s | 3 queries (power, input, errors) |
| 10 concurrent projectors | <10s | 10-15s | >15s | ThreadPoolExecutor with 10 workers |
| Backup 100 settings | <1s | 1-2s | >2s | Create encrypted backup |
| Restore 100 settings | <1s | 1-2s | >2s | Decrypt and restore |
| Backup 500 settings + credentials | <5s | 5-10s | >10s | Create encrypted backup |
| Application cold start | <2s | 2-3s | >3s | Initialize database + load settings |

**Baseline Documentation:**
- All benchmarks will be run on clean state (fresh database, no cache)
- Benchmarks run on Windows 10+ with SSD storage
- Documented in `docs/testing/WEEK3-4_PERFORMANCE_BASELINE.md`

### 5.4 Benchmark Reporting

**Report Structure:**
```markdown
# Week 3-4 Performance Baseline Report

## Environment
- OS: Windows 10 Pro (64-bit)
- Python: 3.12.6
- Database: SQLite 3.x
- Storage: SSD

## Benchmark Results (January 13-25, 2026)

### Database Operations
| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Settings lookup | <5ms | 3.2ms | ✅ PASS |
| Projector list | <10ms | 7.8ms | ✅ PASS |
| Audit log recent | <20ms | 15.3ms | ✅ PASS |
| DB initialization | <100ms | 82ms | ✅ PASS |

### PJLink Commands
| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Power on | <5s | 4.1s | ✅ PASS |
| Status check | <3s | 2.3s | ✅ PASS |
| 10 concurrent | <10s | 8.7s | ✅ PASS |

### Backup/Restore
| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Backup 100 | <1s | 0.7s | ✅ PASS |
| Restore 100 | <1s | 0.8s | ✅ PASS |
| Backup 500 | <5s | 3.2s | ✅ PASS |

## Regression Tracking
(Benchmark changes from previous week)
```

---

## 6. Mock Server Enhancements

### 6.1 Current Mock Server Capabilities

**File:** `tests/mocks/mock_pjlink.py`

**Implemented Features:**
- ✅ PJLink Class 1 commands (POWR, INPT, AVMT, LAMP, ERST, INF1, INF2, NAME, CLSS)
- ✅ MD5 authentication with challenge-response
- ✅ Class 2 command prefix support (%2)
- ✅ Freeze command (FREZ) - Class 2
- ✅ Multi-threaded client handling
- ✅ Configurable port (0 = random available port)
- ✅ Configurable password (None = no auth)
- ✅ Configurable PJLink class (1 or 2)

**Test Coverage:**
- 38 unit tests for mock server functionality

### 6.2 Required Enhancements

#### 6.2.1 Complete Class 2 Command Support (Priority: HIGH)

**Missing Class 2 Commands:**
```python
# Add to MockPJLinkServer.CLASS_2_COMMANDS
CLASS_2_COMMANDS = {
    "FREZ": ("freeze", handle_freeze),                    # ✅ Already implemented
    "SVOL": ("speaker_volume", handle_speaker_volume),    # NEW
    "MVOL": ("microphone_volume", handle_mic_volume),     # NEW
    "IRES": ("input_resolution", handle_input_res),       # NEW
    "RRES": ("recommended_resolution", handle_rec_res),   # NEW
    "FILT": ("filter_usage", handle_filter_usage),        # NEW
    "RLMP": ("replacement_lamp_model", handle_lamp_model),# NEW
    "RFIL": ("replacement_filter_model", handle_filter_model), # NEW
    "SNUM": ("serial_number", handle_serial_number),      # NEW
    "SVER": ("software_version", handle_software_version),# NEW
}
```

**Implementation Example:**
```python
def handle_speaker_volume(self, data: str) -> str:
    """
    Handle speaker volume command (SVOL).

    Query: SVOL ?
    Response: SVOL=<volume>  (0-100)

    Set: SVOL <volume>
    Response: SVOL=OK
    """
    if data == "?":
        return f"SVOL={self.state['speaker_volume']}"
    else:
        try:
            volume = int(data)
            if 0 <= volume <= 100:
                self.state['speaker_volume'] = volume
                return "SVOL=OK"
            else:
                return "SVOL=ERR2"  # Out of range
        except ValueError:
            return "SVOL=ERR2"  # Invalid parameter
```

**Acceptance Criteria:**
- [ ] All 10 Class 2 commands implemented
- [ ] Query and Set operations supported for each
- [ ] Error codes returned for invalid parameters
- [ ] Unit tests for each new command (1-2 tests per command)

#### 6.2.2 Error Injection Framework (Priority: HIGH)

**Purpose:** Test error handling and retry logic without physical hardware

**Implementation:**
```python
class ErrorInjectionConfig:
    """Configuration for error injection in mock server."""
    enabled: bool = False
    error_type: str = "timeout"  # "timeout", "auth_failure", "network_error", "random"
    frequency: float = 1.0  # Probability of error (0.0 to 1.0)
    specific_commands: List[str] = None  # None = all commands, or ["POWR", "INPT"]

class MockPJLinkServer:
    def __init__(self, ..., error_injection: ErrorInjectionConfig = None):
        self.error_injection = error_injection or ErrorInjectionConfig()

    def _should_inject_error(self, command: str) -> bool:
        """Determine if error should be injected for this command."""
        if not self.error_injection.enabled:
            return False

        # Check if command is in specific_commands list
        if self.error_injection.specific_commands:
            if command not in self.error_injection.specific_commands:
                return False

        # Random probability
        import random
        return random.random() < self.error_injection.frequency

    def _inject_error(self, command: str):
        """Inject configured error type."""
        if self.error_injection.error_type == "timeout":
            # Don't send response (client will timeout)
            return None
        elif self.error_injection.error_type == "auth_failure":
            return "PJLINK ERRA"  # Authentication error
        elif self.error_injection.error_type == "network_error":
            # Close connection abruptly
            raise ConnectionError("Network error injected")
        elif self.error_injection.error_type == "random":
            # Random error from list
            errors = [None, "PJLINK ERRA", "ERR1", "ERR2", "ERR3", "ERR4"]
            return random.choice(errors)
```

**Usage Example:**
```python
def test_retry_logic_with_transient_timeout():
    """Test retry logic recovers from transient timeout."""
    # Configure 50% timeout rate
    error_config = ErrorInjectionConfig(
        enabled=True,
        error_type="timeout",
        frequency=0.5
    )

    server = MockPJLinkServer(port=0, error_injection=error_config)
    server.start()

    controller = ProjectorController(
        server.host,
        server.port,
        retry_config=RetryConfig(max_retries=3)
    )

    # Should eventually succeed after retries
    result = controller.power_on()
    assert result.success
```

**Acceptance Criteria:**
- [ ] Error injection for timeout (no response)
- [ ] Error injection for auth failure
- [ ] Error injection for network error (connection close)
- [ ] Error injection for random errors
- [ ] Configurable frequency (0.0 to 1.0)
- [ ] Configurable specific commands
- [ ] Unit tests for error injection framework

#### 6.2.3 Latency Simulation (Priority: MEDIUM)

**Purpose:** Test timeout handling and performance under slow network conditions

**Implementation:**
```python
class LatencyConfig:
    """Configuration for latency simulation."""
    enabled: bool = False
    min_ms: int = 0
    max_ms: int = 0
    distribution: str = "uniform"  # "uniform", "normal", "exponential"

class MockPJLinkServer:
    def __init__(self, ..., latency: LatencyConfig = None):
        self.latency = latency or LatencyConfig()

    def _simulate_latency(self):
        """Sleep to simulate network delay."""
        if not self.latency.enabled or self.latency.max_ms == 0:
            return

        import random
        import time

        if self.latency.distribution == "uniform":
            delay_ms = random.randint(self.latency.min_ms, self.latency.max_ms)
        elif self.latency.distribution == "normal":
            mean = (self.latency.min_ms + self.latency.max_ms) / 2
            std_dev = (self.latency.max_ms - self.latency.min_ms) / 4
            delay_ms = max(self.latency.min_ms,
                          min(self.latency.max_ms,
                              int(random.gauss(mean, std_dev))))
        elif self.latency.distribution == "exponential":
            # Exponential distribution (most requests fast, some very slow)
            delay_ms = min(self.latency.max_ms,
                          int(random.expovariate(1.0 / self.latency.min_ms)))

        time.sleep(delay_ms / 1000.0)
```

**Usage Example:**
```python
def test_timeout_handling_with_slow_projector():
    """Test timeout detection with slow projector response."""
    # Configure 2-5 second latency
    latency_config = LatencyConfig(
        enabled=True,
        min_ms=2000,
        max_ms=5000,
        distribution="uniform"
    )

    server = MockPJLinkServer(port=0, latency=latency_config)
    server.start()

    controller = ProjectorController(
        server.host,
        server.port,
        timeout=3  # 3 second timeout
    )

    # Should timeout on some requests
    result = controller.power_on()
    # (May succeed or timeout based on random latency)
```

**Acceptance Criteria:**
- [ ] Uniform distribution latency
- [ ] Normal distribution latency
- [ ] Exponential distribution latency
- [ ] Configurable min/max latency
- [ ] Unit tests for latency simulation

#### 6.2.4 Multiple Client Handling (Priority: LOW)

**Purpose:** Test concurrent connections without connection pool

**Current State:** MockPJLinkServer already supports multi-threaded clients (ThreadingTCPServer)

**Enhancement:** Add connection tracking and limits

```python
class MockPJLinkServer:
    def __init__(self, ..., max_concurrent_clients: int = 10):
        self.max_concurrent_clients = max_concurrent_clients
        self.active_clients = []
        self.client_lock = threading.Lock()

    def handle_client(self, conn, addr):
        """Handle client connection with tracking."""
        with self.client_lock:
            if len(self.active_clients) >= self.max_concurrent_clients:
                conn.sendall(b"PJLINK ERR3\r\n")  # Unavailable
                conn.close()
                return

            self.active_clients.append(addr)

        try:
            # ... existing client handling ...
        finally:
            with self.client_lock:
                self.active_clients.remove(addr)
```

**Acceptance Criteria:**
- [ ] Track active client connections
- [ ] Enforce max_concurrent_clients limit
- [ ] Reject connections when limit reached
- [ ] Unit tests for client limit enforcement

### 6.3 Mock Server Enhancement Timeline

**Days 11-12 (January 21-22):**

**Day 11:**
- Implement 10 remaining Class 2 commands (2-3 hours)
- Write unit tests for new commands (1-2 hours)
- Implement error injection framework (2 hours)
- Write unit tests for error injection (1 hour)

**Day 12:**
- Implement latency simulation (1-2 hours)
- Write unit tests for latency simulation (1 hour)
- Enhance client connection tracking (1 hour)
- Integration testing with enhanced mock server (2 hours)

**Total Effort:** ~12-14 hours over 2 days

---

## 7. Test Data Fixtures

### 7.1 Existing Fixtures (in conftest.py)

**Already Available:**
- `temp_dir`: Temporary directory for test files
- `temp_db_path`: Temporary database path
- `mock_pjlink_server`: Mock PJLink Class 1 server
- `mock_pjlink_server_with_auth`: Mock server with authentication
- `mock_pjlink_server_class2`: Mock PJLink Class 2 server
- `projector_configs`: Sample projector configurations (4 projectors)
- `in_memory_sqlite_db`: In-memory SQLite database
- `initialized_test_db`: Database with schema and sample data

### 7.2 New Fixtures Required

#### 7.2.1 Corrupted Data Fixtures

**Directory:** `tests/fixtures/corrupted_data/`

**Files to Create:**
1. `corrupt_database.db` - SQLite database with missing app_settings table
2. `corrupt_encryption.db` - Database with tampered encrypted credentials
3. `corrupt_entropy.bin` - Entropy file with wrong size (e.g., 16 bytes instead of 32)
4. `tampered_entropy.bin` - Entropy file with valid size but modified content
5. `corrupt_admin_hash.db` - Database with modified admin_password_hash

**Creation Script:**
```python
# tests/fixtures/corrupted_data/create_corrupt_fixtures.py
import sqlite3
from pathlib import Path

def create_corrupt_database():
    """Create database with missing table."""
    db_path = Path(__file__).parent / "corrupt_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create only projector_config table (missing app_settings)
    cursor.execute("""
        CREATE TABLE projector_config (
            id INTEGER PRIMARY KEY,
            proj_name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_corrupt_encryption():
    """Create database with tampered encrypted credential."""
    db_path = Path(__file__).parent / "corrupt_encryption.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
        CREATE TABLE app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Insert tampered encrypted value (invalid base64)
    cursor.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?)",
        ("projector_password_encrypted", "INVALID_BASE64!!!")
    )
    conn.commit()
    conn.close()

# Run all creation functions
if __name__ == "__main__":
    create_corrupt_database()
    create_corrupt_encryption()
    # ... more creation functions ...
```

#### 7.2.2 Sample Backup Files

**Directory:** `tests/fixtures/backups/`

**Files to Create:**
1. `backup_100_settings.json` - Encrypted backup with 100 settings
2. `backup_with_credentials.json` - Backup with 5 projector credentials
3. `backup_wrong_version.json` - Backup from incompatible version (e.g., v2.0)
4. `backup_corrupted_auth_tag.json` - Backup with modified auth_tag (integrity check fail)

**Creation Script:**
```python
# tests/fixtures/backups/create_backup_fixtures.py
import json
from pathlib import Path
from src.utils.config_backup import BackupManager
from src.database.connection import DatabaseManager

def create_backup_100_settings():
    """Create backup with 100 settings."""
    # Create temporary database
    db = DatabaseManager(":memory:")
    settings = SettingsManager(db)

    # Insert 100 settings
    for i in range(100):
        settings.set(f"key_{i}", f"value_{i}", category=f"cat_{i % 10}")

    # Create backup
    backup_path = Path(__file__).parent / "backup_100_settings.json"
    backup_mgr = BackupManager(db)
    backup_mgr.create_backup(backup_path, "TestBackupPassword123!")

# Run all creation functions
if __name__ == "__main__":
    create_backup_100_settings()
    # ... more creation functions ...
```

#### 7.2.3 v1 Database Fixtures

**Directory:** `tests/fixtures/databases/v1/`

**Files to Create:**
1. `fresh_v1.db` - Fresh v1 database (no data, no indexes)
2. `v1_with_data.db` - v1 database with 50 settings, 10 projectors
3. `v1_large.db` - v1 database with 1000 settings, 100 projectors (migration stress test)

**Creation Script:**
```python
# tests/fixtures/databases/v1/create_v1_databases.py
import sqlite3
from pathlib import Path

def create_fresh_v1():
    """Create fresh v1 database (no indexes, no schema_migrations)."""
    db_path = Path(__file__).parent / "fresh_v1.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create v1 schema (WITHOUT indexes)
    cursor.execute("""
        CREATE TABLE app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE projector_config (
            id INTEGER PRIMARY KEY,
            proj_name TEXT NOT NULL,
            proj_ip TEXT NOT NULL,
            proj_port INTEGER DEFAULT 4352
        )
    """)
    # No indexes, no schema_migrations table
    conn.commit()
    conn.close()

# Run all creation functions
if __name__ == "__main__":
    create_fresh_v1()
    # ... more creation functions ...
```

#### 7.2.4 Network Error Scenarios

**Directory:** `tests/fixtures/network_scenarios/`

**File:** `error_configs.json`

```json
{
  "scenarios": [
    {
      "name": "transient_timeout",
      "description": "50% timeout rate (simulates unstable network)",
      "error_injection": {
        "enabled": true,
        "error_type": "timeout",
        "frequency": 0.5
      }
    },
    {
      "name": "persistent_timeout",
      "description": "100% timeout (projector offline)",
      "error_injection": {
        "enabled": true,
        "error_type": "timeout",
        "frequency": 1.0
      }
    },
    {
      "name": "auth_failure",
      "description": "Authentication always fails (wrong password)",
      "error_injection": {
        "enabled": true,
        "error_type": "auth_failure",
        "frequency": 1.0
      }
    },
    {
      "name": "slow_network",
      "description": "2-5 second latency (slow network)",
      "latency": {
        "enabled": true,
        "min_ms": 2000,
        "max_ms": 5000,
        "distribution": "uniform"
      }
    }
  ]
}
```

**Usage in Tests:**
```python
def test_with_network_scenario(scenario_name: str):
    """Load network scenario from fixtures."""
    import json
    from pathlib import Path

    scenarios_path = Path(__file__).parent.parent / "fixtures" / "network_scenarios" / "error_configs.json"
    with open(scenarios_path) as f:
        scenarios = json.load(f)["scenarios"]

    scenario = next(s for s in scenarios if s["name"] == scenario_name)

    # Configure mock server with scenario
    if "error_injection" in scenario:
        error_config = ErrorInjectionConfig(**scenario["error_injection"])
        server = MockPJLinkServer(port=0, error_injection=error_config)
    # ... etc
```

### 7.3 Fixture Management

**Fixture Creation Workflow:**
1. Create fixture generation scripts in `tests/fixtures/<category>/`
2. Run scripts to generate fixture files
3. Commit fixture files to repository (if small, <1MB)
4. Add `.gitignore` entry for large generated fixtures
5. Document fixtures in `tests/fixtures/README.md`

**Fixture Documentation:**
```markdown
# Test Fixtures

## Corrupted Data
- `corrupt_database.db`: SQLite database with missing app_settings table
- `corrupt_encryption.db`: Database with tampered encrypted credentials
- `corrupt_entropy.bin`: Entropy file with wrong size (16 bytes)

## Backup Files
- `backup_100_settings.json`: Encrypted backup with 100 settings
- `backup_with_credentials.json`: Backup with 5 projector credentials

## v1 Databases
- `fresh_v1.db`: Fresh v1 database (no indexes)
- `v1_with_data.db`: v1 database with 50 settings, 10 projectors

## Network Scenarios
- `error_configs.json`: Predefined network error scenarios
```

---

## 8. Implementation Timeline

### 8.1 T-003 Execution Schedule

**Total Duration:** 12 days (January 13-25, 2026)

**Phase 1: Foundation (Days 3-5, January 13-15)**
- Day 3: Create test fixtures, set up test data
- Day 4: Implement Scenarios 1-3 (15 tests)
- Day 5: Implement Scenarios 4-5 (9 tests)

**Phase 2: Performance & Failure Testing (Days 6-10, January 16-20)**
- Day 6: Implement Scenarios 6-8 (10 performance tests)
- Day 7: Implement Scenarios 9-10 (7 failure tests)
- Day 8: Implement Scenarios 11-12 (8 tests)
- Day 9: Code review, bug fixes
- Day 10: Performance benchmark baseline documentation

**Phase 3: Mock Server & Security (Days 11-14, January 21-25)**
- Day 11: Enhance mock server (Class 2 commands, error injection)
- Day 12: Mock server testing, latency simulation
- Day 13: Implement Scenario 14 (SQL injection prevention, 3 tests)
- Day 14: Final testing, evidence collection, gate review prep

### 8.2 Daily Breakdown

**Day 3 (January 13) - Foundation Setup**
- [ ] Create `tests/fixtures/` directory structure
- [ ] Generate corrupted data fixtures
- [ ] Generate sample backup files
- [ ] Generate v1 database fixtures
- [ ] Create network scenario configurations
- [ ] Document fixtures in README.md

**Day 4 (January 14) - Scenarios 1-3**
- [ ] Implement `test_database_integrity.py` (6 tests)
- [ ] Implement `test_settings_import_export.py` (7 tests)
- [ ] Expand `test_authentication_flow.py` (+5 tests, total 8)
- [ ] Run tests, verify pass rate
- [ ] Update coverage report

**Day 5 (January 15) - Scenarios 4-5**
- [ ] Implement `test_network_timeout_recovery.py` (5 tests)
- [ ] Implement `test_cache_invalidation.py` (4 tests)
- [ ] Run tests, verify pass rate
- [ ] Update coverage report
- [ ] Checkpoint review with @project-supervisor-qa

**Day 6 (January 16) - Performance Tests**
- [ ] Implement `test_database_performance.py` (4 tests)
- [ ] Generate large test datasets (1000 settings, 100 projectors)
- [ ] Run benchmarks, document baseline
- [ ] Verify performance targets met

**Day 7 (January 17) - More Performance Tests**
- [ ] Implement `test_performance_benchmarks.py` (PJLink latency, 3 tests)
- [ ] Implement `test_backup_restore_performance.py` (3 tests)
- [ ] Run all performance benchmarks
- [ ] Create `WEEK3-4_PERFORMANCE_BASELINE.md`

**Day 8 (January 18) - Failure Scenarios**
- [ ] Implement `test_file_permission_failures.py` (4 tests)
- [ ] Implement `test_entropy_corruption_recovery.py` (3 tests)
- [ ] Implement `test_pjlink_class_fallback.py` (4 tests)
- [ ] Implement `test_database_migration_flow.py` (4 tests)
- [ ] Run all failure scenario tests

**Day 9 (January 19) - Code Review & Bug Fixes**
- [ ] Code review with @tech-lead-architect
- [ ] Fix identified bugs
- [ ] Refactor test code (DRY, clear assertions)
- [ ] Update test documentation

**Day 10 (January 20) - Performance Documentation**
- [ ] Finalize performance baseline report
- [ ] Analyze coverage gaps (if any)
- [ ] Write unit tests to fill critical gaps
- [ ] Run full test suite, verify 750+ tests

**Day 11 (January 21) - Mock Server Enhancements**
- [ ] Implement 10 remaining Class 2 commands
- [ ] Implement error injection framework
- [ ] Write unit tests for new mock features
- [ ] Run mock server unit tests (48+ tests)

**Day 12 (January 22) - Mock Server Testing**
- [ ] Implement latency simulation
- [ ] Enhance client connection tracking
- [ ] Integration test enhanced mock server
- [ ] Update mock server documentation

**Day 13 (January 23) - Security Testing**
- [ ] Implement `test_sql_injection_prevention.py` (3 tests)
- [ ] Run security scan (bandit, pip-audit)
- [ ] Verify 0 critical/high vulnerabilities
- [ ] Security review with @security-pentester

**Day 14 (January 24-25) - Final Testing & Gate Review**
- [ ] Run full test suite (750+ tests)
- [ ] Verify coverage ≥85% (stretch: 90%)
- [ ] Collect evidence for all deliverables
- [ ] Create gate review document
- [ ] Submit gate review to @project-supervisor-qa

### 8.3 Checkpoints

**Checkpoint 1: Day 5 (January 15)**
- **Milestone:** Foundation tests complete (24 tests)
- **Validation:** All foundation tests passing
- **Gate:** @project-supervisor-qa quality review
- **Criteria:** Tests green, fixtures documented

**Checkpoint 2: Day 10 (January 20)**
- **Milestone:** All integration tests complete (58 tests)
- **Validation:** Performance benchmarks documented
- **Gate:** @tech-lead-architect performance review
- **Criteria:** All targets met or justified

**Checkpoint 3: Day 14 (January 25)**
- **Milestone:** T-003 COMPLETE
- **Validation:** Gate review APPROVED
- **Gate:** @project-supervisor-qa final approval
- **Criteria:** 750+ tests, 85%+ coverage, 0 failed

---

## 9. Acceptance Criteria

### 9.1 Must Have (Blocking)

**Test Count:**
- [x] Current tests: 578 passing ✅
- [ ] New integration tests: +58 tests
- [ ] New unit tests (from T-001, T-002): +100 tests
- [ ] Mock server tests: +10 tests
- [ ] **Total: 746+ tests passing** (target: 750+)

**Code Coverage:**
- [x] Current coverage: 85.52% ✅
- [ ] Maintain ≥85% coverage after all changes
- [ ] Stretch target: 90% coverage

**Test Quality:**
- [ ] 0 failed tests
- [ ] ≤5 skipped tests (document reason for skips)
- [ ] 100% pass rate

**Integration Scenarios:**
- [ ] All 15 priority scenarios implemented and passing
- [ ] Each scenario has clear documentation (docstrings)
- [ ] Each scenario has assertions for expected outcomes

**Performance Benchmarks:**
- [ ] All performance targets met or justified
- [ ] Performance baseline report created
- [ ] Benchmarks automated with pytest-benchmark

**Mock Server:**
- [ ] All 10 Class 2 commands implemented
- [ ] Error injection framework operational
- [ ] Mock server unit tests passing (48+ tests)

### 9.2 Should Have (Important)

**Documentation:**
- [ ] This test plan document complete and committed
- [ ] Performance baseline report created
- [ ] Fixture README.md created
- [ ] Test coverage report generated (HTML)

**Code Quality:**
- [ ] All new tests follow pytest guide conventions
- [ ] Clear test names (test_<scenario>_<expected_outcome>)
- [ ] Arrange-Act-Assert structure
- [ ] Docstrings for all test functions

**Evidence Collection:**
- [ ] Test execution logs saved
- [ ] Coverage reports saved
- [ ] Performance benchmark results saved
- [ ] Gate review evidence collected

### 9.3 Could Have (Nice to Have)

**Advanced Features:**
- [ ] Latency simulation in mock server
- [ ] Advanced error injection (random errors)
- [ ] Real-time test monitoring dashboard
- [ ] Accessibility test framework stubs

**Optimizations:**
- [ ] 90% code coverage (stretch target)
- [ ] All performance benchmarks in "Target" range (not just "Acceptable")
- [ ] Test execution time <120 seconds for full suite

### 9.4 Verification Checklist

**Before submitting for gate review:**

**Test Execution:**
- [ ] Run: `pytest tests/ -v` → All tests passing
- [ ] Run: `pytest tests/ --cov=src --cov-report=html --cov-fail-under=85` → Coverage ≥85%
- [ ] Run: `pytest -m integration tests/integration/ -v` → All integration tests passing
- [ ] Run: `pytest -m performance tests/integration/ --benchmark-only` → All benchmarks pass
- [ ] Run: `pytest tests/ --collect-only -q | wc -l` → Count ≥750 tests

**Code Quality:**
- [ ] Run: `bandit -r src/ -ll` → 0 high/critical issues
- [ ] Run: `pylint src/` → Score ≥8.5/10
- [ ] Review: All new code has type hints
- [ ] Review: All new functions have docstrings

**Documentation:**
- [ ] This test plan committed to `docs/testing/WEEK3-4_INTEGRATION_TEST_PLAN.md`
- [ ] Performance baseline committed to `docs/testing/WEEK3-4_PERFORMANCE_BASELINE.md`
- [ ] Fixture README committed to `tests/fixtures/README.md`
- [ ] Coverage report generated at `htmlcov/index.html`

**Evidence:**
- [ ] Test execution log saved
- [ ] Coverage report screenshot saved
- [ ] Performance benchmark results saved
- [ ] All deliverables documented in gate review

---

## 10. Appendices

### Appendix A: Test File Inventory

**New Test Files to Create (14 files):**

1. `tests/integration/test_database_integrity.py` - 6 tests
2. `tests/integration/test_settings_import_export.py` - 7 tests
3. `tests/integration/test_authentication_flow.py` - expand with +5 tests (total 8)
4. `tests/integration/test_network_timeout_recovery.py` - 5 tests
5. `tests/integration/test_cache_invalidation.py` - 4 tests
6. `tests/integration/test_database_performance.py` - 4 tests
7. `tests/integration/test_performance_benchmarks.py` - 3 tests (PJLink)
8. `tests/integration/test_backup_restore_performance.py` - 3 tests
9. `tests/integration/test_file_permission_failures.py` - 4 tests
10. `tests/integration/test_entropy_corruption_recovery.py` - 3 tests
11. `tests/integration/test_pjlink_class_fallback.py` - 4 tests
12. `tests/integration/test_database_migration_flow.py` - 4 tests
13. `tests/integration/test_sql_injection_prevention.py` - 3 tests
14. `tests/integration/test_backup_restore_workflow.py` - 7 tests (same as #2, consolidated)

**Total New Integration Tests:** 58 tests

**Fixture Files to Create:**

**Corrupted Data:**
- `tests/fixtures/corrupted_data/corrupt_database.db`
- `tests/fixtures/corrupted_data/corrupt_encryption.db`
- `tests/fixtures/corrupted_data/corrupt_entropy.bin`
- `tests/fixtures/corrupted_data/tampered_entropy.bin`
- `tests/fixtures/corrupted_data/corrupt_admin_hash.db`

**Backup Files:**
- `tests/fixtures/backups/backup_100_settings.json`
- `tests/fixtures/backups/backup_with_credentials.json`
- `tests/fixtures/backups/backup_wrong_version.json`
- `tests/fixtures/backups/backup_corrupted_auth_tag.json`

**v1 Databases:**
- `tests/fixtures/databases/v1/fresh_v1.db`
- `tests/fixtures/databases/v1/v1_with_data.db`
- `tests/fixtures/databases/v1/v1_large.db`

**Network Scenarios:**
- `tests/fixtures/network_scenarios/error_configs.json`

**Documentation:**
- `tests/fixtures/README.md`

### Appendix B: pytest Commands Reference

```bash
# Run all tests
pytest tests/ -v

# Run integration tests only
pytest -m integration tests/integration/ -v

# Run performance tests only
pytest -m performance tests/integration/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term --cov-fail-under=85

# Run specific test file
pytest tests/integration/test_database_integrity.py -v

# Run specific test function
pytest tests/integration/test_database_integrity.py::test_integrity_check_detects_missing_tables -v

# Run tests with benchmark
pytest tests/integration/test_performance_benchmarks.py --benchmark-only

# Save benchmark results
pytest tests/integration/test_performance_benchmarks.py --benchmark-save=week3

# Compare benchmarks
pytest-benchmark compare week3 week2

# Run tests and generate HTML report
pytest tests/ --html=report.html --self-contained-html

# Count total tests
pytest tests/ --collect-only -q | tail -1

# Run tests with verbose output and stop on first failure
pytest tests/ -v -x

# Run tests with parallel execution (if pytest-xdist installed)
pytest tests/ -n auto
```

### Appendix C: Test Naming Conventions

**Format:** `test_<scenario>_<expected_outcome>`

**Good Examples:**
- `test_integrity_check_detects_missing_tables`
- `test_backup_with_wrong_password_fails`
- `test_circuit_breaker_opens_after_3_failures`
- `test_settings_lookup_with_index_under_5ms`

**Bad Examples:**
- `test_integrity` (too vague)
- `test_1` (no descriptive name)
- `test_backup_export` (no expected outcome)

**Test Structure (Arrange-Act-Assert):**
```python
def test_integrity_check_detects_missing_tables():
    """Test that integrity check detects missing app_settings table."""

    # ARRANGE: Set up test state
    db_path = Path(__file__).parent.parent / "fixtures" / "corrupted_data" / "corrupt_database.db"
    db = DatabaseManager(str(db_path))
    checker = DatabaseIntegrityChecker(db)

    # ACT: Execute the operation
    result = checker.check_schema()

    # ASSERT: Verify expected outcome
    assert not result.success
    assert "app_settings" in result.missing_tables
    assert result.error_message == "Missing required table: app_settings"
```

### Appendix D: Risk Mitigation

**Risk 1: T-003 delayed by T-001/T-002**
- **Mitigation:** Start fixture creation on Day 3 (independent of dependencies)
- **Mitigation:** Mock server enhancements independent of T-001/T-002
- **Mitigation:** Prioritize scenarios without dependencies (e.g., cache invalidation)

**Risk 2: Performance benchmarks fail to meet targets**
- **Mitigation:** Document justification for any targets not met
- **Mitigation:** Create follow-up optimization tasks for Week 5-6
- **Mitigation:** Establish "Acceptable" range (not just "Target")

**Risk 3: Mock server enhancements too complex**
- **Mitigation:** Prioritize Class 2 commands over error injection (Class 2 is Must Have)
- **Mitigation:** Defer latency simulation to "Could Have" (not blocking)
- **Mitigation:** Use existing error handling patterns from Class 1 implementation

**Risk 4: Integration test count below 750**
- **Mitigation:** 58 integration tests + 100 unit tests + 10 mock tests = 746 tests (close to target)
- **Mitigation:** Add 5-10 additional edge case tests if needed (e.g., boundary conditions)
- **Mitigation:** Expand existing test scenarios with additional assertions

---

**End of Integration Test Plan**

**Document Status:** READY FOR IMPLEMENTATION
**Next Steps:** Review with @project-supervisor-qa, begin Day 3 implementation (January 13)
**Questions?** Contact @test-engineer-qa or @project-orchestrator

---

**File Statistics:**
- Lines: ~1,850
- Word Count: ~12,500
- Estimated Read Time: 45-60 minutes
- Last Updated: 2026-01-11
- Version: 1.0
