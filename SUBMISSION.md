# Nộp bài (hạn 23:59 cùng ngày)

**Người nộp bài** · Le Gia Hung

1. Kiểm tra lịch sử của `feature/d09` có hai commit theo thứ tự v0 (M0–M4) và v1 (M5–M7).
2. Push nhánh bằng `git push -u origin feature/d09`.
3. Nộp PR với nhánh nguồn `feature/d09` và nhánh đích `main` trong cùng fork Day 9. Kiểm tra hai job `eval-gate` và `eval-gate-v2` trong PR. [PR #2 của bài nộp](https://github.com/LeGiaHung29805/K5-Day09-LeGiaHung-03713-Evaluation-and-Failure-Analysis/pull/2).

Giảng viên chấm commit cuối trước 23:59.

## Core (nên xong trước 17:00)
- [ ] `src/lab9/{stats,graders,evalset}.py` đã hoàn thành TODO M1–M4
- [ ] `src/data/eval/eval_set_v1.jsonl` có `failure_modes`, `labels_v1.json` tách riêng
- [ ] `docs/failure_taxonomy.md`, `docs/trace_case.md` (1 case + regression test), `docs/judge_audit.md`, `docs/eval_card.md`, `docs/PRD_v1.1.md`
- [ ] `src/reports/baseline_v1.json`, `eval_fixed.json`, `eval_seeded_regression.json` (sinh bằng script)
- [ ] `harness_map.yaml` có section `eval` (mẫu: `src/harness_map.eval.yaml`)
- [ ] Job `eval-gate` xanh; dán output gate exit 1 của `seeded_regression` vào mô tả PR

## Advanced / Expert (tới 23:59)
- [ ] `config/fm_map.yaml`, `config/metric_spec_v2.yaml` (slices, `pass_hat_5`, metric FM-08), `stats.pass_at_k/pass_hat_k`, `gate.slice_check`, `gate.integrity_check`
- [ ] `src/data/eval/eval_set_v2.jsonl` + `labels_v2.json` (sinh bằng `evalset --v2 --build`)
- [ ] `src/reports/baseline_v2.json` (sinh bằng script) → job `eval-gate-v2` chạy và xanh
- [ ] Mô tả PR: output `lab9.mutation` (scorecard + `--aa`) và 4 dòng `exit 1` của các trap
- [ ] `docs/eval_card.md` thêm mục v2: ngưỡng chọn từ A/A, slice nào bắt lỗi nào, và giới hạn cỡ mẫu (bug 1/3 seed không phát hiện ổn định với 5 seed)
