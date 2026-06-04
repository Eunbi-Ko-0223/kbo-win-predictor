# ⚾ KBO 2026 시즌 최종 순위 예측기

2015~2025 KBO 데이터로 학습한 머신러닝 모델이, 시즌 중 누적 성적을 바탕으로
각 팀의 **최종 승률과 등수**를 예측합니다.

## 구조 (크롤링 분리)
- `update_data.py` — 현재 성적을 1회 크롤링해 `data/latest_standings.csv` 저장 (하루 1회 자동 실행)
- `app.py` — 저장된 파일만 읽어 예측 (KBO에 직접 접속하지 않음)
- `train_model.py` — 모델 학습·평가 (`model.pkl` 생성)
- `crawl_all.py` — 2015~2025 학습 데이터 일괄 수집

## 로컬 실행
```bash
pip install -r requirements.txt
python update_data.py      # 최신 성적 받아오기
streamlit run app.py       # 사이트 실행
```

## 모델
- RandomForest, 1,330개 스냅샷 학습, 테스트 평균오차(MAE) ±3.1%
- 예측 등수 = 10팀 예측 승률을 정렬해 산출
- 출처: KBO 기록실. ⚠️ 예측은 재미용이며 정확성을 보장하지 않습니다.

자세한 설계 맥락은 `PROJECT_CONTEXT.md` 참고.
