from aura_cloud.engine import CloudControlPlane
from aura_cloud.providers.simulator import SimulatedProvider
from aura_cloud.models import CloudIntent
print(CloudControlPlane(SimulatedProvider()).plan(CloudIntent('aura','local',('compute',))))
