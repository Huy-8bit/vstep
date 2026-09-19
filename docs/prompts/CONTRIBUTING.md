# Maintaining the VSTEP Manual AI Prompt Kit

## Purpose

Giữ tài liệu đồng bộ với production, không dùng tài liệu để thiết kế lại grader.

## When to use

Mỗi khi prompt, schema, rubric, deterministic validator, blueprint hoặc behavior đáng kể đổi.

## Required input

- Diff nguồn, phiên bản hiện hành và các prompt thủ công liên quan.

## Optional input

- Kết quả kiểm tra câu trích/schema, feedback người dùng và dữ liệu giám khảo nếu có.

## Quy ước dự án

1. Khi thay đổi prompt production đáng kể, bump **production prompt version** tương ứng trong cùng thay đổi được phép.
2. Cập nhật bản thường, quick, all-in-one, source links và phần Differences. Mỗi block phải đứng độc lập; không yêu cầu người học tự ghép rubric.
3. Cập nhật `reference/prompt-version-map.md`, ngày đồng bộ, commit/hash trong `reference/source-manifest.json`, cùng schema snapshots nếu contract đổi.
4. Nếu prompt hiện chưa có constant version, ghi rõ “unversioned” và source hash; không phát minh version để lấp chỗ trống. Việc thêm constant mới phải được xử lý trong task code phù hợp, không làm lén trong task chỉ viết docs.
5. Không đưa toàn bộ bài anchor/nhãn benchmark vào prompt chấm để vô tình dạy thuộc điểm. Giữ no-score-inflation, independent criteria và evidence thật. Không đưa secret/private environment values vào docs.
6. Kiểm link tương đối, các biến được khai báo, code fences, mọi schema `$ref`, exact exported native schema, full vs part formulas, key=null của import, audio unavailable và JSON wrappers được đánh dấu thủ công. Không gọi API để kiểm tài liệu hoặc tạo generic test suite.
7. Kiểm thực tế bản quick bằng cách thay dữ liệu vào bản sao: không cần sửa rubric hoặc mở file thứ hai. Kiểm toán source không chứng minh chatbot khác sẽ cho điểm giống hệt; ghi đúng giới hạn này.

## Copy-Paste Prompt

```text
Bạn đang review đồng bộ tài liệu VSTEP, không chỉnh production behavior.
================ SOURCE_DIFF ================
{{SOURCE_DIFF}}
=============================================
================ MANUAL_DOC ================
{{MANUAL_DOC}}
=============================================
Đối chiếu source và tài liệu: rubric, schema fields/enums/nullability, validators, weighting/rounding, full vs partial coverage, audio-only criteria, missing-key behavior, versions, source links, quick/all-in-one copies. Không bịa code chưa cung cấp hoặc version không tồn tại. Liệt kê mismatch và thay đổi tài liệu cần làm; phân biệt production behavior với tiện ích manual. Prompt copy-paste phải tự đủ, placeholders rõ và không chứa secrets/hidden-chain-of-thought requests. Đề nghị cập nhật version map/snapshots khi cần; không tuyên bố đã sửa code, gọi API hay kiểm chứng model nếu chưa thực hiện.
```

## Production source

- [Version map](reference/prompt-version-map.md).
- [Source manifest](reference/source-manifest.json).
- [Output schemas](reference/output-schemas.md).

## Differences from production

Đây là quy ước bảo trì tài liệu; không thay model routing, không tự triển khai hoặc ghi đè historical grades. `manual kit 1.0.0` là phiên bản tài liệu, không phải một constant của backend.

## Làm mới native schema mà không gọi API

Dùng môi trường Python của backend. Manifest liệt kê `module`/`class` chính xác. Gọi `model_json_schema(by_alias=False)` cho từng native schema, lưu dưới `docs/prompts/reference/schemas/`, rồi cập nhật schema nhúng trong các block JSON tương ứng và hashes. Các `Manual*` wrappers là contract tài liệu viết rõ trong output-schemas, cần review riêng; không được biến thành production API chỉ để hợp JSON. Import các schema không tạo request OpenAI.
