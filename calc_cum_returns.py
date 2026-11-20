import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 1. 외부 통신 없이 서버 로컬 시스템에서 한글 폰트 자동 탐색
def get_local_korean_font():
    # 시스템 폰트 디렉토리에서 자주 쓰이는 한글 폰트 검색
    search_patterns = [
        '/usr/share/fonts/**/*Nanum*.tt*',
        '/usr/share/fonts/**/*NotoSansCJK*.tt*',
        '/usr/share/fonts/**/*NotoSansKR*.tt*',
        '/usr/share/fonts/**/*UnDotum*.tt*',
        '/usr/share/fonts/**/*Baekmuk*.tt*',
        '/usr/share/fonts/**/*malgun*.tt*',
        os.path.expanduser('~/.fonts/**/*Nanum*.tt*'),
        os.path.expanduser('~/.local/share/fonts/**/*Nanum*.tt*')
    ]
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
            
    # matplotlib 내장 폰트 목록에서 한글 폰트 이름 검색
    for f in fm.fontManager.ttflist:
        if any(k in f.name for k in ['Nanum', 'Noto Sans CJK', 'Noto Sans KR', 'Malgun', 'UnDotum', 'Baekmuk', 'AppleGothic']):
            return f.fname
            
    return None

font_path = get_local_korean_font()
if font_path:
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    print(f"로컬 한글 폰트 로드 성공: {font_prop.get_name()} ({font_path})")
else:
    font_prop = None
    print("[경고] 서버에 설치된 한글 폰트를 찾지 못했습니다. fc-list :lang=ko 결과를 확인해주세요.")

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

# 4. 시각화
top5_sectors = summary.head(5).index
bot5_sectors = summary.tail(5).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

for sec in top5_sectors:
    axes[0].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[0].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[0].set_title('시가총액 가중(VW) 누적 수익률 상위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[0].set_ylabel('누적 수익률 (%)', fontproperties=font_prop, fontsize=12)
axes[0].legend(loc='upper left', prop=font_prop, fontsize=10)
axes[0].grid(alpha=0.3)

for sec in bot5_sectors:
    axes[1].plot(vw_cum.index, vw_cum[sec] * 100, label=f"{sec} ({summary.loc[sec, 'VW_Cum_Return(%)']}%)")
axes[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
axes[1].set_title('시가총액 가중(VW) 누적 수익률 하위 5개 업종', fontproperties=font_prop, fontsize=14, fontweight='bold')
axes[1].legend(loc='lower left', prop=font_prop, fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('sector_cum_returns.png', dpi=300)
print("sector_cum_returns.png 생성 완료")
