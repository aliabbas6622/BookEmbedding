"""
LLM Correction stage - optional OCR text correction using LLM
"""
from typing import Dict, Any, Optional

from ragstudio.pipeline.base import PipelineStage, PipelineContext


class LLMCorrectionStage(PipelineStage):
    """Optional LLM-based OCR text correction"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("llm_correction", config)
        self.provider_name = config.get("provider", "ollama")
        self.provider_config = config.get("provider_config", {})
        self.enabled = config.get("enabled", True)
        self.max_retries = config.get("max_retries", 2)
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute LLM correction"""
        if not self.enabled:
            # Skip this stage if disabled
            return context
        
        raw_text = context.get("raw_text")
        
        if not raw_text:
            context.add_error("No raw text available. Run ocr_extraction first.")
            return context
        
        try:
            # Get LLM provider
            provider = self._get_provider()
            
            # Attempt correction with retries
            corrected_text = None
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    corrected_text = await provider.correct_ocr_text(
                        ocr_text=raw_text,
                        document_type=context.get("document_type")
                    )
                    break
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        # Wait before retry (could add exponential backoff)
                        continue
            
            if corrected_text is None:
                raise last_error
            
            # Store corrected text
            context.set("cleaned_text", corrected_text)
            context.set("correction_applied", True)
            
            return context
            
        except Exception as e:
            context.add_error(f"LLM correction failed: {str(e)}")
            # Fall back to raw text if correction fails
            context.set("cleaned_text", raw_text)
            context.set("correction_applied", False)
            return context
    
    def _get_provider(self):
        """Get LLM provider instance"""
        if self.provider_name == "ollama":
            from ragstudio.core.providers.llm.ollama import OllamaLLM
            return OllamaLLM(self.provider_config)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider_name}")
