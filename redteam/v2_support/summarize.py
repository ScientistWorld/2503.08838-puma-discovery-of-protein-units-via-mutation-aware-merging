"""Read-only audit analysis; never used to construct or tune candidates."""
import json
from pathlib import Path
from statistics import mean, pstdev

root = Path('/home/user')
r = root / 'redteam'
cases = json.loads((r / 'v2_support/cases.json').read_text())
result = {}
for name in cases:
    p = r / name / 'rank.json'
    receipt = r / name / 'run_receipt.json'
    if p.exists():
        result[name] = json.loads(p.read_text())
    elif receipt.exists():
        result[name] = {'failed_run': json.loads(receipt.read_text())}
seed_scores = [result[f'v2_reference_seed{s}']['absolute_score'] for s in (7, 17, 29)
               if 'absolute_score' in result.get(f'v2_reference_seed{s}', {})]
report = {'cases': result, 'seed_scores': seed_scores}
if seed_scores:
    report['seed_summary'] = {'mean': mean(seed_scores), 'std_population': pstdev(seed_scores),
                              'min': min(seed_scores), 'max': max(seed_scores), 'spread': max(seed_scores) - min(seed_scores)}
(r / 'v2_support/summary.json').write_text(json.dumps(report, indent=2))
for name, score in result.items():
    print(f"{name:42} S={score.get('absolute_score', 'FAILED')} delta={score.get('rank_delta', 'FAILED')} valid={score.get('valid')}")
print('SEEDS', report.get('seed_summary'))
