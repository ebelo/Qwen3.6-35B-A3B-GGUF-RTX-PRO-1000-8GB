# Chronological progression and matched interaction test

Measured on 8 November 2026, on the system and exact composed model documented in [README.md](README.md). All configurations use llama.cpp b12201 (`a2b301831`), fixed context 65,536, eight threads, Flash Attention, q8_0 attention caches, batch 512 and microbatch 256. These are configuration comparisons on one runtime, not benchmarks of historical binaries.

## Chronological progression

The upstream contributions were merged in this order: [MTP #22673](https://github.com/ggml-org/llama.cpp/pull/22673) on 16 May 2026, [expert cache #29887](https://github.com/ggml-org/llama.cpp/pull/29887) on 7 October, then [CPU miss execution #30966](https://github.com/ggml-org/llama.cpp/pull/30966) on 7 November.

| Configuration | Harmonic tokens/s | Change from preceding stage |
|---|---:|---:|
| Automatic static fit, no MTP | 30.57 | Baseline |
| Automatic static fit + MTP2 | 35.62 | +16.5% |
| Dynamic cache 4096 MiB + MTP2, CPU share 0 | 34.26 | -3.8% |
| Dynamic cache 4096 MiB + MTP2, CPU share 0.95 | 47.90 | +39.8% |

The complete strategy gained **56.7%** over static fitting without MTP. Incremental gains depend on already-enabled features; this order does not allocate independent feature credit. The cache stage changes weight placement as well as caching. Static stages use `--fit on --fit-target 1024`; dynamic stages use `--cpu-moe -ngl 99 --fit off`. Baseline/MTP block rates shifted by about 10%.

[chronological-controls.csv](chronological-controls.csv) contains the Qwen subset: eight fresh servers, eight 256-token warmups and 24 measured responses, six per stage. Three synthetic workloads (explanation, Python code, workflow summary) each generate 768 tokens. Block 1 runs the stages forward and block 2 in reverse. This subset came from a three-model experiment whose model order was also reversed between blocks; other models' observations are not published or pooled here.

## Matched MTP × CPU miss-share comparison

This is a fresh experiment, with no observations borrowed from the chronology or earlier screens. The expert cache remains enabled at 4096 MiB in all four cells.

| Cell | CPU miss share | MTP | Harmonic tokens/s | Measured range | Block 1 / block 2 |
|---|---:|---|---:|---:|---:|
| B | 0 | off | 30.51 | 29.27–31.94 | 30.38 / 30.64 |
| C | 0.95 | off | 32.67 | 30.50–33.83 | 33.07 / 32.27 |
| D | 0.95 | max 2 draft tokens | 46.11 | 43.21–51.35 | 43.96 / 48.47 |
| E | 0 | max 2 draft tokens | 34.47 | 31.41–37.38 | 36.64 / 32.55 |

- MTP gains **13.0%** at CPU share 0 and **41.1%** at share 0.95.
- CPU miss handling gains **7.1%** without MTP and **33.8%** with MTP.
- Together, MTP and CPU miss handling gain **51.1%** over neither feature, with expert caching held enabled.

Both blocks show a positive interaction, with material variability: MTP gains at share 0 were 20.6% and 6.2%; at share 0.95, 32.9% and 50.2%. This is descriptive evidence on one laptop and three workloads, not a population-level statistical result or a demonstrated mechanism. Because cache stays on, it is not a three-way factorial test. Share 0 still uses the cache and uploads misses for GPU execution; it is not the cache-disabled static baseline.

[factorial-controls.csv](factorial-controls.csv) contains eight fresh servers in BCDE / EDCB order, eight 256-token warmups and 24 measured 768-token responses, six per cell. Model, sampling, input workloads, runtime, cache, context and thread settings were fixed. Response-level draft and acceptance counters confirmed active MTP in D/E.

## Evidence, reproducibility and execution caveats

Both CSVs are allowlisted timing/configuration projections of the saved Qwen measurements, including warmups. They exclude prompts, answers, timestamps, host identifiers, raw response/request hashes and private paths. Harmonic means exclude warmups; use `n / sum(1 / decode_tps)` over the appropriate experiment/stage. All observations were retained; experiments must not be pooled or substituted into each other's baselines. No inference was rerun for this documentation update. Original local raw requests, responses, settings, telemetry and reconciliation records remain retained.

Chronological execution produced all responses before an erroneous final expected-count guard failed. Independent reconstruction verified the complete parent experiment (96 responses), settings and postflight cleanup; no measurements were repeated. The factorial harness likewise completed all 32 responses before a final listener-cleanup assertion failed. Subsequent read-only postflight found no workers or listener, without an additional kill. The cause of that listener observation is unknown. Raw timing/request reconciliation and telemetry coverage checks passed; these administrative failures were retained rather than hidden.

These are short-input decode-throughput comparisons, not end-to-end latency, filled-context throughput, answer-quality equivalence or a universal optimum. Runtime placement, expert routes, cache history and hardware clocks can affect performance. The retained launcher configuration is unchanged.
