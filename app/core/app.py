from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Auction Intelligence API",
    description="API for auction analysis and intelligent listing optimization",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Auction Intelligence API",
        version="1.0.0",
        description="API for auction analysis and intelligent listing optimization",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Auction Intelligence API - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "version": "1.0.0"},
        status_code=200,
    )

# Import and include routers
from .routers import (
    auctions,
    products,
    profit,
    shipping,
    listings,
    learning,
)

app.include_router(auctions.router, prefix="/api/auctions", tags=["auctions"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(profit.router, prefix="/api/profit", tags=["profit"])
app.include_router(shipping.router, prefix="/api/shipping", tags=["shipping"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        content={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        status_code=500,
    ) 