import os, re, glob, time, pandas as pd
from concurrent.futures import ProcessPoolExecutor

re_sec = re.compile(r'class="h_sub sub_tit7".*?<a[^>]*>([^<]+)</a>', re.S)
re_close = re.compile(r'class="no_today".*?<span class="blind">([\d,]+)</span>', re.S)
re_prev = re.compile(r'class="no_info".*?<span class="blind">([\d,]+)</span>', re.S)
re_shares = re.compile(r'상장주식수.*?<em>([\d,]+)</em>', re.S)

def parse_fast(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()  # 상단 85KB만 읽어서 속도 극대화
        sec = re_sec.search(html).group(1).strip()
        close = float(re_close.search(html).group(1).replace(',', ''))
        prev = float(re_prev.search(html).group(1).replace(',', ''))
        shares = float(re_shares.search(html).group(1).replace(',', ''))
        return [os.path.basename(os.path.dirname(path)), sec, os.path.basename(path).split('_')[-1][:-5], close, prev, shares]
    except Exception:
        return None

if __name__ == '__main__':
    t0 = time.time()
    files = sorted(glob.glob("/mnt/data/stock/*/*.html"))  # 정렬해서 순차 읽기(디스크 속도 향상)
    total = len(files)
    print(f"총 {total:,}개 파일 초고속 추출 시작...")

    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(parse_fast, files, chunksize=1000), 1):
            if r:
                rows.append(r)
            if i % 100000 == 0:
                elapsed = time.time() - t0
                rem = (total - i) / (i / elapsed)
                print(f"진행: {i:,}/{total:,} ({i/total*100:.1f}%) | 경과: {elapsed:.0f}초 | 남은 시간: 약 {rem/60:.1f}분", flush=True)

    df = pd.DataFrame(rows, columns=['Date', 'Sector', 'Code', 'Close', 'PrevClose', 'Shares'])
    df.to_csv(os.path.expanduser("~/raw_stocks.csv"), index=False)
    print(f"1단계 완료! 총 {len(df):,}행 저장됨 (소요시간: {(time.time()-t0)/60:.1f}분)")
