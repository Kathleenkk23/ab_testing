"""High-throughput batch event processing for large-scale A/B testing"""
import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Event, Experiment
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class BatchEventProcessor:
    """
    High-performance batch event processor for large-scale A/B testing.

    **Features:**
    - Bulk inserts for maximum throughput
    - Async processing for concurrent requests
    - Validation and error handling
    - Performance monitoring
    - Memory-efficient processing
    """

    BATCH_SIZE = 1000  # Process in chunks to avoid memory issues
    MAX_CONCURRENT_BATCHES = 5  # Limit concurrent processing

    @staticmethod
    async def process_events_batch_async(
        events_data: List[Dict[str, Any]],
        experiment_id: int
    ) -> Dict[str, Any]:
        """
        Process a batch of events asynchronously for high throughput.

        **Args:**
        - events_data: List of event dictionaries
        - experiment_id: Experiment to associate events with

        **Returns:**
        - Processing results with success/failure counts
        """
        logger.info(f"Starting async batch processing: {len(events_data)} events for experiment {experiment_id}")

        # Validate experiment exists
        db = SessionLocal()
        try:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                return {
                    "success": False,
                    "error": f"Experiment {experiment_id} not found",
                    "processed": 0,
                    "total": len(events_data)
                }
        finally:
            db.close()

        # Process in chunks
        semaphore = asyncio.Semaphore(BatchEventProcessor.MAX_CONCURRENT_BATCHES)
        tasks = []

        for i in range(0, len(events_data), BatchEventProcessor.BATCH_SIZE):
            chunk = events_data[i:i + BatchEventProcessor.BATCH_SIZE]
            task = asyncio.create_task(
                BatchEventProcessor._process_chunk(chunk, experiment_id, semaphore)
            )
            tasks.append(task)

        # Wait for all chunks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        total_processed = 0
        total_failed = 0
        errors = []

        for result in results:
            if isinstance(result, Exception):
                total_failed += BatchEventProcessor.BATCH_SIZE
                errors.append(str(result))
            else:
                total_processed += result.get("processed", 0)
                total_failed += result.get("failed", 0)
                if result.get("errors"):
                    errors.extend(result["errors"])

        return {
            "success": True,
            "processed": total_processed,
            "failed": total_failed,
            "total": len(events_data),
            "errors": errors[:10] if len(errors) > 10 else errors  # Limit error details
        }

    @staticmethod
    async def _process_chunk(
        chunk: List[Dict[str, Any]],
        experiment_id: int,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Process a single chunk of events.
        """
        async with semaphore:
            db = SessionLocal()
            try:
                processed = 0
                failed = 0
                errors = []

                # Validate and prepare events
                valid_events = []
                for event_data in chunk:
                    try:
                        # Basic validation
                        user_id = event_data.get("user_id")
                        variant = event_data.get("variant")
                        event_type = event_data.get("event_type")
                        creative_id = event_data.get("creative_id")

                        if not all([user_id, variant, event_type]):
                            failed += 1
                            errors.append("Missing required fields")
                            continue

                        if variant not in ["control", "treatment"]:
                            failed += 1
                            errors.append(f"Invalid variant: {variant}")
                            continue

                        if event_type not in ["impression", "click", "conversion"]:
                            failed += 1
                            errors.append(f"Invalid event_type: {event_type}")
                            continue

                        # Auto-detect creative_id if not provided
                        if creative_id is None:
                            from app.services.creative import CreativeService
                            creative = CreativeService.get_creative_for_variant(
                                experiment_id, variant, db
                            )
                            if creative:
                                creative_id = creative["creative_id"]

                        valid_events.append(Event(
                            user_id=user_id,
                            experiment_id=experiment_id,
                            variant=variant,
                            event_type=event_type,
                            creative_id=creative_id
                        ))
                        processed += 1

                    except Exception as e:
                        failed += 1
                        errors.append(str(e))

                # Bulk insert valid events
                if valid_events:
                    db.add_all(valid_events)
                    db.commit()

                return {
                    "processed": processed,
                    "failed": failed,
                    "errors": errors[:5]  # Limit per chunk
                }

            except Exception as e:
                logger.error(f"Error processing chunk: {str(e)}")
                db.rollback()
                return {
                    "processed": 0,
                    "failed": len(chunk),
                    "errors": [str(e)]
                }
            finally:
                db.close()

    @staticmethod
    def bulk_insert_events_sqlite(
        events_data: List[Dict[str, Any]],
        experiment_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Use raw SQL for maximum performance on SQLite.

        **Note:** This bypasses SQLAlchemy ORM for speed.
        """
        try:
            # Prepare data for bulk insert
            values = []
            processed = 0
            failed = 0
            errors = []

            for event_data in events_data:
                try:
                    user_id = event_data.get("user_id")
                    variant = event_data.get("variant")
                    event_type = event_data.get("event_type")
                    creative_id = event_data.get("creative_id")

                    # Auto-detect creative_id if not provided
                    if creative_id is None:
                        from app.services.creative import CreativeService
                        creative = CreativeService.get_creative_for_variant(
                            experiment_id, variant, db
                        )
                        if creative:
                            creative_id = creative["creative_id"]

                    # Handle NULL creative_id
                    creative_value = f"{creative_id}" if creative_id is not None else "NULL"
                    values.append(f"({user_id}, {experiment_id}, '{variant}', '{event_type}', {creative_value})")
                    processed += 1

                except Exception as e:
                    failed += 1
                    errors.append(str(e))

            if not values:
                return {"processed": processed, "failed": failed, "errors": errors}

            # Execute bulk insert
            values_str = ",".join(values)
            sql = f"""
            INSERT INTO events (user_id, experiment_id, variant, event_type, creative_id)
            VALUES {values_str}
            """

            db.execute(text(sql))
            db.commit()

            return {
                "processed": len(values),
                "failed": 0,
                "errors": []
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            return {
                "processed": 0,
                "failed": len(events_data),
                "errors": [str(e)]
            }

    @staticmethod
    def validate_event_batch(events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pre-validate a batch of events before processing.

        **Returns:**
        - valid_events: List of valid event dictionaries
        - validation_errors: List of validation error messages
        """
        valid_events = []
        validation_errors = []

        for idx, event_data in enumerate(events_data):
            errors = []

            # Required fields
            if "user_id" not in event_data:
                errors.append("user_id is required")
            elif not isinstance(event_data["user_id"], int) or event_data["user_id"] <= 0:
                errors.append("user_id must be a positive integer")

            if "variant" not in event_data:
                errors.append("variant is required")
            elif event_data["variant"] not in ["control", "treatment"]:
                errors.append("variant must be 'control' or 'treatment'")

            if "event_type" not in event_data:
                errors.append("event_type is required")
            elif event_data["event_type"] not in ["impression", "click", "conversion"]:
                errors.append("event_type must be 'impression', 'click', or 'conversion'")

            if errors:
                validation_errors.append({
                    "index": idx,
                    "errors": errors
                })
            else:
                valid_events.append(event_data)

        return {
            "valid_events": valid_events,
            "validation_errors": validation_errors,
            "total_valid": len(valid_events),
            "total_invalid": len(validation_errors)
        }