import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. 현재 폴더 내 파일명 자동 확인
vw_candidates = ['sector_daily_returns_vw.csv', 'sector_daily_retuns_vw.csv', 'sector_daily_returns.csv', 'sector_daily_retuns.csv']
vw_file = next((f for f in vw_candidates if os.path.exists(f)), None)

if vw_file is None:
    print("현재 폴더의 파일 목록:", os.listdir('.'))
    raise FileNotFoundError("VW 수익률 CSV 파일을 찾을 수 없습니다. 위 목록에서 파일명을 확인해 주세요.")

print(f"사용된 VW 파일: {vw_file}")
df_vw = pd.read_csv(vw_file)
df_ew = pd.read_csv('sector_daily_returns_ew.csv')

# 2. 피벗 변환 및 상관계수 계산
vw_pivot = df_vw.pivot(index='Date', columns='Sector', values='Sector_Return').dropna(axis=1, how='all')
ew_pivot = df_ew.pivot(index='Date', columns='Sector', values='Equal_Weighted_Return').dropna(axis=1, how='all')

vw_corr = vw_pivot.corr(method='pearson')
ew_corr = ew_pivot.corr(method='pearson')

# 3. 대각선 제외 상삼각 행렬 값 추출
iu = np.triu_indices_from(vw_corr.values, k=1)
vw_v = vw_corr.values[iu]
ew_v = ew_corr.values[iu]
mask = ~np.isnan(vw_v) & ~np.isnan(ew_v)
vw_v, ew_v = vw_v[mask], ew_v[mask]

# 4. 그래프 그리기
plt.rcParams['font.family'] = 'DejaVu Sans'
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

sns.histplot(vw_v, kde=True, color='steelblue', label=f'VW (Mean: {np.mean(vw_v):.3f})', stat='density', alpha=0.45, ax=axes[0])
sns.histplot(ew_v, kde=True, color='coral', label=f'EW (Mean: {np.mean(ew_v):.3f})', stat='density', alpha=0.45, ax=axes[0])
axes[0].axvline(np.mean(vw_v), color='steelblue', linestyle='--', linewidth=1.5)
axes[0].axvline(np.mean(ew_v), color='coral', linestyle='--', linewidth=1.5)
axes[0].set_title('Distribution of Pairwise Sector Correlations (VW vs EW)', fontsize=11, fontweight='bold')
axes[0].set_xlabel('Pearson Correlation')
axes[0].set_ylabel('Density')
axes[0].legend()

axes[1].scatter(vw_v, ew_v, alpha=0.25, s=12, color='teal')
axes[1].plot([-0.05, 1.0], [-0.05, 1.0], 'r--', linewidth=1.2, label='y = x (VW = EW)')
axes[1].set_title('Pairwise Correlation Scatter (3,003 Sector Pairs)', fontsize=11, fontweight='bold')
axes[1].set_xlabel('Value-Weighted (VW) Correlation')
axes[1].set_ylabel('Equal-Weighted (EW) Correlation')
axes[1].legend()

plt.tight_layout()
plt.savefig('corr_comparison.png', dpi=150)
print("그래프 저장 완료: corr_comparison.png")
