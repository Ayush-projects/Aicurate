#!/usr/bin/env python3
"""
Script to generate a startup evaluation report and save it to Firebase
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.firebase_service import firebase_service
from services.ai_agent import ai_agent

def main():
    """Generate and save a startup evaluation report"""
    
    print("🚀 Generating startup evaluation report...")
    
    # Load the sample data from the JSON file
    report_path = project_root / 'models' / 'startup_evaluation_report.json'
    
    try:
        with open(report_path, 'r') as f:
            startup_data = json.load(f)
        
        print(f"✅ Loaded startup data for: {startup_data.get('submission', {}).get('startupName', 'Unknown')}")
        
        # Initialize Firebase if not already done
        if not firebase_service.db:
            print("❌ Firebase not initialized")
            return
        
        # Save the report to Firebase
        startup_id = 'strp_001'  # Use the same ID as in the JSON file
        report_ref = firebase_service.db.collection('startup_evaluation_reports').document(startup_id)
        report_ref.set(startup_data)
        
        print(f"✅ Saved startup evaluation report to Firebase with ID: {startup_id}")
        
        # Verify it was saved
        saved_doc = report_ref.get()
        if saved_doc.exists:
            print("✅ Verification: Report successfully saved to Firebase")
        else:
            print("❌ Verification failed: Report not found in Firebase")
            
    except FileNotFoundError:
        print(f"❌ Could not find startup evaluation report file: {report_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
