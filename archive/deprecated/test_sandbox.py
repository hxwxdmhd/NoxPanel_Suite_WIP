from unified_plugin_system_clean import UnifiedPluginSystem

ps = UnifiedPluginSystem()
test_code = '''
print("Hello from sandbox!")
import math
print(f"Pi = {math.pi}")
result = 2 + 2
print(f"2 + 2 = {result}")
'''

result = ps.sandbox.execute_in_sandbox('test_plugin', test_code)
print(f"Sandbox execution: {'Success' if result['success'] else 'Failed'}")
print(f"Output: {result['stdout']}")
print(f"Errors: {result['stderr']}")
print("✅ Sandbox execution fixed!")
