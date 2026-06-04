# 모델 학습 & 평가
#  - 입력 6개로 최종승률 예측
#  - 시즌 단위 검증 (2015~2023 학습 / 2024·2025 테스트)
#  - 단순승률 베이스라인과 비교 (모델이 진짜 가치 있는지)
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "data", "training_data.csv"))

FEATURES = ["progress", "win_rate", "recent10_wr", "streak_num", "home_wr", "away_wr"]
TARGET = "final_win_rate"

# 결측치(시즌 극초반 등) 보정: 비율열은 현재승률로, 그래도 없으면 0.5
for c in ["recent10_wr", "home_wr", "away_wr"]:
    df[c] = df[c].fillna(df["win_rate"]).fillna(0.5)

# ---- 시즌 단위 분할 ----
train = df[df["year"] <= 2023]
test  = df[df["year"] >= 2024]
Xtr, ytr = train[FEATURES], train[TARGET]
Xte, yte = test[FEATURES],  test[TARGET]
print(f"학습 {len(train)}행(2015~2023) / 테스트 {len(test)}행(2024~2025)\n")

# ---- 베이스라인: "현재승률을 그대로 최종승률로 예측" ----
naive_mae = mean_absolute_error(yte, test["win_rate"])
print(f"[베이스라인] 현재승률=최종승률 가정  → MAE {naive_mae:.4f}\n")

# ---- 모델 3종 ----
models = {
    "LinearRegression": LinearRegression(),
    "Ridge(a=1.0)":     Ridge(alpha=1.0),
    "RandomForest":     RandomForestRegressor(n_estimators=300, max_depth=6, random_state=0),
}
results = {}
for name, m in models.items():
    m.fit(Xtr, ytr)
    pred = m.predict(Xte)
    mae, r2 = mean_absolute_error(yte, pred), r2_score(yte, pred)
    results[name] = (m, mae, r2)
    print(f"[{name:16s}] MAE {mae:.4f} | R² {r2:.3f}")

best_name = min(results, key=lambda k: results[k][1])
best_model, best_mae, best_r2 = results[best_name]
print(f"\n>> 최우수: {best_name} (MAE {best_mae:.4f}, R² {best_r2:.3f})")
print(f"   = 평균 오차 약 {best_mae*100:.1f}%p, 베이스라인 대비 {(naive_mae-best_mae)/naive_mae*100:+.0f}% 개선")

# ---- 진행도 구간별 오차 (모델 vs 베이스라인) ----
print("\n=== 진행도 구간별 평균오차(MAE): 모델 vs 단순승률 ===")
test = test.copy()
test["pred"] = best_model.predict(Xte)
bins = [(0,0.25,"초반 0~25%"), (0.25,0.5,"25~50%"), (0.5,0.75,"50~75%"), (0.75,1.01,"75~100%")]
print(f"{'구간':12s} {'표본':>5} {'모델':>8} {'단순승률':>8}")
for lo, hi, label in bins:
    seg = test[(test["progress"]>=lo) & (test["progress"]<hi)]
    if len(seg)==0: continue
    m_mae = mean_absolute_error(seg[TARGET], seg["pred"])
    n_mae = mean_absolute_error(seg[TARGET], seg["win_rate"])
    print(f"{label:12s} {len(seg):>5} {m_mae:>8.4f} {n_mae:>8.4f}")

# ---- 전 시즌 leave-one-season-out 교차검증 (견고성) ----
print("\n=== Leave-one-season-out 교차검증 (Ridge) ===")
maes = []
for yr in sorted(df["year"].unique()):
    tr, va = df[df["year"]!=yr], df[df["year"]==yr]
    mm = Ridge(alpha=1.0).fit(tr[FEATURES], tr[TARGET])
    maes.append(mean_absolute_error(va[TARGET], mm.predict(va[FEATURES])))
print(f"  시즌별 MAE 평균 {np.mean(maes):.4f} (±{np.std(maes):.4f})")

# ---- 최종 모델 저장 (최우수 모델을 전체 데이터로 재학습) ----
if best_name == "RandomForest":
    final_model = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=0)
elif best_name.startswith("Ridge"):
    final_model = Ridge(alpha=1.0)
else:
    final_model = LinearRegression()
final_model.fit(df[FEATURES], df[TARGET])
joblib.dump({"model": final_model, "features": FEATURES, "name": best_name,
             "test_mae": round(best_mae, 4), "test_r2": round(best_r2, 3)},
            os.path.join(HERE, "model.pkl"))
print(f"\n저장 완료 → model.pkl (모델: {best_name}, 전체 {len(df)}행으로 재학습)")

# 참고용: 해석 쉬운 Ridge 계수도 출력
ridge = Ridge(alpha=1.0).fit(df[FEATURES], df[TARGET])
print("[참고] Ridge 계수(영향력):", dict(zip(FEATURES, np.round(ridge.coef_, 3))))
