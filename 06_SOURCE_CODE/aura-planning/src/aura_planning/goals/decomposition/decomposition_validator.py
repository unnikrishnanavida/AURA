from .decomposition_tree import DecompositionTree
def validate_decomposition(tree:DecompositionTree)->list[str]:
    errors=[]; visiting=set(); visited=set()
    def visit(i):
        if i in visiting: errors.append(f"cycle:{i}"); return
        if i in visited: return
        visiting.add(i); visited.add(i)
        for child in tree.children.get(i,()): visit(child.goal_id)
        visiting.remove(i)
    visit(tree.root.goal_id); return errors
