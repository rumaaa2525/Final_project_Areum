import os, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
for r, _, fs in os.walk('/usr/share/fonts'):
    for f in fs:
        if any(k in f.lower() for k in ['nanum', 'noto', 'malgun', 'gulim']) and f.endswith(('.ttf', '.otf')):
            p = os.path.join(r, f); fm.fontManager.addfont(p); plt.rcParams['font.family'] = fm.FontProperties(fname=p).get_name(); break
plt.rcParams['axes.unicode_minus'] = False
df_new = pd.read_csv('top30_new_entrants.csv', dtype={'Code': str})
df_sec = pd.read_csv('top30_sector_shift_summary.csv')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw={'width_ratios': [1.1, 1.2]})
df_new_s = df_new.sort_values('Now_Rank', ascending=False)
y_labels = [f"#{int(r['Now_Rank'])} {r['Name']} [{r['Sector']}]" for _, r in df_new_s.iterrows()]
gains = df_new_s['Rank_Gain'].fillna(0)
bars = ax1.barh(y_labels, gains, color='#2563EB', alpha=0.85, height=0.6)
ax1.set_title(f'신규 진입 종목 및 순위 상승폭 (총 {len(df_new)}개)', fontweight='bold')
ax1.set_xlim(0, max(gains.max() * 1.25, 10))
for bar, (_, r) in zip(bars, df_new_s.iterrows()):
    txt = f"+{int(r['Rank_Gain'])}위 (과거 {int(r['Past_Rank'])}위)" if pd.notna(r['Rank_Gain']) else '신규상장'
    ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, txt, va='center', fontsize=8.5, fontweight='bold')
df_sec_s = df_sec.sort_values(['Net_Count_Change', 'Mean_Rank_Shift'], ascending=True)
colors = ['#2563EB' if x > 0 else ('#EA580C' if x < 0 else '#94A3B8') for x in df_sec_s['Net_Count_Change']]
bars2 = ax2.barh(df_sec_s['Sector'], df_sec_s['Net_Count_Change'], color=colors, alpha=0.85, height=0.6)
ax2.axvline(0, color='#334155', lw=1)
ax2.set_title('업종별 30위권 종목 수 증감 및 잔류종목 순위 이동', fontweight='bold')
ax2.set_xlim(min(df_sec_s['Net_Count_Change'].min() - 1.8, -2), max(df_sec_s['Net_Count_Change'].max() + 2.5, 2))
for bar, (_, r) in zip(bars2, df_sec_s.iterrows()):
    val = r['Net_Count_Change']
    s_str = f" (잔류평균 {r['Mean_Rank_Shift']:+.1f}위)" if r['Retained_Count'] > 0 else ''
    ax2.text(val + (0.12 if val >= 0 else -0.12), bar.get_y() + bar.get_height()/2, f"{int(val):+d}개{s_str}", va='center', ha=('left' if val >= 0 else 'right'), fontsize=8.5, fontweight='bold')
for ax in (ax1, ax2):
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('top30_sector_shift_chart.png', dpi=300, bbox_inches='tight')
print('시각화 저장 완료')
