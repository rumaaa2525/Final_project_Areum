import os
import urllib.request
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def set_korean_font():
    font_candidates = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        'NanumGothic.ttf'
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)
    if font_path is None:
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        font_path = "NanumGothic.ttf"
        urllib.request.urlretrieve(url, font_path)
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False

set_korean_font()

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

summary = pd.DataFrame({
    'VW_Cum_Return(%)': (vw_cum.iloc[-1] * 100).round(2),
    'EW_Cum_Return(%)': (ew_cum.iloc[-1] * 100).round(2),
    'Diff_VW_minus_EW(%p)': ((vw_cum.iloc[-1] - ew_cum.iloc[-1]) * 100).round(2)
}).sort_values(by='VW_Cum_Return(%)', ascending=False)

summary.to_csv('sector_cumulative_returns_summary.csv')
vw_cum.to_csv('sector_cum_returns_vw_series.csv')
ew_cum.to_csv('sector_cum_returns_ew_series.csv')

top5_sectors = summary.head(5).index
bot5_sectors = summary.tail(5).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

for sec in top5_sectors:
    axes[0].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[0].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[0].set_title('시가총액 가중(VW) 누적 수익률 상위 5개 업종', fontsize=13, fontweight='bold')
axes[0].set_ylabel('누적 수익률 (%)')
axes[0].legend(loc='upper left', fontsize=9)
axes[0].grid(alpha=0.3)

for sec in bot5_sectors:
    axes[1].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[1].set_title('시가총액 가중(VW) 누적 수익률 하위 5개 업종', fontsize=13, fontweight='bold')
axes[1].legend(loc='lower left', fontsize=9)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('sector_cum_returns.png', dpi=300)
print("완료")
