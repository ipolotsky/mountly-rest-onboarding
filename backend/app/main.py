from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import analytics, storage
from app.config import settings
from app.database import create_tables, get_session
from app.ingest import FileTooLargeError, UnsupportedFileError
from app.schemas import (
    AdminMetrics,
    AdminOnboardingRow,
    BankingBlock,
    ConfirmRequest,
    CreateOnboardingRequest,
    CreateOnboardingResponse,
    EventsRequest,
    FeedbackRequest,
    LegalBlock,
    MenuBlock,
    OkResponse,
    Onboarding,
)
from app.service import OnboardingNotFoundError, OnboardingService
from app.service import UploadFile as ServiceUpload


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Restaurant Onboarding API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _service(session: Session = Depends(get_session)) -> OnboardingService:
    return OnboardingService(session)


async def _read_uploads(files: list[UploadFile]) -> list[ServiceUpload]:
    uploads: list[ServiceUpload] = []
    for upload in files:
        content = await upload.read()
        uploads.append(
            ServiceUpload(
                filename=upload.filename or "upload",
                media_type=upload.content_type or "",
                content=content,
            )
        )
    return uploads


def _guard(onboarding_id: str, call):
    try:
        return call()
    except OnboardingNotFoundError as error:
        raise HTTPException(status_code=404, detail="Onboarding not found") from error
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except UnsupportedFileError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/onboarding", response_model=CreateOnboardingResponse)
def create_onboarding(
    body: CreateOnboardingRequest, service: OnboardingService = Depends(_service)
) -> CreateOnboardingResponse:
    onboarding_id = service.create(body.locale, body.device)
    return CreateOnboardingResponse(id=onboarding_id)


@app.get("/api/onboarding/{onboarding_id}", response_model=Onboarding)
def get_onboarding(
    onboarding_id: str, service: OnboardingService = Depends(_service)
) -> Onboarding:
    return _guard(onboarding_id, lambda: service.get(onboarding_id))


@app.post("/api/onboarding/{onboarding_id}/legal/parse", response_model=LegalBlock)
async def parse_legal(
    onboarding_id: str,
    files: list[UploadFile] = File(...),
    note: str | None = Form(default=None),
    service: OnboardingService = Depends(_service),
) -> LegalBlock:
    uploads = await _read_uploads(files)
    return _guard(onboarding_id, lambda: service.parse_legal(onboarding_id, uploads))


@app.put("/api/onboarding/{onboarding_id}/legal", response_model=LegalBlock)
def save_legal(
    onboarding_id: str, block: LegalBlock, service: OnboardingService = Depends(_service)
) -> LegalBlock:
    return _guard(onboarding_id, lambda: service.save_legal(onboarding_id, block))


@app.post("/api/onboarding/{onboarding_id}/banking/parse", response_model=BankingBlock)
async def parse_banking(
    onboarding_id: str,
    files: list[UploadFile] = File(...),
    note: str | None = Form(default=None),
    service: OnboardingService = Depends(_service),
) -> BankingBlock:
    uploads = await _read_uploads(files)
    return _guard(onboarding_id, lambda: service.parse_banking(onboarding_id, uploads))


@app.put("/api/onboarding/{onboarding_id}/banking", response_model=BankingBlock)
def save_banking(
    onboarding_id: str, block: BankingBlock, service: OnboardingService = Depends(_service)
) -> BankingBlock:
    return _guard(onboarding_id, lambda: service.save_banking(onboarding_id, block))


@app.post("/api/onboarding/{onboarding_id}/menu/parse", response_model=MenuBlock)
async def parse_menu(
    onboarding_id: str,
    files: list[UploadFile] = File(...),
    note: str | None = Form(default=None),
    service: OnboardingService = Depends(_service),
) -> MenuBlock:
    uploads = await _read_uploads(files)
    return _guard(onboarding_id, lambda: service.parse_menu(onboarding_id, uploads))


@app.put("/api/onboarding/{onboarding_id}/menu", response_model=MenuBlock)
def save_menu(
    onboarding_id: str, block: MenuBlock, service: OnboardingService = Depends(_service)
) -> MenuBlock:
    return _guard(onboarding_id, lambda: service.save_menu(onboarding_id, block))


@app.post("/api/onboarding/{onboarding_id}/confirm", response_model=Onboarding)
def confirm(
    onboarding_id: str, body: ConfirmRequest, service: OnboardingService = Depends(_service)
) -> Onboarding:
    return _guard(onboarding_id, lambda: service.confirm(onboarding_id, body.step))


@app.post("/api/onboarding/{onboarding_id}/publish", response_model=Onboarding)
def publish(
    onboarding_id: str, service: OnboardingService = Depends(_service)
) -> Onboarding:
    return _guard(onboarding_id, lambda: service.publish(onboarding_id))


@app.post("/api/onboarding/{onboarding_id}/feedback", response_model=OkResponse)
def feedback(
    onboarding_id: str, body: FeedbackRequest, service: OnboardingService = Depends(_service)
) -> OkResponse:
    _guard(onboarding_id, lambda: service.feedback(onboarding_id, body.csat, body.answers))
    return OkResponse()


@app.get("/api/onboarding/{onboarding_id}/restaurant", response_model=Onboarding)
def restaurant(
    onboarding_id: str, service: OnboardingService = Depends(_service)
) -> Onboarding:
    return _guard(onboarding_id, lambda: service.assemble_restaurant(onboarding_id))


@app.get("/api/onboarding/{onboarding_id}/files/{file_id}")
def serve_file(
    onboarding_id: str, file_id: str, service: OnboardingService = Depends(_service)
) -> Response:
    stored = service.get_stored_file(onboarding_id, file_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="File not found")
    content = storage.read_file(stored.path)
    return Response(content=content, media_type=stored.media_type)


@app.post("/api/events", response_model=OkResponse)
def ingest_events(
    body: EventsRequest, session: Session = Depends(get_session)
) -> OkResponse:
    for event in body.events:
        analytics.track_client_event(session, event)
    session.commit()
    return OkResponse()


@app.get("/api/admin/onboardings", response_model=list[AdminOnboardingRow])
def admin_onboardings(
    service: OnboardingService = Depends(_service),
) -> list[AdminOnboardingRow]:
    return service.admin_onboardings()


@app.get("/api/admin/metrics", response_model=AdminMetrics)
def admin_metrics(service: OnboardingService = Depends(_service)) -> AdminMetrics:
    return service.admin_metrics()
