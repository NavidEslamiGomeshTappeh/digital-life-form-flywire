# V229 Recovery Runner — GitHub Codespaces

این بسته برای اجرای واقعی V229 در محیطی ساخته شده که outbound Internet دارد.

## اجرا

1. این پوشه را به یک GitHub repository آپلود کنید.
2. در GitHub از **Code → Codespaces → Create codespace on main** استفاده کنید.
3. بعد از ساخته‌شدن Codespace، ترمینال خودش `bootstrap.sh` را اجرا می‌کند.
4. برای اجرای بازیابی چهار root:

```bash
python v229_recovery_runner.py --out v229_results --cache v229_cache
```

برای شروع فقط مسیر اول را آزمایش کنید:

```bash
python v229_recovery_runner.py --route 1 --out v229_results --cache v229_cache
```

## چهار root دقیق

- T4a = 720575940632008007
- T4c = 720575940616224414
- T5a = 720575940625571465
- T5c = 720575940617782941

هیچ root مشابهی جایگزین نمی‌شود.

## ترتیب مسیرها

1. `fafbseg.flywire.get_skeletons(..., dataset=783)`
2. MRC precomputed skeleton endpoint
3. Zenodo bulk dataset

مسیر ۳ تا زمانی که schema واقعی parquet تأیید نشده باشد، SWC جعلی تولید نمی‌کند.

## معیار PASS

PASS فقط وقتی صادر می‌شود که SWC خروجی:

- حداقل یک node داشته باشد؛
- دقیقاً یک structural root داشته باشد؛
- parent reference گمشده نداشته باشد؛
- مختصات finite باشند؛
- root ID درخواست‌شده با root ID داده تطبیق داشته باشد.
