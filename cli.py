#!/usr/bin/env python3
"""
Command Line Interface for AI Assignment Evaluator
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from gemini_evaluator import GeminiEvaluator


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Assignment Evaluator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate a solution with a brief
  python cli.py evaluate --brief assignment.yaml --solution student_submission.zip

  # Evaluate with custom API key
  python cli.py evaluate --brief assignment.json --solution submission.zip --api-key YOUR_KEY

  # List supported assignment types
  python cli.py list-types

  # Test API connection
  python cli.py test-connection
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate an assignment')
    eval_parser.add_argument('--brief', '-b', required=True, 
                           help='Path to assignment brief file (YAML, JSON, PDF, TXT, DOCX)')
    eval_parser.add_argument('--solution', '-s', required=True,
                           help='Path to student solution ZIP file')
    eval_parser.add_argument('--api-key', '-k',
                           help='Google Gemini API key (or set GOOGLE_API_KEY env var)')
    eval_parser.add_argument('--output', '-o',
                           help='Output file for results (JSON format)')
    eval_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
    
    # List types command
    list_parser = subparsers.add_parser('list-types', help='List supported assignment types')
    
    # Test connection command
    test_parser = subparsers.add_parser('test-connection', help='Test API connection')
    test_parser.add_argument('--api-key', '-k',
                           help='Google Gemini API key (or set GOOGLE_API_KEY env var)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'evaluate':
            evaluate_assignment(args)
        elif args.command == 'list-types':
            list_assignment_types()
        elif args.command == 'test-connection':
            test_connection(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def evaluate_assignment(args):
    """Evaluate an assignment using the CLI"""
    print("🚀 Starting assignment evaluation...")
    
    # Validate inputs
    brief_path = Path(args.brief)
    solution_path = Path(args.solution)
    
    if not brief_path.exists():
        raise FileNotFoundError(f"Assignment brief not found: {brief_path}")
    
    if not solution_path.exists():
        raise FileNotFoundError(f"Solution file not found: {solution_path}")
    
    # Initialize evaluator
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable or use --api-key")
    
    evaluator = GeminiEvaluator(api_key)
    
    # Parse assignment brief
    print(f"📋 Reading assignment brief: {brief_path}")
    assignment_brief = parse_assignment_brief(brief_path)
    
    # Evaluate assignment
    print(f"🔍 Evaluating solution: {solution_path}")
    result = evaluator.evaluate(str(solution_path), assignment_brief)
    
    # Display results
    print("\n" + "="*50)
    print("📊 EVALUATION RESULTS")
    print("="*50)
    
    if 'notebook_analysis' in result and result['notebook_analysis']:
        for notebook in result['notebook_analysis']:
            filename = notebook.get('filename', 'Unknown')
            total_score = notebook.get('total_score', 0)
            max_score = notebook.get('max_total_score', 100)
            
            print(f"\n📓 {filename}")
            print(f"   Total Score: {total_score}/{max_score}")
            print(f"   Overall Feedback: {notebook.get('overall_feedback', 'N/A')}")
            
            # Display metric scores
            metrics = ['code_implementation', 'code_quality', 'documentation', 'problem_solving']
            for metric in metrics:
                if metric in notebook:
                    score_info = notebook[metric]
                    score = score_info.get('score', 0)
                    max_metric_score = score_info.get('max_score', 0)
                    feedback = score_info.get('feedback', 'N/A')
                    print(f"   {metric.replace('_', ' ').title()}: {score}/{max_metric_score}")
                    if args.verbose:
                        print(f"     Feedback: {feedback}")
            
            # Display strengths and issues
            if notebook.get('strengths'):
                print("   ✅ Strengths:")
                for strength in notebook['strengths']:
                    print(f"     • {strength}")
            
            if notebook.get('issues'):
                print("   ⚠️  Issues:")
                for issue in notebook['issues']:
                    print(f"     • {issue}")
    else:
        print("❌ No notebook analysis found in results")
    
    # Save results if output file specified
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")
    
    print("\n✅ Evaluation complete!")


def parse_assignment_brief(brief_path: Path) -> dict:
    """Parse assignment brief from various file formats"""
    suffix = brief_path.suffix.lower()
    
    if suffix == '.json':
        with open(brief_path, 'r') as f:
            return json.load(f)
    elif suffix == '.yaml' or suffix == '.yml':
        import yaml
        with open(brief_path, 'r') as f:
            return yaml.safe_load(f)
    elif suffix == '.pdf':
        import PyPDF2
        with open(brief_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            # Simple parsing - in production you might want more sophisticated parsing
            return {"content": text, "type": "pdf"}
    elif suffix in ['.txt', '.md']:
        with open(brief_path, 'r') as f:
            content = f.read()
            return {"content": content, "type": "text"}
    elif suffix == '.docx':
        from docx import Document
        doc = Document(brief_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return {"content": text, "type": "docx"}
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def list_assignment_types():
    """List supported assignment types"""
    print("📋 Supported Assignment Types:")
    print("="*30)
    
    evaluator = GeminiEvaluator("dummy")  # Just to access default briefs
    types = evaluator.list_assignment_types()
    
    for assignment_type in types:
        brief = evaluator.get_assignment_brief(assignment_type)
        title = brief.get('title', assignment_type.title())
        description = brief.get('description', 'No description available')
        
        print(f"\n🔹 {title}")
        print(f"   Type: {assignment_type}")
        print(f"   Description: {description}")
        
        if brief.get('requirements'):
            print("   Requirements:")
            for req in brief['requirements']:
                print(f"     • {req}")


def test_connection(args):
    """Test the API connection"""
    print("🔗 Testing Google Gemini API connection...")
    
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable or use --api-key")
    
    try:
        evaluator = GeminiEvaluator(api_key)
        print("✅ API connection successful!")
        print("✅ Gemini evaluator initialized successfully")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 