# V237 — Credential Boundary Plan

Status: PLANNED, not yet credentialized.

## Read-only discovery boundary

The next service bridge must test Supabase and Neon from inside GitHub Actions only when credentials are actually configured there. The probe must never write database state, create branches, change auth, deploy functions, or expose secrets.

## Required evidence

- Supabase Management API project enumeration succeeds with an Actions secret.
- Neon API project enumeration succeeds with an Actions secret, optionally scoped by organization.
- Missing credentials remain UNKNOWN rather than PASS or FAIL.
- HTTP or network errors become FAIL.
- The evidence artifact contains only status, HTTP status, and counts; never tokens, connection strings, project names, or project IDs.

## Current boundary

ChatGPT-native Supabase currently exposes no projects through either connected account link. Neon is connected but requires an explicit project ID. Therefore neither service is currently proven as GitHub Actions credentialed.
