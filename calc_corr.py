import pandas as pd
import numpy as np

# 1. 데이터 불러오기
df_vw = pd.read_csv('sector_daily_returns.csv')
df_ew = pd.read_csv('sector_daily_returns_ew.csv')

# 2. 날짜(행) x 업종(열) 형태로 피벗 변환
vw_pivot = df_vw.pivot(index='Date', columns='Sector', values='Sector_Return')
ew_pivot = df_ew.pivot(index='Date', columns='Sector', values='Equal_Weighted_Return')

# 데이터가 전부 비어있는 '기타' 업종 제거
vw_pivot = vw_pivot.dropna(axis=1, how='all')
ew_pivot = ew_pivot.dropna(axis=1, how='all')

# 3. 업종 간 피어슨 상관계수 행렬 계산
vw_corr = vw_pivot.corr(method='pearson')
ew_corr = ew_pivot.corr(method='pearson')

# 4. CSV 파일로 결과 저장
vw_corr.to_csv('sector_corr_vw.csv', encoding='utf-8-sig')
ew_corr.to_csv('sector_corr_ew.csv', encoding='utf-8-sig')

# 5. 요약 출력
vw_mean = np.nanmean(vw_corr.values[np.triu_indices_from(vw_corr.values, k=1)])
ew_mean = np.nanmean(ew_corr.values[np.triu_indices_from(ew_corr.values, k=1)])

print("=== 시가총액 가중(VW) 상관계수 일부 ===")
print(vw_corr.iloc[:5, :5].round(4))
print(f"\n[VW] 전체 업종 쌍 평균 상관계수: {vw_mean:.4f}")

print("\n=== 동일 가중(EW) 상관계수 일부 ===")
print(ew_corr.iloc[:5, :5].round(4))
print(f"\n[EW] 전체 업종 쌍 평균 상관계수: {ew_mean:.4f}")
