import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# 1. 데이터 불러오기
vw_candidates = ['sector_daily_returns_vw.csv', 'sector_daily_retuns_vw.csv', 'sector_daily_returns.csv', 'sector_daily_retuns.csv']
vw_file = next((f for f in vw_candidates if os.path.exists(f) and os.path.getsize(f) > 10), 'sector_daily_returns_ew.csv')
df = pd.read_csv(vw_file)

val_col = 'Sector_Return' if 'Sector_Return' in df.columns else 'Equal_Weighted_Return'
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

# 결측치 제거 (모든 국면에서 유효한 업종 쌍만 유지)
mask = ~np.isnan(v_crash) & ~np.isnan(v_norm) & ~np.isnan(v_surge)
v_crash, v_norm, v_surge = v_crash[mask], v_norm[mask], v_surge[mask]

# 5. 통계적 유의성 검정 (Wilcoxon & Fisher-z Paired t-test)
def compare_regimes(v_target, v_base, name):
    diff = np.mean(v_target - v_base)
    # Fisher z-transformation
    z_target = np.arctanh(np.clip(v_target, -0.9999, 0.9999))
    z_base = np.arctanh(np.clip(v_base, -0.9999, 0.9999))
    t_stat, p_t = stats.ttest_rel(z_target, z_base)
    w_stat, p_w = stats.wilcoxon(v_target, v_base)
    print(f"[{name} vs 보통 날] 평균 차이: {diff:+.4f} | Fisher-z t={t_stat:.2f} (p={p_t:.2e}) | Wilcoxon p={p_w:.2e}")

print(f"평균 상관계수 -> 보통 날: {np.mean(v_norm):.4f} | 급락일: {np.mean(v_crash):.4f} | 급등일: {np.mean(v_surge):.4f}")
compare_regimes(v_crash, v_norm, "급락일")
compare_regimes(v_surge, v_norm, "급등일")
compare_regimes(v_crash, v_surge, "급락일 vs 급등일")

# 6. 결과 저장 및 시각화
corr_crash.to_csv('sector_corr_crash.csv', encoding='utf-8-sig')
corr_norm.to_csv('sector_corr_normal.csv', encoding='utf-8-sig')
corr_surge.to_csv('sector_corr_surge.csv', encoding='utf-8-sig')

plt.rcParams['font.family'] = 'DejaVu Sans'
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# 좌측: 3국면 상관계수 밀도 분포
sns.kdeplot(v_norm, color='seagreen', fill=True, alpha=0.25, label=f'Normal (Mean: {np.mean(v_norm):.3f})', ax=axes[0])
sns.kdeplot(v_crash, color='crimson', fill=True, alpha=0.25, label=f'Crash Bottom 15% (Mean: {np.mean(v_crash):.3f})', ax=axes[0])
sns.kdeplot(v_surge, color='royalblue', fill=True, alpha=0.25, label=f'Surge Top 15% (Mean: {np.mean(v_surge):.3f})', ax=axes[0])
axes[0].axvline(np.mean(v_norm), color='seagreen', linestyle='--')
axes[0].axvline(np.mean(v_crash), color='crimson', linestyle='--')
axes[0].axvline(np.mean(v_surge), color='royalblue', linestyle='--')
axes[0].set_title('Sector Correlation Distribution by Market Regime', fontsize=11, fontweight='bold')
axes[0].set_xlabel('Pearson Correlation')
axes[0].legend()

# 우측: 보통 날 대비 급락일/급등일 상관계수 변화 산점도
axes[1].scatter(v_norm, v_crash, alpha=0.2, s=10, color='crimson', label='Crash vs Normal')
axes[1].scatter(v_norm, v_surge, alpha=0.2, s=10, color='royalblue', label='Surge vs Normal')
axes[1].plot([-0.2, 1.0], [-0.2, 1.0], 'k--', linewidth=1.2, label='y = x (No Change)')
axes[1].set_title('Asymmetric Correlation Shift (Crash vs Surge)', fontsize=11, fontweight='bold')
axes[1].set_xlabel('Normal Days Correlation')
axes[1].set_ylabel('Extreme Days Correlation')
axes[1].legend()

plt.tight_layout()
plt.savefig('cond_corr_asymmetric.png', dpi=150)
print("\n저장 완료: sector_corr_crash.csv, sector_corr_normal.csv, sector_corr_surge.csv, cond_corr_asymmetric.png")
