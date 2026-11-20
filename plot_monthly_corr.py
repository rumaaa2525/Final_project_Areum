import matplotlib
matplotlib.use('Agg')  # 리눅스 서버(GUI 없는 환경) 그래프 저장 설정
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. 동적 상관계수 데이터 로드 및 월별 평균 집계
df = pd.read_csv('dynamic_correlation_60d.csv', index_col=0, parse_dates=True)
monthly_df = df.resample('ME').mean()
months = monthly_df.index.strftime('%Y-%m')

x = np.arange(len(months))
width = 0.38

# 2. 그래프 레이아웃 설정
fig, ax = plt.subplots(figsize=(14, 6))

# EW vs VW 월별 평균 막대 그래프
bars_ew = ax.bar(x - width/2, monthly_df['EW_Dynamic_Corr'], width, label='Equal-Weighted (EW) Monthly Mean', color='#1f77b4', alpha=0.88)
bars_vw = ax.bar(x + width/2, monthly_df['VW_Dynamic_Corr'], width, label='Value-Weighted (VW) Monthly Mean', color='#ff7f0e', alpha=0.88)

# 전체 추세 연결선 (EW 기준)
ax.plot(x - width/2, monthly_df['EW_Dynamic_Corr'], color='#0b3d91', marker='o', markersize=4, linewidth=1.5, linestyle='-', alpha=0.7)

# 국면 임계 기준선 (평상시 vs 급락기)
ax.axhline(0.5293, color='#d62728', linestyle='--', linewidth=1.2, alpha=0.85, label='EW Crash Regime Mean (0.529)')
ax.axhline(0.1565, color='#2ca02c', linestyle='--', linewidth=1.2, alpha=0.85, label='EW Normal Regime Mean (0.157)')

# 막대 상단에 수치 표시 (가독성을 위해 EW 막대 위에만 소수점 둘째 자리까지 표시)
for bar in bars_ew:
    h = bar.get_height()
    ax.annotate(f'{h:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8, color='#0b3d91', fontweight='bold')

# 축 및 제목 스타일링
ax.set_title('Monthly Average Dynamic Sector Correlation (60-Day Rolling Window)', fontsize=13, fontweight='bold', pad=14)
ax.set_ylabel('Mean Pairwise Correlation', fontsize=11)
ax.set_xlabel('Month', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(months, rotation=45, ha='right', fontsize=9.5)
ax.set_ylim(0, max(monthly_df['EW_Dynamic_Corr'].max(), 0.58) * 1.12)

ax.grid(axis='y', linestyle=':', alpha=0.6)
ax.legend(loc='upper left', frameon=True, fontsize=9.5)

plt.tight_layout()
plt.savefig('monthly_dynamic_corr.png', dpi=300)
print("월별 상관계수 추이 그래프 저장 완료: monthly_dynamic_corr.png")
