"""Transformers local inference runtime provider for Proton."""

import gc
import asyncio
import threading
from typing import AsyncGenerator, Dict, List, Optional, Any
from pathlib import Path

from proton.core.types import Message, Role, ModelInfo, ModelCapabilities
from proton.providers.base import ModelProvider, StreamChunk, ChatResponse
from proton.hub.registry import ModelRegistry
from proton.hub.hardware import detect_hardware
from proton.core.config import ConfigManager


class TransformersProvider(ModelProvider):
    """
    First-class Hugging Face Transformers model provider for local inference.
    Executes AutoModelForCausalLM and AutoTokenizer directly in-process with GPU/CPU acceleration.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        trust_remote_code: bool = False,
        torch_dtype: str = "auto",
    ):
        self.active_model_id = model_id
        self.device = device
        self.trust_remote_code = trust_remote_code
        self.torch_dtype = torch_dtype

        self._tokenizer = None
        self._model = None
        self._loaded_model_id: Optional[str] = None
        self._lock = asyncio.Lock()
        self._registry = ModelRegistry()

    def _resolve_model_path(self, model_id: str) -> str:
        """Resolve model ID to registered local path or HuggingFace ID."""
        rec = self._registry.get_model(model_id)
        if rec and Path(rec.local_path).exists():
            return rec.local_path
        return model_id

    def _load_model_sync(self, model_id: str):
        """Synchronously load tokenizer and model into memory."""
        if self._model is not None and self._loaded_model_id == model_id:
            return

        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        model_path = self._resolve_model_path(model_id)

        # Unload previous model to prevent VRAM leaks
        self.unload_model()

        # Detect if model directory contains GGUF files
        gguf_file = None
        p = Path(model_path)
        if p.is_dir():
            gguf_files = list(p.glob("*.gguf"))
            if gguf_files:
                gguf_file = gguf_files[0].name
        elif p.is_file() and p.suffix.lower() == ".gguf":
            gguf_file = p.name
            model_path = str(p.parent)

        # Robust Tokenizer Setup
        self._tokenizer = None
        if gguf_file:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    gguf_file=gguf_file,
                    trust_remote_code=self.trust_remote_code,
                )
            except Exception:
                pass

        if self._tokenizer is None:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=self.trust_remote_code,
                )
            except Exception:
                pass

        if self._tokenizer is None:
            # Fallback candidates for popular quantized GGUF architectures
            cand = model_id.lower()
            candidates = []
            if "llama-3.2-1b" in cand:
                candidates.append("unsloth/Llama-3.2-1B-Instruct")
            elif "llama-3.2-3b" in cand:
                candidates.append("unsloth/Llama-3.2-3B-Instruct")
            elif "llama-3" in cand or "llama3" in cand:
                candidates.append("unsloth/llama-3-8b-Instruct")
            elif "qwen" in cand:
                candidates.append("Qwen/Qwen2.5-Coder-1.5B-Instruct")

            for tc in candidates:
                try:
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        tc,
                        trust_remote_code=self.trust_remote_code,
                    )
                    break
                except Exception:
                    continue

        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=self.trust_remote_code,
            )

        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id or 0

        # Determine precision and device based on Proton device mode: "cpu" | "gpu" | "partial" | "auto"
        config_mgr = ConfigManager()
        mode = (self.device or config_mgr.config.device_mode or "auto").lower()

        hw = detect_hardware()
        has_cuda = torch.cuda.is_available()
        has_mps = hw.has_mps

        if mode == "cpu":
            dtype = torch.float32
            device_map = {"": "cpu"}
        elif mode == "gpu":
            if has_cuda:
                dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
                device_map = {"": "cuda:0"}
            elif has_mps:
                dtype = torch.float16
                device_map = None
            else:
                dtype = torch.float32
                device_map = {"": "cpu"}
        elif mode == "partial":
            dtype = torch.bfloat16 if has_cuda and torch.cuda.is_bf16_supported() else (
                torch.float16 if has_cuda or has_mps else torch.float32
            )
            device_map = "auto" if (has_cuda or has_mps) else None
        else:
            dtype = torch.bfloat16 if has_cuda and torch.cuda.is_bf16_supported() else (
                torch.float16 if has_cuda else torch.float32
            )
            device_map = "auto" if has_cuda else None

        model_kwargs = {
            "trust_remote_code": self.trust_remote_code,
            "low_cpu_mem_usage": True,
        }
        if gguf_file:
            model_kwargs["gguf_file"] = gguf_file
        if dtype is not None and not gguf_file:
            model_kwargs["torch_dtype"] = dtype
        if device_map is not None:
            model_kwargs["device_map"] = device_map

        self._model = AutoModelForCausalLM.from_pretrained(
            model_path,
            **model_kwargs,
        )

        if device_map is None:
            if mode == "gpu" and has_mps:
                self._model = self._model.to("mps")
            elif mode == "cpu":
                self._model = self._model.to("cpu")
            elif has_mps:
                self._model = self._model.to("mps")
            else:
                self._model = self._model.to("cpu")

        self._model.eval()
        self._loaded_model_id = model_id

    async def ensure_model_loaded(self, model_id: str):
        """Ensure target model is loaded in thread pool."""
        async with self._lock:
            if self._model is None or self._loaded_model_id != model_id:
                await asyncio.to_thread(self._load_model_sync, model_id)

    def unload_model(self) -> None:
        """Free model weights from GPU VRAM and system memory."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        self._loaded_model_id = None

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _format_messages_to_prompt(self, messages: List[Message]) -> str:
        """Apply chat template or fallback prompt format."""
        if self._tokenizer and hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template:
            hf_messages = [
                {"role": m.role.value if hasattr(m.role, "value") else str(m.role), "content": m.content}
                for m in messages
            ]
            try:
                return self._tokenizer.apply_chat_template(
                    hf_messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        # Fallback chat formatting
        prompt = ""
        for m in messages:
            role_str = m.role.value if hasattr(m.role, "value") else str(m.role)
            prompt += f"<|im_start|>{role_str}\n{m.content}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        return prompt

    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream tokens in real-time using Transformers TextIteratorStreamer."""
        from transformers import TextIteratorStreamer

        target_model = model or self.active_model_id or "default"
        await self.ensure_model_loaded(target_model)

        prompt = self._format_messages_to_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        gen_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=max_tokens or 2048,
            temperature=max(0.01, temperature),
            do_sample=(temperature > 0.05),
            pad_token_id=self._tokenizer.pad_token_id,
            eos_token_id=self._tokenizer.eos_token_id,
        )

        # Run model generation in background thread
        thread = threading.Thread(target=self._model.generate, kwargs=gen_kwargs)
        thread.start()

        # Yield generated tokens as they stream from background thread
        for text in streamer:
            if text:
                yield StreamChunk(delta=text)

        thread.join()
        yield StreamChunk(delta="", finish_reason="stop")

    async def chat_complete(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """Non-streaming complete chat generation."""
        target_model = model or self.active_model_id or "default"
        await self.ensure_model_loaded(target_model)

        prompt = self._format_messages_to_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        def _generate():
            import torch
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens or 2048,
                    temperature=max(0.01, temperature),
                    do_sample=(temperature > 0.05),
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )
            input_len = inputs["input_ids"].shape[1]
            generated_ids = outputs[0][input_len:]
            return self._tokenizer.decode(generated_ids, skip_special_tokens=True)

        generated_text = await asyncio.to_thread(_generate)

        return ChatResponse(
            content=generated_text,
            model=target_model,
            finish_reason="stop",
            usage={"total_tokens": len(generated_text.split())},
        )

    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate text embeddings using mean pooled hidden states."""
        target_model = model or self.active_model_id or "default"
        await self.ensure_model_loaded(target_model)

        def _embed():
            import torch
            embeddings = []
            for text in texts:
                inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self._model.device)
                with torch.no_grad():
                    outputs = self._model(**inputs, output_hidden_states=True)
                    # Mean pool the last hidden state
                    last_hidden = outputs.hidden_states[-1]
                    pooled = last_hidden.mean(dim=1).squeeze().cpu().tolist()
                    embeddings.append(pooled if isinstance(pooled, list) else [float(pooled)])
            return embeddings

        return await asyncio.to_thread(_embed)

    async def list_models(self) -> List[ModelInfo]:
        """List all models registered in local registry."""
        installed = self._registry.list_installed()
        return [
            ModelInfo(
                id=m.id,
                name=m.name,
                provider="transformers",
                capabilities=ModelCapabilities(
                    chat=True,
                    streaming=True,
                    tools=True,
                    embeddings=True,
                ),
                context_window=128000,
                description=f"Local Transformers model: {m.parameters_display} params ({m.size_gb} GB)",
            )
            for m in installed
        ]
