"""学习功能接口：单词讲解。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.schemas import WordRequest, WordResponse
from ..services.study_service import StudyService
from .deps import get_study_service

router = APIRouter(tags=["学习"])


@router.post("/study/word", response_model=WordResponse, summary="学习功能：单词讲解")
def explain_word(
    payload: WordRequest,
    service: StudyService = Depends(get_study_service),
) -> WordResponse:
    explanation = service.explain(payload.word)
    return WordResponse(word=payload.word.strip(), explanation=explanation)
