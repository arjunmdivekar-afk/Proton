import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from huggingface_hub import HfApi, ModelInfo as HfModelInfo

Tuple_Params = Tuple[str, float]
Tuple_SearchResult = Tuple[List["HubModelSummary"], bool, int]


class HubModelSummary(BaseModel):
    """Structured summary of a Hugging Face model."""
    id: str
    author: str
    name: str
    downloads: int = 0
    likes: int = 0
    task: str = "text-generation"
    pipeline_tag: Optional[str] = "text-generation"
    parameters_display: str = "Unknown"
    parameters_billions: float = 0.0
    estimated_size_gb: float = 0.0
    license: str = "Unknown"
    architecture: str = "Transformers"
    quantization: str = "fp16/bf16"
    is_transformers_compatible: bool = True
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    private: bool = False
    requires_remote_code: bool = False


class HubModelDetails(BaseModel):
    """Comprehensive metadata breakdown for a specific model."""
    id: str
    author: str
    name: str
    downloads: int
    likes: int
    task: str
    parameters_display: str
    parameters_billions: float
    estimated_size_gb: float
    license: str
    architecture: str
    quantization: str
    is_transformers_compatible: bool
    requires_remote_code: bool
    tags: List[str]
    siblings_files: List[str] = Field(default_factory=list)
    safetensors_total_bytes: int = 0
    sha: Optional[str] = None
    card_data: Dict[str, Any] = Field(default_factory=dict)
    summary_text: Optional[str] = None


class HuggingFaceHubClient:
    """Client for discovering models through the official huggingface_hub Python library."""

    def __init__(self, token: Optional[str] = None):
        self.api = HfApi(token=token)

    def _extract_parameters(self, model_id: str, tags: List[str]) -> Tuple_Params:
        """Extract parameter count from tags or model ID string."""
        # 1. Check tags for 'params:X' or 'param_count'
        for tag in tags:
            tag_lower = tag.lower()
            m = re.match(r"(?:params|parameters):([0-9.]+)([bmk]?)", tag_lower)
            if m:
                val = float(m.group(1))
                unit = m.group(2)
                if unit == "m":
                    return f"{val:g}M", val / 1000.0
                elif unit == "k":
                    return f"{val:g}K", val / 1e6
                return f"{val:g}B", val

        # 2. Heuristic extraction from model name
        m = re.search(r"[-_]([0-9]+(?:\.[0-9]+)?)[bB](?:[-_]|$)", model_id)
        if m:
            val = float(m.group(1))
            return f"{val:g}B", val

        m_m = re.search(r"[-_]([0-9]+(?:\.[0-9]+)?)[mM](?:[-_]|$)", model_id)
        if m_m:
            val = float(m_m.group(1))
            return f"{val:g}M", val / 1000.0

        return "Unknown", 0.0

    def _extract_license(self, tags: List[str], card_data: Optional[Dict[str, Any]] = None) -> str:
        if card_data and "license" in card_data and card_data["license"]:
            return str(card_data["license"])
        for tag in tags:
            if tag.startswith("license:"):
                return tag.replace("license:", "")
        return "Unknown"

    def _extract_quantization(self, model_id: str, tags: List[str]) -> str:
        tags_str = " ".join(tags).lower() + " " + model_id.lower()
        if "gguf" in tags_str:
            if "q4_k_m" in tags_str or "q4" in tags_str:
                return "GGUF Q4"
            if "q8_0" in tags_str or "q8" in tags_str:
                return "GGUF Q8"
            return "GGUF"
        if "awq" in tags_str or "4bit" in tags_str:
            return "4-bit (AWQ/GPTQ)"
        if "8bit" in tags_str:
            return "8-bit"
        if "bf16" in tags_str:
            return "bf16"
        if "fp16" in tags_str:
            return "fp16"
        return "fp16 / safetensors"

    def _estimate_size_gb(self, param_billions: float, siblings: Optional[List[Any]] = None) -> float:
        if siblings:
            total_bytes = 0
            for s in siblings:
                size = getattr(s, "size", None)
                if size and isinstance(size, int):
                    total_bytes += size
            if total_bytes > 0:
                return round(total_bytes / (1024 ** 3), 2)

        if param_billions > 0:
            return round((param_billions * 1e9 * 2.0) / (1024 ** 3), 2)
        return 0.0

    def search_models(
        self,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "downloads",
        direction: int = -1,
        filter_task: str = "text-generation",
    ) -> Tuple_SearchResult:
        """
        Search models with 20 items per page pagination using official HfApi.
        Does NOT load the entire catalog into memory.
        """
        # Fetch slightly more to determine has_next while keeping page_size chunk
        limit = page_size
        offset = (page - 1) * page_size

        try:
            models_iter = self.api.list_models(
                search=query if query else None,
                filter=filter_task if filter_task else None,
                sort=sort,
                direction=direction,
                limit=limit + offset,
                cardData=True,
            )

            # Paginate slice
            models_list = list(models_iter)
            page_slice = models_list[offset: offset + limit]
            has_next = len(models_list) > offset + limit

            results: List[HubModelSummary] = []
            for m in page_slice:
                m_id = m.id
                parts = m_id.split("/", 1)
                author = parts[0] if len(parts) > 1 else "Community"
                name = parts[1] if len(parts) > 1 else parts[0]
                tags = list(m.tags or [])
                card_data = getattr(m, "cardData", {}) or {}

                param_disp, param_b = self._extract_parameters(m_id, tags)
                size_gb = self._estimate_size_gb(param_b, getattr(m, "siblings", None))
                lic = self._extract_license(tags, card_data)
                quant = self._extract_quantization(m_id, tags)

                is_tf = "transformers" in tags or any(t.startswith("transformers") for t in tags) or True
                req_code = "custom_code" in tags

                results.append(
                    HubModelSummary(
                        id=m_id,
                        author=author,
                        name=name,
                        downloads=m.downloads or 0,
                        likes=m.likes or 0,
                        task=m.pipeline_tag or filter_task or "text-generation",
                        pipeline_tag=m.pipeline_tag,
                        parameters_display=param_disp,
                        parameters_billions=param_b,
                        estimated_size_gb=size_gb,
                        license=lic,
                        architecture="Transformers / AutoModel",
                        quantization=quant,
                        is_transformers_compatible=is_tf,
                        tags=tags[:8],
                        created_at=str(m.created_at) if hasattr(m, "created_at") and m.created_at else None,
                        last_modified=str(m.last_modified) if hasattr(m, "last_modified") and m.last_modified else None,
                        requires_remote_code=req_code,
                    )
                )

            return results, has_next, page
        except Exception as e:
            # Fallback for network error or rate limit
            return [], False, page

    def get_model_details(self, model_id: str) -> Optional[HubModelDetails]:
        """Fetch complete detailed metadata for a single model."""
        try:
            info = self.api.model_info(model_id, files_metadata=True)
            parts = model_id.split("/", 1)
            author = parts[0] if len(parts) > 1 else "Community"
            name = parts[1] if len(parts) > 1 else parts[0]

            tags = list(info.tags or [])
            card_data = getattr(info, "cardData", {}) or {}
            param_disp, param_b = self._extract_parameters(model_id, tags)

            siblings_files = []
            safetensors_bytes = 0
            if info.siblings:
                for s in info.siblings:
                    rfilename = getattr(s, "rfilename", "")
                    if rfilename:
                        siblings_files.append(rfilename)
                    size = getattr(s, "size", 0)
                    if size and isinstance(size, int):
                        safetensors_bytes += size

            size_gb = round(safetensors_bytes / (1024 ** 3), 2) if safetensors_bytes > 0 else self._estimate_size_gb(param_b)
            lic = self._extract_license(tags, card_data)
            quant = self._extract_quantization(model_id, tags)

            sha_val = getattr(info, "sha", None)
            sha_str = str(sha_val) if isinstance(sha_val, str) else None
            desc_val = getattr(info, "description", None)
            desc_str = str(desc_val) if isinstance(desc_val, str) else None

            return HubModelDetails(
                id=model_id,
                author=author,
                name=name,
                downloads=info.downloads if isinstance(getattr(info, "downloads", None), int) else 0,
                likes=info.likes if isinstance(getattr(info, "likes", None), int) else 0,
                task=info.pipeline_tag if isinstance(getattr(info, "pipeline_tag", None), str) else "text-generation",
                parameters_display=param_disp,
                parameters_billions=param_b,
                estimated_size_gb=size_gb,
                license=lic,
                architecture="Transformers / AutoModelForCausalLM",
                quantization=quant,
                is_transformers_compatible=True,
                requires_remote_code="custom_code" in tags,
                tags=tags,
                siblings_files=siblings_files,
                safetensors_total_bytes=safetensors_bytes,
                sha=sha_str,
                card_data=card_data if isinstance(card_data, dict) else {},
                summary_text=desc_str,
            )
        except Exception:
            return None
