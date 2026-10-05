from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(
    prefix="/api/v1/providers",
    tags=["Provider Search"],
)


@router.get("/nearby")
def get_nearby_providers(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
    radius_km: float = Query(
        default=5,
        gt=0,
        le=100,
    ),
    db: Session = Depends(get_db),
):

    query = text(
        """
        SELECT
            pp.id AS provider_id,
            pp.business_name,
            pp.description,
            pp.address,
            pp.city,
            pp.state,
            pp.pincode,

            pp.latitude,
            pp.longitude,

            ST_Distance(
                ST_SetSRID(
                    ST_MakePoint(
                        pp.longitude,
                        pp.latitude
                    ),
                    4326
                )::geography,

                ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    4326
                )::geography

            ) / 1000.0 AS distance_km,

            pp.is_available,
            pp.is_verified,
            pp.service_radius_km

        FROM provider_profiles pp

        WHERE
            pp.latitude IS NOT NULL
            AND pp.longitude IS NOT NULL

            AND pp.is_available = TRUE

            AND ST_DWithin(
                ST_SetSRID(
                    ST_MakePoint(
                        pp.longitude,
                        pp.latitude
                    ),
                    4326
                )::geography,

                ST_SetSRID(
                    ST_MakePoint(
                        :longitude,
                        :latitude
                    ),
                    4326
                )::geography,

                :radius_meters
            )

        ORDER BY distance_km ASC

        LIMIT 50
        """
    )

    result = db.execute(
        query,
        {
            "latitude": latitude,
            "longitude": longitude,
            "radius_meters": radius_km * 1000,
        },
    )

    providers = result.mappings().all()

    return {
        "count": len(providers),
        "providers": providers,
    }