import os
import pandas as pd

# 1. 원본 데이터 로드 (종목코드 앞자리 0 유지를 위해 str로 지정)
df = pd.read_csv(os.path.expanduser("~/raw_stocks.csv"), dtype={'Code': str})
df['Date'] = pd.to_datetime(df['Date'])

# 2. 시가총액 계산 (종가 * 상장주식수)
df['Marcap'] = df['Close'] * df['Shares']

# 3. 기준 날짜 설정 (데이터의 가장 최근 날짜 vs 정확히 2년 6개월 전)
latest_date = df['Date'].max()
target_past_date = latest_date - pd.DateOffset(years=2, months=6)

# 2년 6개월 전 날짜가 휴장일일 수 있으므로, 해당일 이전(또는 당일)의 가장 가까운 거래일 선택
past_date = df[df['Date'] <= target_past_date]['Date'].max()

# 데이터 시작일이 2년 반 전보다 늦을 경우를 대비한 안내
earliest_date = df['Date'].min()
if pd.isna(past_date):
    print(f"[주의] 데이터 시작일({earliest_date.strftime('%Y-%m-%d')})이 목표 과거일({target_past_date.strftime('%Y-%m-%d')})보다 늦습니다.")
    past_date = earliest_date

# 4. 각 시점별 시가총액 상위 30위 추출 (동일 날짜 중복 제거 후 정렬)
df_past = df[df['Date'] == past_date].drop_duplicates(subset=['Code']).sort_values(by='Marcap', ascending=False).head(30).copy()
df_past['Past_Rank'] = range(1, len(df_past) + 1)

df_now = df[df['Date'] == latest_date].drop_duplicates(subset=['Code']).sort_values(by='Marcap', ascending=False).head(30).copy()
df_now['Now_Rank'] = range(1, len(df_now) + 1)

# 5. 교집합(2년 반 전 상위 30위 중 현재도 30위 안에 있는 종목) 계산
retained = pd.merge(
    df_past[['Code', 'Sector', 'Past_Rank', 'Marcap']],
    df_now[['Code', 'Now_Rank', 'Marcap']],
    on='Code',
    suffixes=('_Past', '_Now')
)

# 6. 결과 출력
print("=" * 65)
print(f"데이터 전체 기간 : {earliest_date.strftime('%Y-%m-%d')} ~ {latest_date.strftime('%Y-%m-%d')}")
print(f"과거 비교 기준일 : {past_date.strftime('%Y-%m-%d')} (목표일: {target_past_date.strftime('%Y-%m-%d')})")
print(f"현재 비교 기준일 : {latest_date.strftime('%Y-%m-%d')}")
print(f"상위 30위 유지 종목 수 : {len(retained)}개 / 30개 ({len(retained)/30*100:.1f}%)")
print("=" * 65)

if len(retained) > 0:
    # 시가총액 단위를 '조 원'으로 보기 좋게 변환
    retained['Past_Marcap(조)'] = (retained['Marcap_Past'] / 1e12).round(2)
    retained['Now_Marcap(조)'] = (retained['Marcap_Now'] / 1e12).round(2)
    
    cols = ['Code', 'Sector', 'Past_Rank', 'Now_Rank', 'Past_Marcap(조)', 'Now_Marcap(조)']
    print(retained[cols].sort_values('Now_Rank').to_string(index=False))

# CSV로도 저장 (필요시 활용)
retained.to_csv('top30_retained_stocks.csv', index=False, encoding='utf-8-sig')
