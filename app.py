# KBO 2026 시즌 최종 승률 & 등수 예측 사이트 (Streamlit)
#  ※ 크롤링 분리 구조: 이 앱은 KBO에 접속하지 않음.
#    update_data.py가 미리 저장한 data/latest_standings.csv 만 읽어 예측.
#  ※ 한국어/English 이중 언어 지원 (우측 상단 토글). 텍스트는 모두 TXT 사전에서 가져온다.
import os
import joblib
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "latest_standings.csv")

bundle = joblib.load(os.path.join(HERE, "model.pkl"))
MODEL, FEATURES = bundle["model"], bundle["features"]
TEST_MAE = bundle.get("test_mae")

# ── 영어 모드에서 보여줄 팀명(한글 팀명은 데이터의 키로 유지, 표시만 번역) ──
TEAM_EN = {"두산": "Doosan", "롯데": "Lotte", "삼성": "Samsung",
           "한화": "Hanwha", "키움": "Kiwoom"}  # LG/KT/SSG/NC/KIA는 그대로

# ── 모든 화면 텍스트 (언어별) ──
TXT = {
    "ko": {
        "page_title": "KBO 2026 승률 예측",
        "title": "⚾ KBO 2026 시즌 최종 순위 예측기",
        "subtitle": "저장된 최신 성적을 바탕으로, 2015~2025 학습 모델이 시즌 최종 승률과 등수를 예측합니다.",
        "no_data": "아직 데이터가 없어요. 먼저 `python update_data.py` 를 실행해 최신 성적을 받아오세요.",
        "info_box": "데이터 기준일 <b>{asof}</b> &nbsp;·&nbsp; 진행도 약 <b>{pct}%</b> ({games}경기) "
                    "&nbsp;·&nbsp; 모델 평균오차 <b>{acc}</b>",
        "acc_none": "정보 없음",
        "select_label": "팀을 선택하세요",
        "select_placeholder": "어떤 팀을 응원하시나요?",
        "m_cur_wr": "현재 승률",
        "m_cur_rank": "현재 순위",
        "m_pred_wr": "예측 최종 승률",
        "m_pred_rank": "예측 최종 순위",
        "rank_unit": "위",
        "no_change": "변동없음",
        "exp_features": "🔍 예측에 사용한 지표 (선택 팀 기준)",
        "feat_caption": "아래 6개 지표를 입력으로 최종 승률을 예측합니다. (KBO 현재 누적 성적에서 계산)",
        "feat_caption_empty": "위에서 팀을 선택하면 해당 팀의 입력 지표가 표시됩니다.",
        "feat_col_name": "지표",
        "feat_col_val": "현재 값",
        "exp_table": "📊 전체 팀 예측 순위 보기",
        "tbl_rank": "예측순위", "tbl_team": "팀", "tbl_games": "경기",
        "tbl_cur_wr": "현재승률", "tbl_pred_wr": "예측최종승률",
        "exp_about": "ℹ️ 모델 / 데이터 안내",
        "about": (
            "- 모델: **{name}** (2015~2025, 1,330개 스냅샷 학습)\n"
            "- 정확도: 테스트 평균오차(MAE) **±{mae}%**, R² **{r2}**\n"
            "- 예측 등수 = 10팀의 예측 최종 승률을 정렬해 매김 (별도 등수 모델 아님)\n"
            "- 데이터는 `update_data.py`가 하루 1회 갱신 (이 사이트는 KBO에 직접 접속하지 않음)\n"
            "- 출처: KBO 기록실. ⚠️ 예측은 재미용이며 정확성을 보장하지 않습니다."
        ),
        "features": {
            "progress":    "진행도 (치른 경기 ÷ 144)",
            "win_rate":    "현재 승률",
            "recent10_wr": "최근 10경기 승률",
            "streak_num":  "연속 (연승 +, 연패 −)",
            "home_wr":     "홈 승률",
            "away_wr":     "원정 승률",
        },
    },
    "en": {
        "page_title": "KBO 2026 Win-Rate Predictor",
        "title": "⚾ KBO 2026 Final Standings Predictor",
        "subtitle": "Using the latest saved records, a model trained on 2015–2025 data "
                    "predicts each team's final win rate and rank.",
        "no_data": "No data yet. Run `python update_data.py` first to fetch the latest standings.",
        "info_box": "Data as of <b>{asof}</b> &nbsp;·&nbsp; about <b>{pct}%</b> played ({games} games) "
                    "&nbsp;·&nbsp; model avg. error <b>{acc}</b>",
        "acc_none": "n/a",
        "select_label": "Select a team",
        "select_placeholder": "Which team are you rooting for?",
        "m_cur_wr": "Current win rate",
        "m_cur_rank": "Current rank",
        "m_pred_wr": "Predicted final win rate",
        "m_pred_rank": "Predicted final rank",
        "rank_unit": "",
        "no_change": "no change",
        "exp_features": "🔍 Features used for the prediction (selected team)",
        "feat_caption": "The final win rate is predicted from these six features "
                        "(computed from current cumulative KBO records).",
        "feat_caption_empty": "Select a team above to see its input features.",
        "feat_col_name": "Feature",
        "feat_col_val": "Current value",
        "exp_table": "📊 Full projected standings (all teams)",
        "tbl_rank": "Pred. rank", "tbl_team": "Team", "tbl_games": "Games",
        "tbl_cur_wr": "Current WR", "tbl_pred_wr": "Predicted final WR",
        "exp_about": "ℹ️ Model / data notes",
        "about": (
            "- Model: **{name}** (trained on 1,330 snapshots, 2015–2025)\n"
            "- Accuracy: test mean absolute error (MAE) **±{mae}%**, R² **{r2}**\n"
            "- Ranks are derived by sorting the 10 teams' predicted final win rates "
            "(not a separate ranking model)\n"
            "- Data is refreshed once a day by `update_data.py` (this site never contacts KBO directly)\n"
            "- Source: KBO records. ⚠️ Predictions are for fun and accuracy is not guaranteed."
        ),
        "features": {
            "progress":    "Progress (games played ÷ 144)",
            "win_rate":    "Current win rate",
            "recent10_wr": "Last-10-games win rate",
            "streak_num":  "Streak (wins +, losses −)",
            "home_wr":     "Home win rate",
            "away_wr":     "Away win rate",
        },
    },
}

# ── 언어 상태 (위젯 생성 전에 기본값 보장 → set_page_config에서도 사용 가능) ──
if "lang" not in st.session_state:
    st.session_state.lang = "ko"
LANG = st.session_state.lang
L = TXT[LANG]
is_en = LANG == "en"

def team_disp(name):
    """영어 모드면 팀명을 영문으로 표시 (데이터 키는 한글 유지)."""
    return TEAM_EN.get(name, name) if is_en else name

st.set_page_config(page_title=L["page_title"], page_icon="⚾", layout="centered")

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
/* 변동없음 delta: 강제 화살표만 숨김 (텍스트만 표시) */
.st-key-nochg [data-testid="stMetricDelta"] svg { display: none; }
</style>
""", unsafe_allow_html=True)

# ── 우측 상단 언어 토글 ──
_sp, lang_col = st.columns([3, 1])
with lang_col:
    choice = st.radio(
        "🌐 Language",
        options=["ko", "en"],
        format_func=lambda c: "한국어" if c == "ko" else "English",
        index=0 if LANG == "ko" else 1,
        horizontal=True,
        key="lang",
    )
# radio가 st.session_state.lang을 갱신하면 다음 rerun에서 L이 새 언어로 반영됨.
# (이번 실행분이 곧바로 바뀌도록 즉시 동기화)
if choice != LANG:
    L = TXT[choice]
    is_en = choice == "en"

# 제목 & 설명 (가운데 정렬, 컬러 이모지)
st.markdown(
    f"<h1 style='text-align:center; margin-bottom:0.2rem;'>{L['title']}</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.95rem; margin-top:0;'>"
    f"{L['subtitle']}</p>",
    unsafe_allow_html=True)

if not os.path.exists(DATA):
    st.error(L["no_data"])
    st.stop()

df = pd.read_csv(DATA)

# 예측 + 등수 (반올림 전 원본값으로 등수 → 1~10위 유일). 내부 컬럼은 언어무관 영문 키.
pred_raw = MODEL.predict(df[FEATURES])
df["pred_wr"] = pred_raw.round(3)
df["pred_rank"] = pd.Series(pred_raw, index=df.index).rank(ascending=False, method="first").astype(int)
df["cur_rank"] = df["cur_wr"].rank(ascending=False, method="first").astype(int)

asof = str(df["asof"].iloc[0])
games = int(df["games"].iloc[0])
acc = f"±{TEST_MAE*100:.1f}%" if TEST_MAE is not None else L["acc_none"]
asof_fmt = f"{asof[:4]}-{asof[4:6]}-{asof[6:8]}" if len(asof) == 8 and asof.isdigit() else asof

# 정보 박스 (가운데 정렬, 작은 글씨, 모델 정확도 포함)
st.markdown(
    "<div style='background:#e8f0fe; border:1px solid #d3e2fb; border-radius:8px; "
    "padding:8px 12px; text-align:center; font-size:0.8rem; color:#34507d;'>"
    + L["info_box"].format(asof=asof_fmt, pct=round(games / 144 * 100), games=games, acc=acc)
    + "</div>",
    unsafe_allow_html=True)
st.write("")

# 팀 선택 (첫 화면엔 팀이 선택돼 있지 않음). 표시만 번역하고 값은 한글 팀명 유지.
pick = st.selectbox(L["select_label"], df["team"].tolist(),
                    index=None, placeholder=L["select_placeholder"],
                    format_func=team_disp)

# 결과 영역 (선택 여부와 무관하게 항상 metric 4개 → 레이아웃 고정)
ru = L["rank_unit"]
c1, c2, c3, c4 = st.columns(4)
if pick:
    row = df[df["team"] == pick].iloc[0]
    cur_rank, pred_rank = int(row["cur_rank"]), int(row["pred_rank"])
    move = cur_rank - pred_rank   # +면 순위 상승 (등수 숫자 감소)
    c1.metric(L["m_cur_wr"], f"{row['cur_wr']:.3f}")
    c2.metric(L["m_cur_rank"], f"{cur_rank}{ru}")
    c3.metric(L["m_pred_wr"], f"{row['pred_wr']:.3f}",
              delta=f"{row['pred_wr'] - row['cur_wr']:+.3f}")
    if move != 0:
        c4.metric(L["m_pred_rank"], f"{pred_rank}{ru}", delta=f"{move:+d}")
    else:
        # 변동없음: Streamlit 화살표를 숨기고 텍스트만 표시 (위 CSS)
        box = c4.container(key="nochg")
        box.metric(L["m_pred_rank"], f"{pred_rank}{ru}", delta=L["no_change"], delta_color="off")
else:
    c1.metric(L["m_cur_wr"], "—")
    c2.metric(L["m_cur_rank"], "—")
    c3.metric(L["m_pred_wr"], "—")
    c4.metric(L["m_pred_rank"], "—")

# ───────────── 하단 정보 영역 (토글 3개, 위치 고정) ─────────────
st.write("")
st.write("")
st.divider()

with st.expander(L["exp_features"]):
    if pick:
        st.caption(L["feat_caption"])
        tbl = pd.DataFrame(
            [(L["features"][f], round(float(row[f]), 3)) for f in FEATURES],
            columns=[L["feat_col_name"], L["feat_col_val"]],
        )
        st.table(tbl)
    else:
        st.caption(L["feat_caption_empty"])

with st.expander(L["exp_table"]):
    show = (df[["pred_rank", "team", "games", "cur_wr", "pred_wr"]]
            .sort_values("pred_rank")
            .reset_index(drop=True))
    show["team"] = show["team"].map(team_disp)
    show = show.rename(columns={"pred_rank": L["tbl_rank"], "team": L["tbl_team"],
                                "games": L["tbl_games"], "cur_wr": L["tbl_cur_wr"],
                                "pred_wr": L["tbl_pred_wr"]})
    st.dataframe(show, use_container_width=True, hide_index=True)

with st.expander(L["exp_about"]):
    st.markdown(L["about"].format(
        name=bundle.get("name", "?"),
        mae=f"{TEST_MAE*100:.1f}" if TEST_MAE is not None else "?",
        r2=bundle.get("test_r2", "?"),
    ))
