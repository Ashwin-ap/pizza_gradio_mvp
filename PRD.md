# PRD — SliceMatic Ordering System (Stage 2 MVP)

> **Product:** SliceMatic pizza ordering app · **Stage:** 2 — Working MVP on Gradio
> **Companion docs:** `STAGE2_PLAN.md` (build approach), `PizzaFlow_Assignment_Brief_FDE.md` (spec), `SliceMatic_Business_Economics.md` (pricing reference)

---

## 1. Executive Summary

A single-file **Python Gradio** application that digitises ordering for SliceMatic, a single-outlet pizza delivery brand in New Ashok Nagar, Delhi. It replaces phone-based ordering with a guided, step-by-step flow: customer intake → quantity → menu selection → itemised bill → payment → confirmation. Menu data loads from three `.txt` files at runtime, pricing applies a quantity discount and 18% GST, and every completed order is persisted to a parseable log. The MVP prioritises **correctness and robustness over aesthetics** — it must run end-to-end without crashing on any valid or invalid input.

## 2. Mission

Give SliceMatic a reliable digital intake system that prices orders correctly, validates every input defensively, and records each order for later business analysis — proving the core ordering logic before it is rebuilt as a full-stack product in Stage 3.

## 3. Target Users

| User | Need |
|---|---|
| **Customer** (urban, 18–35, within ~4 km) | Place a customisable pizza order quickly with clear pricing and a confirmed bill. |
| **Counter / billing staff** | A predictable flow that never crashes and produces an accurate, itemised bill. |
| **Owner / analyst** | A clean, parseable orders log to extract revenue, popular items, and demand patterns. |
| **Grader (evaluator)** | A system that handles every edge case, loads swapped menu files, and prices exactly per spec. |

## 4. MVP Scope

### 4.1 In Scope
- **Customer intake** — name (letters/spaces, 2–40 chars) and Indian mobile (10 digits, starts 6/7/8/9), with specific error messages and re-prompts.
- **Quantity** — integer 1–10; automatic 10% discount at qty ≥ 5; reject > 10.
- **Menu selection** — one base + one pizza + one topping, loaded from `Types_of_Base.txt`, `Types_of_Pizza.txt`, `Types_of_Toppings.txt` at startup; selection by item number.
- **Bill** — itemised, rendered in `gr.HTML`; shows unit price, quantity, subtotal, discount, GST @ 18% on post-discount total, and final payable.
- **Payment** — exactly three modes (Cash / Card / UPI) with a per-mode confirmation message.
- **Order persistence** — append each completed order to `orders_log.txt` in a pipe-separated, block-delimited format with all required fields.
- **Defensive handling** — all 8 mandated edge cases handled with no unhandled exception.

### 4.2 Out of Scope (Stage 3)
Web frontend (Vercel), database (Supabase), admin dashboard/auth, AI features (OpenRouter), multi-topping/cart, accounts, real payments, and delivery tracking.

## 5. Core Patterns

- **Pure logic ⟂ UI** — parsing, validation, pricing, and logging are pure functions with no Gradio import; the Gradio layer is a thin shell. Enables a browser-free test harness.
- **Defense in depth (no crashes)** — (1) `gr.Textbox` for every input so raw strings reach our validators (never `gr.Number`, which silently coerces `2.5`→`2`); (2) explicit validators `raise gr.Error("specific msg")`, which suppresses outputs so the user stays on the same step; (3) a `@safe_handler` decorator converts any unexpected exception into a clean error modal. Launch with `show_error=True`.
- **State-driven wizard** — six `gr.Group`s, one visible at a time; a single per-session `gr.State` order dict threads through handlers (never a module-level global). Forward-only with a "New order" reset.
- **Runtime menu loading** — files parsed defensively (`ID;Name;Price`): strip whitespace, skip blank/malformed lines, validate price is numeric and positive; `N` derived from the parsed list so swapped files of any size work. On load failure, show a clear banner and disable the flow rather than hard-exit.
- **Deterministic pricing** — fixed calc order: `unit = base + pizza + topping` → `subtotal = unit × qty` → 10% discount if qty ≥ 5 → GST 18% on post-discount → final. `float` + `round(…, 2)`; verified against the reference bill (₹3594.87).
- **Parseable persistence** — append-mode write under a `threading.Lock`; one order per block, pipe-separated `key=value` fields, blank line between orders; each item carries `ID:Name:Price` so the log is self-contained after a file swap.

## 6. Non-Functional Requirements

- **Robustness:** zero unhandled exceptions on any input; all 8 edge cases handled.
- **Portability:** runs from one `.py`; `gradio==5.49.1`, Python 3.10–3.12; local launch (`share=False`).
- **Maintainability:** pure-function core with a `test_core.py` covering the golden bill, discount boundary, and edge cases.
- **Resilience to file swap:** no hardcoded menu data; defensive parser tolerant of malformed lines and missing files.

## 7. Success Metrics (Stage 2 Rubric — 30 pts)

| Component | Pts |
|---|---|
| Input validation & error handling (8 edge cases, no crashes) | 8 |
| Menu file loading (runtime, malformed/missing, swap-safe) | 6 |
| Pricing & discount logic (threshold, GST on post-discount, accurate bill) | 7 |
| Payment flow (3 modes, reject invalid, confirmation) | 4 |
| Order logging (parseable, all fields, appended each run) | 5 |

## 8. Deliverables

`app.py` · the 3 menu `.txt` files · sample `orders_log.txt`. Supporting (optional): `requirements.txt`, `test_core.py`, `README.md`.

---

*Assumption:* this PRD scopes the **Stage 2 MVP only**; the Stage 3 full-stack rebuild and AI feature are noted as out of scope (§4.2). Detailed implementation specs live in `STAGE2_PLAN.md`.
