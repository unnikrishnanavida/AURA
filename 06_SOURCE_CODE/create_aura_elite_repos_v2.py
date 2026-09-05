#!/usr/bin/env python3
# AURA ELITE REPOSITORIES V2
# Safe architecture generator for research, cloud, desktop, execution-complete and mobile.
from __future__ import annotations
import argparse
from pathlib import Path

COMMON = ['docs/architecture','docs/operations','docs/security','docs/adr','examples','scripts','tests/unit','tests/integration','tests/e2e','tests/fixtures','benchmarks','deployment/docker','.github/workflows']

REPOS = {
'aura-research': {'pkg':'aura_research','features':['epistemic ledger','claim passports','evidence provenance graph','contradiction-aware synthesis','uncertainty calibration','hypothesis graph','novelty analysis','reproducibility capsules','source freshness decay','research replay'],'modules':['questions/decomposition','questions/intent','claims/models','claims/lifecycle','claims/passport','evidence/models','evidence/fusion','evidence/quality','sources/passport','sources/freshness','sources/trust','hypotheses/graph','hypotheses/generator','hypotheses/falsification','contradictions/detector','contradictions/resolution','uncertainty/calibration','uncertainty/abstention','novelty/analysis','novelty/prior_art','experiments/plan','experiments/reproducibility','ledger/events','ledger/replay','ledger/provenance_graph','synthesis/engine','synthesis/citation_map','governance/research_policy','security/source_integrity','providers/contracts','providers/registry']},
'aura-cloud': {'pkg':'aura_cloud','features':['intent compiler','cloud digital twin','policy-before-plan','blast-radius estimation','drift detection','canary and rollback gates','cost and carbon awareness','multi-cloud failover','safe chaos contracts','change provenance ledger'],'modules':['intent/compiler','intent/models','intent/validator','providers/contracts','providers/registry','providers/capability_matrix','digital_twin/models','digital_twin/state','digital_twin/simulator','policy/engine','policy/as_code','policy/approval','planning/plan','planning/blast_radius','planning/dependencies','deployment/canary','deployment/rollback','deployment/change_control','drift/detector','drift/reconciler','resilience/failover','resilience/circuit_breaker','finops/cost_model','finops/budget_guard','sustainability/carbon_estimator','chaos/safe_experiment','chaos/contracts','ledger/change_events','ledger/provenance','observability/health','observability/metrics','observability/tracing','security/identity_boundary','security/secret_boundary']},
'aura-desktop': {'pkg':'aura_desktop','features':['local-first workspace','secure capability broker','crash recovery','workspace replay','intent routing','accessibility adaptation','plugin isolation','privacy-preserving telemetry','cross-device handoff','local cognitive cockpit'],'modules':['app/bootstrap','app/lifecycle','workspace/models','workspace/manager','workspace/journal','intent/router','intent/commands','capabilities/broker','capabilities/manifest','capabilities/approval','ipc/contracts','ipc/authentication','ipc/validation','plugins/manifest','plugins/registry','plugins/isolation','state/store','state/snapshots','state/recovery','replay/session_replay','replay/crash_reconstruction','handoff/device_handoff','privacy/local_telemetry','accessibility/adaptive_ui','accessibility/preferences','updates/update_policy','updates/rollback','integrations/aura','integrations/desktop_os','observability/diagnostics','observability/redaction']},
'aura-execution-complete': {'pkg':'aura_execution','features':['Execution DNA','action genome','capability graph','precondition and postcondition contracts','multi-dimensional budgets','checkpoint and recovery','deterministic replay','saga compensation','shadow execution','approval gates','execution provenance'],'modules':['action_genome/identity','action_genome/lineage','action_genome/performance','actions/models','actions/preconditions','actions/postconditions','actions/dispatch','capabilities/graph','capabilities/matching','capabilities/registry','budgets/models','budgets/tracker','budgets/reservation','approval/gates','approval/models','execution_state/models','execution_state/transitions','checkpoints/models','checkpoints/manager','checkpoints/recovery','saga/compensation','saga/orchestrator','shadow/simulator','shadow/comparator','concurrency/scheduler','concurrency/coordination','flight_recorder/events','flight_recorder/replay','flight_recorder/reconstruction','provenance/lineage','provenance/explanations','memory_bridge/retrieval','memory_bridge/writing','learning_bridge/signals','learning_bridge/authorization','security/policy_boundary','security/sandbox_boundary','kernel/runtime','kernel/lifecycle']},
'aura-mobile': {'pkg':'aura_mobile','features':['offline-first intelligence','privacy-aware context','device trust','capability broker','energy-aware scheduling','conflict-safe sync','secure handoff','adaptive accessibility','local intent cache','sensor minimization'],'modules':['app/bootstrap','app/lifecycle','offline/cache','offline/queue','offline/conflicts','sync/engine','sync/contracts','sync/handoff','permissions/broker','permissions/models','device/trust','device/attestation_contract','context/models','context/minimization','context/policy','runtime/network','runtime/battery','runtime/sessions','energy/budget','energy/scheduler','privacy/data_minimization','privacy/local_retention','sensors/contracts','sensors/minimization','intent/local_router','intent/cache','accessibility/preferences','accessibility/adaptive','notifications/policy','notifications/priority','security/secure_storage_contract','security/replay_protection','observability/redaction','observability/health']}
}

def module_text(repo, mod):
    return f'# {repo}: {mod}\n# Contract module. Implement one real responsibility; preserve provenance and explicit failure semantics.\n'

def root_files(repo, features):
    feature_text='\n'.join('- '+x for x in features)
    return {
      'README.md': '# '+repo+'\n\n## Elite AURA capabilities\n'+feature_text+'\n',
      'ARCHITECTURE.md': '# Architecture\n\nArchitecture-first, contracts at trust boundaries, vertical-slice implementation, replay and provenance where applicable.\n',
      'SECURITY.md':'# Security\n\nHigh-risk changes require review, explicit authorization, and regression tests.\n',
      'CONTRIBUTING.md':'# Contributing\n\nDo not replace domain behavior with generic placeholder engines.\n',
      '.gitignore':'.venv/\n__pycache__/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.env\nbuild/\ndist/\n',
      '.env.example':'AURA_ENVIRONMENT=development\n',
      'pyproject.toml':'[build-system]\nrequires=["setuptools>=69"]\nbuild-backend="setuptools.build_meta"\n\n[project]\nname="'+repo+'"\nversion="0.2.0"\nrequires-python=">=3.11"\n\n[project.optional-dependencies]\ndev=["pytest>=8","ruff>=0.6","mypy>=1.10"]\n\n[tool.setuptools.packages.find]\nwhere=["src"]\n',
      'docs/architecture/dependency_rules.md':'# Dependency Rules\n\nDomain code must not depend on UI or deployment code. Integrations depend on contracts.\n',
      'docs/architecture/unique_features.md':'# Unique Features\n\nAURA-specific behavior must remain explicit, testable, and observable.\n',
      'docs/operations/runbook.md':'# Operations Runbook\n\nDocument startup, failure modes, recovery, rollback and incidents.\n',
      'docs/security/threat_review.md':'# Threat Review\n\nRecord assets, trust boundaries, attack paths, mitigations and residual risk.\n',
      '.github/workflows/ci.yml':'name: ci\non: [push,pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with: {python-version: "3.11"}\n      - run: python -m pip install -e ".[dev]"\n      - run: pytest\n',
      'deployment/docker/Dockerfile':'FROM python:3.11-slim\nWORKDIR /app\nCOPY . /app\nRUN pip install --no-cache-dir .\nCMD ["python","-c","print(\"Provide production entrypoint\")"]\n'
    }

def special_code(pkg, repo):
    p='src/'+pkg
    out={f'{p}/__init__.py':"__version__ = '0.2.0'\n",f'{p}/core/ids.py':'from uuid import uuid4\ndef new_id(): return str(uuid4())\n'}
    if repo=='aura-research':
      out[f'{p}/uncertainty/abstention.py']='def should_abstain(c,t=.55): return c<t\ndef honest_answer(c): return "I do not know based on sufficient evidence." if should_abstain(c) else None\n'
      out['tests/unit/test_abstention.py']='from aura_research.uncertainty.abstention import honest_answer\ndef test_abstain(): assert "do not know" in honest_answer(.1).lower()\n'
    elif repo=='aura-cloud':
      out[f'{p}/planning/blast_radius.py']='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass BlastRadius: affected_resources:int; critical_dependencies:int\ndef risk_score(x): return min(1.0,(x.affected_resources+3*x.critical_dependencies)/100)\n'
      out[f'{p}/deployment/change_control.py']='def may_deploy(approved,simulation_passed,risk): return approved and simulation_passed and risk<.5\n'
      out['tests/unit/test_blast_radius.py']='from aura_cloud.planning.blast_radius import BlastRadius,risk_score\ndef test_risk(): assert risk_score(BlastRadius(0,10))>risk_score(BlastRadius(10,0))\n'
    elif repo=='aura-desktop':
      out[f'{p}/capabilities/broker.py']='class CapabilityBroker:\n def __init__(self,granted=()): self.granted=set(granted)\n def require(self,x):\n  if x not in self.granted: raise PermissionError(f"capability denied: {x}")\n'
      out[f'{p}/state/recovery.py']='def choose_recovery(recorded): return "RECORDED" if recorded else "RECONSTRUCTED"\n'
      out['tests/unit/test_default_deny.py']='import pytest\nfrom aura_desktop.capabilities.broker import CapabilityBroker\ndef test_deny():\n with pytest.raises(PermissionError): CapabilityBroker().require("filesystem.write")\n'
    elif repo=='aura-execution-complete':
      out[f'{p}/budgets/reservation.py']='from dataclasses import dataclass\n@dataclass\nclass Budget:\n limit:int; used:int=0\n def reserve(self,n):\n  if n<0 or self.used+n>self.limit: return False\n  self.used+=n; return True\n'
      out[f'{p}/approval/gates.py']='def authorize(high_risk,approved): return approved if high_risk else True\n'
      out[f'{p}/saga/compensation.py']='def compensation_order(done): return list(reversed(done))\n'
      out['tests/unit/test_budget.py']='from aura_execution.budgets.reservation import Budget\ndef test_budget():\n b=Budget(3); assert b.reserve(2); assert not b.reserve(2)\n'
    elif repo=='aura-mobile':
      out[f'{p}/permissions/broker.py']='class PermissionBroker:\n def __init__(self,granted=()): self.granted=set(granted)\n def require(self,x):\n  if x not in self.granted: raise PermissionError(f"permission denied: {x}")\n'
      out[f'{p}/offline/queue.py']='from dataclasses import dataclass,field\n@dataclass\nclass SyncQueue:\n items:list[dict]=field(default_factory=list)\n def enqueue(self,x): self.items.append(dict(x))\n def drain(self):\n  x,self.items=self.items,[]; return x\n'
      out['tests/unit/test_default_deny.py']='import pytest\nfrom aura_mobile.permissions.broker import PermissionBroker\ndef test_deny():\n with pytest.raises(PermissionError): PermissionBroker().require("camera")\n'
    return out

def add_inits(files):
    for path in list(files):
      if path.startswith('src/') and path.endswith('.py'):
        parent=Path(path).parent
        while str(parent).startswith('src'):
          files.setdefault(str(parent/'__init__.py'),'')
          if str(parent)=='src': break
          parent=parent.parent

def dirs_for(files):
    dirs=set(COMMON)
    for path in files:
      if path.startswith('src/'):
        parent=Path(path).parent
        while str(parent).startswith('src'):
          dirs.add(str(parent))
          if str(parent)=='src': break
          parent=parent.parent
    return dirs

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--force',action='store_true'); ap.add_argument('--report',action='store_true'); a=ap.parse_args()
 print('\nAURA ELITE REPOSITORIES V2\n'+'='*65)
 plans=[]
 for repo,spec in REPOS.items():
  files=root_files(repo,spec['features']); pkg=spec['pkg']; p='src/'+pkg
  for m in spec['modules']: files[f'{p}/{m}.py']=module_text(repo,m)
  files.update(special_code(pkg,repo)); add_inits(files); plans.append((repo,files))
  print(f'{repo:26} directories={len(dirs_for(files)):3} files={len(files):3}')
 if a.report: print('\nREPORT MODE: nothing written.'); return
 root=Path(a.root).expanduser().resolve(); root.mkdir(parents=True,exist_ok=True); written=preserved=0
 for repo,files in plans:
  base=root/repo
  for d in dirs_for(files): (base/d).mkdir(parents=True,exist_ok=True)
  for rel,content in files.items():
   target=base/rel; target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.stat().st_size>0 and not a.force: preserved+=1; continue
   target.write_text(content,encoding='utf-8'); written+=1
 print(f'\nTarget: {root}\nWritten: {written}\nExisting non-empty preserved: {preserved}')
 print('Architecture created. Implement vertical slices and tests before claiming production readiness.')

if __name__=='__main__': main()
