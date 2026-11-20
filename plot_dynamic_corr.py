import matplotlib
matplotlib.use('Agg')  # 리눅스 서버(GUI 없는 환경) 그래프 저장 필수 설정
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# 1. 동적 상관계수 데이터 로드
df = pd.read_csv('dynamic_correlation_60d.csv', index_col=0, parse_dates=True)

# 2. README 및 발표용 핵심 요약 통계 산출
ew_mean, vw_mean = df['EW_Dynamic_Corr'].mean(), df['VW_Dynamic_Corr'].mean()
ew_min_dt, ew_min = df['EW_Dynamic_Corr'].idxmin(), df['EW_Dynamic_Corr'].min()
ew_max_dt, ew_max = df['EW_Dynamic_Corr'].idxmax(), df['EW_Dynamic_Corr'].max()

vw_min_dt, vw_min = df['VW_Dynamic_Corr'].idxmin(), df['VW_Dynamic_Corr'].min()
vw_max_dt, vw_max = df['VW_Dynamic_Corr'].idxmax(), df['VW_Dynamic_Corr'].max()

ew_gt_vw_ratio = (df['EW_minus_VW'] > 0).mean() * 100

print("=" * 60)
print(f"분석 기간: {df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')} (총 {len(df)}거래일)")
print("-" * 60)
print(f"[EW 동적 상관계수] 평균: {ew_mean:.4f} | 최저: {ew_min:.4f} ({ew_min_dt.strftime('%Y-%m-%d')}) | 최고: {ew_max:.4f} ({ew_max_dt.strftime('%Y-%m-%d')})")
print(f"[VW 동적 상관계수] 평균: {vw_mean:.4f} | 최저: {vw_min:.4f} ({vw_min_dt.strftime('%Y-%m-%d')}) | 최고: {vw_max:.4f} ({vw_max_dt.strftime('%Y-%m-%d')})")
print(f"[EW > VW 유지 비율] 전체 기간 중 {ew_gt_vw_ratio:.2f}% 구간에서 EW 상관계수가 VW보다 높음")
print("=" * 60)

# 3. 2단 서브플롯 시각화 (상단: EW vs VW 추이 및 국면 기준선 / 하단: EW-VW 격차)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2.2, 1]})

# [상단 패널] 60일 이동 평균 상관계수 시계열
ax1.plot(df.index, df['EW_Dynamic_Corr'], label='Equal-Weighted (EW, 60d Rolling)', color='#1f77b4', linewidth=2)
ax1.plot(df.index, df['VW_Dynamic_Corr'], label='Value-Weighted (VW, 60d Rolling)', color='#ff7f0e', linewidth=2)

# 기존 국면 분석(EW 기준) 임계치 참고선 표시
ax1.axhline(0.5293, color='#d62728', linestyle='--', linewidth=1.2, alpha=0.8, label='EW Crash Regime Mean (0.529)')
ax1.axhline(0.1565, color='#2ca02c', linestyle='--', linewidth=1.2, alpha=0.8, label='EW Normal Regime Mean (0.157)')

# 최고점 및 최저점 주석 표시 (EW 기준)
ax1.scatter([ew_max_dt], [ew_max], color='#d62728', zorder=5)
ax1.annotate(f"Peak: {ew_max:.3f}\n({ew_max_dt.strftime('%Y-%m-%d')})",
             xy=(ew_max_dt, ew_max), xytext=(10, -15), textcoords='offset points',
             fontsize=9, fontweight='bold', color='#d62728')

ax1.scatter([ew_min_dt], [ew_min], color='#2ca02c', zorder=5)
ax1.annotate(f"Trough: {ew_min:.3f}\n({ew_min_dt.strftime('%Y-%m-%d')})",
             xy=(ew_min_dt, ew_min), xytext=(10, 8), textcoords='offset points',
             fontsize=9, fontweight='bold', color='#2ca02c')

ax1.set_title('60-Day Rolling Average Pairwise Sector Correlation (EW vs. VW)', fontsize=13, fontweight='bold', pad=12)
ax1.set_ylabel('Average Correlation', fontsize=11)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper left', frameon=True, fontsize=9.5)

# [하단 패널] EW - VW 격차(Spread) 추이
ax2.plot(df.index, df['EW_minus_VW'], color='#6a3d9a', linewidth=1.5, label='Spread (EW - VW)')
ax2.fill_between(df.index, df['EW_minus_VW'], 0, where=(df['EW_minus_VW'] >= 0), color='#6a3d9a', alpha=0.2)
ax2.fill_between(df.index, df['EW_minus_VW'], 0, where=(df['EW_minus_VW'] < 0), color='#e31a1c', alpha=0.2)
ax2.axhline(0, color='black', linestyle='-', linewidth=1)

ax2.set_ylabel('Spread (EW - VW)', fontsize=11)
ax2.set_xlabel('Date', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper left', frameon=True, fontsize=9.5)

# x축 날짜 포맷 정리
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=30)

plt.tight_layout()
plt.savefig('dynamic_corr_trend.png', dpi=300)
print("그래프 저장 완료: dynamic_corr_trend.png")
