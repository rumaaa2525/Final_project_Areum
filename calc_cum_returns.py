import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 1. 한글 폰트 설정 (NanumGothic.ttf 고정)
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
fm.fontManager.addfont(font_path)
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드 및 Wide format 변환
vw_raw = pd.read_csv('sector_daily_returns_vw.csv')
ew_raw = pd.read_csv('sector_daily_returns_ew.csv')

def to_wide_returns(df):
    cols = df.columns.tolist()
    date_col = next((c for c in cols if 'date' in c.lower()), cols[0])
    sector_col = next((c for c in cols if 'sector' in c.lower()), None)
    if sector_col is not None:
        val_col = next((c for c in cols if 'return' in c.lower()), [c for c in cols if c not in [date_col, sector_col]][0])
        df[date_col] = pd.to_datetime(df[date_col])
        df[val_col] = pd.to_numeric(df[val_col].astype(str).str.replace('%', '', regex=False), errors='coerce')
        wide = df.pivot_table(index=date_col, columns=sector_col, values=val_col)
    else:
        df[date_col] = pd.to_datetime(df[date_col])
        wide = df.set_index(date_col)
        for c in wide.columns:
            wide[c] = pd.to_numeric(wide[c].astype(str).str.replace('%', '', regex=False), errors='coerce')
    return wide.sort_index()

vw_daily = to_wide_returns(vw_raw)
ew_daily = to_wide_returns(ew_raw)

if vw_daily.abs().max().max() > 1:
    vw_daily = vw_daily / 100.0
if ew_daily.abs().max().max() > 1:
    ew_daily = ew_daily / 100.0

vw_cum = (1 + vw_daily.fillna(0)).cumprod() - 1
ew_cum = (1 + ew_daily.fillna(0)).cumprod() - 1

# 3. 요약표 및 시계열 저장
summary = pd.DataFrame({
    'VW_Cum_Return(%)': (vw_cum.iloc[-1] * 100).round(2),
    'EW_Cum_Return(%)': (ew_cum.iloc[-1] * 100).round(2),
    'Diff_VW_minus_EW(%p)': ((vw_cum.iloc[-1] - ew_cum.iloc[-1]) * 100).round(2)
}).sort_values(by='VW_Cum_Return(%)', ascending=False)

summary.to_csv('sector_cumulative_returns_summary.csv')
vw_cum.to_csv('sector_cum_returns_vw_series.csv')
ew_cum.to_csv('sector_cum_returns_ew_series.csv')

# 4-1. 시각화 1: 시가총액 가중(VW) 기준 (sector_cum_returns.png)
top5_vw = summary.head(5).index
bot5_vw = summary.tail(5).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
for sec in top5_vw:
    axes[0].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[0].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[0].set_title('시가총액 가중(VW) 누적 수익률 상위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[0].set_ylabel('누적 수익률 (%)', fontproperties=font_prop, fontsize=12)
axes[0].legend(loc='upper left', prop=font_prop, fontsize=10)
axes[0].grid(alpha=0.3)

for sec in bot5_vw:
    axes[1].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[1].set_title('시가총액 가중(VW) 누적 수익률 하위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[1].legend(loc='lower left', prop=font_prop, fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('sector_cum_returns.png', dpi=300)
plt.close()

# 4-2. 시각화 2: 동일 가중(EW) 기준 (sector_cum_returns_ew.png)
summary_ew_sorted = summary.sort_values(by='EW_Cum_Return(%)', ascending=False)
top5_ew = summary_ew_sorted.head(5).index
bot5_ew = summary_ew_sorted.tail(5).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
for sec in top5_ew:
    axes[0].plot(ew_cum.index, ew_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'EW_Cum_Return(%)']}%)")
axes[0].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[0].set_title('동일 가중(EW) 누적 수익률 상위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[0].set_ylabel('누적 수익률 (%)', fontproperties=font_prop, fontsize=12)
axes[0].legend(loc='upper left', prop=font_prop, fontsize=10)
axes[0].grid(alpha=0.3)

for sec in bot5_ew:
    axes[1].plot(ew_cum.index, ew_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'EW_Cum_Return(%)']}%)")
axes[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[1].set_title('동일 가중(EW) 누적 수익률 하위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[1].legend(loc='lower left', prop=font_prop, fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('sector_cum_returns_ew.png', dpi=300)
plt.close()

print("완료: sector_cum_returns.png (VW) 및 sector_cum_returns_ew.png (EW) 생성 완료")
