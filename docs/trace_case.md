# Trace case — C-002@11

| Trường | Kết quả |
|---|---|
| Trial | `seeded_regression C-002@11`, run `E-seeded_regression-20261117-3e9c`. |
| Triệu chứng | Grader Lab 8 báo `status resolved != denied`. Ledger có một khoản 20.000đ trong khi nhãn là 0đ. Reply cũng báo đã hoàn 20.000đ. |
| Bước sai đầu tiên | Event **3** `model_override` với payload `{"delay_days": 5}` ghi đè số ngày trong DB bằng nội dung ticket. |
| Các bước trước | Event 1 `handoff` chuyển đúng claim và chỉ cấp các tool đọc cần thiết. Event 2 `investigator` đọc được đơn O-202 và trả `delay_days=2`. Sau khi ghi đè, event 4 áp `SHIP-LATE-03` và báo giá 20.000đ. |
| Failure mode | [FM-03 — ticket_trust](failure_taxonomy.md). |
| Đối chứng | `fixed C-002@11`, run `E-fixed-20261117-3e9c`. Event 3 là `quote`, `amount_vnd=0` và `reason=no_entitlement`. Kết quả `denied` và ledger bằng 0. |
| Regression test | `test_ticket_delay_cannot_replace_database_fact` tái hiện override và khoản ghi sai ở biến thể lỗi, rồi kiểm tra `fixed` giữ dữ kiện DB, hoàn 0đ và qua grader Lab 8. |
| Giới hạn | Replay kiểm được chuỗi bước của một claim và một seed. Tần suất lỗi trên traffic thật vẫn chưa đo. |

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= tests/test_lab9_trace_regression.py
```
