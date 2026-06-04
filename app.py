# KBO 2026 시즌 최종 승률 & 등수 예측 사이트 (Streamlit)
#  ※ 크롤링 분리 구조: 이 앱은 KBO에 접속하지 않음.
#    update_data.py가 미리 저장한 data/latest_standings.csv 만 읽어 예측.
import os
import joblib
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "latest_standings.csv")

bundle = joblib.load(os.path.join(HERE, "model.pkl"))
MODEL, FEATURES = bundle["model"], bundle["features"]
TEST_MAE = bundle.get("test_mae")

FEATURE_KR = {
    "progress":    "진행도 (치른 경기 ÷ 144)",
    "win_rate":    "현재 승률",
    "recent10_wr": "최근 10경기 승률",
    "streak_num":  "연속 (연승 +, 연패 −)",
    "home_wr":     "홈 승률",
    "away_wr":     "원정 승률",
}

st.set_page_config(page_title="KBO 2026 승률 예측", page_icon="⚾", layout="centered")

# 전역 스타일: metric 가운데 정렬 + 높이 고정(아래 요소 위치 안정)
st.markdown("""
<style>
[data-testid="stMetric"] {
    text-align: center;
    min-height: 105px;   /* delta 유무와 상관없이 높이 고정 */
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] { display: flex; justify-content: center; }
[data-testid="stMetricDelta"] { align-self: center; }
/* 변동없음 delta: 강제 화살표만 숨김 (텍스트 '변동없음'만 표시) */
.st-key-nochg [data-testid="stMetricDelta"] svg { display: none; }
</style>
""", unsafe_allow_html=True)

# 제목 & 설명 (가운데 정렬, 컬러 이모지)
st.markdown(
    "<h1 style='text-align:center; margin-bottom:0.2rem;'>⚾ KBO 2026 시즌 최종 순위 예측기</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.95rem; margin-top:0;'>"
    "저장된 최신 성적을 바탕으로, 2015~2025 학습 모델이 시즌 최종 승률과 등수를 예측합니다.</p>",
    unsafe_allow_html=True)

if not os.path.exists(DATA):
    st.error("아직 데이터가 없어요. 먼저 `python update_data.py` 를 실행해 최신 성적을 받아오세요.")
    st.stop()

df = pd.read_csv(DATA)

# 예측 + 등수 (반올림 전 원본값으로 등수 → 1~10위 유일)
pred_raw = MODEL.predict(df[FEATURES])
df["예측최종승률"] = pred_raw.round(3)
df["예측최종등수"] = pd.Series(pred_raw, index=df.index).rank(ascending=False, method="first").astype(int)
df["현재등수"]     = df["cur_wr"].rank(ascending=False, method="first").astype(int)

asof = str(df["asof"].iloc[0])
games = int(df["games"].iloc[0])
acc = f"±{TEST_MAE*100:.1f}%" if TEST_MAE is not None else "정보 없음"
asof_fmt = f"{asof[:4]}-{asof[4:6]}-{asof[6:8]}" if len(asof) == 8 and asof.isdigit() else asof

# 정보 박스 (가운데 정렬, 작은 글씨, 모델 정확도 포함)
st.markdown(
    "<div style='background:#e8f0fe; border:1px solid #d3e2fb; border-radius:8px; "
    "padding:8px 12px; text-align:center; font-size:0.8rem; color:#34507d;'>"
    f"데이터 기준일 <b>{asof_fmt}</b> &nbsp;·&nbsp; 진행도 약 <b>{round(games/144*100)}%</b> ({games}경기) "
    f"&nbsp;·&nbsp; 모델 평균오차 <b>{acc}</b></div>",
    unsafe_allow_html=True)
st.write("")

# 팀 선택 (첫 화면엔 팀이 선택돼 있지 않음)
pick = st.selectbox("팀을 선택하세요", df["team"].tolist(),
                    index=None, placeholder="어떤 팀을 응원하시나요?")

# 결과 영역 (선택 여부와 무관하게 항상 metric 4개 → 레이아웃 고정)
c1, c2, c3, c4 = st.columns(4)
if pick:
    row = df[df["team"] == pick].iloc[0]
    cur_rank, pred_rank = int(row["현재등수"]), int(row["예측최종등수"])
    move = cur_rank - pred_rank   # +면 순위 상승 (등수 숫자 감소)
    c1.metric("현재 승률", f"{row['cur_wr']:.3f}")
    c2.metric("현재 순위", f"{cur_rank}위")
    c3.metric("예측 최종 승률", f"{row['예측최종승률']:.3f}",
              delta=f"{row['예측최종승률'] - row['cur_wr']:+.3f}")
    if move != 0:
        c4.metric("예측 최종 순위", f"{pred_rank}위", delta=f"{move:+d}")
    else:
        # 변동없음: Streamlit 화살표를 숨기고 '-'로 대체 (아래 CSS)
        box = c4.container(key="nochg")
        box.metric("예측 최종 순위", f"{pred_rank}위", delta="변동없음", delta_color="off")
else:
    c1.metric("현재 승률", "—")
    c2.metric("현재 순위", "—")
    c3.metric("예측 최종 승률", "—")
    c4.metric("예측 최종 순위", "—")

# ───────────── 하단 정보 영역 (토글 3개, 위치 고정) ─────────────
st.write("")
st.write("")
st.divider()

with st.expander("🔍 예측에 사용한 지표 (선택 팀 기준)"):
    if pick:
        st.caption("아래 6개 지표를 입력으로 최종 승률을 예측합니다. (KBO 현재 누적 성적에서 계산)")
        tbl = pd.DataFrame(
            [(FEATURE_KR[f], round(float(row[f]), 3)) for f in FEATURES],
            columns=["지표", "현재 값"],
        )
        st.table(tbl)
    else:
        st.caption("위에서 팀을 선택하면 해당 팀의 입력 지표가 표시됩니다.")

with st.expander("📊 전체 팀 예측 순위 보기"):
    show = (df[["예측최종등수", "team", "games", "cur_wr", "예측최종승률"]]
            .sort_values("예측최종등수")
            .rename(columns={"예측최종등수": "예측순위", "team": "팀",
                             "games": "경기", "cur_wr": "현재승률"})
            .reset_index(drop=True))
    st.dataframe(show, use_container_width=True, hide_index=True)

with st.expander("ℹ️ 모델 / 데이터 안내"):
    st.markdown(
        f"- 모델: **{bundle.get('name','?')}** (2015~2025, 1,330개 스냅샷 학습)\n"
        f"- 정확도: 테스트 평균오차(MAE) **±{TEST_MAE*100:.1f}%**, R² **{bundle.get('test_r2','?')}**\n"
        "- 예측 등수 = 10팀의 예측 최종 승률을 정렬해 매김 (별도 등수 모델 아님)\n"
        "- 데이터는 `update_data.py`가 하루 1회 갱신 (이 사이트는 KBO에 직접 접속하지 않음)\n"
        "- 출처: KBO 기록실. ⚠️ 예측은 재미용이며 정확성을 보장하지 않습니다."
    )
