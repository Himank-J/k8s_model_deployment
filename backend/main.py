from typing import Annotated
import io
import numpy as np
import onnxruntime as ort
from PIL import Image
from fastapi import FastAPI, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# Create main FastAPI app
app = FastAPI(
    title="Image Classification API",
    description="FastAPI application serving an ONNX model for image classification",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
INPUT_SIZE = (160, 160)
MEAN = np.array([0.485, 0.456, 0.406])
STD = np.array([0.229, 0.224, 0.225])
LABELS = ['Beagle', 'Boxer', 'Bulldog', 'Dachshund', 'German_Shepherd', 'Golden_Retriever', 'Labrador_Retriever', 'Poodle', 'Rottweiler', 'Yorkshire_Terrier']
BREED_FACTS = {
    'Beagle': "Beagles have approximately 220 million scent receptors, compared to a human's mere 5 million!",
    'Boxer': "Boxers were among the first dogs to be employed as police dogs.",
    'Bulldog': "Despite their tough appearance, Bulldogs were bred to be companion dogs.",
    'Dachshund': "Dachshunds were originally bred to hunt badgers - their name literally means 'badger dog' in German!",
    'German_Shepherd': "German Shepherds can learn a new command in as little as 5 repetitions.",
    'Golden_Retriever': "Golden Retrievers were originally bred as hunting dogs.",
    'Labrador_Retriever': "Labs have a special water-resistant coat and unique otter-like tail.",
    'Poodle': "Despite their elegant appearance, Poodles were originally water retrievers!",
    'Rottweiler': "Rottweilers are descendants of Roman drover dogs.",
    'Yorkshire_Terrier': "Yorkies were originally bred to catch rats in clothing mills."
}

# Load the ONNX model
try:
    print("Loading ONNX model...")
    ort_session = ort.InferenceSession("models/onnx_model.onnx")
    ort_session.run(
        ["output"], {"input": np.random.randn(1, 3, *INPUT_SIZE).astype(np.float32)}
    )
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    raise

class PredictionResponse(BaseModel):
    predictions: dict
    success: bool
    message: str

def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.convert("RGB")
    image = image.resize(INPUT_SIZE)
    img_array = np.array(image).astype(np.float32) / 255.0
    img_array = (img_array - MEAN) / STD
    img_array = img_array.transpose(2, 0, 1)
    img_array = np.expand_dims(img_array, 0)
    return img_array

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: Annotated[bytes, File(description="Image file to classify")]):
    try:
        image = Image.open(io.BytesIO(file))
        processed_image = preprocess_image(image)
        
        outputs = ort_session.run(
            ["output"], {"input": processed_image.astype(np.float32)}
        )

        logits = outputs[0][0]
        probabilities = np.exp(logits) / np.sum(np.exp(logits))

        top_indices = np.argsort(probabilities)[-5:][::-1]
        predictions = {LABELS[i]: float(probabilities[i]) for i in top_indices}

        return PredictionResponse(
            predictions=predictions,
            success=True,
            message="Classification successful"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "model_loaded": True},
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)