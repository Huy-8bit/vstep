from collections import defaultdict

from app.db.base import utcnow
from app.models.reading import ReadingResult


def practice_score(correct: int, total: int) -> float:
    return round(correct / total * 10, 2) if total else 0


def breakdown(items):
    result = []
    for key, answers in items.items():
        correct = sum(a.is_correct is True for a in answers)
        answered = sum(a.selected_answer is not None for a in answers)
        result.append(
            {
                "key": key,
                "total": len(answers),
                "correct": correct,
                "answered": answered,
                "accuracy": round(correct / len(answers) * 100, 1),
                "time_spent_seconds": sum(a.time_spent_seconds for a in answers),
            }
        )
    return result


def strategy_feedback(types, passages, unanswered):
    feedback = []
    if unanswered:
        feedback.append(
            {
                "kind": "coverage",
                "title_vi": f"Bạn bỏ trống {unanswered} câu",
                "explanation_vi": "Dành một lượt cuối để kiểm tra navigator và xử lý các câu chưa trả lời trước khi nộp.",
                "question_type": None,
            }
        )
    ranked = sorted(types, key=lambda row: (row["accuracy"], -row["total"]))
    if ranked and ranked[0]["accuracy"] < 100:
        weak = ranked[0]
        feedback.append(
            {
                "kind": "weakness",
                "title_vi": f"Ưu tiên luyện {weak['key']}",
                "explanation_vi": f"Bạn đúng {weak['correct']}/{weak['total']} câu dạng này ({weak['accuracy']}%). Đọc lại bằng chứng và so sánh từng phương án gây nhiễu.",
                "question_type": weak["key"],
            }
        )
        strong = ranked[-1]
        if strong["accuracy"] > weak["accuracy"]:
            feedback.append(
                {
                    "kind": "strength",
                    "title_vi": f"Kết quả tốt hơn ở dạng {strong['key']}",
                    "explanation_vi": f"Bạn đúng {strong['correct']}/{strong['total']} câu. Tiếp tục áp dụng cách xác định thông tin trong bài cho các dạng còn lại.",
                    "question_type": strong["key"],
                }
            )
    elif ranked:
        feedback.append(
            {
                "kind": "strength",
                "title_vi": "Bạn trả lời đúng toàn bộ bài này",
                "explanation_vi": f"Bạn đúng {sum(row['correct'] for row in ranked)}/{sum(row['total'] for row in ranked)} câu. Hãy thử một bài đọc chưa làm để tiếp tục theo dõi khả năng đọc hiểu.",
                "question_type": None,
            }
        )
    measured = [p for p in passages if p["time_spent_seconds"] > 0]
    total_time = sum(p["time_spent_seconds"] for p in measured)
    if len(measured) > 1 and total_time:
        slow = max(measured, key=lambda p: p["time_spent_seconds"])
        share = slow["time_spent_seconds"] / total_time
        if share > 0.5:
            feedback.append(
                {
                    "kind": "timing",
                    "title_vi": "Cân đối thời gian giữa các bài đọc",
                    "explanation_vi": f"Khoảng {share:.0%} thời gian đang xem câu hỏi được ghi nhận ở một passage. Hãy đánh dấu câu khó và quay lại sau. Đây là thời gian ước lượng từ trình duyệt.",
                    "question_type": None,
                }
            )
    return feedback


class ReadingScoringService:
    def finalize(self, session, expired=False):
        if session.result:
            return session.result
        submitted = session.expires_at if expired else utcnow()
        types, passages = defaultdict(list), defaultdict(list)
        for answer in session.answers:
            answer.is_correct = (
                None
                if answer.selected_answer is None
                else answer.selected_answer == answer.question.correct_answer
            )
            types[answer.question.question_type].append(answer)
            passages[answer.question.passage_id].append(answer)
        correct = sum(a.is_correct is True for a in session.answers)
        incorrect = sum(a.is_correct is False for a in session.answers)
        unanswered = session.question_count - correct - incorrect
        by_type, by_passage = breakdown(types), breakdown(passages)
        session.status, session.submitted_at = ("EXPIRED" if expired else "SUBMITTED"), submitted
        session.result = ReadingResult(
            correct_count=correct,
            incorrect_count=incorrect,
            unanswered_count=unanswered,
            accuracy=round(correct / session.question_count * 100, 1),
            score=practice_score(correct, session.question_count),
            duration_seconds=max(0, int((submitted - session.started_at).total_seconds())),
            question_type_breakdown=by_type,
            passage_breakdown=by_passage,
            strategy_feedback=strategy_feedback(by_type, by_passage, unanswered),
        )
        return session.result
