def spend_anomaly(current,baseline): return 0.0 if baseline<=0 else max(0,(current-baseline)/baseline)
