import os, re, urllib.request, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

for r, _, fs in os.walk('/usr/share/fonts'):
    for f in fs:
        if any(k in f.lower() for k in ['nanum', 'noto', 'malgun', 'gulim']) and f.endswith(('.ttf', '.otf')):
            p = os.path.join(r, f)
            fm.fontManager.addfont(p)
            plt.rcParams['font.family'] = fm.FontProperties(fname=p).get_name()
            break
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('top30_retained_stocks.csv', dtype={'Code': str})
df['Code'] = df['Code'].str.zfill(6)

url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
html = urllib.request.urlopen(url).read().decode('euc-kr', errors='ignore')
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
name_map = {}
for row in rows:
    cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
    if len(cols) >= 2 and cols[1].isdigit():
        name_map[cols[1].zfill(6)] = cols[0]

df['Name'] = df['Code'].map(name_map).fillna(df['Code'])
df.to_csv('top30_retained_stocks.csv', index=False, encoding='utf-8-sig')
print("기업명 매핑 결과:\n", df[['Code', 'Name', 'Past_Rank', 'Now_Rank']])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={'width_ratios': [1, 1.5]})
n_ret = len(df)

ax1.pie([n_ret, 30 - n_ret], labels=[f'유지 ({n_ret}개)', f'교체 ({30-n_ret}개)'], autopct='%1.1f%%',
        startangle=90, colors=['#2563EB', '#E2E8F0'], wedgeprops=dict(width=0.45, edgecolor='w'))
ax1.text(0, 0, f"{n_ret} / 30", ha='center', va='center', fontsize=18, fontweight='bold')
ax1.set_title('시가총액 상위 30위 유지 비율 (2.5년 전 대비)', fontweight='bold')

for _, r in df.sort_values('Now_Rank').iterrows():
    c = '#2563EB' if r['Now_Rank'] < r['Past_Rank'] else ('#EA580C' if r['Now_Rank'] > r['Past_Rank'] else '#64748B')
    ax2.plot([0, 1], [r['Past_Rank'], r['Now_Rank']], marker='o', color=c, lw=1.8)
    ax2.text(-0.04, r['Past_Rank'], f"#{int(r['Past_Rank'])} {r['Name']}", ha='right', va='center', fontsize=9)
    ax2.text(1.04, r['Now_Rank'], f"#{int(r['Now_Rank'])} {r['Name']} [{r['Sector']}]", ha='left', va='center', fontsize=9, fontweight='bold', color=c)

ax2.set(ylim=(31.5, 0.5), xlim=(-0.55, 1.85), xticks=[0, 1], xticklabels=['2.5년 전', '현재'])
ax2.set_title('유지 종목별 순위 변동 (상승: 파랑 / 하락: 주황)', fontweight='bold')
for s in ['top', 'right', 'bottom']: ax2.spines[s].set_visible(False)

plt.tight_layout()
plt.savefig('top30_retention_chart.png', dpi=300, bbox_inches='tight')
print("완료! 폰트:", plt.rcParams['font.family'])
