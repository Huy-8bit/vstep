# Vocabulary Coach

Vocabulary Coach học từ Writing, Speaking và Reading **sau khi nộp/chấm**. Gợi ý ưu tiên cụm từ, collocation và cách diễn đạt tự nhiên; không thay từ thường bằng từ hiếm để tạo vẻ nâng cao.

## Nguồn và lưu trữ

- Writing: lỗi/câu gốc, cơ hội diễn đạt, 5–8 cụm từ hữu ích cho chủ đề, lỗi lặp lại có bằng chứng từ ≥2 bài khác nhau. Pipeline chuẩn bị gợi ý sau feedback và trước correction; lỗi AI ở pha này không đổi điểm.
- Speaking: transcript và lỗi dùng từ, cách nói tự nhiên phù hợp phần thi. Không dùng transcript làm bằng chứng phát âm. Từ đã lưu có liên kết tới Pronunciation Coach dùng ghi âm thật.
- Reading: chỉ khi đã nộp, chọn từ/cụm trong đoạn rồi xem nghĩa trong ngữ cảnh và lưu; có thể yêu cầu năm cụm từ của passage. Câu trích và từ được kiểm tra có trong passage thuộc phiên của chính người học.

`vocabulary_recommendation_batches` cache gợi ý theo người dùng, nguồn/phiên bản nội dung, model và prompt version. `user_vocabulary_items` chứa nghĩa, nghĩa trong ngữ cảnh, register, collocations, patterns, câu gốc/cải thiện, ví dụ, lý do học, kỹ năng/chủ đề nguồn và lịch ôn. `vocabulary_item_sources` giữ nhiều nguồn của một mục đã lưu. Lưu trùng không đặt lại tiến độ. `vocabulary_reviews` lưu từng lượt, câu trả lời và kết quả; đáp án mẫu của bài ôn không trả trước khi gửi câu trả lời.

## Học và ôn

`/vocabulary`: đến hạn hôm nay, từ mới, đang học/đã quen, đã nhớ, lỗi thường gặp, lịch sử ôn; lọc theo kỹ năng/chủ đề và tìm cụm từ.

| Dạng | Cách đánh giá |
| --- | --- |
| Nghĩa Việt → nhớ cụm Anh | Khớp cụm mục tiêu hoặc biến thể được biên soạn; chuẩn hóa hoa/thường và dấu câu |
| Điền chỗ trống | Khớp cụm được bỏ khỏi ví dụ ngữ cảnh |
| Chọn collocation | Một lựa chọn mục tiêu và ba distractors |
| Sửa câu/cụm cũ | Khớp cách sửa hoặc natural options; chỉ mở khi có lỗi gốc và cách sửa |
| Đặt câu mới | AI kiểm tra dùng cụm tự nhiên đúng nghĩa; độ tin cậy <0,8 giữ nguyên mức ghi nhớ |

Bốn dạng đầu là luyện nhớ cách diễn đạt đã học, không phải bộ chấm mọi câu tiếng Anh đúng có thể có. Feedback giải thích khi câu trả lời chưa khớp, không coi đó là lỗi ngữ pháp chính thức.

Mức ghi nhớ: NEW → LEARNING → FAMILIAR → MASTERED. Lượt đúng đến hạn tăng bước; lượt sai lùi bước và hẹn lại ngày sau. Làm lặp trước hạn không tăng mastery. `VOCABULARY_REVIEW_DAYS=1,3,7,14,30` cấu hình lịch ôn, không phải phương pháp chính thức của VSTEP. Câu trả lời/lịch ôn được cập nhật cùng transaction và chống submit lặp.

Dashboard có số mục đã lưu/đã luyện/đã nhớ, lỗi lặp thực tế, xu hướng chọn từ/collocation dựa trên lượt ôn và chủ đề luyện nhiều. Không bịa nhận xét tiến bộ khi thiếu dữ liệu. Sau bài Practice cùng chủ đề, hệ thống gợi ý thử đặt câu với tối đa ba cụm đã học; Full Exam không có vòng gợi ý dùng lại này.

API chính: `/vocabulary/recommendations`, `/items`, `/items/{id}/reviews`, `/reviews/{id}/answer`, `/progress`, `/history`, `/reuse`. Mọi truy cập kiểm tra user và trạng thái nguồn. Không có API key vẫn xem/lưu gợi ý đã tạo, đọc sổ từ và làm bốn dạng ôn khớp đáp án; gợi ý mới và đặt câu cần AI.
