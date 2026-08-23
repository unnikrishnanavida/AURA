class ReliabilityLearner:
    def update(self,stats,success):
        stats["runs"]=stats.get("runs",0)+1;stats["successes"]=stats.get("successes",0)+int(success)
        return stats["successes"]/stats["runs"]
