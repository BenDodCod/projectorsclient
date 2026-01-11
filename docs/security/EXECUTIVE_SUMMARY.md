# Security Threat Model - Executive Summary

**Project:** Enhanced Projector Control Application
**Date:** 2026-01-10
**Author:** Security Manager & Penetration Testing Engineer
**Status:** Week 1-2 Preparation Phase

---

## Risk Overview

| Category | Count | Action Required |
|----------|-------|-----------------|
| **CRITICAL** | 4 | Fix immediately (Task 2, Week 1) |
| **HIGH** | 8 | Fix before Phase 3 |
| **MEDIUM** | 10 | Address Weeks 3-6 |
| **LOW** | 6 | Document and monitor |

---

## Top 5 Critical Threats

### 1. T-001: Plaintext SQL Server Credentials (CRITICAL)
**Issue:** Legacy `projectors.proj_pass` column stores passwords in plaintext in SQL Server.

**Impact:** Database breach exposes all projector passwords immediately.

**Fix:** Read-only access in v1.0, encrypted column in v1.1, deprecate plaintext in v1.2.

---

### 2. T-002: Admin Password Bypass (CRITICAL)
**Issue:** Attacker can delete password hash from SQLite database, triggering first-run wizard.

**Impact:** Complete bypass of admin authentication, full configuration access.

**Fix:** Implement database integrity verification using HMAC.

---

### 3. T-003: DPAPI Without Entropy (CRITICAL)
**Issue:** DPAPI encryption without application-specific entropy allows same-user decryption.

**Impact:** Malware running as same user can extract all stored credentials.

**Fix:** Add application-specific entropy: `hashlib.sha256(app_secret + machine_name)`.

---

### 4. T-007: SQL Injection Potential (CRITICAL)
**Issue:** If any query uses string concatenation instead of parameterization, injection is possible.

**Impact:** Data extraction, modification, potential server compromise.

**Fix:** Audit all queries, mandatory parameterization, automated CI checks.

---

### 5. T-010: PJLink MD5 Authentication (HIGH)
**Issue:** PJLink protocol uses weak MD5 authentication (protocol design limitation).

**Impact:** Network attacker can capture and crack projector passwords.

**Fix:** Cannot fix protocol. Document limitations, require network isolation and strong passwords.

---

## Immediate Actions for @backend-infrastructure-dev (Task 2)

### Week 1 Deliverables:

| Priority | Action | File/Component |
|----------|--------|----------------|
| P1 | Add DPAPI entropy to encrypt/decrypt | `src/utils/security.py` |
| P2 | Implement database integrity check | `src/utils/db_integrity.py` |
| P3 | Implement account lockout | `src/utils/rate_limiter.py` |
| P4 | Add SecureFormatter for logging | `src/utils/logging_config.py` |
| P5 | Implement Windows ACL file security | `src/utils/file_security.py` |
| P6 | Audit all SQL queries (parameterized) | All database access code |

---

## Security Requirements Summary

### Must Have (v1.0):
- [x] bcrypt with work factor >= 12 for admin password
- [ ] DPAPI encryption with application entropy
- [ ] Database integrity verification
- [ ] Account lockout (5 attempts, 5 minutes)
- [ ] Parameterized SQL queries everywhere
- [ ] Credential redaction in logs
- [ ] Windows ACL on database file

### Should Have (v1.0 or v1.1):
- [ ] SecureString wrapper for memory clearing
- [ ] JSON schema validation for imports
- [ ] Configuration export encryption (AES-GCM)
- [ ] Path traversal prevention

### Documentation Required:
- [ ] PJLink protocol security limitations
- [ ] Network isolation requirements
- [ ] Strong password guidance

---

## Architecture Threat Summary

```
+------------------+     +------------------+     +------------------+
| SQLite Database  |     | Network Layer    |     | SQL Server       |
|------------------|     |------------------|     |------------------|
| T-002: DB bypass |     | T-008: PJLink    |     | T-001: Plaintext |
| T-003: DPAPI     |     |   credential     |     |   passwords      |
| T-011: ACL       |     |   capture        |     | T-007: SQL       |
|                  |     | T-013: TLS       |     |   injection      |
+------------------+     +------------------+     +------------------+
```

---

## Coordination Notes

**For @backend-infrastructure-dev:**
- Prioritized vulnerability list delivered (see Section 6 in full document)
- Code examples for all critical fixes included (see Section 8)
- Security requirements mapped to specific functions

**For @tech-lead-architect:**
- Architecture-level security concerns documented
- Network security limitations (PJLink) require deployment guidance
- Recommend security architecture review meeting

**For @test-engineer-qa:**
- Penetration test scenarios documented (27 threats cataloged)
- Security test requirements specified
- CI/CD security scan configuration provided

---

## Approval Required

- [ ] Tech Lead Architect approval
- [ ] Project Orchestrator approval
- [ ] Security review complete

---

## Next Steps

1. **Wednesday AM:** @backend-infrastructure-dev begins Task 2 security implementation
2. **Week 1-2:** Implement P1-P6 critical/high fixes
3. **Week 3:** Security review of implementation
4. **Ongoing:** Medium/Low issues addressed in subsequent phases

---

**Full Threat Model:** `docs/security/threat_model.md`

**Questions/Concerns:** Contact Security Manager
