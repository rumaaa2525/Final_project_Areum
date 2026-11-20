import pandas as pd
import numpy as np

# 1. 세로형(Long) 원본 데이터 로드 (UTF-8 BOM 인코딩 처리)
vw_raw = pd.read_csv('sector_daily_returns_vw.csv', encoding='utf-8-sig')
ew_raw = pd.read_csv('sector_daily_returns_ew.csv', encoding='utf-8-sig')

# 2. 날짜(Date)를 행, 업종(Sector)을 열로 피벗 변환 (날짜당 1행 시계열로 정렬)
vw_ret = vw_raw.pivot(index='Date', columns='Sector', values='Sector_Return').sort_index()
ew_ret = ew_raw.pivot(index='Date', columns='Sector', values='Equal_Weighted_Return').sort_index()

vw_ret.index = pd.to_datetime(vw_ret.index)
ew_ret.index = pd.to_datetime(ew_ret.index)

def calc_dynamic_avg_corr(df, window=60):
    """시점별 전체 업종 쌍의 평균 상관계수(대각선 제외) 계산"""
    rolling_corr = df.rolling(window=window).corr()

    dates = df.index[window - 1:]
    avg_corrs = []

    for dt in dates:
        mat = rolling_corr.loc[dt].values
        upper_tri = mat[np.triu_indices_from(mat, k=1)]
        avg_corrs.append(np.nanmean(upper_tri))

    return pd.Series(avg_corrs, index=dates, name=f'Rolling_{window}d_Corr')

# 3. 60거래일(약 1분기) 기준 동적 평균 상관계수 산출
dyn_ew = calc_dynamic_avg_corr(ew_ret, window=60)
dyn_vw = calc_dynamic_avg_corr(vw_ret, window=60)

# 4. 결과 통합 및 저장
dyn_summary = pd.DataFrame({
    'EW_Dynamic_Corr': dyn_ew,
    'VW_Dynamic_Corr': dyn_vw,
    'EW_minus_VW': dyn_ew - dyn_vw
})
dyn_summary.to_csv('dynamic_correlation_60d.csv')

print(f"완료! 총 {len(dyn_summary)}거래일 데이터가 dynamic_correlation_60d.csv에 저장되었습니다.")
print(dyn_summary.head())
