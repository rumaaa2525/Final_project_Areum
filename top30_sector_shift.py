import os, re, urllib.request, pandas as pd

# 1. 원본 데이터 로드 및 시가총액 계산
df = pd.read_csv(os.path.expanduser("~/raw_stocks.csv"), dtype={'Code': str})
df['Date'] = pd.to_datetime(df['Date'])
df['Code'] = df['Code'].str.zfill(6)
df['Marcap'] = df['Close'] * df['Shares']

# 2. KRX 기업명 매핑
url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
html = urllib.request.urlopen(url).read().decode('euc-kr', errors='ignore')
name_map = {
    cols[1].zfill(6): cols[0]
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
    if len(cols := [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]) >= 2 and cols[1].isdigit()
}

# 3. 기준일 설정 및 전체 시장 순위 산출
latest_date = df['Date'].max()
target_past = latest_date - pd.DateOffset(years=2, months=6)
past_date = df[df['Date'] <= target_past]['Date'].max()
if pd.isna(past_date):
    past_date = df['Date'].min()

df_past_all = df[df['Date'] == past_date].drop_duplicates('Code').sort_values('Marcap', ascending=False).reset_index(drop=True)
df_past_all['Past_Rank'] = df_past_all.index + 1

df_now_all = df[df['Date'] == latest_date].drop_duplicates('Code').sort_values('Marcap', ascending=False).reset_index(drop=True)
df_now_all['Now_Rank'] = df_now_all.index + 1

top30_past = df_past_all.head(30).copy()
top30_now = df_now_all.head(30).copy()

# 4. 신규 진입 종목 (현재 Top 30 - 과거 Top 30) 추출
new_codes = set(top30_now['Code']) - set(top30_past['Code'])
new_entrants = pd.merge(
    top30_now[top30_now['Code'].isin(new_codes)][['Code', 'Sector', 'Now_Rank', 'Marcap']],
    df_past_all[['Code', 'Past_Rank']],
    on='Code', how='left'
)
new_entrants['Name'] = new_entrants['Code'].map(name_map).fillna(new_entrants['Code'])
new_entrants['Rank_Gain'] = new_entrants['Past_Rank'] - new_entrants['Now_Rank']
new_entrants['Now_Marcap(조)'] = (new_entrants['Marcap'] / 1e12).round(2)
new_entrants = new_entrants[['Code', 'Name', 'Sector', 'Past_Rank', 'Now_Rank', 'Rank_Gain', 'Now_Marcap(조)']].sort_values('Now_Rank')
new_entrants.to_csv('top30_new_entrants.csv', index=False, encoding='utf-8-sig')

# 5. 업종별 순위 이동 크기 집계 (유지 + 신규 + 이탈 전체 기준)
past_sec = top30_past.groupby('Sector').agg(Past_Count=('Code', 'count'), Past_Mean_Rank=('Past_Rank', 'mean'))
now_sec = top30_now.groupby('Sector').agg(Now_Count=('Code', 'count'), Now_Mean_Rank=('Now_Rank', 'mean'))
sec_summary = pd.merge(past_sec, now_sec, on='Sector', how='outer').fillna({'Past_Count': 0, 'Now_Count': 0})

# 유지 종목 기준 업종별 순위 이동 크기 (양수 = 순위 상승, 음수 = 순위 하락)
retained = pd.merge(top30_past[['Code', 'Sector', 'Past_Rank']], top30_now[['Code', 'Now_Rank']], on='Code')
retained['Rank_Shift'] = retained['Past_Rank'] - retained['Now_Rank']
retained['Abs_Shift'] = retained['Rank_Shift'].abs()
ret_sec = retained.groupby('Sector').agg(
    Retained_Count=('Code', 'count'),
    Mean_Rank_Shift=('Rank_Shift', 'mean'),
    Mean_Abs_Shift=('Abs_Shift', 'mean')
)

sec_summary = sec_summary.join(ret_sec).fillna({'Retained_Count': 0, 'Mean_Rank_Shift': 0, 'Mean_Abs_Shift': 0})
sec_summary['Net_Count_Change'] = sec_summary['Now_Count'] - sec_summary['Past_Count']
sec_summary = sec_summary.round(2).sort_values(['Now_Count', 'Net_Count_Change'], ascending=False).reset_index()
sec_summary.to_csv('top30_sector_shift_summary.csv', index=False, encoding='utf-8-sig')

print(f"\n[1. 신규 진입 종목 ({len(new_entrants)}개)]")
print(new_entrants.to_string(index=False))
print("\n[2. 업종별 상위 30위 점유 및 순위 이동 크기]")
print(sec_summary.to_string(index=False))
