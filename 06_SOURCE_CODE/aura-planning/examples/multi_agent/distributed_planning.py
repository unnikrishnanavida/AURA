def distribute(tasks,agents):
    return {agent:list(tasks[i::len(agents)]) for i,agent in enumerate(agents)} if agents else {}
