import logging
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)



def standard_response_generator(
    success, message, http_status, data={}
):
    logger.info("API RESPONSE")
    response = {
        "success": success,
        "message": message,
        "data": data,
    }
    json_compatible_response = jsonable_encoder(response)
    api_response = JSONResponse(status_code=http_status, content=json_compatible_response)
    logger.info(f"RESPONSE_STATUS_CODE : {api_response.status_code}")
    logger.info(f"RESPONSE_DATA : {response}")
    logger.info(f"RESPONSE_HEADERS : {api_response.headers}")
    return api_response
