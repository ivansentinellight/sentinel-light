from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import mercadopago
import httpx
import csv
from datetime import datetime

app = FastAPI()

# Configurar MercadoPago
sdk = mercadopago.SDK("APP_USR-3150792417618580-042616-c4e389684373db475f06b2298aaec8e3-2241684433")

# Configurar plantillas
templates = Jinja2Templates(directory="templates")

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# MODELO para crear preferencia
class PreferenceData(BaseModel):
    titulo: str
    precio: float

# RUTA: Página principal
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# RUTA: Crear Preferencia de Pago
@app.post("/crear-preferencia")
def crear_preferencia(preference_data: PreferenceData):
    try:
        preference_data_mp = {
            "items": [{
                "title": preference_data.titulo,
                "quantity": 1,
                "unit_price": float(preference_data.precio),
                "currency_id": "ARS"
            }],
            "back_urls": {
                "success": "http://127.0.0.1:8000/success",
                "failure": "http://127.0.0.1:8000/failure",
                "pending": "http://127.0.0.1:8000/pending"
            }
        }
        preference_response = sdk.preference().create(preference_data_mp)
        if preference_response["status"] != 201:
            raise HTTPException(status_code=400, detail=f"MercadoPago Error: {preference_response['response']}")
        preference_id = preference_response["response"]["id"]
        init_point = preference_response["response"]["init_point"]
        return {"init_point": init_point, "preference_id": preference_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RUTA: Éxito de pago
@app.get("/success", response_class=HTMLResponse)
async def payment_success(request: Request):
    return templates.TemplateResponse("pago_exitoso.html", {"request": request})

# RUTA: Fallo de pago
@app.get("/failure", response_class=HTMLResponse)
async def payment_failure(request: Request):
    return templates.TemplateResponse("pago_fallido.html", {"request": request})

# RUTA: Pago pendiente
@app.get("/pending", response_class=HTMLResponse)
async def payment_pending(request: Request):
    return templates.TemplateResponse("pago_pendiente.html", {"request": request})

# 📄 RUTA: Política de Privacidad
@app.get("/privacidad", response_class=HTMLResponse)
async def privacidad(request: Request):
    return templates.TemplateResponse("privacidad.html", {"request": request})

# 📄 RUTA: Términos de Servicio
@app.get("/terminos", response_class=HTMLResponse)
async def terminos(request: Request):
    return templates.TemplateResponse("terminos.html", {"request": request})

# 🔥 RUTA: Dashboard Gratis (Plan Gratis)
@app.get("/dashboard-gratis", response_class=HTMLResponse)
async def dashboard_gratis(request: Request):
    return templates.TemplateResponse("scanner_gratis.html", {"request": request})

# 🛡️ RUTA: Escanear Email (simulada)
@app.get("/check-email/")
async def check_email(email: str):
    if "hack" in email.lower():
        return {"pwned": True, "data": "Este correo fue encontrado en filtraciones"}
    else:
        return {"pwned": False, "data": "Este correo no aparece en filtraciones conocidas"}

# 🛡️ RUTA: Escanear Website (simulada)
@app.get("/check-website/")
async def check_website(url: str):
    ssl_valid = "https" in url.lower()
    headers_found = {
        "Strict-Transport-Security": "Configurado",
        "Content-Security-Policy": "Configurado",
        "X-Content-Type-Options": "Configurado",
        "X-XSS-Protection": "Configurado",
    }
    return {"ssl_valid": ssl_valid, "headers": headers_found}

# 🚀 RUTA: Scanner POST para formulario
@app.post("/scanner", response_class=HTMLResponse)
async def scanner_submit(request: Request, email: str = Form(None), url: str = Form(None)):
    email_result = None
    website_result = None
    if email:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:8000/check-email/?email={email}")
            email_result = response.json()
        except Exception as e:
            email_result = {"error": str(e)}
    if url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:8000/check-website/?url={url}")
            website_result = response.json()
        except Exception as e:
            website_result = {"error": str(e)}
    return templates.TemplateResponse("scanner_gratis.html", {
        "request": request,
        "email_result": email_result,
        "website_result": website_result
    })

# RUTA: Formulario de contacto con reCAPTCHA
@app.post("/contact", response_class=HTMLResponse)
async def handle_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    g_recaptcha_response: str = Form(...)
):
    try:
        secret_key = "6LfPmycrAAAAAC12QW5C6WEEyJWOGjgHgoVLZvrK"
        data = {
            'secret': secret_key,
            'response': g_recaptcha_response
        }
        async with httpx.AsyncClient() as client:
            verification = await client.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            verification_result = verification.json()
        if not verification_result.get("success"):
            return templates.TemplateResponse("index.html", {"request": request, "confirmation": "❌ Error de verificación reCAPTCHA. Intenta nuevamente."})
        with open("contact_messages.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().isoformat(), name, email, message])
        confirmation = "✅ ¡Gracias por tu mensaje! Lo recibimos correctamente."
        return templates.TemplateResponse("index.html", {"request": request, "confirmation": confirmation})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "confirmation": f"❌ Error al enviar el mensaje: {str(e)}"})
