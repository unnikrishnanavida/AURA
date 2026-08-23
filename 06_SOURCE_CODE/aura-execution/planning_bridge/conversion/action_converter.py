from aura_execution.actions.models.executable_action import ExecutableAction
def convert_action(planned,handler=None):return ExecutableAction(planned.action_id,planned.action_id,planned.capability,inputs=planned.inputs,handler=handler)
