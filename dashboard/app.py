from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from core import proxy_state

app = FastAPI(title="Mini Burp Suite Dashboard")

# Introduce the external HTML templates directory to FastAPI
templates = Jinja2Templates(directory="dasboard/templates")


@app.get("/")
def show_dashboard(request: Request):
    # Fetch the latest captured packet from the shared flag register
    packet_to_show = proxy_state["current_request"] if proxy_state["current_request"] else "No request intercepted yet."

    # Pass request as a direct parameter to satisfy Jinja2Templates requirements
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={"captured_packet": packet_to_show}
    )