#!/usr/bin/env python3
"""
Tests for the Gemini Evaluator
"""

import pytest
import tempfile
import zipfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from gemini_evaluator import GeminiEvaluator


class TestGeminiEvaluator:
    """Test cases for GeminiEvaluator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_key = "test-api-key"
        self.evaluator = GeminiEvaluator(self.api_key)
    
    def test_initialization(self):
        """Test evaluator initialization"""
        assert self.evaluator.api_key == self.api_key
        assert self.evaluator.model is not None
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key"""
        with pytest.raises(ValueError, match="Google API key is required"):
            GeminiEvaluator()
    
    def test_extract_zip_contents(self):
        """Test ZIP file extraction"""
        # Create a temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_ref:
                zip_ref.writestr('test.ipynb', '{"cells": []}')
                zip_ref.writestr('README.md', '# Test Assignment')
        
        try:
            contents = self.evaluator.extract_zip_contents(tmp_zip.name)
            assert 'test.ipynb' in contents
            assert 'README.md' in contents
            assert contents['test.ipynb'] == '{"cells": []}'
            assert contents['README.md'] == '# Test Assignment'
        finally:
            os.unlink(tmp_zip.name)
    
    def test_extract_empty_zip(self):
        """Test extraction of empty ZIP file"""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_ref:
                pass  # Empty ZIP
        
        try:
            contents = self.evaluator.extract_zip_contents(tmp_zip.name)
            assert contents == {}
        finally:
            os.unlink(tmp_zip.name)
    
    def test_clean_malformed_json(self):
        """Test JSON cleaning functionality"""
        malformed_json = '''
        {
            "notebook_analysis":[
            0:{
                "filename":"test.ipynb"
                "score":85
            }
            1:{
                "filename":"test2.ipynb"
                "score":90
            }
            ]
        }
        '''
        
        cleaned = self.evaluator.clean_malformed_json(malformed_json)
        assert '0:{' not in cleaned
        assert '1:{' not in cleaned
        assert 'filename":"test.ipynb"' in cleaned
    
    def test_parse_json_with_fallbacks(self):
        """Test JSON parsing with fallbacks"""
        # Test valid JSON
        valid_json = '{"test": "value"}'
        result = self.evaluator.parse_json_with_fallbacks(valid_json)
        assert result == {"test": "value"}
        
        # Test malformed JSON
        malformed_json = '{"test": "value"'  # Missing closing brace
        result = self.evaluator.parse_json_with_fallbacks(malformed_json)
        assert result is None
    
    def test_list_assignment_types(self):
        """Test listing assignment types"""
        types = self.evaluator.list_assignment_types()
        assert isinstance(types, list)
        assert 'snowflake' in types
        assert 'pyspark' in types
        assert 'powerbi' in types
    
    def test_get_assignment_brief(self):
        """Test getting assignment brief"""
        brief = self.evaluator.get_assignment_brief('snowflake')
        assert isinstance(brief, dict)
        assert 'title' in brief
        assert 'requirements' in brief
        assert 'expected_outputs' in brief
    
    def test_get_assignment_brief_invalid_type(self):
        """Test getting assignment brief for invalid type"""
        brief = self.evaluator.get_assignment_brief('invalid_type')
        assert brief == {}
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_evaluate_assignment_success(self, mock_generate):
        """Test successful assignment evaluation"""
        # Mock the Gemini response
        mock_response = Mock()
        mock_response.text = '''
        {
            "notebook_analysis": [
                {
                    "filename": "test.ipynb",
                    "code_implementation": {
                        "score": 25,
                        "max_score": 30,
                        "feedback": "Good implementation"
                    },
                    "code_quality": {
                        "score": 20,
                        "max_score": 25,
                        "feedback": "Well-structured code"
                    },
                    "documentation": {
                        "score": 15,
                        "max_score": 20,
                        "feedback": "Good comments"
                    },
                    "problem_solving": {
                        "score": 22,
                        "max_score": 25,
                        "feedback": "Addresses requirements"
                    },
                    "total_score": 82,
                    "max_total_score": 100,
                    "overall_feedback": "Strong implementation",
                    "strengths": ["Good structure"],
                    "issues": ["Missing error handling"],
                    "requirements_covered": ["Create warehouse"],
                    "cells": []
                }
            ],
            "files_analyzed": ["test.ipynb"],
            "evaluation_timestamp": "2024-01-01T12:00:00",
            "assignment_type": "snowflake"
        }
        '''
        mock_generate.return_value = mock_response
        
        # Create a temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_ref:
                zip_ref.writestr('test.ipynb', '{"cells": []}')
        
        try:
            result = self.evaluator.evaluate_assignment(tmp_zip.name, 'snowflake')
            
            assert 'notebook_analysis' in result
            assert len(result['notebook_analysis']) == 1
            assert result['notebook_analysis'][0]['filename'] == 'test.ipynb'
            assert result['notebook_analysis'][0]['total_score'] == 82
            assert 'files_analyzed' in result
            assert 'evaluation_timestamp' in result
            assert 'assignment_type' in result
            
        finally:
            os.unlink(tmp_zip.name)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_evaluate_assignment_empty_zip(self, mock_generate):
        """Test evaluation with empty ZIP file"""
        # Create an empty ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_ref:
                pass  # Empty ZIP
        
        try:
            result = self.evaluator.evaluate_assignment(tmp_zip.name, 'snowflake')
            
            assert 'error' in result
            assert result['error'] == 'No files found in ZIP archive'
            assert result['overall_score'] == 0
            assert result['overall_percentage'] == 0
            
        finally:
            os.unlink(tmp_zip.name)
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_evaluate_assignment_api_error(self, mock_generate):
        """Test evaluation with API error"""
        # Mock API error
        mock_generate.side_effect = Exception("API Error")
        
        # Create a temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_ref:
                zip_ref.writestr('test.ipynb', '{"cells": []}')
        
        try:
            result = self.evaluator.evaluate_assignment(tmp_zip.name, 'snowflake')
            
            assert 'error' in result
            assert 'Evaluation failed' in result['error']
            assert result['overall_score'] == 0
            assert result['overall_percentage'] == 0
            
        finally:
            os.unlink(tmp_zip.name)


if __name__ == "__main__":
    pytest.main([__file__]) 