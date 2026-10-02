from config import GEMINI_API_KEY
from fastapi  import APIRouter, HTTPException
from database import contracts_collection
from bson import objectid

router = APIRouter(
    prefix="/analyse"  ,
    tags=["analysis"]
)

@router.post("/{contract_id}")
async def analyse_contract(contract_id:str):
    """
        Analyse a contract using AI and return insights.
    """
    
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            details =  "AI API key is not configured"
        )
        
    
        
    contract = contracts_collection.find_one({"_id" : objectid(contract_id)})
    
    if contract :
        raise HTTPException(
            status_code=404,
            detail = "Contract not found"
        )
        
    if not contract.get("text_contenrt") :
            
        raise HTTPException(
                    status_code=400,
                    detail = "Contract has not text content to analyse"
                )
        
        
    contracts_collection.update_one({
        "_id" : objectid(contract_id),
      
    },   {
                "$set" : {
                    "analysis_status" : "in_progress"
                }
            })
    
    result = await analyse_contract(contract_id, contract["text_content"])


