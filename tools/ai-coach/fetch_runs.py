"""실제 유저 익명 플레이 기록(Firestore runs)을 받아 train.py가 읽는 모양으로 바꾼다.

  python3 fetch_runs.py runs.jsonl [--since v0.60]

계정 단계(stage)는 영구 강화 레벨 합(up)과 타워 레벨 합(twl)으로 봇 프리셋에 맞춰 나눈다.
"""
import json, sys, urllib.request, argparse

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--since', default='v0.60')
a = ap.parse_args()
KEY = 'AIzaSyD2aPHmBuH_RARc0btJeKoWyhNe616PKDI'   # 공개해도 되는 웹 API 키 (게임 코드에도 있음)
URL = f'https://firestore.googleapis.com/v1/projects/room-defense/databases/(default)/documents:runQuery?key={KEY}'

def ver_ok(v):
    try: return tuple(int(x) for x in v.lstrip('v').split('.')) >= tuple(int(x) for x in a.since.lstrip('v').split('.'))
    except Exception: return False
def stage(up, twl):   # presets.py: early 강화 3단계씩(합 ~24) · mid 6단계(~41)+타워 Lv5 · late 10단계(~62)+타워 Lv9
    if up < 8 and twl < 5: return 'fresh'
    if up < 30: return 'early'
    if up < 52: return 'mid'
    return 'late'

rows, last = [], None
while True:
    q = {'structuredQuery': {'from': [{'collectionId': 'runs'}], 'orderBy': [{'field': {'fieldPath': 'ts'}}], 'limit': 300}}
    if last: q['structuredQuery']['startAt'] = {'values': [{'timestampValue': last}], 'before': False}
    req = urllib.request.Request(URL, data=json.dumps(q).encode(), headers={'Content-Type': 'application/json'})
    page = [x['document'] for x in json.load(urllib.request.urlopen(req)) if 'document' in x]
    if not page: break
    for d in page:
        f = d['fields']; g = lambda k, t='stringValue': f.get(k, {}).get(t)
        if not ver_ok(g('ver') or ''): continue
        try: per = json.loads(g('per') or '{}')
        except Exception: per = {}
        up, twl = int(g('up', 'integerValue') or 0), int(g('twl', 'integerValue') or 0)
        rows.append(dict(stage=stage(up, twl), deck=(g('deck') or '').split(','), wave=int(g('wave', 'integerValue') or 0), per=per,
                         auto=int(g('auto', 'integerValue') or 0), ver=g('ver'), real=True))
    last = page[-1]['fields']['ts']['timestampValue']
    if len(page) < 300: break
with open(a.out, 'w') as o:
    for r in rows: o.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'{len(rows)}판 저장 → {a.out}')
