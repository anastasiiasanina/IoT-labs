import asyncio
import json
from typing import Set, Dict, List, Any, ClassVar
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body, Depends
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select
from datetime import datetime
from pydantic import BaseModel, field_validator
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)

# FastAPI app setup
app = FastAPI()
# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# SQLAlchemy model
class ProcessedAgentDataCreate(BaseModel):
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float

class ProcessedAgentDataInDB(ProcessedAgentDataCreate):
    id: int
    timestamp: datetime

# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )


class ProcessedAgentData(Base):
    __tablename__ = "processed_agent_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    road_state = Column(String)
    user_id = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# WebSocket subscriptions
subscriptions: Dict[int, Set[WebSocket]] = {}


# FastAPI WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in subscriptions:
        subscriptions[user_id] = set()
    subscriptions[user_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].remove(websocket)


# Function to send data to subscribed users
async def send_data_to_subscribers(user_id: int, data):
    if user_id in subscriptions:
        for websocket in subscriptions[user_id]:
            await websocket.send_json(json.dumps(data))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI CRUDL endpoints

@app.post("/processed_agent_data/")
async def create_processed_agent_data(
    data: ProcessedAgentDataCreate,
    db: Session = Depends(get_db)
):
    db_item = ProcessedAgentData(
        road_state=data.road_state,
        user_id=data.user_id,
        x=data.x,
        y=data.y,
        z=data.z,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def read_processed_agent_data(
    processed_agent_data_id: int,
    db: Session = Depends(get_db)
):
    db_item = db.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data(db: Session = Depends(get_db)):
    return db.query(ProcessedAgentData).all()


@app.put(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def update_processed_agent_data(
    processed_agent_data_id: int,
    data: ProcessedAgentDataCreate,
    db: Session = Depends(get_db)
):
    db_item = db.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.road_state = data.road_state
    db_item.user_id = data.user_id
    db_item.x = data.x
    db_item.y = data.y
    db_item.z = data.z
    db_item.latitude = data.latitude
    db_item.longitude = data.longitude
    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def delete_processed_agent_data(
    processed_agent_data_id: int,
    db: Session = Depends(get_db)
):
    db_item = db.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return db_item


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
