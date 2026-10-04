# Digital Life Form — FlyWire

نسخه 1.2.0

این پروژه یک سامانهٔ پژوهش-مهندسی provenance-first برای استخراج دقیق و قابل‌بازتولید بخش‌های مشخصی از connectome فای‌وایر است.

چهار نورون مرجع FAFB v783:
- T4a — 720575940632008007
- T4c — 720575940616224414
- T5a — 720575940625571465
- T5c — 720575940617782941

هستهٔ شواهد شامل 649 ردیف سیناپس دقیق، 75 زوج directed، چهار morphology دقیق SWC، شواهد provenance تاریخی، بازسازی الگوریتم dendrite subtree، و ممیزی coordinate frame است.

نسخهٔ 1.1 یک claim ledger، artifact-integrity manifest و قرارداد بررسی مستقل Codex/Zenodo قابل‌بررسی ماشینی اضافه می‌کند. فرمان‌های زیر زنجیرهٔ شواهد را بررسی می‌کنند:

```bash
python -m dlf_flywire validate
python -m dlf_flywire audit
python -m dlf_flywire verify-sources
```

پروژه بین مشاهدهٔ منبع، محاسبهٔ قطعی، corroboration مستقل، استنباط زیستی و موارد حل‌نشده مرز مشخص می‌گذارد. نزدیک‌ترین نقطهٔ SWC به مختصات سیناپس به‌تنهایی compartment زیستی را ثابت نمی‌کند.

فایل‌های نسخه‌های آزمایشی قبلی از سطح محصول حذف شده‌اند و تاریخچهٔ Git برای audit باقی مانده است. ادامهٔ پروژه از [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) انجام می‌شود.
