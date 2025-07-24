# Plugin Security Audit Report
**Generated:** 2025-07-18 19:39:55

## Summary
- **Total Plugins Audited:** 5
- **Secure Plugins:** 0
- **Critical Issues:** 4
- **Overall Security Score:** 0.06

## Detailed Results
### example_security_plugin
- **Security Level:** HIGH
- **Compliance Score:** 0.00
- **Violations:** 7
- **Security Violations:**
  - DANGEROUS_IMPORTS: Dangerous import detected: sys
  - DANGEROUS_IMPORTS: Dangerous import detected: os
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: os\.path
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: __file__
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+os\b
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+sys\b
  - FILE_SYSTEM_ACCESS: Plugin file is world-writable

### example_service_plugin
- **Security Level:** CRITICAL
- **Compliance Score:** 0.00
- **Violations:** 13
- **Security Violations:**
  - DANGEROUS_IMPORTS: Dangerous import detected: sys
  - DANGEROUS_IMPORTS: Dangerous import detected: os
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: os\.path
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: __file__
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+os\b
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+sys\b
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - FILE_SYSTEM_ACCESS: Plugin file is world-writable

### network_monitor_plugin
- **Security Level:** CRITICAL
- **Compliance Score:** 0.30
- **Violations:** 2
- **Security Violations:**
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - FILE_SYSTEM_ACCESS: Plugin file is world-writable

### sample_secure_plugin
- **Security Level:** CRITICAL
- **Compliance Score:** 0.00
- **Violations:** 10
- **Security Violations:**
  - DANGEROUS_IMPORTS: Dangerous import detected: os
  - DANGEROUS_IMPORTS: Dangerous import detected: sys
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: open\s*\(
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: os\.path
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: os\.path
  - FILE_SYSTEM_ACCESS: Dangerous pattern detected: __file__
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+os\b
  - DANGEROUS_IMPORTS: Dangerous pattern detected: import\s+sys\b
  - CODE_INJECTION: Dangerous pattern detected: getattr\s*\(
  - FILE_SYSTEM_ACCESS: Plugin file is world-writable

### security_scanner_plugin
- **Security Level:** CRITICAL
- **Compliance Score:** 0.00
- **Violations:** 4
- **Security Violations:**
  - SUBPROCESS_EXECUTION: Dangerous pattern detected: os\.system
  - CODE_INJECTION: Dangerous pattern detected: eval\s*\(
  - CODE_INJECTION: Dangerous pattern detected: exec\s*\(
  - FILE_SYSTEM_ACCESS: Plugin file is world-writable
