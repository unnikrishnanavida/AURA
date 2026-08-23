def decompose(goal):
    text=getattr(goal,"description",str(goal))
    return tuple(part.strip() for part in text.split(" and ") if part.strip())
