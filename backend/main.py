from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.responses import HTMLResponse
from datetime import datetime
from pydantic import BaseModel
from backend.models import QueryRequest, QueryResponse
from ragqexec import run_pipeline  # You will patch this next
import os
from dotenv import load_dotenv

# Load API key from .env if exists
load_dotenv()
API_KEY = os.getenv("NDRA_API_KEY")

app = FastAPI(
    title="Neuro-Semantic Document Research Assistance (NDRA)",
    description="Semantic Query Interface for Policy Documents",
    version="1.0.0"
)

@app.middleware("http")
async def verify_token(request: Request, call_next):
    # Skip token check for root or favicon
    if request.url.path not in ["/", "/favicon.ico", "/ndra", "/docs", "/redoc", "/openapi.json"]:
        if API_KEY:
            token = request.headers.get("Authorization")
            if token != f"Bearer {API_KEY}":
                return JSONResponse(status_code=403, content={"error": "Unauthorized Access, Get an Auth Token From Administrator"})
    return await call_next(request)

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "✅ NDRA API is up and running."

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return PlainTextResponse("", status_code=204)

@app.post("/ndra/run", response_model=QueryResponse)
async def ndra_run(query_input: QueryRequest):
    try:
        result = run_pipeline(query_input.query, query_input.metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

@app.get("/ndra", response_class=HTMLResponse)
async def ndra_dashboard():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>NDRA API Interface</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(to right, #e0f7fa, #ffffff);
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                color: #333;
            }}

            .container {{
                text-align: center;
                background: #fff;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
                max-width: 600px;
                animation: fadeIn 1s ease-in-out;
            }}

            h1 {{
                font-size: 2.2rem;
                color: #0077cc;
                margin-bottom: 10px;
            }}

            .status {{
                font-size: 1.2rem;
                margin-top: 10px;
                color: green;
                font-weight: bold;
            }}

            .description {{
                margin-top: 20px;
                font-size: 1rem;
                line-height: 1.6;
            }}

            .buttons {{
                margin-top: 30px;
            }}

            .buttons button {{
                background-color: #0077cc;
                border: none;
                padding: 12px 24px;
                margin: 10px;
                border-radius: 8px;
                color: white;
                font-size: 1rem;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}

            .buttons button:hover {{
                background-color: #005fa3;
            }}

            .typewriter {{
                font-size: 1.1rem;
                font-style: italic;
                margin-top: 20px;
                color: #555;
                min-height: 1.5em;
            }}

            .time {{
                margin-top: 20px;
                font-size: 1rem;
                color: #777;
            }}

            .footer {{
                margin-top: 10px;
                font-size: 0.9rem;
                color: #aaa;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>NDRA API is Up and Running</h1>
            <div class="status">Status: <span id="liveStatus">Checking...</span></div>
            <div class="typewriter" id="typewriter"></div>
            <div class="description">
                NDRA (Neuro-Semantic Document Research Assistant) helps you ask vague queries over insurance documents and returns accurate, explainable results.
            </div>
            <div class="buttons">
                <button onclick="window.open('/docs', '_blank')">📘 Open API Docs</button>
                <button onclick="window.open('/redoc', '_blank')">📖 Open Redocs</button>
                <button onclick="window.open('https://github.com/PardhuSreeRushiVarma20060119/NDRA', '_blank')">🚀 GitHub Repo</button>
                <button onclick="window.open('mailto:pardhusreevarma@gmail.com?subject=NDRA%20Feedback&body=Your%20feedback%20here...', '_blank')">📧 Email Us</button>
                <button onclick="window.open('/ndra/run', '_blank')">📨 Run /ndra/run</button>
            </div>
            <div class="time">🕒 Server Time: {current_time}</div>
            <div class="status">System Status: <span style="color: green;">Operational</span></div>
            <div class="footer">© 2025 Neuro-Semantic Document Research Assistance (NDRA)</div>
            <div class="footer">Version: 1.0.0</div>
        </div>

        <script>
            // Typewriter effect
            const text = "Built for intelligent, traceable clause-level document QA.";
            let i = 0;
            function typeWriter() {{
                if (i < text.length) {{
                    document.getElementById("typewriter").innerHTML += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, 40);
                }}
            }}
            typeWriter();

            // Status checker (simulate alive status)
            setTimeout(() => {{
                document.getElementById("liveStatus").textContent = "✅ Online";
                document.getElementById("liveStatus").style.color = "green";
            }}, 500);
        </script>
    </body>
    </html>
    """)