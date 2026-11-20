import os, pandas as pd

df = pd.read_csv(os.path.expanduser("~/raw_stocks.csv"))
df = df[df['PrevClose'] > 0].copy()

df['ret'] = (df['Close'] - df['PrevClose']) / df['PrevClose']
df['prev_marcap'] = df['PrevClose'] * df['Shares']
df['weight'] = df['prev_marcap'] / df.groupby(['Date', 'Sector'])['prev_marcap'].transform('sum')
df['weighted_ret'] = df['weight'] * df['ret']

res = df.groupby(['Date', 'Sector'], as_index=False)['weighted_ret'].sum()
res.rename(columns={'weighted_ret': 'Sector_Return'}, inplace=True)
res.sort_values(['Date', 'Sector'], inplace=True)

out = os.path.expanduser("~/sector_daily_returns.csv")
res.to_csv(out, index=False, encoding='utf-8-sig')
print("2단계 완료!")
