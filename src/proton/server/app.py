"""FastAPI application factory for Proton Server."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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

    # Mount routers
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

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
