def state_diff(before,after):
    keys=set(before)|set(after)
    return {k:(before.get(k),after.get(k)) for k in keys if before.get(k)!=after.get(k)}
