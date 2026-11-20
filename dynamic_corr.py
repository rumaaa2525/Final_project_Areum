import pandas as pd
import numpy as np

# 1. 일별 수익률 시계열 로드
vw_ret = pd.read_csv('sector_daily_returns_vw.csv', index_col=0, parse_dates=True)
ew_ret = pd.read_csv('sector_daily_returns_ew.csv', index_col=0, parse_dates=True)

# 2. 문자열(object) 컬럼 제외 및 강제 숫자형 변환 (에러 방지)
vw_ret = vw_ret.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all')
ew_ret = ew_ret.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all')

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
print("완료! dynamic_correlation_60d.csv 파일이 생성되었습니다.")
print(dyn_summary.head())
