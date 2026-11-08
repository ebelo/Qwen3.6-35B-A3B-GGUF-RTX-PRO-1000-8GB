[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=18290,[int]$Tokens=768,
      [string]$Output=(Join-Path $PSScriptRoot 'benchmark-results'))
$ErrorActionPreference='Stop'
$base = "http://127.0.0.1:$Port"
New-Item -ItemType Directory -Force $Output | Out-Null
$cases=@(
@{name='explain';text='Explain how operating systems schedule tasks, manage memory, and handle concurrent disk requests. Give detailed examples and discuss tradeoffs.'},
@{name='code';text='Write a Python implementation of an LRU cache with get and put operations, constant time complexity, capacity validation, and tests. Explain the invariants and edge cases.'},
@{name='summary';text=(('The warehouse receives shipments each morning. Every shipment has a unique identifier, supplier, quantity and timestamp. Workers scan items before storage. Failed scans enter a review queue. Inventory updates must be atomic and duplicate shipments must not be counted twice. Daily reports track discrepancies and delivery delays. ' * 24)+' Summarize the workflow and propose a concrete recovery procedure for duplicate events and interrupted inventory updates.')}
)

$rows=@()
foreach ($case in (@(@{name='warmup';text='Explain the purpose of databases, indexes and transactions.'})+$cases)) {
    $templateBody=@{messages=@(@{role='user';content=$case.text});add_generation_prompt=$true;chat_template_kwargs=@{enable_thinking=$false}}|ConvertTo-Json -Depth 10
    $templ=Invoke-RestMethod "$base/apply-template" -Method Post -ContentType application/json -Body $templateBody -TimeoutSec 30
    $n=if($case.name -eq 'warmup'){256}else{$Tokens}
    $body=@{prompt=$templ.prompt;n_predict=$n;temperature=0;seed=42;ignore_eos=$true;cache_prompt=$false;stream=$false}|ConvertTo-Json -Depth 10
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $r=Invoke-RestMethod "$base/completion" -Method Post -ContentType application/json -Body $body -TimeoutSec 600
    $watch.Stop()
    if($r.timings.predicted_n -ne $n){throw 'Unexpected generated length'}
    $t=$r.timings
    $rows += [pscustomobject]@{workload=$case.name;tokens=$t.predicted_n;decode_tps=$t.predicted_per_second;decode_ms=$t.predicted_ms;prompt_tokens=$t.prompt_n;prefill_tps=$t.prompt_per_second;wall_ms=$watch.Elapsed.TotalMilliseconds}
    $rows | Export-Csv (Join-Path $Output 'measurements.csv') -NoTypeInformation
}
$rates=@($rows | Where-Object workload -ne 'warmup' | ForEach-Object { [double]$_.decode_tps })
$inverse=($rates | ForEach-Object { 1.0 / $_ } | Measure-Object -Sum).Sum
Write-Output ("Harmonic mean decode tokens/s: {0:N2}" -f ($rates.Count/$inverse))
