class WritingFeedbackService:
    def __init__(self, llm):
        self.llm = llm

    async def feedback(self, payload, user_id):
        return await self.llm.writing_feedback(payload, user_id)


class CorrectionService:
    def __init__(self, llm):
        self.llm = llm

    async def correct(self, payload, user_id):
        return await self.llm.writing_corrections(payload, user_id)
