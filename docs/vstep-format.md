# VSTEP.3–5: format và quy ước của ứng dụng

VSTEP.3–5 là **một bài thi đa bậc**. Không chọn B1/B2/C1 làm độ khó đề. Nguồn cấu trúc: Quyết định 729/QĐ-BGDĐT; [mô tả format của ĐH Ngoại ngữ – ĐHQGHN](https://vstep.vnu.edu.vn/test-format/) và [trang công bố định dạng/đề minh họa](https://vstep.vnu.edu.vn/dinh-dang-de-thi-vstep-3-5/). Bộ đề trong ứng dụng là nội dung tự biên soạn, không sao chép kho đề chính thức.

| Kỹ năng | Cấu trúc công khai | Quy ước triển khai của sản phẩm |
| --- | --- | --- |
| Writing | 60 phút; Task 1 thư/email khoảng 120 từ, trọng số 1/3; Task 2 luận khoảng 250 từ, trọng số 2/3 | Hiển thị yêu cầu ít nhất 120/250 từ; gợi ý phân bổ 20/40 phút. Task 1 dùng thư đến 60–120 từ, 2–4 nhu cầu giao tiếp được lưu kín; Task 2 dùng stimulus ngắn và yêu cầu viết cho người đọc có học vấn. |
| Speaking | Khoảng 12 phút; Social Interaction với hai chủ đề/3–6 câu; Solution Discussion với ba lựa chọn; Topic Development có ý gợi ý, ý riêng và thảo luận | Mặc định 3/4/5 phút, cấu hình bằng `SPEAKING_PART{1,2,3}_SECONDS`; thời lượng hướng dẫn, không tự cắt bản ghi. Part 1 gồm hai chủ đề; Quick Practice luyện một câu. Follow-up Part 3 chỉ mở sau bài nói chính. |
| Reading | 60 phút; 4 bài đọc, 40 câu trắc nghiệm. Trang format tiếng Anh của ULIS công bố khoảng 1.900–2.500 từ | Blueprint sản phẩm chọn **1.900–2.050 từ**, 10 câu/bài, ít nhất ba chủ đề. Đây là khoảng hẹp được chọn cho simulator, không khẳng định là giới hạn chính thức. |

Reference dùng chung nằm trong `backend/app/vstep_reference/`. Nhóm ACCESSIBLE/MODERATE/CHALLENGING/ADVANCED chỉ cân bằng câu đọc nội bộ, không tương đương nhãn B1/B2/C1 và không trả về API làm bài.

## Chấm điểm và học sau bài thi

- Writing: Task Fulfillment, Organization, Vocabulary, Grammar; evidence → calibration → feedback → Vocabulary Coach → correction. Thang luyện tập bằng trọng số giữa bốn tiêu chí là mô hình sản phẩm; không tuyên bố có rubric giám khảo mật. Mỗi Task chỉ hiển thị **Điểm AI ước tính** và không suy ra bậc. Đủ hai Task mới tính `(Task1 + Task2 × 2) / 3` và tùy chọn “Năng lực Writing tham khảo”.
- Speaking: Grammar, Vocabulary, Pronunciation, Fluency, Structures/Coherence & Cohesion trọng số bằng nhau trong mô hình hiện tại. Phát âm và độ trôi chảy phải có bằng chứng audio; không đoán lỗi âm từ transcript. Thiếu hoặc thiếu tin cậy thì không kết luận lỗi cụ thể.
- Reading: so sánh lựa chọn với answer key bằng code; điểm luyện tập `đúng / tổng × 10`, không dùng LLM chấm đúng/sai hay tuyên bố bảng quy đổi chính thức.
- Không có gợi ý từ vựng, dịch, chữa câu hay đáp án trước khi nộp. Bài đầy đủ cũng không có thử thách gợi ý dùng lại từ đã học. Học từ và phát âm mở sau bài làm.

Điểm AI phục vụ luyện tập, không phải chứng nhận VSTEP. Đề, đáp án và điểm lịch sử được giữ; bản chấm mới chỉ thay thế khi người học chủ động yêu cầu chấm lại, bản trước được lưu revision. Những đề cũ chưa được kiểm định vẫn xem được qua phiên cũ nhưng không tự vào ngân hàng đã kiểm định.
