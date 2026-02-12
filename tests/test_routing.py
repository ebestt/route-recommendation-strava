from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import Base
from app.models import SegmentEdge
from app.services.routing import recommend


def test_recommend_prefers_popular_path():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Local = sessionmaker(bind=engine, class_=Session)

    with Local() as db:
        # Path A-B-C (short but unpopular)
        db.add_all(
            [
                SegmentEdge(start_key="0.0:0.0", end_key="0.0:0.01", distance_m=1000, popularity_count=1, avg_speed_mps=6),
                SegmentEdge(start_key="0.0:0.01", end_key="0.0:0.02", distance_m=1000, popularity_count=1, avg_speed_mps=6),
                # Alternate A-D-C (slightly longer but very popular)
                SegmentEdge(start_key="0.0:0.0", end_key="0.01:0.01", distance_m=1300, popularity_count=20, avg_speed_mps=6),
                SegmentEdge(start_key="0.01:0.01", end_key="0.0:0.02", distance_m=1300, popularity_count=20, avg_speed_mps=6),
            ]
        )
        db.commit()

        route = recommend(db, (0.0, 0.0), (0.0, 0.02), target_km=10)
        assert route is not None
        assert route.path[1] == (0.01, 0.01)
