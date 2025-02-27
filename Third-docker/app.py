from fastapi import FastAPI, Form

app = FastAPI() 

File_path = "/data/storage.txt" # Path to the file where the inputs will be saved/persistance storage

##submit endpoint to receive input from the user and save it to a file
@app.post("/submit/")
def submit_input(user_input: str = Form(...)):
    with open(File_path, "a") as f:
        f.write(user_input + "\n")
    return {"status": "input received", "input": user_input}

##read endpoint to read the saved inputs from the file

@app.get("/")
def read_input():
    try:
        with open(File_path, "r") as f:
            content = f.read().splitlines()
    except FileNotFoundError:
        content = []
    return {"saved_inputs": content}