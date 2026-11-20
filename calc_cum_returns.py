import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['axes.unicode_minus'] = False

# 1. 원본 CSV 로드
vw_raw = pd.read_csv('sector_daily_returns_vw.csv')
ew_raw = pd.read_csv('sector_daily_returns_ew.csv')

print("VW 컬럼 목록:", vw_raw.columns.tolist())
print("EW 컬럼 목록:", ew_raw.columns.tolist(), "\n")

# 2. Long format(Date, Sector, Return) -> Wide format(날짜 x 업종) 자동 변환 함수
def to_wide_returns(df):
    cols = df.columns.tolist()
    # 날짜 컬럼 찾기 (보통 첫 번째 컬럼이나 'Date' 포함 컬럼)
    date_col = next((c for c in cols if 'date' in c.lower()), cols[0])
    # 업종 컬럼 찾기 (문자열 컬럼 중 날짜 제외)
    sector_col = next((c for c in cols if 'sector' in c.lower()), None)
    
    if sector_col is not None:
        # 수익률 값 컬럼 찾기
        val_col = next((c for c in cols if 'return' in c.lower()), [c for c in cols if c not in [date_col, sector_col]][0])
        df[date_col] = pd.to_datetime(df[date_col])
        df[val_col] = pd.to_numeric(df[val_col].astype(str).str.replace('%', '', regex=False), errors='coerce')
        wide = df.pivot_table(index=date_col, columns=sector_col, values=val_col)
    else:
        # 이미 Wide format인 경우
        df[date_col] = pd.to_datetime(df[date_col])
        wide = df.set_index(date_col)
        for c in wide.columns:
            wide[c] = pd.to_numeric(wide[c].astype(str).str.replace('%', '', regex=False), errors='coerce')
            
    return wide.sort_index()

vw_daily = to_wide_returns(vw_raw)
ew_daily = to_wide_returns(ew_raw)

# 3. 퍼센트(%) 단위 자동 보정 및 누적 수익률 계산: (1 + r_t)의 누적곱 - 1
if vw_daily.abs().max().max() > 1:
    vw_daily = vw_daily / 100.0
if ew_daily.abs().max().max() > 1:
    ew_daily = ew_daily / 100.0

vw_cum = (1 + vw_daily.fillna(0)).cumprod() - 1
ew_cum = (1 + ew_daily.fillna(0)).cumprod() - 1

# 4. 전체 기간 최종 누적 수익률(%) 요약표 및 시계열 저장
summary = pd.DataFrame({
    'VW_Cum_Return(%)': (vw_cum.iloc[-1] * 100).round(2),
    'EW_Cum_Return(%)': (ew_cum.iloc[-1] * 100).round(2),
    'Diff_VW_minus_EW(%p)': ((vw_cum.iloc[-1] - ew_cum.iloc[-1]) * 100).round(2)
}).sort_values(by='VW_Cum_Return(%)', ascending=False)

summary.to_csv('sector_cumulative_returns_summary.csv')
vw_cum.to_csv('sector_cum_returns_vw_series.csv')
ew_cum.to_csv('sector_cum_returns_ew_series.csv')

print("=== 업종별 최종 누적 수익률 상위 5개 (VW 기준) ===")
print(summary.head(5))
print("\n=== 업종별 최종 누적 수익률 하위 5개 (VW 기준) ===")
print(summary.tail(5))

# 5. 시각화 (상위 5개 & 하위 5개 업종 누적 수익률 추이)
top5_sectors = summary.head(5).index
bot5_sectors = summary.tail(5).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

for sec in top5_sectors:
    axes[0].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[0].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[0].set_title('Top 5 Sectors Cumulative Return (VW)', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Cumulative Return (%)')
axes[0].legend(loc='upper left', fontsize=9)
axes[0].grid(alpha=0.3)

for sec in bot5_sectors:
    axes[1].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[1].set_title('Bottom 5 Sectors Cumulative Return (VW)', fontsize=13, fontweight='bold')
axes[1].legend(loc='lower left', fontsize=9)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('sector_cum_returns.png', dpi=300)
print("\n[완료] sector_cumulative_returns_summary.csv, sector_cum_returns_vw_series.csv, sector_cum_returns_ew_series.csv, sector_cum_returns.png 생성 완료")
