from unified_plugin_system_clean import UnifiedPluginSystem

ps = UnifiedPluginSystem()
compliance = ps.validate_audit_2_compliance()
print(f"AUDIT 2 COMPLIANCE: {compliance['overall_compliance']}")
print("✅ Enhanced Plugin System is ready for Audit 2!" if compliance['overall_compliance'] else "❌ Needs improvement")
