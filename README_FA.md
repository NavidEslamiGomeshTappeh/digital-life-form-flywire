# V229 Recovery Runner

چهار root دقیق FlyWire v783 را بدون جایگزین‌کردن نورون مشابه بازیابی می‌کند.

ترتیب: 1) fafbseg، 2) MRC precomputed، 3) Zenodo bulk.

T4a 720575940632008007 / VFB_fw077172
T4c 720575940616224414 / VFB_fw091869
T5a 720575940625571465 / VFB_fw056211
T5c 720575940617782941 / VFB_fw077474

اجرا: `python v229_recovery_runner.py --route all`

هیچ fallback جعلی یا نورون مشابه پذیرفته نمی‌شود. Route 3 در صورت schema نامطمئن عمداً FAIL می‌دهد.
