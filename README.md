# Qwen3.6-35B-A3B on RTX PRO 1000 8 GB — Windows GGUF recipe

A standalone, native-Windows llama.cpp profile measured on **8 November 2026**. Selected longer-validation decode rate: **48.22 tokens/s**. This is a tested profile for one system, not a universal best configuration or a speed guarantee.

Most expert weights remain in system RAM; a GPU expert cache and CPU execution of eligible cache misses make the model usable with 8 GB VRAM. See [CPU miss handling PR #30966](https://github.com/ggml-org/llama.cpp/pull/30966) and [speculative decoding](https://github.com/ggml-org/llama.cpp/blob/b12201/docs/speculative.md).

## Requirements and runtime

- Windows x64, Intel Core Ultra 7 265H (16 reported logical processors), 64 GB system RAM, NVIDIA RTX PRO 1000 Blackwell **Laptop** GPU (8150 MiB VRAM). An 8 GB GPU alone does not establish equivalent performance.
- Recorded runtime: **llama.cpp b12201, commit a2b301831**, CUDA 13.5 Windows x64 build, with available CUDA 13 runtime libraries and a compatible NVIDIA driver.
- Download [llama.cpp b12201 Windows CUDA 13.5 ZIP](https://github.com/ggml-org/llama.cpp/releases/download/b12201/llama-b12201-bin-win-cuda-13.5-x64.zip) and [matching CUDA runtime DLL ZIP](https://github.com/ggml-org/llama.cpp/releases/download/b12201/cudart-llama-bin-win-cuda-13.5-x64.zip), from the [release](https://github.com/ggml-org/llama.cpp/releases/tag/b12201). Extract the executable and DLLs together into `runtime/`. The original test used existing local CUDA 13 DLLs; a clean installation with this matching DLL package has not been benchmarked.
- Check `runtime\llama-server.exe --version`, `--list-devices` and `--help` before loading. The CUDA GPU and `--moe-cache-cpu-share` must be available. A CUDA 12.4 build enumerated no GPU in the recorded environment.
- Run one model at a time. Final measurements used AC power, effective Windows **Best performance** mode and plugged-in PCIe Link State Power Management Off. A Balanced power *plan* can coexist with Best performance *mode*. Firmware thermal mode and maximum hardware power allocation were not independently verified.

[Original model](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) · [GGUF model files](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF). Model and runtime licenses remain upstream; no weights or binaries are distributed here.

### Important: exact Qwen artifact

The benchmark used a **locally composed** MTP GGUF, not the downloadable Unsloth MTP file. It preserved 733 tensors from the base UD-Q4_K_M and added 20 MTP tensors using the MTP header. Exact output: 22,663,387,424 bytes; SHA-256 `ad2c4475849c923233dda2269facec79d3b056de08627ea770a3f6ef6592bf54`.

Download inputs (large files; not included here):

- [Base UD-Q4_K_M, pinned](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/resolve/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf), SHA-256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`.
- [MTP UD-Q4_K_M, pinned](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/resolve/5bc3e238d916f48a861bac2f8a1990a0e9b7e98d/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf), published SHA-256 `0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b`.

Use `Compose-Qwen.py` with Python 3.11 or later to build the exact benchmark artifact from these two files:

```powershell
python .\Compose-Qwen.py --base .\base.gguf --mtp .\mtp.gguf --output .\models\Qwen3.6-35B-A3B-local-base-MTP-Q4_K_M.gguf
```

The composer verifies both input hashes, layout, and output hash. Its parser was checked against the recorded artifact; a fresh full composition has not been rerun for this publication. It needs space for both downloads and the output (roughly 68 GB). The public MTP file can instead be passed with `-Model`, but it is a different base quantization: **48.22 tokens/s was not measured with that alternative**. MTP flags require an MTP-equipped artifact.

At 3072 MiB, eight threads and MTP2, changing CPU miss share 0 to 0.95 increased three-workload screening harmonic mean from 31.04 to 46.45 tokens/s (+49.6%). At share 0.95, disabling MTP gave 32.69 versus 46.45 with MTP2 (+42.1%). Increasing cache to 4096 MiB gave 50.51 in the 384-token screen; longer validation was 48.22. Four draft tokens did not improve the aggregate.

## Launch

The launcher uses repo-relative defaults and accepts absolute paths, including paths with spaces:

```powershell
.\Start-Model.ps1
# Or use files stored elsewhere:
.\Start-Model.ps1 -Runtime "D:\llama\llama-server.exe" -Model "D:\models\Qwen3.6-35B-A3B-local-base-MTP-Q4_K_M.gguf"
```

Run in a PowerShell session permitted by your local script policy. `-PrintCommand` prints one argument per line without starting inference. The foreground server binds **127.0.0.1:18290** only; Ctrl+C stops it. There is no web UI, background service, account integration or remote exposure. Check `http://127.0.0.1:18290/health`; OpenAI-compatible API base is `http://127.0.0.1:18290/v1`. No automatic download is performed. Verify downloaded model hashes with `Get-FileHash -Algorithm SHA256`.

| Selected setting | Value |
|---|---:|
| Expert cache | 4096 MiB |
| CPU miss share | 0.95 |
| CPU / batch threads | 8 / 8 |
| Allocated context | 65,536 tokens |
| Speculation | MTP, maximum 2 tokens |

All profiles use `-ngl 99 --cpu-moe`, one request slot, Flash Attention, q8_0 K/V caches, batch 512, microbatch 256, `--fit off`, Jinja templates and prompt caching requested off. `Start-Model.ps1` contains the full recorded benchmark arguments with only portable paths and configurable port substituted; `profile.json` summarizes the selection. The newly packaged launcher has been command/parse checked, not rebenchmarked. The original main launcher passed health and 64-token generation checks after profile installation.

## Benchmark evidence

| 768-token workload | Server decode tokens/s |
|---|---:|
| OS explanation | 48.82 |
| Python LRU-cache code | 52.69 |
| Synthetic warehouse summary | 43.94 |
| Harmonic mean, warmup excluded | **48.22** |

`results.csv` is an allowlisted numeric projection of the original native-Windows timing rows, including warmups. It excludes prompts, responses, timestamps, machine identifiers and private paths. Source evidence was the complete Windows lab report, recommended configuration JSON and validation measurements dated 2026-11-08; no inference was rerun to publish these repositories.

### Method and reproducibility

Start a fresh server, wait for health, then in a second PowerShell window run:

```powershell
.\Benchmark.ps1
# Screening length used in the original tuning:
.\Benchmark.ps1 -Tokens 384
```

The benchmark sends only bundled synthetic workloads to localhost and writes timing-only CSV under ignored `benchmark-results/`. It does not start or stop the server. It first applies the model's chat template (`enable_thinking=false` requested), runs a separate 256-token warmup, then explanation, coding and repeated-document summary. Qwen/Gemma honored non-thinking templates; LFM retained native reasoning behavior. Measured outputs use temperature 0, seed 42, `cache_prompt=false`, `ignore_eos=true`, and 768 generated tokens. Forcing length is not natural completion and can continue beyond an answer. Summary inputs were approximately 1350–1470 tokens; allocated context was **not filled**.

Aggregate = `3 / (1/r1 + 1/r2 + 1/r3)` using server-reported decode rates, excluding warmup. The server reports 767 timed token intervals for 768-token output, so requested token count divided by decode time is slightly different. These are decode-only rates, not prompt processing or end-to-end response speed; CSV also retains prefill and wall timings.

Across all three models, the investigation recorded 196 requests including warmups, plus three launcher smoke checks. Early raw-prompt median screens and later chat-templated harmonic means are distinct protocols. Longer validation restarted selected candidates and changed model order; this was not randomized repeated crossover testing. Cache history, expert routes, desktop activity and GPU clocks can affect results. No near-limit context throughput, accuracy equivalence of speculative/plain output, hallucination rate or coding success is established. Different models' reasoning behavior makes output-token comparisons imperfect. Reproduce on your own system before drawing broader conclusions.
