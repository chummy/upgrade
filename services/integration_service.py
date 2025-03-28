from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import random
from services.event_bus import subscribe_to_event

class IntegrationService:
    def __init__(self):
        self.setup_event_listeners()
    
    def setup_event_listeners(self):
        # Subscribe to events that should trigger integration operations
        subscribe_to_event("pathway:initialized", self.handle_pathway_initialized)
        subscribe_to_event("pathway:step:completed", self.handle_pathway_step_completed)
    
    def handle_pathway_initialized(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Integration handling pathway:initialized event: {event.id}")
    
    def handle_pathway_step_completed(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Integration handling pathway:step:completed event: {event.id}")
    
    def execute_integration(self, db: Session, config_id: int, operation: str, payload: Dict[str, Any]):
        # Create integration request
        request = models.IntegrationRequest(
            config_id=config_id,
            operation=operation,
            payload=payload,
            status="pending"
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)
        
        try:
            # Update status
            request.status = "processing"
            db.commit()
            
            # Execute the integration
            # In a real implementation, this would call the external system
            # For now, we'll simulate a successful response
            result = None
            
            if operation == "getPatient":
                result = {
                    "id": payload.get("patientId"),
                    "externalId": f"EHR-{payload.get('patientId')}",
                    "demographics": {
                        "firstName": "John",
                        "lastName": "Smith",
                        "dateOfBirth": "1955-03-15",
                        "gender": "male"
                    },
                    "diagnoses": [
                        {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"}
                    ],
                    "medications": [
                        {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}
                    ]
                }
            elif operation == "createOrders":
                result = {
                    "orderId": f"order-{datetime.now().timestamp()}",
                    "patientId": payload.get("patientId"),
                    "tests": [
                        {
                            "code": test,
                            "status": "ordered",
                            "orderedDate": datetime.now().isoformat()
                        } for test in payload.get("tests", [])
                    ]
                }
            else:
                result = {"message": "Operation executed successfully"}
            
            # Update request with result
            request.status = "completed"
            request.result = result
            request.completed_at = datetime.now()
            
            db.commit()
            db.refresh(request)
            
            return result
        except Exception as e:
            # Update request with error
            request.status = "failed"
            request.error = str(e)
            request.completed_at = datetime.now()
            
            db.commit()
            
            raise e
    
    def get_integration_configs(self, db: Session):
        return db.query(models.IntegrationConfig).order_by(models.IntegrationConfig.name.asc()).all()
    
    def upsert_integration_config(self, db: Session, config: Dict[str, Any]):
        if "id" in config and config["id"]:
            # Update existing config
            db_config = db.query(models.IntegrationConfig).filter(
                models.IntegrationConfig.id == config["id"]
            ).first()
            
            if not db_config:
                raise ValueError(f"Integration config {config['id']} not found")
            
            for key, value in config.items():
                if key != "id" and hasattr(db_config, key):
                    setattr(db_config, key, value)
            
            db_config.updated_at = datetime.now()
            
            db.commit()
            db.refresh(db_config)
            
            return db_config
        else:
            # Create new config
            db_config = models.IntegrationConfig(
                name=config["name"],
                system_type=config["system_type"],
                endpoint=config["endpoint"],
                auth_type=config["auth_type"],
                auth_config=config["auth_config"],
                enabled=config.get("enabled", True),
                mappings=config.get("mappings"),
                transformations=config.get("transformations")
            )
            
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            
            return db_config

# Create a singleton instance
integration_service = IntegrationService()
