TOLERANCE = 1e-8

def calculate(c, feeders, reserve, external, consumption, losses, work, refills, requests, inspections, visits):
    initial=c.reserve+sum(f.initial for f in c.feeders)
    final=reserve+sum(f['level'] for f in feeders)
    residual=initial+external-consumption-losses-final
    shortage=sum(f['shortage'] for f in feeders)
    service=(c.service_end-c.service_start)*len(feeders)
    return {'shortage':shortage/len(feeders), 'waste':100*losses/(initial+external) if initial+external else None,
            'refills':refills,'work':work,'availability':max(0,min(100,100*(1-shortage/service))),
            'initial':initial,'external':external,'consumption':consumption,'losses':losses,'recoverable':0,
            'final':final,'reserve_final':reserve,'balance_error':residual,'consistent':abs(residual)<=TOLERANCE,
            'potential_demand':sum(f['potential'] for f in feeders),'unmet_demand':sum(f['unmet'] for f in feeders),
            'pending':sum(f['request']!='none' for f in feeders),'requests':requests,'inspections':inspections,'visits':visits}
