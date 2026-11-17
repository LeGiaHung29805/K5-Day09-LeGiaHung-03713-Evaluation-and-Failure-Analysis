# src/reports/

Mọi lệnh dưới đây chạy trong thư mục `src/`, nên file JSON được ghi vào `src/reports/`.

## Report nộp Lab Day 9

| File | Lệnh tạo |
| --- | --- |
| `baseline_v1.json` | `python -m lab9.eval --shape swarm --out reports/baseline_v1.json` |
| `eval_fixed.json` | `python -m lab9.eval --shape fixed` |
| `eval_seeded_regression.json` | `python -m lab9.eval --shape seeded_regression` |
| `baseline_v2.json` | `python -m lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json` |

Ba report v1 được nộp trong commit v0. Baseline v2 được nộp trong commit v1. [Checklist nộp Day 9](../../SUBMISSION.md).

## Báo cáo của bài gốc Day 8

Nhóm **commit** các file do công cụ của lab sinh ra. Đây là bằng chứng nộp bài:

| File | Lệnh tạo | Bắt buộc |
| --- | --- | --- |
| `benchmark.json` | `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` | Có |
| `crash.json` | `python -m lab8.crash_test --count 20 --out reports/crash.json` | Có |
| `hidden_selfcheck.json` | benchmark trên `student_drop/` (xem `src/README.md`, mục Tự kiểm trên bộ hidden) | Không |
| `bonus_*.json` | script bonus của nhóm | Chỉ khi làm bonus |

Không sửa tay file JSON. Giảng viên chạy lại đúng các lệnh trên trên máy chấm. Số không khớp thì mục Reproducibility mất điểm. `hidden_grade.json` chỉ giảng viên tạo và bị gitignore.
