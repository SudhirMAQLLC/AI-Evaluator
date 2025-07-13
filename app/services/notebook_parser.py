"""
Notebook Parser Service

Handles parsing of Jupyter notebooks (.ipynb) and other code files.
Extracts code cells and identifies programming languages.
"""

import json
import logging
import zipfile
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import nbformat
from nbformat import NotebookNode

from app.models import CodeCell, NotebookFile, LanguageType
from app.config import settings

logger = logging.getLogger(__name__)


class NotebookParser:
    """Parser for Jupyter notebooks and code files."""
    
    def __init__(self):
        """Initialize the notebook parser."""
        self.supported_extensions = {
            '.ipynb': self._parse_notebook,
            '.py': self._parse_python_file,
            '.sql': self._parse_sql_file,
            '.scala': self._parse_scala_file,
            '.r': self._parse_r_file
        }
    
    def parse_file(self, file_path: str) -> List[NotebookFile]:
        """Parse a single file or ZIP archive containing multiple files."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.zip':
            return self.parse_zip_file(file_path)
        elif file_ext in self.supported_extensions:
            # Parse single file
            notebook_file = self.supported_extensions[file_ext](file_path, Path(file_path).name)
            return [notebook_file] if notebook_file else []
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return []
    
    def parse_zip_file(self, zip_path: str) -> List[NotebookFile]:
        """Parse all supported files from a ZIP archive."""
        notebook_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for zip bomb
                total_size = sum(info.file_size for info in zip_ref.filelist)
                if total_size > settings.max_file_size:
                    raise ValueError(f"ZIP file too large: {total_size} bytes")
                
                # Extract and parse each file
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue
                    
                    file_ext = Path(file_info.filename).suffix.lower()
                    if file_ext in self.supported_extensions:
                        try:
                            # Extract file to temporary location
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                                with zip_ref.open(file_info.filename) as source_file:
                                    temp_file.write(source_file.read())
                                    temp_file_path = temp_file.name
                            
                            # Parse the file
                            notebook_file = self.supported_extensions[file_ext](temp_file_path, file_info.filename)
                            if notebook_file:
                                notebook_files.append(notebook_file)
                            
                            # Clean up temporary file
                            os.unlink(temp_file_path)
                            
                        except Exception as e:
                            logger.error(f"Failed to parse {file_info.filename}: {e}")
                            continue
                
        except Exception as e:
            logger.error(f"Failed to parse ZIP file {zip_path}: {e}")
            raise
        
        return notebook_files
    
    def _parse_notebook(self, file_path: str, filename: str) -> Optional[NotebookFile]:
        """Parse a Jupyter notebook file."""
        try:
            # Load notebook
            notebook = nbformat.read(file_path, as_version=4)
            
            cells = []
            for i, cell in enumerate(notebook.cells):
                if cell.cell_type == 'code':
                    code_cell = self._extract_code_cell(cell, i)
                    if code_cell:
                        cells.append(code_cell)
            
            if not cells:
                logger.warning(f"No code cells found in {filename}")
                return None
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return NotebookFile(
                filename=filename,
                file_size=file_size,
                cell_count=len(cells),
                cells=cells
            )
            
        except Exception as e:
            logger.error(f"Failed to parse notebook {filename}: {e}")
            return None
    
    def _extract_code_cell(self, cell: NotebookNode, index: int) -> Optional[CodeCell]:
        """Extract code cell from notebook cell."""
        try:
            source = cell.source
            if not source or not source.strip():
                return None
            
            # Determine language
            language = self._detect_language(source)
            
            # Count lines
            line_count = len(source.splitlines())
            
            # Get execution count if available
            execution_count = getattr(cell, 'execution_count', None)
            
            return CodeCell(
                cell_id=f"cell_{index}",
                language=language,
                code=source.strip(),
                line_count=line_count,
                execution_count=execution_count
            )
            
        except Exception as e:
            logger.error(f"Failed to extract code cell {index}: {e}")
            return None
    
    def _detect_language(self, code: str) -> LanguageType:
        """Detect programming language from code content."""
        code_lower = code.lower()
        
        # SQL detection
        sql_keywords = ['select', 'from', 'where', 'insert', 'update', 'delete', 'create', 'drop', 'alter']
        if any(keyword in code_lower for keyword in sql_keywords):
            return LanguageType.SQL
        
        # PySpark detection
        pyspark_keywords = ['spark', 'spark.sql', 'dataframe', 'rdd', 'pyspark']
        if any(keyword in code_lower for keyword in pyspark_keywords):
            return LanguageType.PYSPARK
        
        # Python detection (default for notebooks)
        return LanguageType.PYTHON
    
    def _parse_python_file(self, file_path: str, filename: str) -> Optional[NotebookFile]:
        """Parse a Python file as a single code cell."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if not code.strip():
                return None
            
            cell = CodeCell(
                cell_id="main",
                language=LanguageType.PYTHON,
                code=code.strip(),
                line_count=len(code.splitlines())
            )
            
            file_size = os.path.getsize(file_path)
            
            return NotebookFile(
                filename=filename,
                file_size=file_size,
                cell_count=1,
                cells=[cell]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Python file {filename}: {e}")
            return None
    
    def _parse_sql_file(self, file_path: str, filename: str) -> Optional[NotebookFile]:
        """Parse a SQL file as a single code cell."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if not code.strip():
                return None
            
            cell = CodeCell(
                cell_id="main",
                language=LanguageType.SQL,
                code=code.strip(),
                line_count=len(code.splitlines())
            )
            
            file_size = os.path.getsize(file_path)
            
            return NotebookFile(
                filename=filename,
                file_size=file_size,
                cell_count=1,
                cells=[cell]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse SQL file {filename}: {e}")
            return None
    
    def _parse_scala_file(self, file_path: str, filename: str) -> Optional[NotebookFile]:
        """Parse a Scala file (for Spark) as a single code cell."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if not code.strip():
                return None
            
            cell = CodeCell(
                cell_id="main",
                language=LanguageType.PYSPARK,  # Treat as PySpark for evaluation
                code=code.strip(),
                line_count=len(code.splitlines())
            )
            
            file_size = os.path.getsize(file_path)
            
            return NotebookFile(
                filename=filename,
                file_size=file_size,
                cell_count=1,
                cells=[cell]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Scala file {filename}: {e}")
            return None
    
    def _parse_r_file(self, file_path: str, filename: str) -> Optional[NotebookFile]:
        """Parse an R file as a single code cell."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if not code.strip():
                return None
            
            cell = CodeCell(
                cell_id="main",
                language=LanguageType.PYTHON,  # Treat as Python for evaluation
                code=code.strip(),
                line_count=len(code.splitlines())
            )
            
            file_size = os.path.getsize(file_path)
            
            return NotebookFile(
                filename=filename,
                file_size=file_size,
                cell_count=1,
                cells=[cell]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse R file {filename}: {e}")
            return None
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if a file can be processed."""
        try:
            # Check file size
            if os.path.getsize(file_path) > settings.max_file_size:
                return False
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            
            # Handle ZIP files separately
            if file_ext == '.zip':
                return self._validate_zip_file(file_path)
            
            # Check if extension is supported
            if file_ext not in self.supported_extensions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation failed for {file_path}: {e}")
            return False
    
    def _validate_zip_file(self, zip_path: str) -> bool:
        """Validate ZIP file for security and content."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for zip bomb
                total_size = 0
                file_count = 0
                has_supported_files = False
                
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue
                    
                    total_size += file_info.file_size
                    file_count += 1
                    
                    # Check for reasonable limits
                    if total_size > settings.max_file_size:
                        return False
                    if file_count > 1000:  # Reasonable limit
                        return False
                    
                    # Check for suspicious file names
                    filename = file_info.filename.lower()
                    if any(suspicious in filename for suspicious in ['..', '~', '/etc/', '/proc/']):
                        return False
                    
                    # Check if file has supported extension
                    file_ext = Path(filename).suffix.lower()
                    if file_ext in self.supported_extensions:
                        has_supported_files = True
                
                # Must contain at least one supported file
                return has_supported_files
                
        except Exception as e:
            logger.error(f"ZIP validation failed: {e}")
            return False
    
    def get_file_statistics(self, notebook_files: List[NotebookFile]) -> Dict:
        """Get statistics about parsed files."""
        stats = {
            'total_files': len(notebook_files),
            'total_cells': sum(len(f.cells) for f in notebook_files),
            'languages': {},
            'total_size': sum(f.file_size for f in notebook_files),
            'average_cells_per_file': 0
        }
        
        if notebook_files:
            stats['average_cells_per_file'] = stats['total_cells'] / stats['total_files']
        
        # Count languages
        for notebook_file in notebook_files:
            for cell in notebook_file.cells:
                lang = cell.language.value
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
        
        return stats


# Global parser instance
parser = NotebookParser() 