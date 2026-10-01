# V229 — دستور اجرای واقعی

## 1) Probe شبکه

```bash
python scripts/network_probe.py
```

## 2) اجرای مسیر اصلی

```bash
python v229_recovery_runner.py --route 1 --out v229_results --cache v229_cache
```

## 3) اگر مسیر 1 شکست خورد، هر سه مسیر

```bash
python v229_recovery_runner.py --route all --out v229_results --cache v229_cache
```

## 4) خروجی مورد انتظار

`v229_results/V229_recovery_report.json`

و در صورت PASS برای هر نورون، فایل SWC متناظر.

**تا قبل از مشاهده این فایل‌ها، V229 PASS محسوب نمی‌شود.**
