"""Quick smoke test for aura-sdk package."""
import sys
sys.path.insert(0, r'C:\Users\navid\Desktop\AURA\06_SOURCE_CODE\aura-sdk')
import aura_sdk

print('AuraSDK:', aura_sdk.AuraSDK().start())
from aura_sdk.adapters.adapter_manager import AdapterManager
am = AdapterManager()
am.register('one', {'x':1})
print('Adapter keys:', am.list())
from aura_sdk.analytics.analytics_manager import AnalyticsManager
an = AnalyticsManager()
an.record('evt', {'a':2})
print('Analytics events:', an.get_events('evt'))
from aura_sdk.benchmarking.benchmark_manager import BenchmarkManager
bm = BenchmarkManager()
bm.start('t1')
import time
time.sleep(0.01)
print('Timer t1 elapsed:', bm.stop('t1'))

# Test injected validator on a known validator class
from aura_sdk.analytics import validator as valmod
import inspect
cls = None
for name, obj in inspect.getmembers(valmod, inspect.isclass):
    if name.endswith('Validator'):
        cls = obj
        break
if cls:
    v = cls()
    print('Validator present:', cls.__name__, 'validate->', v.validate({'ok':True}))
else:
    print('No validator class in analytics.validator')
