TYPES = {
    "detail": ("DETAIL", "Tìm thông tin chi tiết"),
    "main_idea": ("MAIN_IDEA_OR_TITLE", "Ý chính và tiêu đề"),
    "vocabulary": ("VOCABULARY_IN_CONTEXT", "Từ vựng trong ngữ cảnh"),
    "reference": ("REFERENCE", "Từ quy chiếu"),
    "inference": ("INFERENCE", "Suy luận từ bằng chứng"),
    "purpose": ("AUTHOR_PURPOSE", "Mục đích tác giả"),
    "attitude": ("AUTHOR_ATTITUDE", "Thái độ tác giả"),
    "tone": ("TONE", "Giọng điệu"),
    "negative_detail": ("NEGATIVE_DETAIL", "Thông tin không được đề cập"),
    "sentence_meaning": ("QUOTE_OR_SENTENCE_INTERPRETATION", "Hiểu ý nghĩa câu"),
    "sentence_insertion": ("SENTENCE_INSERTION", "Chèn câu vào đoạn"),
    "paragraph_completion": ("PARAGRAPH_OR_PASSAGE_COMPLETION", "Hoàn thành đoạn văn"),
    "organization": ("ORGANIZATION", "Cấu trúc bài đọc"),
}
CONCEPTS = {key: label for key, label in TYPES.values()}
