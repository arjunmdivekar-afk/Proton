"""FastAPI application factory for Proton Server."""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from proton.server.routes.health import router as health_router
from proton.server.routes.chat import router as chat_router
from proton.server.routes.agent import router as agent_router
from proton.server.routes.tasks import router as tasks_router
from proton.server.routes.memory import router as memory_router
from proton.server.routes.graph import router as graph_router
from proton.server.routes.rag import router as rag_router
from proton.server.routes.inspect import router as inspect_router
from proton.server.routes.benchmark import router as benchmark_router
from proton.server.routes.security import router as security_router
from proton.server.routes.tools import router as tools_router
from proton.server.routes.models import router as models_router
from proton.server.routes.workspace import router as workspace_router
from proton.server.routes.terminal import router as terminal_router
from proton.server.routes.developer import router as developer_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup & shutdown."""
    # Startup actions
    yield
    # Shutdown actions


def create_app() -> FastAPI:
    """Instantiate and configure the Proton FastAPI server."""
    app = FastAPI(
        title="Proton Autonomous AI Server",
        description=(
            "Enterprise-grade REST & SSE API for Proton AI Core. Exposes autonomous agents, "
            "GraphRAG AST intelligence, stateful engineering tasks, explicit categorized memory, "
            "model benchmarking, security verification, and deterministic tool execution."
        ),
        version="2.6.4",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration for Web UIs and external frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    from proton.server.routes.doctor import router as doctor_router

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(agent_router)
    app.include_router(tasks_router)
    app.include_router(memory_router)
    app.include_router(graph_router)
    app.include_router(rag_router)
    app.include_router(inspect_router)
    app.include_router(benchmark_router)
    app.include_router(security_router)
    app.include_router(tools_router)
    app.include_router(models_router)
    app.include_router(workspace_router)
    app.include_router(terminal_router)
    app.include_router(developer_router)
    app.include_router(doctor_router)

    # Mount static assets directory
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # SPA Fallback routes for deep-linking
    index_path = static_dir / "index.html"

    @app.get("/", include_in_schema=False)
    @app.get("/chat", include_in_schema=False)
    @app.get("/chat/{path:path}", include_in_schema=False)
    @app.get("/agent", include_in_schema=False)
    @app.get("/agent/{path:path}", include_in_schema=False)
    @app.get("/terminal", include_in_schema=False)
    @app.get("/workspace", include_in_schema=False)
    @app.get("/developer", include_in_schema=False)
    @app.get("/models", include_in_schema=False)
    @app.get("/graphrag", include_in_schema=False)
    @app.get("/tasks", include_in_schema=False)
    @app.get("/tasks/{path:path}", include_in_schema=False)
    @app.get("/memory", include_in_schema=False)
    @app.get("/security", include_in_schema=False)
    @app.get("/diagnostics", include_in_schema=False)
    @app.get("/settings", include_in_schema=False)
    async def serve_spa():
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/docs")

    return app


app = create_app()
