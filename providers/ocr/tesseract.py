"""
Tesseract.js OCR Provider Implementation
Uses pytesseract (Python wrapper for Tesseract) for OCR
"""
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import tempfile
import shutil

from providers.ocr.base import OCRProvider, OCRResult


class TesseractOCR(OCRProvider):
    """Tesseract OCR provider using system tesseract command"""
    
    def __init__(self, lang: str = "eng", config: Optional[str] = None):
        self.lang = lang
        self.config = config or "--oem 3 --psm 6"
        self._initialized = False
        self._tesseract_path: Optional[str] = None
    
    @property
    def name(self) -> str:
        return "tesseract"
    
    def initialize(self) -> bool:
        """Check if tesseract is available and set up"""
        try:
            # Check if tesseract is installed
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._tesseract_path = shutil.which("tesseract")
                self._initialized = True
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._initialized = False
            return False
    
    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        if not self._initialized:
            return self.initialize()
        return self._initialized and self._tesseract_path is not None
    
    def extract_text(self, file_path: Path) -> OCRResult:
        """
        Extract text from PDF or image using Tesseract
        
        For PDFs, converts to images first using pdftoppm or similar
        """
        if not self.is_available():
            raise RuntimeError("Tesseract OCR is not available")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self._extract_from_image(file_path)
        elif suffix == ".pdf":
            return self._extract_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _extract_from_image(self, image_path: Path) -> OCRResult:
        """Extract text from a single image"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            
            cmd = [
                "tesseract",
                str(image_path),
                str(output_path),
                "-l", self.lang,
                *self.config.split()
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(f"Tesseract failed: {result.stderr}")
            
            # Read the output text
            output_file = output_path.with_suffix(".txt")
            if output_file.exists():
                text = output_file.read_text()
            else:
                text = ""
            
            return OCRResult(
                text=text,
                confidence=0.0,  # Tesseract CLI doesn't easily provide confidence
                pages=[{"text": text, "page_number": 1}]
            )
    
    def _extract_from_pdf(self, pdf_path: Path) -> OCRResult:
        """
        Extract text from PDF by converting pages to images first
        Requires pdftoppm (from poppler-utils)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            images_dir = tmpdir_path / "images"
            images_dir.mkdir()
            
            # Convert PDF to images using pdftoppm
            cmd = [
                "pdftoppm",
                "-png",
                "-r", "300",  # 300 DPI
                str(pdf_path),
                str(images_dir / "page")
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                # Try alternative: convert command
                try:
                    self._extract_from_pdf_with_convert(pdf_path, images_dir)
                except Exception:
                    raise RuntimeError(f"Failed to convert PDF to images: {result.stderr}")
            
            # Process each page
            pages = []
            all_text = []
            page_images = sorted(images_dir.glob("*.png"))
            
            for idx, page_image in enumerate(page_images, 1):
                page_result = self._extract_from_image(page_image)
                page_text = page_result.text
                all_text.append(page_text)
                pages.append({
                    "text": page_text,
                    "page_number": idx
                })
            
            full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
            
            return OCRResult(
                text=full_text,
                confidence=0.0,
                pages=pages
            )
    
    def _extract_from_pdf_with_convert(self, pdf_path: Path, images_dir: Path):
        """Alternative PDF to image conversion using ImageMagick's convert"""
        cmd = [
            "convert",
            "-density", "300",
            str(pdf_path),
            "-quality", "100",
            str(images_dir / "page.png")
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Convert failed: {result.stderr}")
