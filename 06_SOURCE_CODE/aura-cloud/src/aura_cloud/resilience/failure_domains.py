def analyze(resources): return {str(x.get('failure_domain','unknown')) for x in resources}
