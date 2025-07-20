#!/usr/bin/env python3
"""
GPT-4.1 nano Assignment Evaluator using Puter AI JavaScript Library
Uses Puter AI for intelligent assignment evaluation with correctness checking
Note: This requires running in a browser environment with puter.js
"""

import os
import zipfile
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class GPTEvaluator:
    def __init__(self, api_key: str = None):
        """Initialize the GPT evaluator with API key"""
        self.api_key = api_key or os.getenv('PUTER_API_KEY')
        if not self.api_key:
            raise ValueError("Puter API key is required. Set PUTER_API_KEY environment variable or pass api_key parameter.")
        
        # Puter AI uses JavaScript library, not REST API
        # This evaluator is designed to work with the puter.js library in browser environment
        print("⚠️  Note: Puter AI uses JavaScript library (puter.js) in browser environment")
        print("   Use gpt_streamlit_app.py or puter_demo.html for browser-based evaluation")
        
        # Default assignment briefs (same as Gemini evaluator)
        self.default_briefs = {
            "snowflake": {
                "title": "Snowflake Data Engineering Assignment",
                "description": "Set up a Snowflake environment, ingest data from CSV files, manage data access using masking and RLS policies.",
                "requirements": [
                    "Create Snowflake warehouse",
                    "Create schema",
                    "Create transactions table",
                    "Apply masking policy",
                    "Create stored procedure",
                    "Create task for automation"
                ],
                "expected_outputs": [
                    "Warehouse created",
                    "Schema created", 
                    "Table with transactions data",
                    "Masking policy applied",
                    "Stored procedure created",
                    "Task created"
                ]
            },
            "pyspark": {
                "title": "PySpark Data Processing Assignment",
                "description": "Process large datasets using PySpark, implement data transformations, and create visualizations.",
                "requirements": [
                    "Load data from CSV files",
                    "Perform data cleaning",
                    "Apply transformations",
                    "Create aggregations",
                    "Generate visualizations",
                    "Save processed data"
                ],
                "expected_outputs": [
                    "Clean dataset",
                    "Transformation pipeline",
                    "Aggregation results",
                    "Visualization charts",
                    "Processed data files"
                ]
            },
            "powerbi": {
                "title": "Power BI Dashboard Assignment",
                "description": "Create interactive dashboards and reports using Power BI with data modeling and DAX calculations.",
                "requirements": [
                    "Import data sources",
                    "Create data model",
                    "Write DAX measures",
                    "Design dashboard layout",
                    "Add interactive elements",
                    "Create multiple reports"
                ],
                "expected_outputs": [
                    "Data model",
                    "DAX measures",
                    "Dashboard layout",
                    "Interactive reports",
                    "Documentation"
                ]
            }
        }

    def extract_zip_contents(self, zip_path: str) -> Dict[str, str]:
        """Extract and read all files from ZIP"""
        contents = {}
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if not file_info.is_dir():
                    file_path = file_info.filename
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            contents[file_path] = content
                    except Exception as e:
                        contents[file_path] = f"Error reading file: {str(e)}"
        
        return contents

    def clean_malformed_json(self, text: str) -> str:
        """Simple JSON cleaning for basic malformed patterns"""
        import re
        
        # Basic fixes for common malformed JSON patterns
        # Replace "0:{" with "{"
        text = re.sub(r'\d+:\{', '{', text)
        
        # Add commas between objects
        text = re.sub(r'\}\s*\n\s*\{', '},\n{', text)
        
        return text

    def create_evaluation_prompt(self, assignment_type: str, files_content: Dict[str, str], 
                                assignment_brief: Dict = None) -> str:
        """Create a comprehensive evaluation prompt for GPT"""
        
        # Use default brief if none provided
        if not assignment_brief:
            assignment_brief = self.default_briefs.get(assignment_type, {})
        
        # Format files content
        files_text = "\n\n".join([
            f"=== FILE: {filename} ===\n{content}"
            for filename, content in files_content.items()
        ])
        
        prompt = f"""
You are an expert assignment evaluator for {assignment_type.upper()} assignments. Your primary responsibility is to VERIFY CORRECTNESS - check if the student's solution actually meets the specific requirements stated in the assignment brief.

ASSIGNMENT BRIEF:
Title: {assignment_brief.get('title', 'N/A')}
Description: {assignment_brief.get('description', 'N/A')}

REQUIREMENTS:
{chr(10).join([f"- {req}" for req in assignment_brief.get('requirements', [])])}

EXPECTED OUTPUTS:
{chr(10).join([f"- {out}" for out in assignment_brief.get('expected_outputs', [])])}

STUDENT SUBMISSION FILES:
{files_text}

CRITICAL EVALUATION INSTRUCTIONS:

**STEP 1: REQUIREMENT VERIFICATION (MOST IMPORTANT)**
For each requirement in the assignment brief, you MUST verify:
- Does the code actually implement this specific requirement?
- Are the expected outputs/artifacts present?
- Is the implementation correct and functional?

**STEP 2: DETAILED SCORING**
For each notebook file, provide detailed scoring across these metrics:

1. **Code Implementation (0-30 points)**
   - CORRECTNESS: Does the code actually solve the assigned problem?
   - REQUIREMENT COMPLIANCE: Are all specific requirements implemented?
   - FUNCTIONALITY: Does the code execute and produce expected outputs?
   - SPECIFIC CHECKS: Look for exact tables, functions, procedures mentioned in requirements

2. **Code Quality (0-25 points)**
   - Code structure and organization
   - Best practices implementation
   - Error handling and robustness
   - Performance considerations

3. **Documentation (0-20 points)**
   - Code comments and explanations
   - Markdown cell quality
   - Implementation documentation
   - README quality (if applicable)

4. **Problem Solving (0-25 points)**
   - COMPLETENESS: Does the solution address ALL requirements?
   - LOGICAL APPROACH: Is the solution approach sound?
   - EDGE CASES: Are edge cases handled appropriately?

**STEP 3: REQUIREMENT-SPECIFIC CHECKS**
For each requirement, explicitly check:
- Is the specific table/function/procedure created?
- Are the exact column names and data types correct?
- Is the masking policy/RLS policy implemented as specified?
- Are the expected outputs generated?
- Does the code actually run and produce results?

**STEP 4: PENALTY FOR INCORRECT SOLUTIONS**
- If the solution doesn't address the assignment requirements: MAXIMUM 30 points total
- If key requirements are missing: Significant score reduction
- If the solution is completely off-topic: 0-10 points total

Please format your response as VALID JSON with the following structure:

{{
    "notebook_analysis": [
        {{
            "filename": "notebook1.ipynb",
            "code_implementation": {{
                "score": 25,
                "max_score": 30,
                "feedback": "CORRECTNESS CHECK: [Specific verification of requirements]. Good implementation of warehouse creation, missing error handling"
            }},
            "code_quality": {{
                "score": 20,
                "max_score": 25,
                "feedback": "Well-structured code, could improve error handling"
            }},
            "documentation": {{
                "score": 15,
                "max_score": 20,
                "feedback": "Good comments, needs more detailed explanations"
            }},
            "problem_solving": {{
                "score": 22,
                "max_score": 25,
                "feedback": "COMPLETENESS CHECK: [Verification of all requirements]. Addresses main requirements, some edge cases missing"
            }},
            "total_score": 82,
            "max_total_score": 100,
            "overall_feedback": "CORRECTNESS VERIFICATION: [Summary of requirement compliance]. Strong implementation with minor documentation issues",
            "strengths": ["Good code structure", "Proper SQL syntax", "Requirements met: [list specific requirements]"],
            "issues": ["Missing error handling", "Limited documentation", "Missing requirements: [list missing requirements]"],
            "requirements_covered": ["Create warehouse", "Create schema"],
            "requirements_missing": ["Apply masking policy", "Create stored procedure"],
            "correctness_verification": {{
                "requirements_implemented": ["Create warehouse", "Create schema"],
                "requirements_missing": ["Apply masking policy", "Create stored procedure"],
                "expected_outputs_present": ["Warehouse created", "Schema created"],
                "expected_outputs_missing": ["Masking policy applied", "Stored procedure created"],
                "overall_correctness_score": 60
            }},
            "cells": [
                {{
                    "cell_index": 0,
                    "cell_type": "code",
                    "cell_score": 8,
                    "feedback": "Good SQL implementation",
                    "requirements_covered": ["Create warehouse"],
                    "correctness_check": "Warehouse creation SQL is correct and functional"
                }}
            ]
        }}
    ],
    "files_analyzed": ["notebook1.ipynb", "notebook2.ipynb"],
    "evaluation_timestamp": "2024-01-01T12:00:00",
    "assignment_type": "{assignment_type}",
    "overall_correctness_summary": {{
        "total_requirements": {len(assignment_brief.get('requirements', []))},
        "requirements_implemented": 0,
        "requirements_missing": 0,
        "correctness_percentage": 0,
        "is_solution_correct": false
    }}
}}

CRITICAL EVALUATION RULES:
1. ALWAYS verify each requirement is actually implemented in the code
2. Check for specific table names, column names, and data types mentioned in requirements
3. Verify that expected outputs are actually generated
4. If requirements are missing or incorrect, significantly reduce scores
5. If the solution is completely off-topic, give very low scores
6. Be strict about correctness - this is the most important aspect

CRITICAL: Ensure your response is valid JSON. Use proper array syntax with square brackets [] and commas between array elements. Do not use numeric indices like 0:, 1:, etc.
"""
        return prompt

    def parse_json_with_fallbacks(self, text: str) -> Dict[str, Any]:
        """Try multiple approaches to parse JSON response"""
        
        # Try 1: Direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try 2: Clean malformed JSON
        try:
            cleaned = self.clean_malformed_json(text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Try 3: Extract JSON from markdown code blocks
        try:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Try 4: Find JSON-like structure and fix it
        try:
            # Look for the start of JSON structure
            start_idx = text.find('{')
            if start_idx != -1:
                # Find matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    json_str = text[start_idx:end_idx]
                    cleaned = self.clean_malformed_json(json_str)
                    return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # If all parsing attempts fail, return None
        return None

    def evaluate_assignment(self, zip_path: str, assignment_type: str = "snowflake", 
                          assignment_brief: Dict = None) -> Dict[str, Any]:
        """Evaluate an assignment using GPT-4.1 nano via Puter AI"""
        
        # This method is not meant to be called directly from Python
        # Puter AI requires browser environment with puter.js
        return {
            "error": "Puter AI requires browser environment with puter.js library. Use gpt_streamlit_app.py or puter_demo.html instead.",
            "overall_score": 0,
            "overall_percentage": 0,
            "note": "Puter AI uses JavaScript library, not REST API. Please use the browser-based interfaces."
        }

    def parse_text_response(self, text: str, files_content: Dict[str, str], 
                           assignment_type: str) -> List[Dict[str, Any]]:
        """Parse text response when JSON parsing fails"""
        # Create a basic structure from text response
        notebooks = []
        
        # Extract notebook names from files
        notebook_files = [f for f in files_content.keys() if f.endswith('.ipynb')]
        
        for notebook_file in notebook_files:
            notebook = {
                "filename": notebook_file,
                "code_implementation": {
                    "score": 15,
                    "max_score": 30,
                    "feedback": "Unable to parse detailed evaluation - basic scoring applied"
                },
                "code_quality": {
                    "score": 12,
                    "max_score": 25,
                    "feedback": "Unable to parse detailed evaluation - basic scoring applied"
                },
                "documentation": {
                    "score": 10,
                    "max_score": 20,
                    "feedback": "Unable to parse detailed evaluation - basic scoring applied"
                },
                "problem_solving": {
                    "score": 12,
                    "max_score": 25,
                    "feedback": "Unable to parse detailed evaluation - basic scoring applied"
                },
                "total_score": 49,
                "max_total_score": 100,
                "overall_feedback": f"Evaluation parsing failed. Raw response: {text[:500]}...",
                "strengths": ["File present"],
                "issues": ["Evaluation parsing failed"],
                "requirements_covered": [],
                "requirements_missing": [],
                "correctness_verification": {
                    "requirements_implemented": [],
                    "requirements_missing": [],
                    "expected_outputs_present": [],
                    "expected_outputs_missing": [],
                    "overall_correctness_score": 0
                },
                "cells": []
            }
            notebooks.append(notebook)
        
        return {
            "notebook_analysis": notebooks,
            "files_analyzed": list(files_content.keys()),
            "evaluation_timestamp": datetime.now().isoformat(),
            "assignment_type": assignment_type,
            "overall_correctness_summary": {
                "total_requirements": 0,
                "requirements_implemented": 0,
                "requirements_missing": 0,
                "correctness_percentage": 0,
                "is_solution_correct": False
            }
        }

    def get_assignment_brief(self, assignment_type: str) -> Dict:
        """Get assignment brief for a specific type"""
        return self.default_briefs.get(assignment_type, {})

    def list_assignment_types(self) -> List[str]:
        """List available assignment types"""
        return list(self.default_briefs.keys())

    def evaluate(self, solution_path: str, assignment_brief: dict) -> dict:
        """Legacy method for compatibility"""
        return self.evaluate_assignment(solution_path, assignment_brief=assignment_brief)

    def get_prompt(self, solution_path: str, assignment_brief: dict) -> str:
        """Get the evaluation prompt for debugging"""
        files_content = self.extract_zip_contents(solution_path)
        return self.create_evaluation_prompt("snowflake", files_content, assignment_brief)


def test_gpt_evaluator():
    """Test the GPT evaluator"""
    try:
        # Test with sample data
        evaluator = GPTEvaluator()
        
        # Test assignment types
        types = evaluator.list_assignment_types()
        print(f"Available assignment types: {types}")
        
        # Test assignment brief
        brief = evaluator.get_assignment_brief("snowflake")
        print(f"Snowflake brief: {brief['title']}")
        
        print("GPT Evaluator test completed successfully!")
        print("Note: For actual evaluation, use gpt_streamlit_app.py or puter_demo.html")
        
    except Exception as e:
        print(f"GPT Evaluator test failed: {str(e)}")


if __name__ == "__main__":
    test_gpt_evaluator() 