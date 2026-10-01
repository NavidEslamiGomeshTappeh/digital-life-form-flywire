# Digital Life Form — FlyWire

## V229 — بازیابی دقیق نورون‌های FlyWire

این مخزن ابزار بازیابی و اعتبارسنجی چهار نورون دقیق FlyWire v783 را نگهداری می‌کند. پروژه هیچ نورون مشابه یا حدس‌زده‌ای را جایگزین نورون درخواستی نمی‌کند.

| نورون | Root ID | VFB ID |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

ترتیب بازیابی: fafbseg/FlyWire، سپس MRC precomputed و در نهایت Zenodo.

### مدرک واقعی

فایل `v229_results/V229_recovery_report.json` نتیجه ثبت‌شده بازیابی واقعی چهار نورون را نگهداری می‌کند و شامل تعداد node، بررسی root ساختاری، parent reference، هندسه و SHA-256 است.

تست نرم‌افزار با موفقیت بازیابی داده خارجی یکی نیست؛ این دو سطح جداگانه ثبت می‌شوند.

### اجرا

    python -m py_compile v229_recovery_runner.py
    python test_v229_recovery_runner.py
    python v229_recovery_runner.py --route all --out v229_results --cache v229_cache

### قوانین اعتبارسنجی

Root ID واقعی داده باید با Root ID درخواست‌شده برابر باشد. SWC باید node داشته باشد، دقیقاً یک structural root داشته باشد، parent گمشده نداشته باشد و مختصات آن finite باشند.

### وضعیت

V229 یک milestone واقعی در لایه بازیابی مورفولوژی است؛ ادعای ساخت کل مغز مگس یا معادل‌بودن زیستی ندارد.

راهنمای کامل‌تر در `ABOUT.md` و `docs/VALIDATION.md` قرار دارد.