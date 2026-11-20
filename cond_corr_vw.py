import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# 1. 시가총액 가중(VW) 데이터 파일 탐색
vw_paths = [
    'sector_daily_returns_vw.csv',
    '../sector_daily_returns_vw.csv',
    '../sector_daily_returns.csv',
    'sector_daily_returns.csv'
]

target_file = next((f for f in vw_paths if os.path.exists(f) and os.path.getsize(f) > 100), None)
if target_file is None:
    raise FileNotFoundError("유효한 시가총액 가중(VW) CSV 파일을 찾을 수 없습니다.")

df = pd.read_csv(target_file)
print(f"로드된 파일: {target_file}")
print(f"컬럼 목록: {list(df.columns)}\n")

# 시가총액 가중 수익률 컬럼 자동 매칭
vw_col_candidates = ['Value_Weighted_Return', 'VW_Return', 'Sector_Return', 'Return']
val_col = next((c for c in vw_col_candidates if c in df.columns), None)

if val_col is None:
    raise ValueError(f"시가총액 가중 수익률 컬럼을 찾을 수 없습니다. 현재 컬럼: {list(df.columns)}")

print(f"사용된 수익률 컬럼: {val_col}")
pivot_df = df.pivot(index='Date', columns='Sector', values=val_col).dropna(axis=1, how='all')

# 2. 일별 시장 수익률(Proxy) 계산
mkt_ret = pivot_df.mean(axis=1)

# 3. 3국면 분리: 급락일(하위 15%), 보통 날(중간 70%), 급등일(상위 15%)
q_low = mkt_ret.quantile(0.15)
q_high = mkt_ret.quantile(0.85)

crash_days = pivot_df[mkt_ret <= q_low]
normal_days = pivot_df[(mkt_ret > q_low) & (mkt_ret < q_high)]
surge_days = pivot_df[mkt_ret >= q_high]

print(f"전체 거래일: {len(pivot_df)}일")
print(f" - 급락일 (하위 15%, <= {q_low*100:.2f}%): {len(crash_days)}일")
print(f" - 보통 날 (중간 70%): {len(normal_days)}일")
print(f" - 급등일 (상위 15%, >= {q_high*100:.2f}%): {len(surge_days)}일\n")

# 4. 국면별 상관계수 행렬 및 상삼각 벡터 추출
def get_upper_corr(sub_df):
    corr_mat = sub_df.corr(method='pearson')
    iu = np.triu_indices_from(corr_mat.values, k=1)
    return corr_mat, corr_mat.values[iu]

corr_crash, v_crash = get_upper_corr(crash_days)
corr_norm, v_norm = get_upper_corr(normal_days)
corr_surge, v_surge = get_upper_corr(surge_days)

mask = ~np.isnan(v_crash) & ~np.isnan(v_norm) & ~np.isnan(v_surge)
v_crash, v_norm, v_surge = v_crash[mask], v_norm[mask], v_surge[mask]

# 5. 통계적 유의성 검정 및 요약 CSV 자동 저장
summary_rows = []
mean_norm = np.mean(v_norm)
mean_crash = np.mean(v_crash)
mean_surge = np.mean(v_surge)

summary_rows.append({
    "Weighting_Method": "Value-Weighted (VW)",
    "Market_Regime": "Normal (보통 날)",
    "Criterion": f"중간 70% ({q_low*100:.2f}% < R_m < +{q_high*100:.2f}%)",
    "Trading_Days": len(normal_days),
    "Mean_Correlation": round(mean_norm, 4),
    "Diff_vs_Normal": 0.0000,
    "Ratio_vs_Normal": 1.00,
    "Fisher_z_t_stat": None,
    "Fisher_z_p_value": None,
    "Wilcoxon_p_value": None
})

def evaluate_and_record(v_target, v_base, regime_name, criterion_str, days_count):
    diff = np.mean(v_target - v_base)
    ratio = np.mean(v_target) / np.mean(v_base)
    z_target = np.arctanh(np.clip(v_target, -0.9999, 0.9999))
    z_base = np.arctanh(np.clip(v_base, -0.9999, 0.9999))
    t_stat, p_t = stats.ttest_rel(z_target, z_base)
    w_stat, p_w = stats.wilcoxon(v_target, v_base)
    print(f"[{regime_name}] 평균 상관계수: {np.mean(v_target):.4f} (차이: {diff:+.4f}, {ratio:.2f}배) | Fisher-z t={t_stat:.2f} (p={p_t:.2e}) | Wilcoxon p={p_w:.2e}")
    summary_rows.append({
        "Weighting_Method": "Value-Weighted (VW)",
        "Market_Regime": regime_name,
        "Criterion": criterion_str,
        "Trading_Days": days_count,
        "Mean_Correlation": round(np.mean(v_target), 4),
        "Diff_vs_Normal": round(diff, 4),
        "Ratio_vs_Normal": round(ratio, 2),
        "Fisher_z_t_stat": round(t_stat, 2),
        "Fisher_z_p_value": p_t,
        "Wilcoxon_p_value": p_w
    })

print(f"[Normal (보통 날)] 평균 상관계수: {mean_norm:.4f}")
evaluate_and_record(v_surge, v_norm, "Surge (급등일)", f"상위 15% (R_m >= +{q_high*100:.2f}%)", len(surge_days))
evaluate_and_record(v_crash, v_norm, "Crash (급락일)", f"하위 15% (R_m <= {q_low*100:.2f}%)", len(crash_days))

# Crash vs Surge 직접 비교 출력
diff_cs = np.mean(v_crash - v_surge)
z_c = np.arctanh(np.clip(v_crash, -0.9999, 0.9999))
z_s = np.arctanh(np.clip(v_surge, -0.9999, 0.9999))
t_cs, p_cs = stats.ttest_rel(z_c, z_s)
_, w_cs = stats.wilcoxon(v_crash, v_surge)
print(f"[Crash vs Surge 비대칭 비교] 차이: {diff_cs:+.4f} | Fisher-z t={t_cs:.2f} (p={p_cs:.2e}) | Wilcoxon p={w_cs:.2e}")

# 6. VW 결과 파일 저장
pd.DataFrame(summary_rows).to_csv('conditional_correlation_summary_vw.csv', index=False, encoding='utf-8-sig')
corr_crash.to_csv('sector_corr_crash_vw.csv', encoding='utf-8-sig')
corr_norm.to_csv('sector_corr_normal_vw.csv', encoding='utf-8-sig')
corr_surge.to_csv('sector_corr_surge_vw.csv', encoding='utf-8-sig')

plt.rcParams['font.family'] = 'DejaVu Sans'
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

sns.kdeplot(v_norm, color='seagreen', fill=True, alpha=0.25, label=f'Normal (Mean: {mean_norm:.3f})', ax=axes[0])
sns.kdeplot(v_crash, color='crimson', fill=True, alpha=0.25, label=f'Crash Bottom 15% (Mean: {mean_crash:.3f})', ax=axes[0])
sns.kdeplot(v_surge, color='royalblue', fill=True, alpha=0.25, label=f'Surge Top 15% (Mean: {mean_surge:.3f})', ax=axes[0])
axes[0].axvline(mean_norm, color='seagreen', linestyle='--')
axes[0].axvline(mean_crash, color='crimson', linestyle='--')
axes[0].axvline(mean_surge, color='royalblue', linestyle='--')
axes[0].set_title('VW Sector Correlation Distribution by Market Regime', fontsize=11, fontweight='bold')
axes[0].set_xlabel('Pearson Correlation (Value-Weighted)')
axes[0].legend()

axes[1].scatter(v_norm, v_crash, alpha=0.2, s=10, color='crimson', label='Crash vs Normal')
axes[1].scatter(v_norm, v_surge, alpha=0.2, s=10, color='royalblue', label='Surge vs Normal')
axes[1].plot([-0.2, 1.0], [-0.2, 1.0], 'k--', linewidth=1.2, label='y = x (No Change)')
axes[1].set_title('VW Asymmetric Correlation Shift (Crash vs Surge)', fontsize=11, fontweight='bold')
axes[1].set_xlabel('Normal Days Correlation (VW)')
axes[1].set_ylabel('Extreme Days Correlation (VW)')
axes[1].legend()

plt.tight_layout()
plt.savefig('cond_corr_asymmetric_vw.png', dpi=150)
print("\nVW 저장 완료: conditional_correlation_summary_vw.csv, sector_corr_*_vw.csv, cond_corr_asymmetric_vw.png")
