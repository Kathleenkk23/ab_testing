from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database setup
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


from sqlalchemy import create_engine, Index
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database setup
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_indexes():
    """
    Create database indexes for optimal query performance.

    **Indexes created:**
    - experiments.name: For experiment lookup by name
    - assignments.experiment_id + user_id: For user assignment checks
    - assignments.experiment_id: For experiment assignment counts
    - events.experiment_id + variant + event_type: For metrics calculation
    - events.experiment_id + event_type: For impression/conversion counts
    - events.variant + event_type: For cross-experiment analysis
    """
    try:
        # Experiment indexes
        Index('idx_experiments_name', Base.metadata.tables['experiments'].c.name)

        # Assignment indexes
        Index('idx_assignments_experiment_user',
              Base.metadata.tables['assignments'].c.experiment_id,
              Base.metadata.tables['assignments'].c.user_id)
        Index('idx_assignments_experiment',
              Base.metadata.tables['assignments'].c.experiment_id)

        # Event indexes (most critical for performance)
        Index('idx_events_experiment_variant_type',
              Base.metadata.tables['events'].c.experiment_id,
              Base.metadata.tables['events'].c.variant,
              Base.metadata.tables['events'].c.event_type)
        Index('idx_events_experiment_type',
              Base.metadata.tables['events'].c.experiment_id,
              Base.metadata.tables['events'].c.event_type)
        Index('idx_events_variant_type',
              Base.metadata.tables['events'].c.variant,
              Base.metadata.tables['events'].c.event_type)
        Index('idx_events_created_at',
              Base.metadata.tables['events'].c.created_at)

        print("✅ Database indexes created successfully")
        return True

    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False


def optimize_database():
    """
    Run database optimization commands for SQLite.

    **Optimizations:**
    - VACUUM: Reclaim unused space
    - ANALYZE: Update query planner statistics
    - WAL mode: Better concurrent access
    """
    try:
        with engine.connect() as conn:
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA cache_size=10000;")  # 10MB cache
            conn.execute("PRAGMA temp_store=MEMORY;")

            # Analyze tables for better query planning
            conn.execute("ANALYZE;")

            # Vacuum to reclaim space (only if needed)
            # conn.execute("VACUUM;")  # Commented out as it can be slow

        print("✅ Database optimized successfully")
        return True

    except Exception as e:
        print(f"❌ Error optimizing database: {e}")
        return False


def get_database_stats():
    """
    Get database statistics for monitoring.

    **Returns:**
    - Table row counts
    - Index information
    - Database file size
    """
    try:
        stats = {}

        with engine.connect() as conn:
            # Get table row counts
            tables = ['experiments', 'assignments', 'events']
            for table in tables:
                result = conn.execute(f"SELECT COUNT(*) FROM {table};")
                stats[f'{table}_count'] = result.fetchone()[0]

            # Get database file size
            result = conn.execute("PRAGMA page_count;")
            page_count = result.fetchone()[0]
            result = conn.execute("PRAGMA page_size;")
            page_size = result.fetchone()[0]
            stats['database_size_bytes'] = page_count * page_size
            stats['database_size_mb'] = round(page_count * page_size / (1024 * 1024), 2)

        return stats

    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return None
