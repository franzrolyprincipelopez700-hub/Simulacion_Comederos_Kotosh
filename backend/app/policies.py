def inspection_times(c):
    if c.policy == 'P0': return sorted(set(c.schedule))
    interval = c.step if c.policy == 'P2' and c.continuous else c.interval
    return [i*interval for i in range(int(c.horizon/interval)+1) if i*interval<c.horizon]

def requires_reload(c, feeder):
    return feeder['level'] <= c.threshold*feeder['capacity']+1e-10 if c.policy=='P2' else feeder['level']<c.target*feeder['capacity']-1e-10
