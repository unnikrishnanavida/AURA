from aura_cloud.engine import CloudControlPlane
from aura_cloud.providers.simulator import SimulatedProvider
from aura_cloud.models import CloudIntent
def test_plan(): assert CloudControlPlane(SimulatedProvider()).plan(CloudIntent('a','r',('compute',))).provider=='simulated'
