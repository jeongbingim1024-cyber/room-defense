"""AI 밸런스 코치: 플레이 기록으로 '타워 가치 모델'을 학습한다.

데이터
  - 봇 플레이(mix.py): {stage, deck[9], wave, per{타워: {s, dmg, ...}}}
  - 실제 유저 기록(fetch_runs.py → runs.jsonl): {stage, deck[9], wave, per{...}} 같은 모양 (stage = 계정 단계)

모델 (릿지 회귀)
  log(1 + 버틴 웨이브) ≈ 단계별 기본값 + Σ (엔트리에 넣은 타워의 가치)
  → 타워 가치 β = '이 타워를 엔트리에 넣으면 같은 단계에서 몇 % 더 버티나'
  부트스트랩 200번으로 신뢰구간을 구해, 확실히 센 타워(너프 후보)·약한 타워(버프 후보)를 고른다.

쓰기
  python3 train.py data1.jsonl [data2.jsonl ...] [--apply ../../index.html] [--real runs.jsonl --real-weight 3]
  - ai_model.json  : 학습 결과 (게임에 넣는 AI_VAL 표 포함)
  - report.md      : 사람이 읽는 패치 추천
  - --apply        : index.html 안의 /*AI_VAL*/ ... /*END_AI_VAL*/ 표를 새 값으로 바꾼다
"""
import json, sys, math, re, os, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('data', nargs='+')
ap.add_argument('--real', default=None, help='실제 유저 기록 jsonl')
ap.add_argument('--real-weight', type=float, default=3.0, help='실제 유저 한 판을 봇 몇 판만큼 칠지')
ap.add_argument('--apply', default=None)
ap.add_argument('--lam', type=float, default=2.0, help='릿지 강도')
ap.add_argument('--boot', type=int, default=200)
ap.add_argument('--reset', default='', help='패치로 수치가 바뀐 타워: 게임에 넣는 표에서 0(등급 평균)으로 (새 데이터가 쌓일 때까지)')
a = ap.parse_args()

KEYS = open(os.path.join(HERE, 'keys.txt')).read().strip().split(',')
TD = json.load(open(os.path.join(HERE, 'tdef.json')))           # {k: {name, g, base, cost, ...}}
ST = ['fresh', 'early', 'mid', 'late']

rows = []
for f in a.data:
    for l in open(f):
        r = json.loads(l)
        if r.get('stage') in ST and r.get('deck'): rows.append((r, 1.0))
if a.real and os.path.exists(a.real):
    for l in open(a.real):
        r = json.loads(l)
        if r.get('stage') in ST and r.get('deck'): rows.append((r, a.real_weight))
nreal = sum(1 for _, w in rows if w != 1.0)
print(f'판 수: 봇 {len(rows) - nreal} · 실제 유저 {nreal}')

ki = {k: i for i, k in enumerate(KEYS)}
def design(rs):
    X = np.zeros((len(rs), len(ST) + len(KEYS))); y = np.zeros(len(rs)); w = np.zeros(len(rs))
    for i, (r, wt) in enumerate(rs):
        X[i, ST.index(r['stage'])] = 1
        for k in r['deck']:
            if k in ki: X[i, len(ST) + ki[k]] = 1
        y[i] = math.log1p(r['wave']); w[i] = wt
    return X, y, w

def ridge(X, y, w, lam):
    P = np.ones(X.shape[1]) * lam; P[:len(ST)] = 1e-6                       # 단계 기본값은 벌점 없음
    W = np.sqrt(w)[:, None]
    A = (X * W).T @ (X * W) + np.diag(P); b = (X * W).T @ (y * W[:, 0])
    return np.linalg.solve(A, b)

X, y, w = design(rows)
beta = ridge(X, y, w, a.lam)
pred = X @ beta; r2 = 1 - np.sum(w * (y - pred) ** 2) / np.sum(w * (y - np.average(y, weights=w)) ** 2)
rng = np.random.default_rng(7); boots = []
for _ in range(a.boot):
    idx = rng.integers(0, len(rows), len(rows)); boots.append(ridge(X[idx], y[idx], w[idx], a.lam))
boots = np.array(boots)

def centered(b):   # 등급 안 평균을 0으로 (같은 등급 칸끼리만 바꿀 수 있으니까)
    v = b[len(ST):].copy()
    for g in range(4):
        ks = [ki[k] for k in KEYS if TD[k]['g'] == g]; v[ks] -= v[ks].mean()
    return v
val = centered(beta); bv = np.array([centered(b) for b in boots])
lo, hi = np.percentile(bv, 5, axis=0), np.percentile(bv, 95, axis=0)

# 보조 지표: 판 안에서 같은 시간 대비 피해 (효율지수, 1 = 그 판 평균)
eff = {k: [] for k in KEYS}
for r, wt in rows:
    per = r.get('per') or {}
    ts = sum(v['s'] for v in per.values()); td = sum(v['dmg'] for v in per.values())
    if ts <= 0 or td <= 0: continue
    base = td / ts
    for k, v in per.items():
        if k in eff and v['s'] >= 30: eff[k].append(((v['dmg'] / v['s']) / base, v['s'] * wt))
effm = {k: (sum(e * s for e, s in x) / sum(s for e, s in x) if x else float('nan')) for k, x in eff.items()}
cnt = {k: int(X[:, len(ST) + ki[k]].sum()) for k in KEYS}

out = []
for k in KEYS:
    i = ki[k]; pct = math.exp(val[i]) - 1
    verdict = '너프 후보' if lo[i] > 0.06 else '버프 후보' if hi[i] < -0.06 else ''
    out.append(dict(k=k, name=TD[k]['name'], g=TD[k]['g'], val=round(float(val[i]), 4), pct=round(pct * 100, 1),
                    lo=round((math.exp(lo[i]) - 1) * 100, 1), hi=round((math.exp(hi[i]) - 1) * 100, 1),
                    eff=round(effm[k], 2) if effm[k] == effm[k] else None, n=cnt[k], verdict=verdict))
RESET = [k for k in a.reset.split(',') if k]
for o in out:
    if o['k'] in RESET: o['verdict'] = (o['verdict'] + ' ' if o['verdict'] else '') + '(패치됨, 표에선 0)'
model = dict(version=1, n_bot=len(rows) - nreal, n_real=nreal, r2=round(float(r2), 3), lam=a.lam,
             stage_base={s: round(float(math.expm1(beta[i])), 1) for i, s in enumerate(ST)},
             AI_VAL={o['k']: (0 if o['k'] in RESET else o['val']) for o in out}, towers=out)
json.dump(model, open(os.path.join(HERE, 'ai_model.json'), 'w'), ensure_ascii=False, indent=1)

G = ['일반', '희귀', '영웅', '전설']
md = [f'# AI 밸런스 코치 리포트', '', f'- 학습 판 수: 봇 {model["n_bot"]} · 실제 유저 {nreal}',
      f'- 모델 설명력(R²): {model["r2"]} · 단계별 기본 웨이브: ' + ', '.join(f'{s} {v}' for s, v in model['stage_base'].items()), '',
      '가치 = 같은 등급 평균 타워 대신 이 타워를 엔트리에 넣으면 몇 % 더 버티는지 (90% 구간). 효율 = 판 안에서 같은 시간 대비 피해(1 = 평균).', '']
for g in range(4):
    md += [f'## {G[g]}', '', '| 타워 | 가치 | 90% 구간 | 효율 | 판 | 판정 |', '|---|---|---|---|---|---|']
    for o in sorted([o for o in out if o['g'] == g], key=lambda o: -o['val']):
        md.append(f"| {o['name']} | {o['pct']:+.1f}% | {o['lo']:+.0f} ~ {o['hi']:+.0f}% | {o['eff'] if o['eff'] is not None else '-'} | {o['n']} | {o['verdict']} |")
    md.append('')
open(os.path.join(HERE, 'report.md'), 'w').write('\n'.join(md))
print('\n'.join(md))

if a.apply:
    src = open(a.apply, encoding='utf-8').read()
    tbl = '{' + ','.join(f'{k}:{model["AI_VAL"][k]}' for k in KEYS) + '}'
    src2, n = re.subn(r'/\*AI_VAL\*/.*?/\*END_AI_VAL\*/', '/*AI_VAL*/' + tbl + '/*END_AI_VAL*/', src, flags=re.S)
    src2 = re.sub(r"const AI_META = \{[^}]*\}", f"const AI_META = {{ n: {model['n_bot'] + nreal}, real: {nreal}, r2: {model['r2']} }}", src2)
    if n: open(a.apply, 'w', encoding='utf-8').write(src2); print('AI_VAL 표를 게임에 넣음:', a.apply)
    else: print('index.html에 /*AI_VAL*/ 표시가 없어요')
