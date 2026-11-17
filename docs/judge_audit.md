# Judge audit

`FAIL` là lớp dương. Mỗi tiêu chí dùng 100 case replay với nhãn người.

| Tiêu chí | TP / FP / FN / TN | κ | Precision | Recall | Tỷ lệ lỗi quan sát → hiệu chỉnh | Quyết định |
|---|---|---:|---:|---:|---|---|
| `tone_ok` | 24 / 4 / 6 / 66 | 0,757 | 0,857 | 0,800 | 28% → 30% | Qua sàn κ ≥ 0,6, P ≥ 0,8, R ≥ 0,7. Dùng để đánh giá tone trên replay. |
| `helpful` | 9 / 0 / 21 / 70 | 0,375 | 1,000 | 0,300 | 9% → 30% | Loại khỏi gate. |

## Audit bất đồng

| Case | Judge | Người | Kết luận đối chiếu | Thay đổi rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Theo người. Cách xưng hô “em/anh” kèm “nha” quá thân mật cho mẫu hỗ trợ. | Cho ví dụ FAIL với xưng hô thân mật, dù câu có lời nhờ lịch sự. |
| H-029 | PASS | FAIL | Theo người. Cụm “không cần nhắn thêm” gạt yêu cầu hỗ trợ của khách. | Xem lời chặn khách tiếp tục trao đổi là dấu hiệu FAIL. |
| H-042 | FAIL | PASS | Theo người. Reply báo kết quả và thời gian nhận tiền bằng giọng lịch sự. | Cho ví dụ PASS với thông báo ngắn, đủ kết quả và bước tiếp theo. |
| HL-015 | PASS | FAIL | Theo người. Reply báo 55.000đ, ghi chú ledger là 40.000đ. | Bắt buộc đối chiếu số tiền với ledger bằng code. |
| HL-016 | PASS | FAIL | Theo người. Reply báo 55.000đ, ledger 35.000đ. Lời xin lỗi dài che mất sai lệch. | Chấm tính đúng của số tiền trước khi chấm văn phong. |
| HL-020 | PASS | FAIL | Theo người. Reply báo 90.000đ khi ledger ghi 120.000đ. | Kiểm sai lệch theo cả hai hướng. |
| HL-047 | PASS | FAIL | Theo người. “Ok bạn … xử lý rồi nhé” sai chuẩn xưng hô và mơ hồ về kết quả. | Ghi rõ chuẩn xưng hô và yêu cầu nêu trạng thái hoặc hành động tiếp theo. |

`helpful` bỏ sót 21/30 lỗi. Rogan–Gladen điều chỉnh ước lượng tỷ lệ lỗi tổng thể, còn các verdict sai ở từng claim vẫn giữ nguyên. Cần một bộ reply mới gắn nhãn người để đo lại sau khi cập nhật rubric. Những lỗi tiền và approval trong gate dùng grader code.
