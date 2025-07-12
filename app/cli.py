"""
CLI Tool for AI Code Evaluator

Command-line interface for:
- File evaluation
- Batch processing
- Report generation
- Status monitoring
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from app.services.notebook_parser import parser
from app.services.ai_evaluator import evaluator
from app.services.evaluation_service import evaluation_service

console = Console()


class CodeEvaluatorCLI:
    """CLI interface for the AI Code Evaluator."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize CLI with API URL."""
        self.api_url = api_url
        self.api_base = f"{api_url}/api/v1"
    
    def evaluate_file(self, file_path: str, output: Optional[str] = None, wait: bool = True) -> Dict[str, Any]:
        """Evaluate a single file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            console.print(f"[red]Error: File {file_path} does not exist[/red]")
            return {}
        
        # Validate file
        if not parser.validate_file(str(file_path)):
            console.print(f"[red]Error: Invalid file {file_path}[/red]")
            return {}
        
        console.print(f"[green]Evaluating file: {file_path}[/green]")
        
        try:
            # Upload file
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f.read())}
                response = requests.post(f"{self.api_base}/evaluate", files=files)
            
            if response.status_code != 200:
                console.print(f"[red]Upload failed: {response.json().get('detail', 'Unknown error')}[/red]")
                return {}
            
            result = response.json()
            evaluation_id = result['evaluation_id']
            console.print(f"[green]Evaluation started: {evaluation_id}[/green]")
            
            if wait:
                return self._wait_for_completion(evaluation_id, output)
            else:
                return {'evaluation_id': evaluation_id, 'status': 'started'}
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return {}
    
    def _wait_for_completion(self, evaluation_id: str, output: Optional[str] = None) -> Dict[str, Any]:
        """Wait for evaluation completion and return results."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Evaluating...", total=None)
            
            while True:
                try:
                    # Check status
                    response = requests.get(f"{self.api_base}/evaluations/{evaluation_id}/status")
                    if response.status_code != 200:
                        progress.update(task, description="Failed to get status")
                        return {}
                    
                    status_data = response.json()
                    status = status_data['status']
                    progress_value = status_data.get('progress', 0)
                    
                    progress.update(task, description=f"Status: {status} - {progress_value:.1f}%")
                    
                    if status == 'completed':
                        progress.update(task, description="✅ Evaluation completed!")
                        break
                    elif status == 'failed':
                        progress.update(task, description="❌ Evaluation failed!")
                        return {}
                    
                    time.sleep(2)
                    
                except Exception as e:
                    progress.update(task, description=f"Error: {str(e)}")
                    return {}
            
            # Get results
            try:
                response = requests.get(f"{self.api_base}/evaluations/{evaluation_id}/results")
                if response.status_code == 200:
                    results = response.json()
                    
                    # Display results
                    self._display_results(results)
                    
                    # Save to file if specified
                    if output:
                        with open(output, 'w') as f:
                            json.dump(results, f, indent=2, default=str)
                        console.print(f"[green]Results saved to: {output}[/green]")
                    
                    return results
                else:
                    console.print(f"[red]Failed to get results: {response.json().get('detail', 'Unknown error')}[/red]")
                    return {}
                    
            except Exception as e:
                console.print(f"[red]Error getting results: {str(e)}[/red]")
                return {}
    
    def _display_results(self, results: Dict[str, Any]):
        """Display evaluation results in a formatted way."""
        console.print("\n" + "="*80)
        console.print(f"[bold blue]Evaluation Results: {results['filename']}[/bold blue]")
        console.print("="*80)
        
        # Project overview
        overview_table = Table(title="Project Overview")
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")
        
        overview_table.add_row("Project Score", f"{results['project_score']:.1f}/10")
        overview_table.add_row("Total Files", str(len(results['files'])))
        overview_table.add_row("Total Cells", str(results['total_cells']))
        overview_table.add_row("Processing Time", f"{results['completed_at'] - results['created_at']:.1f}s")
        
        console.print(overview_table)
        
        # Files summary
        if results['files']:
            console.print("\n[bold]Files Summary:[/bold]")
            files_table = Table()
            files_table.add_column("Filename", style="cyan")
            files_table.add_column("Score", style="green")
            files_table.add_column("Cells", style="yellow")
            files_table.add_column("Size (KB)", style="magenta")
            
            for file_data in results['files']:
                score = file_data['overall_score']
                score_color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
                
                files_table.add_row(
                    file_data['filename'],
                    f"[{score_color}]{score:.1f}[/{score_color}]",
                    str(file_data['cell_count']),
                    f"{file_data['file_size'] / 1024:.1f}"
                )
            
            console.print(files_table)
            
            # Detailed analysis
            console.print("\n[bold]Detailed Analysis:[/bold]")
            for file_data in results['files']:
                self._display_file_analysis(file_data)
    
    def _display_file_analysis(self, file_data: Dict[str, Any]):
        """Display detailed file analysis."""
        console.print(f"\n[bold cyan]📄 {file_data['filename']} - Score: {file_data['overall_score']:.1f}[/bold cyan]")
        
        # Score breakdown
        if file_data['score_breakdown']:
            console.print("\n[bold]Score Breakdown:[/bold]")
            breakdown_table = Table()
            breakdown_table.add_column("Criterion", style="cyan")
            breakdown_table.add_column("Score", style="green")
            
            for criterion, score in file_data['score_breakdown'].items():
                score_color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
                breakdown_table.add_row(
                    criterion.replace('_', ' ').title(),
                    f"[{score_color}]{score:.1f}[/{score_color}]"
                )
            
            console.print(breakdown_table)
        
        # Cells analysis
        console.print(f"\n[bold]Code Cells ({len(file_data['cells'])}):[/bold]")
        for cell in file_data['cells']:
            self._display_cell_analysis(cell)
    
    def _display_cell_analysis(self, cell: Dict[str, Any]):
        """Display cell analysis."""
        score = cell['overall_score']
        score_color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
        
        console.print(f"\n  [bold]🔧 {cell['cell_id']} - {cell['language']} - Score: [{score_color}]{score:.1f}[/{score_color}][/bold]")
        
        # Code preview
        code_lines = cell['code'].split('\n')
        if len(code_lines) > 5:
            code_preview = '\n'.join(code_lines[:5]) + '\n...'
        else:
            code_preview = cell['code']
        
        console.print(Panel(code_preview, title="Code", border_style="blue"))
        
        # Issues
        if cell['issues']:
            console.print("  [bold red]Issues:[/bold red]")
            for issue in cell['issues']:
                console.print(f"    ⚠️  {issue}")
        
        # Suggestions
        if cell['suggestions']:
            console.print("  [bold green]Suggestions:[/bold green]")
            for suggestion in cell['suggestions']:
                console.print(f"    💡 {suggestion}")
    
    def list_evaluations(self):
        """List all evaluations."""
        try:
            response = requests.get(f"{self.api_base}/evaluations")
            if response.status_code == 200:
                evaluations = response.json()
                
                if evaluations:
                    table = Table(title="Recent Evaluations")
                    table.add_column("ID", style="cyan")
                    table.add_column("Filename", style="green")
                    table.add_column("Status", style="yellow")
                    table.add_column("Progress", style="magenta")
                    table.add_column("Created", style="blue")
                    
                    for eval_data in evaluations:
                        status_color = "green" if eval_data['status'] == 'completed' else "yellow" if eval_data['status'] == 'processing' else "red"
                        table.add_row(
                            eval_data['evaluation_id'][:8] + "...",
                            eval_data['filename'],
                            f"[{status_color}]{eval_data['status']}[/{status_color}]",
                            f"{eval_data['progress']:.1f}%",
                            eval_data['created_at'][:19]
                        )
                    
                    console.print(table)
                else:
                    console.print("[yellow]No evaluations found[/yellow]")
            else:
                console.print(f"[red]Failed to fetch evaluations: {response.json().get('detail', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    def get_status(self, evaluation_id: str):
        """Get evaluation status."""
        try:
            response = requests.get(f"{self.api_base}/evaluations/{evaluation_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                
                table = Table(title=f"Evaluation Status: {evaluation_id}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in status_data.items():
                    table.add_row(key.replace('_', ' ').title(), str(value))
                
                console.print(table)
            else:
                console.print(f"[red]Failed to get status: {response.json().get('detail', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    def get_results(self, evaluation_id: str, output: Optional[str] = None):
        """Get evaluation results."""
        try:
            response = requests.get(f"{self.api_base}/evaluations/{evaluation_id}/results")
            if response.status_code == 200:
                results = response.json()
                
                # Display results
                self._display_results(results)
                
                # Save to file if specified
                if output:
                    with open(output, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                    console.print(f"[green]Results saved to: {output}[/green]")
                
                return results
            else:
                console.print(f"[red]Failed to get results: {response.json().get('detail', 'Unknown error')}[/red]")
                return {}
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return {}
    
    def get_statistics(self):
        """Get evaluation statistics."""
        try:
            response = requests.get(f"{self.api_base}/statistics")
            if response.status_code == 200:
                stats = response.json()
                
                table = Table(title="Evaluation Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in stats.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            table.add_row(f"{key.replace('_', ' ').title()} - {sub_key}", str(sub_value))
                    else:
                        table.add_row(key.replace('_', ' ').title(), str(value))
                
                console.print(table)
            else:
                console.print(f"[red]Failed to get statistics: {response.json().get('detail', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Code Evaluator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate a single file
  python -m app.cli evaluate notebooks.zip --output results.json
  
  # Evaluate without waiting
  python -m app.cli evaluate notebooks.zip --no-wait
  
  # List evaluations
  python -m app.cli list
  
  # Get status
  python -m app.cli status <evaluation_id>
  
  # Get results
  python -m app.cli results <evaluation_id> --output results.json
  
  # Get statistics
  python -m app.cli stats
        """
    )
    
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API server URL (default: http://localhost:8000)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate a file')
    eval_parser.add_argument('file', help='File to evaluate')
    eval_parser.add_argument('--output', '-o', help='Output file for results')
    eval_parser.add_argument('--no-wait', action='store_true', help='Don\'t wait for completion')
    
    # List command
    subparsers.add_parser('list', help='List evaluations')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get evaluation status')
    status_parser.add_argument('evaluation_id', help='Evaluation ID')
    
    # Results command
    results_parser = subparsers.add_parser('results', help='Get evaluation results')
    results_parser.add_argument('evaluation_id', help='Evaluation ID')
    results_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Statistics command
    subparsers.add_parser('stats', help='Get statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance
    cli = CodeEvaluatorCLI(args.api_url)
    
    try:
        if args.command == 'evaluate':
            cli.evaluate_file(args.file, args.output, not args.no_wait)
        elif args.command == 'list':
            cli.list_evaluations()
        elif args.command == 'status':
            cli.get_status(args.evaluation_id)
        elif args.command == 'results':
            cli.get_results(args.evaluation_id, args.output)
        elif args.command == 'stats':
            cli.get_statistics()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 