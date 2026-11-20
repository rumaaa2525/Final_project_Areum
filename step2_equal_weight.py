import os
import pandas as pd

# 1. 이미 추출된 종목별 원본 데이터 로드 (전일 종가 0 이하 제외)
df = pd.read_csv(os.path.expanduser("~/raw_stocks.csv"))
df = df[df['PrevClose'] > 0].copy()

# 2. 개별 종목 일별 단순 수익률 계산
df['ret'] = (df['Close'] - df['PrevClose']) / df['PrevClose']

# 3. 날짜·업종별 동일 가중 수익률 (단순 산술평균) 및 구성 종목 수 계산
res = df.groupby(['Date', 'Sector'], as_index=False).agg(
    Equal_Weighted_Return=('ret', 'mean'),
    Stock_Count=('Code', 'count')
)

res.sort_values(['Date', 'Sector'], inplace=True)

# 4. 결과 저장
out = os.path.expanduser("~/sector_daily_returns_ew.csv")
res.to_csv(out, index=False, encoding='utf-8-sig')
print("동일 가중 수익률 계산 완료! 미리보기:\n", res.head(10))
