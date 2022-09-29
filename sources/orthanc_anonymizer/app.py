from fastapi import FastAPI, Header
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse
from starlette.background import BackgroundTask
import logging
import urllib.parse
import os
import httpx
import typing

logging.basicConfig(level=logging.DEBUG)


# try to read a secret first from a secret file or from an env var.
# stop execution if not
def get_secret_or_die(name: str):
    secret_file_path = f"/run/secrets/{name}"
    if os.path.exists(secret_file_path) and os.path.isfile(secret_file_path):
        with open(secret_file_path, "rt") as secret_file:
            return secret_file.read().strip()

    if os.environ.get(name) is not None:
        return os.environ.get(name)

    logging.error(f"Secret '{name}' is not defined, can not start without it")
    exit(-1)


orthanc_root = get_secret_or_die("ORTHANC_ROOT")

a_client = httpx.AsyncClient(base_url=orthanc_root)
s_client = httpx.Client(base_url=orthanc_root)

app = FastAPI()


# generic class to handle anonymization of a route.
# the anonymization itself is provided in the modifier method passed at construct time
class Anonymizer:

    modifier: typing.Callable
    block_any_query_args: bool

    def __init__(self, modifier: typing.Callable, block_any_query_args: bool = True):
        self.modifier = modifier
        self.block_any_query_args = block_any_query_args

    async def handle(self, request: Request):
        url = httpx.URL(path=request.url.path,
                        query=request.url.query.encode("utf-8"))

        # disallow "full", "short", "requestedTags"
        if len(request.query_params) > 0 and self.block_any_query_args:
            return JSONResponse(content={}, status_code=403)

        orthanc_request = s_client.build_request(request.method, url,
                                        headers=request.headers.raw,
                                        content=await request.body())
        orthanc_response = s_client.send(orthanc_request, stream=False)

        # custom anonymization
        anonymized_response = self.modifier(orthanc_response.json())

        return JSONResponse(content=anonymized_response,
                            status_code=orthanc_response.status_code)

def anonymize_tag(tags: dict, key: str, value: str = "Anonymized"):
    if key in tags:
        tags[key] = value

def remove_tag(tags: dict, key: str):
    if key in tags:
        del tags[key]

def anonymize_tags(tags):
    # note: only the MainDicomTags and ExtraMainDicomTags are used by the OsimisViewer
    anonymize_tag(tags, "PatientName")
    anonymize_tag(tags, "PatientID")
    anonymize_tag(tags, "PatientSex", "U")
    remove_tag(tags, "PatientBirthDate")

    remove_tag(tags, "StudyInstanceUID")
    remove_tag(tags, "StudyID")
    remove_tag(tags, "StudyTime")
    remove_tag(tags, "StudyDate")
    remove_tag(tags, "AccessionNumber")
    remove_tag(tags, "InstitutionName")
    remove_tag(tags, "ReferringPhysicianName")
    remove_tag(tags, "ConsultingPhysicianName")
    remove_tag(tags, "RequestingPhysician")

    return tags


def anonymize_patient(s):
    s["MainDicomTags"] = anonymize_tags(s["MainDicomTags"])
    return s


def anonymize_study(s):
    s["PatientMainDicomTags"] = anonymize_tags(s["PatientMainDicomTags"])
    s["MainDicomTags"] = anonymize_tags(s["MainDicomTags"])
    return s

def anonymize_series_study(s):
    s["PatientMainDicomTags"] = anonymize_tags(s["PatientMainDicomTags"])
    s["MainDicomTags"] = anonymize_tags(s["MainDicomTags"])
    return s

def anonymize_viewer_study(s):
    s["PatientMainDicomTags"] = anonymize_tags(s["PatientMainDicomTags"])
    s["MainDicomTags"] = anonymize_tags(s["MainDicomTags"])
    return s

def anonymize_viewer_series(s):
    for (instance_id, instance_info) in s["instancesInfos"].items():
        anonymize_tags(instance_info["TagsSubset"])

    anonymize_tags(s["middleInstanceInfos"]["TagsSubset"])
    return s

# generic reverse proxy with no modifications
async def generic_reverse_proxy(request: Request):
    url = httpx.URL(path=request.url.path,
                    query=request.url.query.encode("utf-8"))
    rp_req = a_client.build_request(request.method, url,
                                  headers=request.headers.raw,
                                  content=await request.body())
    rp_resp = await a_client.send(rp_req, stream=True)
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )

############## untouched routes
## images
app.add_route("/osimis-viewer/images/{instance_id:str}/{frame_id:int}/high-quality", generic_reverse_proxy, ["GET"])
app.add_route("/osimis-viewer/images/{instance_id:str}/{frame_id:int}/medium-quality", generic_reverse_proxy, ["GET"])
app.add_route("/osimis-viewer/images/{instance_id:str}/{frame_id:int}/low-quality", generic_reverse_proxy, ["GET"])
app.add_route("/osimis-viewer/images/{instance_id:str}/{frame_id:int}/pixeldata-quality", generic_reverse_proxy, ["GET"])

## static resources
app.add_route("/osimis-viewer/app/{path:path}", generic_reverse_proxy, ["GET"])
app.add_route("/osimis-viewer/languages/{path:path}", generic_reverse_proxy, ["GET"])
app.add_route("/osimis-viewer/config.js", generic_reverse_proxy, ["GET"])

############## anonymized routes
app.add_route("/osimis-viewer/studies/{study_id:str}", Anonymizer(anonymize_viewer_study).handle, ["GET"])
app.add_route("/osimis-viewer/series/{series_id:str}", Anonymizer(anonymize_viewer_series).handle, ["GET"])
app.add_route("/studies/{study_id:str}", Anonymizer(anonymize_study).handle, ["GET"])
app.add_route("/series/{study_id:str}/study", Anonymizer(anonymize_series_study).handle, ["GET"])
app.add_route("/patients/{patient_id:str}", Anonymizer(anonymize_patient).handle, ["GET"])
