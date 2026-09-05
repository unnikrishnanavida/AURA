from enum import Enum
class ReplanningReason(str,Enum):
    STATE_CHANGE="state_change"; ACTION_FAILURE="action_failure"; GOAL_CHANGE="goal_change"; CONSTRAINT_CHANGE="constraint_change"; PLAN_DRIFT="plan_drift"
