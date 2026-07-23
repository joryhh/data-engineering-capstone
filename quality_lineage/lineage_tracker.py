import uuid
from datetime import datetime, UTC
from contextlib import contextmanager

from openlineage.client import OpenLineageClient
from openlineage.client.transport.console import ConsoleTransport, ConsoleConfig
from openlineage.client.event_v2 import RunEvent, RunState, Run, Job
from openlineage.client.uuid import generate_new_uuid

NAMESPACE = "wafra-capstone"

# ConsoleTransport prints lineage events to stdout instead of needing a
# running Marquez server — keeps this demonstrable without extra infra.
client = OpenLineageClient(transport=ConsoleTransport(ConsoleConfig()))


@contextmanager
def track_stage(stage_name: str):
    """Emits a START event on entry, then COMPLETE or FAIL on exit,
    depending on whether an exception was raised inside the block."""
    run_id = str(generate_new_uuid())
    job = Job(namespace=NAMESPACE, name=stage_name)
    run = Run(runId=run_id)

    print(f"\n📡 [LINEAGE] START  -> stage='{stage_name}' run_id={run_id}")
    client.emit(RunEvent(
        eventType=RunState.START,
        eventTime=datetime.now(UTC).isoformat(),
        run=run,
        job=job,
        producer="https://github.com/joryhh/data-engineering-capstone",
    ))

    try:
        yield
    except Exception:
        print(f"📡 [LINEAGE] FAIL   -> stage='{stage_name}' run_id={run_id}")
        client.emit(RunEvent(
            eventType=RunState.FAIL,
            eventTime=datetime.now(UTC).isoformat(),
            run=run,
            job=job,
            producer="https://github.com/joryhh/data-engineering-capstone",
        ))
        raise
    else:
        print(f"📡 [LINEAGE] COMPLETE -> stage='{stage_name}' run_id={run_id}")
        client.emit(RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now(UTC).isoformat(),
            run=run,
            job=job,
            producer="https://github.com/joryhh/data-engineering-capstone",
        ))


if __name__ == "__main__":
    # Demo: one stage succeeds, one stage deliberately fails
    with track_stage("bronze_ingestion_demo"):
        print("   ... doing bronze work ...")

    try:
        with track_stage("silver_merge_demo"):
            print("   ... doing silver work ...")
            raise ValueError("Simulated failure to prove FAIL event emission")
    except ValueError:
        print("   (expected exception caught, FAIL event already emitted above)")
