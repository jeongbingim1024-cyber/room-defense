import json
UPS=['scrap','hp','dmg','range','loot','fence','crit']
def ups(n, cap=0): d={k:min(n, 6 if k in('range','fence') else 10) for k in UPS}; d['cap']=cap; return d
P = {
 'fresh': {},
 'early': {'up': ups(3), 'chars':[['jogger',0,2]], 'chEq':'jogger', 'gear':[[s,0,2,1] for s in ['helm','top','pants','shoes','lid','broom']]},
 'mid': {'up': ups(6,1), 'tw': {'laser':3,'tesla':3,'cannon':3,'sling':1,'hammer':3,'swatter':3,'coil':3,'fridge':1,'microwave':1},
         'twL': {'laser':5,'tesla':5,'cannon':5,'sling':3,'hammer':5,'swatter':5,'coil':5},
         'deck':['fan','laser','glue','hammer','coil','swatter','tesla','cannon','sling'],
         'chars':[['mech',1,5]], 'chEq':'mech', 'pets':[['puppy',0]], 'petEq':'puppy',
         'gear':[[s,2,2,3] for s in ['helm','top','pants','shoes','lid','broom']]},
 'late': {'up': ups(10,2), 'unl': {'slot2':True,'autorep':True,'freeroll':True,'perk4':True},
          'tw': {k:10 for k in ['deskfan','magnifier','tape','fridge','candle','powerstrip','microwave','aircon','railgun','laser','tesla','cannon','sling','hammer','swatter','coil','fan','glue']},
          'twL': {k:9 for k in ['magnifier','fridge','candle','powerstrip','microwave','railgun','laser','tesla','cannon','sling','hammer','swatter','coil']},
          'deck':['fan','magnifier','glue','fridge','candle','powerstrip','microwave','cannon','railgun'],
          'chars':[['hero',6,10],['mech',6,10]], 'chEq':'hero', 'chEq2':'mech', 'pets':[['dragon',3]], 'petEq':'dragon',
          'gear':[[s,4,3,5] for s in ['helm','top','pants','shoes','lid','broom']]},
}
if __name__=='__main__': print(json.dumps(P)[:200])
