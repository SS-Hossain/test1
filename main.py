from fastapi import FastAPI,Path, HTTPException, Query
from pydantic import BaseModel, Field, computed_field
import json
from typing import Annotated, Literal, Optional as optional
from fastapi.responses import JSONResponse

app = FastAPI()

class Patient(BaseModel):
    id:Annotated[str,Field(..., description="ID of the patient", example="P001")]
    name:Annotated[str,Field(..., description="Name of the patient", example="John Doe")]
    city:Annotated[str,Field(..., description="City of residence", example="New York")]
    age:Annotated[int,Field(...,gt = 0, lt = 120, description = "Age of the patient", example=30)]
    gender:Annotated[Literal['male','female','other'], Field(..., description = "Gender of the patient")]
    weight:Annotated[float,Field(...,gt = 0, description="Weight of the patient in kg", example=70.5)]
    height:Annotated[float,Field(...,gt = 0, description="Height of the patient in mtrs", example=1.75)]


    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 25:
            return "Normal weight"
        elif 25 <= self.bmi < 30:
            return "Normal weight"
        else:
            return "Obese"
        
class Update(BaseModel):
   
    name:Annotated[optional[str],Field(default = None)]
    city:Annotated[optional[str],Field(default = None)]
    age:Annotated[optional[int],Field(default = None,gt = 0, lt = 120)]
    gender:Annotated[optional[Literal['male','female','other']], Field(default = None)]
    weight:Annotated[optional[float],Field(default = None, gt = 0)]
    height:Annotated[optional[float],Field(default = None, gt = 0)]


def load_patients():
    with open('patients.json') as f:
        data = json.load(f)
    return data

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)

@app.get("/")
def hello():
    return {'message':'Patient Management System API'}


@app.get("/about")
def about():
    return {'message':'A fully functional API to manage your patient records'}

@app.get("/view")
def view():
    data = load_patients()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id:str = Path(..., description = "ID of the patient",example = "P001")):
    data = load_patients()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail="Patient not found")
    

@app.get("/sort")
def sort_patents(sort_by:str = Query(..., description = "Field to sort by weight, bmi or height", example = "weight"),
                 order:str = Query("asc", description = "Sort order: asc or desc", example = "asc")):
    
    valid_field = ["weight", "bmi", "height"]

    if sort_by not in valid_field:
        raise HTTPException(status_code = 400, detail = f"Invalid sort field. Must be weight, bmi or height {sort_by}")

    order_by = True if order == "desc" else False

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code = 400, detail = f"Invalid sort order. Must be asc or desc {order}")
    
    data = load_patients()
    sorted_data = sorted(
        data.values(), 
        key = lambda x: x.get(sort_by, 0), 
        reverse=order_by
        )

    return sorted_data

@app.post("/create")
def create(patient:Patient):

    # load data
    data = load_patients()

    # check if patient already exists

    if patient.id in data:
        raise HTTPException(status_code = 400, detail = "Patient already exists")
    
    # convert Patient object to dict and add new data to database
    data[patient.id] = patient.model_dump(exclude = {"id"})

    #save data back to json file
    save_data(data)

    return JSONResponse(status_code = 201, content = {'message':'Patient created successfully'})


@app.put("/update/{patient_id}")
def update(patient_id:str, update:Update):
    data = load_patients()

    if patient_id not in data:
        raise HTTPException(status_code = 404, detail = "Patient not found")
    
    existing_patient_info = data[patient_id]

    updated_patient_info = update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    # existing atient info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id    
    patient_pydantic_obj = Patient(**existing_patient_info)

    # convert pydantic object to dict
    existing_patient_info = patient_pydantic_obj.model_dump(exclude = 'id')

    # add this dict back to data with patient id as key
    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code = 200, content = {'message':'Patient updated successfully'})


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id:str):
    data = load_patients()

    if patient_id not in data:
        raise HTTPException(status_code = 404, detail = "Patient not found")
    
    del data[patient_id]

    save_data(data)
    return JSONResponse(status_code = 200, content = {'message':'Patient deleted successfully'})




