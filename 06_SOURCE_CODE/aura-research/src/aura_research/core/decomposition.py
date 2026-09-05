from .question import ResearchQuestion
class QuestionDecomposer:
    def decompose(self, q: ResearchQuestion) -> list[str]:
        return [q.text.strip()] if q.text.strip() else []
