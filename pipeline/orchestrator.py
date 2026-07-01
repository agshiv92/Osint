"""
Phantom Signal — Pipeline Orchestrator
Automates the end-to-end processing of PENDING raw signals through the entire pipeline.
"""
import logging
import streamlit as st

from data.database import get_raw_signals, update_raw_signal_status
from pipeline.normalization import normalize_raw_signal
from pipeline.filtration import run_filtration
from pipeline.simulation import run_simulation
from pipeline.alert_generator import generate_alert_document

logger = logging.getLogger(__name__)


def run_orchestrator_batch(progress_callback=None, limit=10):
    """
    Fetch PENDING raw signals and process them through the pipeline.
    Optionally provide a progress_callback(status_text, progress_pct) for Streamlit UI.
    """
    pending = get_raw_signals(status="PENDING", limit=limit)
    total = len(pending)
    
    if total == 0:
        if progress_callback:
            progress_callback("No pending signals to process.", 100)
        return 0

    success_count = 0

    for idx, raw_signal in enumerate(pending):
        sig_id = raw_signal["signal_id"]
        title_snippet = raw_signal.get("title", "")[:30] + "..."
        
        try:
            # 1. Normalization
            if progress_callback:
                progress_callback(f"[{idx+1}/{total}] Normalizing: {title_snippet}", int((idx / total) * 100))
            
            fraud_signal = normalize_raw_signal(raw_signal)
            if not fraud_signal:
                update_raw_signal_status(sig_id, "DISCARDED")
                continue
            
            update_raw_signal_status(sig_id, "NORMALIZED")
            
            # 2. Filtration
            if progress_callback:
                progress_callback(f"[{idx+1}/{total}] Filtering: {title_snippet}", int(((idx + 0.33) / total) * 100))
            
            assessment = run_filtration(fraud_signal)
            if not assessment:
                update_raw_signal_status(sig_id, "FILTERED")
                continue
            
            if not assessment.get("overall_passed"):
                update_raw_signal_status(sig_id, "FILTERED")
                continue
            
            # 3. Simulation
            if progress_callback:
                progress_callback(f"[{idx+1}/{total}] Simulating Impact: {title_snippet}", int(((idx + 0.66) / total) * 100))
            
            simulation = run_simulation(fraud_signal, assessment, scenario_name="Automated Batch Run")
            
            # 4. Alert Generation
            if progress_callback:
                progress_callback(f"[{idx+1}/{total}] Generating Alert: {title_snippet}", int(((idx + 0.85) / total) * 100))
                
            alert = generate_alert_document(fraud_signal, assessment, simulation)
            if alert:
                update_raw_signal_status(sig_id, "ALERTED")
                success_count += 1
            else:
                update_raw_signal_status(sig_id, "FILTERED")
                
        except Exception as e:
            logger.error(f"Error processing signal {sig_id}: {e}")
            update_raw_signal_status(sig_id, "DISCARDED")
            continue

    if progress_callback:
        progress_callback(f"Finished! Generated {success_count} new alerts.", 100)

    return success_count
