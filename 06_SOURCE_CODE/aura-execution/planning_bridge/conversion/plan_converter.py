from .action_converter import convert_action
def convert_plan(plan,handlers=None):return [convert_action(a,(handlers or {}).get(a.action_id)) for a in plan.actions]
