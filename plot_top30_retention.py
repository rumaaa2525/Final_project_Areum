import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 1. 리눅스 서버 내 한글 폰트 자동 탐색 및 설정
font_candidates = ['NanumGothic', 'NanumBarunGothic', 'Malgun Gothic', 'AppleGothic', 'Noto Sans CJK KR']
available_fonts = {f.name for f in fm.fontManager.ttflist}
selected_font = next((f for f in font_candidates if f in available_fonts), None)

if selected_font:
    plt.rcParams['font.family'] = selected_font
    use_korean = True
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'
    use_korean = False
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드
df = pd.read_csv('top30_retained_stocks.csv', dtype={'Code': str})
retained_count = len(df)
dropped_count = 30 - retained_count

# 3. 1행 2열 그래프 레이아웃 설정
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={'width_ratios': [1, 1.4]})
fig.patch.set_facecolor('white')

# --- [왼쪽] 도넛 차트: 상위 30위 유지 비율 ---
sizes = [retained_count, dropped_count]
colors = ['#2563EB', '#E2E8F0']
labels = [
    f'유지 종목 ({retained_count}개)' if use_korean else f'Retained ({retained_count})',
    f'이탈/교체 ({dropped_count}개)' if use_korean else f'Replaced ({dropped_count})'
]

wedges, texts, autotexts = ax1.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors,
    pctdistance=0.75,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
    textprops=dict(fontsize=11, fontweight='bold')
)
autotexts[0].set_color('white')
autotexts[1].set_color('#475569')

center_text = f"{retained_count} / 30"
ax1.text(0, 0, center_text, ha='center', va='center', fontsize=18, fontweight='bold', color='#1E293B')
ax1.set_title(
    '시가총액 상위 30위 유지 비율 (2.5년 전 대비)' if use_korean else 'Top 30 Market Cap Retention Rate (2.5Y)',
    fontsize=13, fontweight='bold', pad=15
)

# --- [오른쪽] 슬로프 차트: 유지된 종목의 순위 변화 (과거 vs 현재) ---
df_sorted = df.sort_values('Now_Rank').reset_index(drop=True)

ax2.axvline(0, color='#94A3B8', linestyle='--', linewidth=1, alpha=0.7)
ax2.axvline(1, color='#94A3B8', linestyle='--', linewidth=1, alpha=0.7)

for _, row in df_sorted.iterrows():
    p_rank = row['Past_Rank']
    n_rank = row['Now_Rank']
    code = row['Code']
    sector = row['Sector']
    
    # 순위 상승(파랑), 하락(주황), 유지(회색)
    if n_rank < p_rank:
        line_color = '#2563EB'
    elif n_rank > p_rank:
        line_color = '#EA580C'
    else:
        line_color = '#64748B'
        
    ax2.plot([0, 1], [p_rank, n_rank], marker='o', color=line_color, linewidth=1.8, alpha=0.85)
    
    # 왼쪽(과거 순위) 라벨
    ax2.text(-0.04, p_rank, f"#{int(p_rank)} ({code})", ha='right', va='center', fontsize=9, color='#334155')
    # 오른쪽(현재 순위) 라벨
    right_label = f"#{int(n_rank)} {code} [{sector}]" if use_korean else f"#{int(n_rank)} {code}"
    ax2.text(1.04, n_rank, right_label, ha='left', va='center', fontsize=9, fontweight='bold', color=line_color)

ax2.set_ylim(31.5, 0.5)  # 1위가 맨 위로 오도록 Y축 반전
ax2.set_xlim(-0.45, 1.75)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(
    ['2.5년 전 순위 (Past)' if use_korean else '2.5 Years Ago',
     '현재 순위 (Current)' if use_korean else 'Current'],
    fontsize=11, fontweight='bold'
)
ax2.set_ylabel('시가총액 순위 (Rank)' if use_korean else 'Market Cap Rank', fontsize=11)
ax2.set_title(
    '유지 종목별 시가총액 순위 변동 (상승: 파랑 / 하락: 주황)' if use_korean else 'Rank Trajectory of Retained Stocks (Up: Blue / Down: Orange)',
    fontsize=13, fontweight='bold', pad=15
)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['bottom'].set_visible(False)
ax2.grid(axis='y', linestyle=':', alpha=0.4)

plt.tight_layout()
output_file = 'top30_retention_chart.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"시각화 저장 완료: {output_file} (한글폰트 적용: {selected_font})")
