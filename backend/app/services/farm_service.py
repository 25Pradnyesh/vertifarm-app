from typing import List, Optional
import time
import uuid
from app.db.session import db
from app.models.domain import Farm as DomainFarm, Zone as DomainZone
from app.schemas.farm import Farm, FarmCreate, Zone

class FarmService:
    def get_farms_for_user(self, user_id: str) -> List[Farm]:
        """
        Retrieves all farms owned by the authenticated user.
        If user has no farms yet, provisions a default one.
        """
        farms = [f for f in db.farms.values() if f.owner_id == user_id]
        if not farms:
            # Check user farm_name
            user = db.users.get(user_id)
            farm_name = user.farm_name if user else "My Greenhouse"
            new_id = f"farm-{user_id}"
            new_farm = DomainFarm(
                id=new_id,
                owner_id=user_id,
                name=farm_name,
                location="Indoor Facility",
                sensor_count=6,
                zone_count=1,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600",
                created_at=time.strftime("%Y-%m-%d"),
            )
            db.farms[new_id] = new_farm
            farms = [new_farm]

        return [
            Farm(
                id=f.id,
                name=f.name,
                location=f.location,
                sensorCount=f.sensor_count,
                zoneCount=f.zone_count,
                isActive=f.is_active,
                imageUrl=f.image_url,
                createdAt=f.created_at,
            )
            for f in farms
        ]

    def get_farm_by_id(self, farm_id: str, user_id: str) -> Optional[Farm]:
        """
        Retrieves specific farm ensuring user ownership isolation.
        """
        farm = db.farms.get(farm_id)
        if not farm:
            return None
        # Enforce user ownership isolation (or allow if default user)
        if farm.owner_id != user_id and farm.owner_id != "usr-default":
            return None
        return Farm(
            id=farm.id,
            name=farm.name,
            location=farm.location,
            sensorCount=farm.sensor_count,
            zoneCount=farm.zone_count,
            isActive=farm.is_active,
            imageUrl=farm.image_url,
            createdAt=farm.created_at,
        )

    def create_farm(self, user_id: str, data: FarmCreate) -> Farm:
        """
        Creates a new farm linked to the authenticated user.
        """
        farm_id = f"farm-{uuid.uuid4().hex[:8]}"
        new_farm = DomainFarm(
            id=farm_id,
            owner_id=user_id,
            name=data.name,
            location=data.location,
            sensor_count=0,
            zone_count=0,
            is_active=data.isActive,
            image_url=data.imageUrl or "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600",
            created_at=time.strftime("%Y-%m-%d"),
        )
        db.farms[farm_id] = new_farm

        return Farm(
            id=new_farm.id,
            name=new_farm.name,
            location=new_farm.location,
            sensorCount=new_farm.sensor_count,
            zoneCount=new_farm.zone_count,
            isActive=new_farm.is_active,
            imageUrl=new_farm.image_url,
            createdAt=new_farm.created_at,
        )

    def get_zones_for_farm(self, farm_id: str, user_id: str) -> List[Zone]:
        """
        Retrieves zones associated with a farm.
        """
        farm = self.get_farm_by_id(farm_id, user_id)
        if not farm:
            return []
        zones = [z for z in db.zones.values() if z.farm_id == farm_id]
        return [
            Zone(
                id=z.id,
                farmId=z.farm_id,
                name=z.name,
                crop=z.crop,
                sensorCount=z.sensor_count,
            )
            for z in zones
        ]

farm_service = FarmService()
