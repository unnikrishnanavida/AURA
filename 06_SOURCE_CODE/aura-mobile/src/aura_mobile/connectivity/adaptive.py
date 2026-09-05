def choose_mode(online,bandwidth):return 'offline' if not online else ('full' if bandwidth>=2 else 'constrained')
