import json
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.forms.upload_form import UploadClassificationForm, delete_folder
from app.forms.image_histograme_form import ImageHistogrameForm
from app.ml.classification_utils import classify_image
from app.utils import list_images
from PIL import Image, ImageEnhance
import os


app = FastAPI()
config = Configuration()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/info")
def info() -> dict[str, list[str]]:
    """Returns a dictionary with the list of models and
    the list of available image files."""
    list_of_images = list_images()
    list_of_models = Configuration.models
    data = {"models": list_of_models, "images": list_of_images}
    return data


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """The home page of the service."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/classifications")
def create_classify(request: Request):
    return templates.TemplateResponse(
        "classification_select.html",
        {"request": request, "images": list_images(), "models": Configuration.models},
    )


@app.get("/upload")
def create_classify(request: Request):
    return templates.TemplateResponse(
        "upload_classification_select.html",
        {"request": request, "images": list_images(), "models": Configuration.models},
    )


@app.get("/transformations", response_class=HTMLResponse)
def show_transformation_form(request: Request):
    return templates.TemplateResponse(
        "transformation_form.html",
        {
            "request": request,
            "images": list_images(),
        },
    )


@app.get("/download/json/{image_id}")
async def download_json(image_id: str):
    classification_scores = classify_image(image_id)
    return JSONResponse(content=classification_scores, media_type="application/json")


@app.get("/download_results/{image_id}")
async def download_results(image_id: str, model_id: str):
    classification_scores = classify_image(model_id=model_id, img_id=image_id)
    return JSONResponse(content=classification_scores)


@app.get("/image_histogrames")
def create_classify(request: Request):
    return templates.TemplateResponse(
        "image_histograme_select.html",
        {"request": request, "images": list_images()},
    )


@app.post("/classifications")
async def request_classification(request: Request):
    form = ClassificationForm(request)
    await form.load_data()
    image_id = form.image_id
    model_id = form.model_id
    classification_scores = classify_image(model_id=model_id, img_id=image_id)
    return templates.TemplateResponse(
        "classification_output.html",
        {
            "request": request,
            "image_id": image_id,
            "model_id": model_id,
            "classification_scores": json.dumps(classification_scores),
        },
    )


@app.post("/upload")
async def request_classification(request: Request, background_tasks: BackgroundTasks):
    form = UploadClassificationForm(request)
    try:
        await form.load_data()
        image_id = form.image_id
        upload_dir = form.upload_dir
        relative_image_path = upload_dir[11:] + "/" + image_id
        model_id = form.model_id
        classification_scores = classify_image(
            model_id=model_id, img_id=image_id, img_dir=upload_dir
        )
        if hasattr(form, "upload_dir"):
            background_tasks.add_task(delete_folder, upload_dir)

        return templates.TemplateResponse(
            "upload_classification_output.html",
            {
                "request": request,
                "image_id": image_id,
                "image_dir": relative_image_path,
                "classification_scores": json.dumps(classification_scores),
            },
        )
    except Exception as e:
        print(f"Error during classification: {e}")
        if hasattr(form, "upload_dir"):
            background_tasks.add_task(delete_folder, form.upload_dir)

        return templates.TemplateResponse(
            "upload_classification_select.html",
            {
                "request": request,
                "images": list_images(),
                "models": Configuration.models,
                "error_message": "Invalid file or classification error. Please try again.",
            },
            status_code=400,
        )


@app.post("/transformations", response_class=HTMLResponse)
async def apply_transformation(
    request: Request,
    image_id: str = Form(...),
    color: float = Form(...),
    brightness: float = Form(...),
    contrast: float = Form(...),
    sharpness: float = Form(...),
):
    image_path = os.path.join(config.image_folder_path, image_id)
    img = Image.open(image_path)

    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    output_path = os.path.join("app", "static", "transformed_image.jpeg")
    img.save(output_path)

    return templates.TemplateResponse(
        "transformation_result.html",
        {
            "request": request,
            "original_image": image_id,
            "transformed_image": "transformed_image.jpeg",
        },
    )


@app.post("/image_histogrames")
async def request_classification(request: Request):
    form = ImageHistogrameForm(request)
    await form.load_data()
    image_id = form.image_id
    return templates.TemplateResponse(
        "image_histograme_output.html",
        {
            "request": request,
            "image_id": image_id,
        },
    )
