from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
from fasthtml.common import (
    Html, Script, Head, Title, Body, Div, Form, Input, Img, P, to_xml, Style
)
from shad4fast import (
    ShadHead, Card, CardHeader, CardTitle, CardDescription, CardContent,
    Alert, AlertTitle, AlertDescription, Button, Badge, Separator, Lucide, Progress
)
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_URL = os.getenv('BACKEND_URL')
print(f'Backend URL set to: {BACKEND_URL}')

@app.get("/", response_class=HTMLResponse)
async def ui_home():
    content = Html(
        Head(
            Title("Dog Breed Classifier"),
            ShadHead(tw_cdn=True, theme_handle=True),
            Script(
                src="https://unpkg.com/htmx.org@2.0.3",
                integrity="sha384-0895/pl2MU10Hqc6jd4RvrthNlDiE9U1tWmX7WRESftEDRosgxNsQG/Ze9YMRzHq",
                crossorigin="anonymous",
            ),
            Style(
                """
                body {
                    background: url('https://media.giphy.com/media/3o7aD0QrhhK5TYwpuU/giphy.gif'); /* Giphy GIF as background */
                    background-size: cover; /* Cover the entire background */
                    background-repeat: no-repeat; /* Do not repeat the image */
                    background-attachment: fixed; /* Keep the background fixed during scrolling */
                }
                """
            ),
        ),
        Body(
            Div(
                Card(
                    CardHeader(
                        Div(
                            CardTitle("Dog Breed Classifier 🐶"),
                            Badge("AI Powered", variant="secondary", cls="w-fit bg-gradient-to-r from-blue-500 to-green-500 text-white font-bold hover:from-blue-600 hover:to-green-600 transition duration-300"),
                            cls="flex items-center justify-between",
                        ),
                        CardDescription(
                            "Upload an image to classify the breed of the dog. Our AI model will analyze it instantly!"
                        ),
                    ),
                    CardContent(
                        Form(
                            Div(
                                Div(
                                    Input(
                                        type="file",
                                        name="file",
                                        accept="image/*",
                                        required=True,
                                        cls="mb-4 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 file:cursor-pointer",
                                    ),
                                    P(
                                        "Drag and drop an image or click to browse",
                                        cls="text-sm text-muted-foreground text-center mt-2",
                                    ),
                                    cls="border-2 border-dashed rounded-lg p-4 hover:border-primary/50 transition-colors",
                                ),
                                Img(
                                    src="",
                                    id="file-preview",
                                    alt="File Preview",
                                    cls="mt-4 w-full h-auto rounded-lg shadow-lg hidden",
                                ),
                                Button(
                                    Lucide("sparkles", cls="mr-2 h-4 w-4"),
                                    "Classify Image",
                                    type="submit",
                                    cls="w-full bg-gradient-to-r from-blue-500 to-green-500 text-white hover:from-blue-600 hover:to-green-600 transition duration-300",
                                ),
                                cls="space-y-4",
                            ),
                            enctype="multipart/form-data",
                            hx_post="/classify",
                            hx_target="#result",
                        ),
                        Div(id="result", cls="mt-6"),
                    ),
                    cls="w-full max-w-3xl shadow-lg transition-transform transform hover:scale-105",
                    standard=True,
                ),
                cls="container flex items-center justify-center min-h-screen p-4",
            ),
            cls="bg-background text-foreground",
        ),
    )
    return to_xml(content)

@app.post("/classify", response_class=HTMLResponse)
async def classify(request: Request):
    try:
        form = await request.form()
        file = form["file"].file.read()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/predict",
                files={"file": file}
            )
            
            if response.status_code != 200:
                raise Exception("Failed to get prediction from backend service")
                
            result = response.json()
            
            # Create results display
            results = Div(
                Badge(
                    f"Predicted breed: {max(result['predictions'].items(), key=lambda x: x[1])[0]}",
                    variant="outline",
                    cls="bg-green-500/20 hover:bg-green-500/20 border-green-500/50 text-lg",
                ),
                Div(
                    *[
                        Div(
                            P(f"{breed}: {prob:.2%}"),
                            Progress(value=int(prob * 100), cls="h-2"),
                            cls="space-y-2",
                        )
                        for breed, prob in result["predictions"].items()
                    ],
                    cls="mt-4 space-y-4",
                ),
                cls="animate-in fade-in-50 duration-500",
            )
            
            return to_xml(results)
            
    except Exception as e:
        error_alert = Alert(
            AlertTitle("Error ❌"),
            AlertDescription(str(e)),
            variant="destructive",
            cls="mt-4",
        )
        return to_xml(error_alert)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)