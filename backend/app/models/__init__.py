# Import all models so SQLAlchemy/Alembic can discover them
from .user import User
from .site import Site, Zone
from .operator import Operator, OperatorCertification, OperatorBreak
from .machine import Machine, MachineModel, MachineFault, MachineMaintenance
from .task import Task, TaskEvent
from .telemetry import Telemetry, WearableEvent, EnvironmentalData
from .safety import (
    Alert, ProximityEvent, Incident,
    PrestartCheck, MachinePermission,
    DashcamEvent, AuditLog,
)
from .training import TrainingModule, OperatorTraining, TrainingRecommendation
from .operator_extras import NearMissEvent, GutCheckResponse

__all__ = [
    "User",
    "Site", "Zone",
    "Operator", "OperatorCertification", "OperatorBreak",
    "Machine", "MachineModel", "MachineFault", "MachineMaintenance",
    "Task", "TaskEvent",
    "Telemetry", "WearableEvent", "EnvironmentalData",
    "Alert", "ProximityEvent", "Incident",
    "PrestartCheck", "MachinePermission",
    "DashcamEvent", "AuditLog",
    "TrainingModule", "OperatorTraining", "TrainingRecommendation",
    "NearMissEvent", "GutCheckResponse",
]
