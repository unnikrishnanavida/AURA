class ConstraintPropagator:
    def propagate(self, domains, constraints):
        domains={k:set(v) for k,v in domains.items()}
        changed=True
        while changed:
            changed=False
            for constraint in constraints:
                if hasattr(constraint,"propagate"):
                    new=constraint.propagate(domains)
                    if new!=domains: domains=new; changed=True
        return domains
