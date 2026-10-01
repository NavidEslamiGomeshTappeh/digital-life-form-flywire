#!/usr/bin/env python3
import socket, ssl, urllib.request
HOSTS=[
    "flyem.mrc-lmb.cam.ac.uk",
    "zenodo.org",
    "github.com",
    "fafbseg-py.readthedocs.io",
]
URLS=[
    "https://flyem.mrc-lmb.cam.ac.uk/",
    "https://zenodo.org/",
]
print("=== V229 NETWORK PROBE ===")
for h in HOSTS:
    try:
        ans=socket.getaddrinfo(h,443,type=socket.SOCK_STREAM)
        ips=sorted({x[4][0] for x in ans})
        print(f"DNS PASS  {h}: {', '.join(ips)}")
    except Exception as e:
        print(f"DNS FAIL  {h}: {type(e).__name__}: {e}")
for u in URLS:
    try:
        req=urllib.request.Request(u,headers={"User-Agent":"V229-Recovery-Probe/2.0"})
        with urllib.request.urlopen(req,timeout=20) as r:
            print(f"HTTPS PASS {u}: {r.status} {r.headers.get('content-type','')}")
    except Exception as e:
        print(f"HTTPS FAIL {u}: {type(e).__name__}: {e}")
print("=== END PROBE ===")
