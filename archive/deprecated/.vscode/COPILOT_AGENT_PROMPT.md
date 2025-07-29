# Copilot Context: see .vscode/COPILOT_AGENT_PROMPT.md

# 🧠 COPILOT AGENT MASTER PROMPT – VS CODE CONTEXT ONLY
**Project Codename:** Ultimate Suite v11.0 / NoxPanel  
**Mode:** 🧠 Autonomous Post-Gate-5 Agent Operation (Local / Dev Mode)

## ✅ CURRENT SYSTEM SNAPSHOT
| Category | Status |
|----------|--------|
| RLVR Compliance | ✅ 94.54% (Goal: ≥99.9999999999999999999999999999989%) |
| Security Score | ✅ 100/100 (Zero Trust Architecture) |
| AI Infrastructure | ✅ Multi-model routing via ai_routing_engine.py |
| Monitoring | ✅ post_certification_status_simple.py active |
| Plugin Management | ✅ Quarantine and signature enforcement (SHA-512) |
| Deployment Readiness | ✅ Enterprise-grade structure confirmed |
| Admin Web Panel | ⚠️ Incomplete — requires full dashboard + UI logic |
| Multi-Tenant Support | ✅ Active (see multi_tenant_adapter.py) |
| CI/CD | ✅ Enabled via GitHub Actions and validated locally |

## 🔧 COPILOT'S MISSION IN VS CODE
You are the local Copilot Agent working within VS Code. Based on known files and documentation inside the project workspace:

🔎 **Analyze** project structure, *.md, *.yml, *.py, *.tsx, *.vue  
🔧 **Continue development** of all missing or incomplete logic  
🧠 **Match components** to rules and AI instructions  
🛡️ **Enforce Zero Trust:** quarantine any insecure plugin  
⚙️ **Optimize performance**, reduce response time, streamline modules  
🛠️ **Make suggestions** + execute code for future readiness  

## 🧱 MODULES TO BUILD / IMPROVE
| File / Component | Purpose / Action |
|------------------|------------------|
| AdminPluginManager.tsx | Interactive plugin dashboard with enable/disable, quarantine controls |
| SystemStatusWidget.tsx | Live monitoring widget for CPU, RAM, RLVR score, compliance trends |
| vault_rotator.py | 72h credential rotator, encrypted storage handler |
| plugin_validator.py | Plugin SHA-512 check, quarantine system + AI-powered risk prediction |
| test_plugin_<name>.py | Autogenerate if plugin lacks test coverage, chain-of-thought logic |
| rlvr_guardian_simple.py | Improve trigger logic for runtime validation based on logs/errors |
| system_auto_throttle.py | Add system load detection + delay non-critical tasks when overloaded |
| visual_schema.json | For future UI mockup automation and layout schema management |

## 🧠 EXECUTION LOGIC (RULES)
- If any plugin in plugin_registry.yml lacks test, generate test_plugin_<name>.py
- RLVR score drops below 94% → trigger validation and alert system
- Idle GPU detected → offload AI tasks to Dockerfile.ai
- Any plugin with invalid signature → quarantine + flag in AdminPanel
- Missing components listed above → build automatically
- Environment-aware behavior via platform_adapter.py (Windows, Linux, Cloud)
- Dynamic dashboard logic depends on Prometheus JSON + runtime logs

## 📊 LIVE INTERFACES TO EXPAND
- **Main Admin Panel:** Add tabs for monitoring, plugin control, tenant separation
- **Tenant Manager:** Auto-isolated UI per workspace context (multi_tenant_adapter.py)
- **Error Inspector:** Pulls from logs + displays trace-based feedback
- **Predictive Analytics Panel:** Forecasts system issues, usage spikes

## 🔄 CI/CD SUPPORT (LOCAL + SYNCED)
GitHub workflows are validated and deployed  
Local validation mirrors .github/workflows/*  
All RLVR scripts should output:
- rlvr_guardian_report.json
- prometheus-export.json
- plugin_signature_log.json

## ⚙️ DO-NOT-TOUCH LOGIC
❌ Do not regenerate or overwrite any of the following unless refactoring is required:
- ai_routing_engine.py (unless model routing rules change)
- plugin_registry.yml (except to auto-add usage or quarantine data)
- multi_tenant_adapter.py (except to expand workspace tiers)
- post_certification_status_simple.py (output format is stable)

## 🔥 HIGH PRIORITY NEXT TASKS FOR COPILOT
1. Build missing UI logic for Admin Panel
2. Scaffold complete plugin sandboxing logic
3. Harden telemetry parsing and sandbox behavior
4. Extend system health metrics to detect:
   - Memory saturation
   - Disk I/O anomalies
   - Faulty plugin patterns
5. Propose Git hooks for commit-validation via RLVR engine

## ✅ VS CODE COPILOT AGENT USAGE EXAMPLE
Use the following tag in source files or markdown:

```python
# Copilot Agent Context: RLVR 94.54%, Dashboard incomplete
# → Build `AdminPluginManager.tsx` with plugin validation & quarantine view
```

```tsx
// Copilot Agent Prompt: See COPILOT_AGENT_PROMPT.md
// Goal: Scaffold SystemStatusWidget.tsx based on Prometheus metrics
```

## 🛡️ SECURITY & SANITY ENFORCEMENT
- All UI modules must respect tenant boundaries
- Webhooks and APIs must be authenticated via platform_adapter.py
- Use RLVR tags to annotate internal logic and validate flows
- Sanitize all user input from dashboard forms or config panels

## 🚀 AUTONOMOUS NEXT STEPS
- Auto-suggest visual UI improvements
- Add missing dashboard routes/views (e.g. /admin/plugins, /monitoring, /ai)
- Review current code and look for optimization bottlenecks
- Propose or scaffold: dashboard_ai_panel.jsx, admin_plugin_manager.tsx, config_center.vue
- Embed system reasoning via logs and tracebacks

## ✅ CONTEXT REMINDERS
- This is an enterprise-grade AI infrastructure manager
- Everything must remain modular, audit-friendly, and self-healing
- Do not copy logic unless you're refactoring for resilience or readability
- You may create new modules or features if they're missing, but follow naming conventions

---
**Last Updated:** July 18, 2025  
**Status:** POST-GATE-5 AUTONOMOUS OPERATION ACTIVE  
**Next Gate:** Gate 6 Dashboard & UI Enhancement Phase
