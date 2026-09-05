def calibrate(raw, contradiction):
    return max(0,min(1,raw*(1-0.6*max(0,min(1,contradiction)))))
