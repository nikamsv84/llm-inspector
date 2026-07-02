from fastapi import FastAPI
app = FastAPI(title="mini burp suit test api")

@app.get("/")
def health_check():
    return "welcome to burp suite"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Mini Burp Suite"}
@app.get("/requests/{request_id}")
def get_result_details(request_id:str):
    return {"message": f"Fetching request history for ID: {request_id}"}