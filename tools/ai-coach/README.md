# AI 밸런스 코치

봇 플레이 + 실제 유저 익명 기록으로 '타워 가치'를 학습해 패치를 돕는 도구.

```bash
# 1) 봇 데이터 (게임을 로컬 서버로 띄운 뒤, 2코어 기준 500판 약 25분)
python3 -m http.server 8766            # 레포 루트에서
URL=http://localhost:8766/index.html python3 tools/ai-coach/mix.py 125 tools/ai-coach/data/bot_new.jsonl 7919          # 손으로 섞어 쓰는 봇
MODE=auto URL=http://localhost:8766/index.html python3 tools/ai-coach/mix.py 200 tools/ai-coach/data/auto_new.jsonl 15485863   # AUTO 자동 설치 봇

# 2) 실제 유저 기록 받기 (Firestore runs, 읽기 공개)
python3 tools/ai-coach/fetch_runs.py tools/ai-coach/runs.jsonl

# 3) 학습 → report.md · ai_model.json, --apply 로 게임 안 AI_VAL 표 갱신
cd tools/ai-coach && python3 train.py data/bot_*.jsonl data/auto_*.jsonl --real runs.jsonl --apply ../../index.html
# 수치를 바꾼 타워는 --reset 타워1,타워2 로 표에서 0(등급 평균)으로 (새 데이터가 쌓일 때까지)
# data/old_*.jsonl 은 패치 전 기록 (비교용, 학습엔 안 씀)
```

- 모델: `log(1+버틴 웨이브) ≈ 계정 단계 기본값 + Σ 엔트리 타워 가치` (릿지 회귀, λ=2), 부트스트랩 200번 90% 구간
- 가치는 같은 등급 평균을 0으로 맞춘 값 (엔트리 칸은 같은 등급끼리만 바꿀 수 있어서)
- 판정: 90% 구간 전체가 +6% 위면 너프 후보, -6% 아래면 버프 후보
- 실제 유저 한 판은 기본으로 봇 3판만큼 가중치 (`--real-weight`)
- `h.js` 밸런스 봇·시뮬레이터, `presets.py` 계정 단계 프리셋, `keys.txt` 타워 목록, `tdef.json` 타워 기본 수치
