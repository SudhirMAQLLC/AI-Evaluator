import tempfile
import zipfile
from typing import Any
import os
import requests

# For docx
try:
    import docx
except ImportError:
    docx = None
# For pdf
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
# For ipynb
try:
    import nbformat
except ImportError:
    nbformat = None

class AssignmentEvaluator:
    async def evaluate(self, assignment_file, solution_zip, model="tinyllama") -> dict:
        assignment_text = await self._extract_and_summarize_assignment(assignment_file)
        notebooks = await self._extract_notebooks(solution_zip)
        results = {}
        for nb_name, code_text in notebooks.items():
            feedback = self._evaluate_with_llm(assignment_text, code_text, model, nb_name)
            results[nb_name] = feedback
        return results

    async def _extract_and_summarize_assignment(self, assignment_file) -> str:
        suffix = assignment_file.filename.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.'+suffix) as tmp:
            tmp.write(await assignment_file.read())
            tmp_path = tmp.name
        try:
            if suffix == 'docx' and docx:
                doc = docx.Document(tmp_path)
                text = '\n'.join([p.text for p in doc.paragraphs])
            elif suffix == 'pdf' and PyPDF2:
                with open(tmp_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
            elif suffix == 'txt':
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                text = "Unsupported assignment file type or missing dependency."
        finally:
            os.remove(tmp_path)
        return self._summarize_text(text)

    async def _extract_notebooks(self, solution_zip) -> dict:
        """Extract all .ipynb files and their code cells from the zip. Returns {filename: code_text}."""
        import shutil
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(await solution_zip.read())
            tmp_path = tmp.name
        extracted_dir = tempfile.mkdtemp()
        notebooks = {}
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
            for root, _, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.ipynb') and nbformat:
                        nb_path = os.path.join(root, file)
                        with open(nb_path, 'r', encoding='utf-8') as f:
                            nb = nbformat.read(f, as_version=4)
                            code_blocks = [cell.source for cell in nb.cells if cell.cell_type == 'code']
                            code_text = '\n\n'.join(code_blocks)
                            notebooks[file] = self._summarize_text(code_text)
        finally:
            os.remove(tmp_path)
            try:
                shutil.rmtree(extracted_dir)
            except Exception:
                pass
        return notebooks

    def _summarize_text(self, text: str, max_chars: int = 2000) -> str:
        # Simple stub: truncate to max_chars
        return text[:max_chars] + ('...' if len(text) > max_chars else '')

    def _evaluate_with_llm(self, assignment_text, notebook_code, model="tinyllama", nb_name=None):
        import json as pyjson
        import re
        url = "http://localhost:11434/api/generate"
        prompt = f"""You are an expert notebook evaluator.\n\nAssignment:\n{assignment_text}\n\nStudent Notebook: {nb_name}\n\nPlease provide a short, concise evaluation of this notebook.\n- Your feedback should be direct and to the point.\n- At the end, output the score as: Score: X/10 (on a separate line).\n- Only output the score once, at the end.\n"""
        data = {
            "model": model,
            "prompt": prompt
        }
        try:
            response = requests.post(url, json=data, timeout=120, stream=True)
            response.raise_for_status()
            feedback = ""
            for line in response.iter_lines():
                if line:
                    try:
                        obj = pyjson.loads(line.decode('utf-8'))
                        feedback += obj.get('response', '')
                    except Exception:
                        continue
            # Parse score from feedback
            score_match = re.search(r"Score:\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10", feedback)
            score = float(score_match.group(1)) if score_match else None
            # Remove score line from feedback
            feedback_clean = re.sub(r"Score:\s*[0-9]+(?:\.[0-9]+)?\s*/\s*10", "", feedback, flags=re.IGNORECASE).strip()
            return {"score": score, "feedback": feedback_clean, "notebook": nb_name}
        except Exception as e:
            return {"score": 0, "feedback": f"LLM evaluation failed: {e}", "notebook": nb_name}

assignment_evaluator = AssignmentEvaluator() 