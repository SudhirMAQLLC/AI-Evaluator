from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from app.services.assignment_evaluator import assignment_evaluator

router = APIRouter()

@router.post("/evaluate", response_model=dict)
async def evaluate_assignment(
    assignment_file: UploadFile = File(...),
    solution_zip: UploadFile = File(...),
    model: str = Form("tinyllama")
):
    """Evaluate a student solution against an assignment using LLM and open-source tools."""
    try:
        result = await assignment_evaluator.evaluate(assignment_file, solution_zip, model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 