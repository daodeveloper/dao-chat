from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    """Rebuild index on startup if documents are newer than index"""
    try:
        from .startup import rebuild_index_if_needed
        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, rebuild_index_if_needed)
        logger.info("Startup index check completed")
    except Exception as e:
        logger.error(f"Error during startup index check: {e}", exc_info=True)
        # Don't fail startup if index check fails

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)