from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import admin, documents, search

app = FastAPI(
    title="NLP sustav za sažimanje, izdvajanje ključnih informacija i semantičko pretraživanje državnih zakona",
    version="0.1.0",
    license_info={
        "name": "Apache 2.0 License",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS – allow NextJS dev server and same-origin production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(documents.router, prefix="/api")
app.include_router(search.router,    prefix="/api")
app.include_router(admin.router,     prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "version": app.version}
