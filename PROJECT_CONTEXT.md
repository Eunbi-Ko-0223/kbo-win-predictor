# KBO 승률 예측 프로젝트 — 맥락 정리

> 이 파일은 작업 맥락을 보존하기 위한 문서야. 새 세션에서 이걸 먼저 읽으면 이어서 작업할 수 있어.

## 목표
2015~2025 KBO 데이터로 **2026 팀별 최종 승률을 예측**하는 머신러닝 모델 + 웹사이트.

## 모델 종류 (중요)
**모델 A — 시즌 중 예측**으로 확정.
- 입력: 시즌 진행 중 **그 시점까지의 누적 기록**
- 정답(y): 그 시즌 **최종 승률**
- 사용 시나리오: 사이트에서 팀을 고르면 → 현재(2026) 누적 성적을 크롤링 → 모델이 최종 승률 예측

> ⚠️ 피한 함정: "시즌 전체 합계 통계 → 그 시즌 승률"은 **데이터 누수(leakage)**라 금지. (결과로 결과를 맞히는 꼴, 시즌 중 예측 불가)

## 데이터 출처 (크롤링)
KBO 기록실, ASP.NET 사이트. `requests`로 가능 (Selenium 불필요).
- **입력 스냅샷**: `TeamRankDaily.aspx` — 과거 임의 날짜 조회.
  - 핵심: 숨은 필드 `hfSearchDate`(YYYYMMDD)가 진짜 날짜. `__EVENTTARGET=...btnCalendarSelect`로 트리거.
- **정답 y(최종승률)**: `TeamRank.aspx` — `ddlYear`로 연도 선택 시 그 해 정규시즌 최종순위.
- 정규시즌만 사용 (`ddlSeries=0`).

## 데이터 부족 해결책
시즌 11개 × 10팀 = 110행으로는 부족 → **시즌 진행도별 스냅샷**으로 증식.
- 시즌당 약 13개 날짜(진행도 ~5%~100%)를 크롤링 → 약 1,330행 확보.
- 매일 긁지 않음(중복 정보). 진행도 분산이 핵심.

## 변수 설계
- **정답 y**: `final_win_rate` (final_standings.csv의 `win_rate` 한 열에서만 추출)
- **입력 X (현재 사용중)**: `progress`(경기/144), `win_rate`(현재승률, 핵심),
  `recent10_wr`(최근10경기 승률), `streak_num`(연승+/연패-), `home_wr`, `away_wr`
- **식별자(입력 아님)**: year, date, team
- **팀명 통일**: SK→SSG, 넥센→키움
- **버린 중복열**: rank(←승률), win/loss/draw(←승률+경기), games(↔progress)
- **팀명을 입력으로 안 씀**: "두산은 원래 잘해" 같은 암기 방지 (팀 전력은 해마다 변함)

## 과적합 방지 원칙
1. 단순 모델 우선 (LinearRegression / Ridge)
2. **시즌 단위 검증** (무작위 분할 금지). 예: 2015~2023 학습 / 2024·2025 테스트
3. 변수 수 절제

## 향후 추가 예정 (2단계 업그레이드)
타격/투수 페이지(`Record/Team/...`)에서 **스냅샷별** 추가 지표 수집 중.
- 활용할 것(비율로): **경기당 득점**, **OPS**(또는 출루율+장타율)
- ⚠️ 반드시 **투수 페이지의 실점/자책점**도 함께 → **득실차(피타고리안)** = 최강 예측지표
- 비율(rate)로 쓸 것. 개수(count)는 progress와 중복.
- 중복/약한 지표(안타·루타·타점·타율·희생번트·삼진 등)는 제외.

## 파일 구조
- `data/training_data.csv` — 학습용 (가공 완료, 입력+정답)
- `data/all_snapshots.csv` — raw 스냅샷 백업
- `data/final_standings.csv` — 연도별 최종성적 (y 출처)
- `data/latest_standings.csv` — 현재 성적 (update_data.py가 생성, app.py가 읽음)
- `crawl_all.py` — 학습데이터 크롤러 (2015~2025 일괄)
- `train_model.py` — 모델 학습·평가
- `update_data.py` — **데이터 수집기**: 현재 성적 1회 크롤링 → latest_standings.csv (스케줄 실행)
- `app.py` — Streamlit 웹사이트 (KBO 접속 안 함, 저장 파일만 읽음)

## 배포 구조 (크롤링 분리)
방문자마다 크롤링 ❌ → **update_data.py를 하루 1회 스케줄 실행**해 파일 저장, app.py는 그 파일만 읽음.
- 로컬: Windows 작업 스케줄러로 `python update_data.py` 매일 실행
- 클라우드: GitHub Actions(cron)로 update_data.py 실행 후 latest_standings.csv 커밋 → Streamlit Cloud 자동 갱신

## 진행 상태
- [x] 크롤링 (2015~2025)
- [x] 데이터 가공 (training_data.csv)
- [x] 모델 학습·평가 (RandomForest, 테스트 MAE 0.031)
- [x] 사이트 프로토타입 (app.py) + 크롤링 분리 리팩터링
- [ ] 클라우드 배포 (GitHub + Streamlit Cloud)
- [ ] (2단계) 득점/실점/OPS 등 추가 변수 → 득실차
