"""
AI Agent Service for processing startup submissions and generating structured reports
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
import requests
import os
from datetime import datetime, timezone
from pathlib import Path
import mimetypes
import time
from google import genai
from google.genai import types
from services.firebase_service import firebase_service
from firebase_admin import firestore

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model = "gemini-2.5-pro"
        else:
            logger.warning("GEMINI_API_KEY not found. AI processing will be simulated.")
            self.client = None
            self.model = None
    
    def process_submission(self, submission_id: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a startup submission and generate structured JSON report
        """
        try:
            logger.info(f"Starting AI processing for submission: {submission_id}")
            
            # Update status to processing
            self._update_submission_status(submission_id, 'processing')
            
            # Extract and upload files for AI processing
            uploaded_files = self._extract_file_contents(submission_data.get('submission', {}).get('uploadedAssets', []))
            
            # Generate AI analysis
            if self.client:
                ai_report = self._generate_ai_report(submission_data, uploaded_files)
            else:
                ai_report = self._generate_mock_report(submission_data, uploaded_files)
            
            # Save the report to Firebase
            self._save_ai_report(submission_id, ai_report)
            
            # Update submission status to completed
            self._update_submission_status(submission_id, 'completed')
            
            logger.info(f"Successfully processed submission: {submission_id}")
            return ai_report
            
        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}")
            self._update_submission_status(submission_id, 'failed')
            raise
    
    def _extract_file_contents(self, uploaded_assets: List[Dict[str, Any]]) -> List[Any]:
        """
        Extract and upload files to GenAI for processing
        """
        uploaded_files = []
        
        for asset in uploaded_assets:
            try:
                file_type = asset.get('type', '')
                file_path = asset.get('file_path', '')
                filename = asset.get('filename', '')
                
                if not file_path or not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                # Upload file to GenAI
                if self.client:
                    uploaded_file = self._upload_file_to_genai(file_path)
                    if uploaded_file:
                        uploaded_files.append(uploaded_file)
                        logger.info(f"Uploaded {filename} to GenAI")
                else:
                    # Simulate file content for testing
                    content = self._simulate_file_extraction(file_type, file_path)
                    uploaded_files.append({
                        'type': file_type,
                        'filename': filename,
                        'content': content
                    })
                
            except Exception as e:
                logger.error(f"Error processing file {asset.get('filename', 'unknown')}: {e}")
                continue
        
        return uploaded_files
    
    def _upload_file_to_genai(self, file_path: str) -> Optional[Any]:
        """
        Upload a file to GenAI using the new API
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Guess MIME type
            mime_type, _ = mimetypes.guess_type(path.name)
            mime_type = mime_type or "application/octet-stream"
            
            # Upload file
            f = self.client.files.upload(file=path, config={"mime_type": mime_type})
            
            # Wait for processing
            while getattr(f, "state", None) and getattr(f.state, "name", "") == "PROCESSING":
                time.sleep(2)
                f = self.client.files.get(name=f.name)
            
            if getattr(f, "state", None) and getattr(f.state, "name", "") != "ACTIVE":
                raise RuntimeError(f"File not ready: {f}")
            
            return f
            
        except Exception as e:
            logger.error(f"Error uploading file to GenAI: {e}")
            return None
    
    def _simulate_file_extraction(self, file_type: str, file_url: str) -> str:
        """
        Simulate file content extraction based on file type
        """
        # This is a placeholder - in production, you'd implement actual file parsing
        content_map = {
            'pitch_deck_pdf': f"Pitch deck content from {file_url} - Company overview, market analysis, financial projections, team information, and growth strategy.",
            'video_pitch': f"Video pitch transcript from {file_url} - Founder presenting company vision, product demo, market opportunity, and funding requirements.",
            'audio_pitch': f"Audio pitch transcript from {file_url} - Voice recording of founder explaining business model and growth plans.",
            'financial_model_spreadsheet': f"Financial model data from {file_url} - Revenue projections, expense breakdown, cash flow analysis, and funding requirements.",
            'product_demo_video': f"Product demo transcript from {file_url} - Step-by-step walkthrough of product features and user interface.",
            'founder_update_doc': f"Founder update document from {file_url} - Recent company updates, milestones achieved, and future plans."
        }
        
        return content_map.get(file_type, f"Content from {file_type} file")
    
    def _generate_ai_report(self, submission_data: Dict[str, Any], uploaded_files: List[Any]) -> Dict[str, Any]:
        """
        Generate AI-powered analysis using Gemini
        """
        try:
            # Prepare the prompt for the AI agent
            prompt = self._build_ai_prompt(submission_data, uploaded_files)
            
            # Generate response from Gemini
            if self.client:
                contents = [*uploaded_files, prompt]
                response = self.client.models.generate_content(model=self.model, contents=contents)
                response_text = response.text
            else:
                # Fallback for testing
                response_text = '{"error": "AI not available"}'
            
            # Extract JSON from response
            ai_report = self._extract_json_from_response(response_text)
            
            return ai_report
            
        except Exception as e:
            logger.error(f"Error generating AI report: {e}")
            # Fallback to mock report
            return self._generate_mock_report(submission_data, uploaded_files)
    
    def make_llm_request(self, prompt: str) -> str:
        """
        Make a simple LLM request with just text prompt (no files)
        """
        try:
            if self.client:
                response = self.client.models.generate_content(model=self.model, contents=prompt)
                return response.text
            else:
                # Fallback for testing - return a mock response
                logger.warning("AI client not available, returning mock response")
                return '{"error": "AI not available", "message": "Mock response for testing"}'
                
        except Exception as e:
            logger.error(f"Error making LLM request: {e}")
            raise
    
    def _build_ai_prompt(self, submission_data: Dict[str, Any], uploaded_files: List[Any]) -> str:
        """
        Build the comprehensive prompt for the AI agent
        """
        submission = submission_data.get('submission', {})
        
        # Build file content summary
        file_summary = ""
        if uploaded_files:
            if hasattr(uploaded_files[0], 'name'):  # GenAI file objects
                file_summary = f"Processing {len(uploaded_files)} uploaded files for analysis."
            else:  # Mock file objects
                file_summary = "\n".join([
                    f"**{file.get('type', 'unknown').upper()}:**\n{file.get('content', 'No content')}\n" 
                    for file in uploaded_files
                ])
        
        # Create the prompt using string formatting to avoid f-string issues with JSON
        startup_name = submission.get('startupName', 'Unknown')
        location = submission.get('location', {})
        founding_date = submission.get('foundingDate', 'Unknown')
        description = submission.get('description') or submission_data.get('companyProfile', {}).get('description') or 'No description provided'
        extended_description = submission_data.get('companyProfile', {}).get('description')
        extended_description_section = ""
        if extended_description and extended_description != description:
            extended_description_section = "- Extended Submission Narrative: \"" + extended_description + "\"\n"
        uploaded_assets_count = len(submission.get('uploadedAssets', []))
        
        # Use string concatenation to avoid f-string issues with JSON braces
        prompt = """
ROLE
You are an AI investment analyst. You will read ALL ATTACHED FILES (PDFs, decks, spreadsheets, etc.) provided in this request and compile a structured, investor-grade dossier with 100+ metrics covering company, founders, traction, market, competition, and financial health.

SOURCES & PRIORITY
1) PRIMARY: Use the ATTACHED FILES as the single source of truth.
2) SECONDARY: Supplement gaps with **reliable public sources** (Crunchbase, PitchBook public pages, LinkedIn profiles, official company websites, reputable press releases, and trusted media). Ignore gated pages or unverifiable blogs.
3) If facts conflict across sources, prefer:  
   (a) the most recent dated ATTACHED FILES; else  
   (b) the most reputable and most recent public source.  
   Document contradictions concisely in `aiInsights.summary`.

DATA ENRICHMENT
• Go beyond surface-level. Include founder backgrounds, hiring patterns, funding rounds, market size benchmarks, CX scores, risks, compliance readiness, and other institutional-grade datapoints.  
• Infer insights like runway, retention, burn ratio, GTM maturity, AI differentiation, and regulatory gaps.  
• Always prioritize structured quantification (numeric metrics, percentages, valuations, CAGR, TAM/SAM/SOM).  
• Capture investor-style red flags and differentiators.  

CURRENCY NORMALIZATION
• Use **USD as the reference currency** for any values that don't have a schema-mandated currency.  
• Where the schema's field name explicitly expects INR (e.g., monthlyGMVINR), keep INR in that field.  
• Additionally, when you convert non-USD figures, state the **assumed FX rate and its date** in `aiInsights.summary` (e.g., "Converted INR→USD at 1 USD = 83.2 INR on 2025-09-21"). If an exact date is unavailable, say "as of today".  
• If a numeric value is not available in any source, set `"NA"`.

STRICT OUTPUT RULES
• Return EXACTLY ONE valid JSON object conforming to the schema below.  
• Do NOT add or remove keys. Do NOT change key casing. No extra commentary or markdown.  
• Every field must exist. If a field is unknown or unverifiable, set it to `"NA"` (or empty array/object consistent with the schema).  
• If you must synthesize a minimal `submission` block, it is allowed, but all other factual fields must come from sources or be `"NA"`.  
• Be concise and factual, investor-grade, and consistent across metrics.

SUBMISSION DATA:
- Startup Name: """ + startup_name + """
- Location: """ + str(location) + """
- Founding Date: """ + founding_date + """
- Description: """ + description + """
""" + extended_description_section + """- Uploaded Assets: """ + str(uploaded_assets_count) + """ files

FILE CONTENTS:
""" + file_summary + """

SCHEMA (copy the exact keys and structure):
{
    "startupId": "strp_001",
    "submission": {
      "submittedBy": "founder@hyperpay.com",
      "submittedAt": "2025-09-20T14:32:15Z",
      "startupName": "HyperPay",
      "location": {
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India"
      },
      "foundingDate": "2023-07-01",
      "founderIds": ["user_riya_sharma", "user_ankur_jain"],
      "uploadedAssets": [
        {
          "type": "pitch_deck_pdf",
          "filename": "hyperpay_pitch.pdf",
          "url": "https://firebase/.../pitch_deck.pdf"
        }
      ]
    },
  
    "companyProfile": {
      "description": "HyperPay offers an AI-driven unified checkout API for Indian and SEA merchants, enabling multi-rail payments and real-time fraud detection.",
      "tagline": "One checkout. All payments.",
      "sector": "Fintech",
      "subsectors": ["Payment Gateway", "Embedded Finance", "RiskTech"],
      "businessModel": "B2B SaaS with volume-based pricing",
      "companyStage": "Seed",
      "teamSize": 14,
      "legalEntity": "HyperPay Technologies Pvt Ltd",
      "corporateStructure": "Privately held, incorporated under MCA India",
      "ipAssets": ["1 patent filed - 'Dynamic Payment Routing'", "Trademark filed - 'HyperPay'"]
    },
  
    "founderProfiles": [
      {
        "id": "user_riya_sharma",
        "name": "Riya Sharma",
        "linkedIn": "https://linkedin.com/in/riyasharma",
        "email": "riya@hyperpay.com",
        "education": "IIT Delhi, B.Tech CS",
        "experience": [
          {
            "company": "Paytm",
            "role": "Product Manager",
            "durationYears": 3
          }
        ],
        "commitmentLevel": {
          "fullTime": true,
          "equityHoldingPercent": 58,
          "personalCapitalInvestedINR": 1000000
        },
        "founderMarketFitScore": 8.6
      }
    ],
  
    "teamStructure": {
      "totalEmployees": 14,
      "departments": {
        "Engineering": 6,
        "Product": 2,
        "Growth": 2,
        "Risk & Compliance": 1,
        "Support": 1,
        "CX": 2
      },
      "advisors": [
        {
          "name": "Meera Bhatia",
          "expertise": "Fintech Regulation",
          "affiliation": "Ex-NPCI"
        }
      ]
    },
  
    "product": {
      "platformAvailability": ["Web", "Android SDK", "Flutter SDK"],
      "apiDocsUrl": "https://docs.hyperpay.com",
      "aiFeatures": ["Fraud Detection", "Smart Routing", "Chargeback Forecasting"],
      "goToMarketChannels": ["Partner ISVs", "Startup accelerators", "Cold outbound"],
      "demoStatus": "Live",
      "productMaturity": "MVP+",
      "roadmapHighlights": [
        "Enable UPI AutoPay by Q4 2025",
        "Launch SEA expansion pilot by Q1 2026"
      ]
    },
  
    "traction": {
      "activeMerchants": 180,
      "monthlyGMVINR": 52000000,
      "monthlyRevenueINR": 450000,
      "growthMoM": 15.2,
      "CACINR": 820,
      "LTVINR": 11400,
      "retentionRate30Day": 91,
      "retentionRate90Day": 86.2,
      "churnRate": 2.1,
      "avgIntegrationTimeDays": 1.8,
      "activationRatePercent": 82,
      "supportSatisfactionScore": 93,
      "onboardingNPS": 72,
      "monthlySupportTickets": 34,
      "integrationSuccessRate": 98.7
    },
  
    "market": {
      "TAMUSD": 4000000000,
      "SAMUSD": 1000000000,
      "SOMUSD": 150000000,
      "keyRegions": ["India", "Indonesia", "Singapore"],
      "marketGrowthRateYoY": 30,
      "macros": {
        "UPIPenetration": "85%",
        "MerchantDigitizationRate": "65%",
        "RBI Compliance Readiness": "Yes"
      },
      "emergingTrends": ["Tokenization", "Instant Settlements", "Embedded Lending"]
    },
  
    "competitorLandscape": {
      "primaryCompetitors": [
        {
          "name": "Razorpay",
          "tagline": "Powering payments for India",
          "strengths": ["Trust", "Mature APIs", "Banking partners"],
          "weaknesses": ["Support", "Onboarding Time"],
          "fundingUSD": 741000000,
          "valuationUSD": 7000000000
        }
      ],
      "positioningMatrix": {
        "xAxis": "Developer Experience",
        "yAxis": "AI Capabilities",
        "coordinates": {
          "HyperPay": { "x": 9, "y": 8.5 },
          "Razorpay": { "x": 8.5, "y": 6.2 }
        }
      }
    },
  
    "financials": {
      "monthlyBurnINR": 380000,
      "revenueToBurnRatio": 1.18,
      "runwayMonths": 11,
      "fundingRequiredINR": 40000000,
      "valuationINR": 130000000,
      "plannedUseOfFunds": {
        "Engineering": 40,
        "Marketing": 30,
        "Compliance": 10,
        "Infrastructure": 10,
        "Other": 10
      },
      "existingInvestors": [
        {
          "name": "AngelList India",
          "type": "Angel Syndicate"
        }
      ]
    },
  
    "aiInsights": {
      "summary": "HyperPay shows strong early traction in a growing market, with an experienced founder team and a clear moat via their AI-driven fraud module. Risk exposure lies in compliance scalability and market saturation in core sectors.",
      "autoGeneratedDealMemo": true,
      "confidenceScore": 85.4,
      "keyDifferentiators": ["AI fraud engine", "1-day integration", "Voice KYC"],
      "flaggedRisks": ["No SOC2 audit", "SEA market expansion untested"],
      "investmentReadiness": "High",
      "recommendedNextStep": "Schedule call with founder"
    },
  
    "scores": {
      "FounderMarketFit": 8.6,
      "ProductDifferentiation": 8.3,
      "GoToMarketStrategy": 7.9,
      "CXScore": 9.2,
      "Traction": 8.1,
      "FinancialHealth": 7.2,
      "TeamQuality": 8.0,
      "MarketPotential": 9.0,
      "RiskAdjustedScore": 7.8,
      "OverallScore": 8.4
    },
  
    "agentPipeline": [
      {
        "agentName": "multimodal-ingestor",
        "status": "completed",
        "outputs": ["text", "audio", "video", "excel"]
      },
      {
        "agentName": "curation-mapper",
        "status": "completed",
        "mappedMetrics": 50
      },
      {
        "agentName": "public-data-enhancer",
        "status": "completed",
        "enrichedFields": ["competitorLandscape", "founderProfile", "TAM"]
      },
      {
        "agentName": "deal-note-generator",
        "status": "completed",
        "confidenceScore": 85.4
      }
    ],
  
    "timestamps": {
      "submittedAt": "2025-09-20T14:32:15Z",
      "processedAt": "2025-09-20T18:45:00Z",
      "lastUpdated": "2025-09-20T18:50:00Z"
    },
  
    "version": "1.1"
  }

OUTPUT FORMAT
Return only the single JSON object. No extra text or markdown.
"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from AI response, handling markdown code blocks
        """
        try:
            # Remove markdown code blocks if present
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, response_text, re.DOTALL)
            
            if match:
                json_str = match.group(1)
            else:
                # Try to find JSON object in the response
                json_pattern = r'\{.*\}'
                match = re.search(json_pattern, response_text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            raise ValueError(f"Failed to extract valid JSON from AI response: {e}")
    
    def _generate_mock_report(self, submission_data: Dict[str, Any], uploaded_files: List[Any]) -> Dict[str, Any]:
        """
        Generate a mock report when AI is not available
        """
        submission = submission_data.get('submission', {})
        current_time = datetime.now(timezone.utc).isoformat()
        
        return {
            "startupId": submission_data.get('startupId', 'strp_mock'),
            "submission": {
                "submittedBy": submission.get('submittedBy', 'unknown@example.com'),
                "submittedAt": submission.get('submittedAt', current_time),
                "startupName": submission.get('startupName', 'Unknown Startup'),
                "location": submission.get('location', {"city": "Unknown", "state": "Unknown", "country": "Unknown"}),
                "foundingDate": submission.get('foundingDate', '2023-01-01'),
                "founderIds": submission.get('founderIds', ['unknown_founder']),
                "uploadedAssets": submission.get('uploadedAssets', [])
            },
            "companyProfile": {
                "description": submission.get('description', 'No description available'),
                "tagline": "Innovative startup solution",
                "sector": "Technology",
                "subsectors": ["SaaS", "AI"],
                "businessModel": "B2B SaaS",
                "companyStage": "Seed",
                "teamSize": 5,
                "legalEntity": "Unknown Entity",
                "corporateStructure": "Private company",
                "ipAssets": []
            },
            "founderProfiles": [
                {
                    "id": "unknown_founder",
                    "name": "Unknown Founder",
                    "linkedIn": "NA",
                    "email": submission.get('submittedBy', 'unknown@example.com'),
                    "education": "NA",
                    "experience": [],
                    "commitmentLevel": {
                        "fullTime": True,
                        "equityHoldingPercent": 100,
                        "personalCapitalInvestedINR": 0
                    },
                    "founderMarketFitScore": 5.0
                }
            ],
            "teamStructure": {
                "totalEmployees": 5,
                "departments": {"Engineering": 3, "Product": 1, "Growth": 1},
                "advisors": []
            },
            "product": {
                "platformAvailability": ["Web"],
                "apiDocsUrl": "NA",
                "aiFeatures": [],
                "goToMarketChannels": ["Direct sales"],
                "demoStatus": "NA",
                "productMaturity": "MVP",
                "roadmapHighlights": []
            },
            "traction": {
                "activeMerchants": 0,
                "monthlyGMVINR": 0,
                "monthlyRevenueINR": 0,
                "growthMoM": 0,
                "CACINR": 0,
                "LTVINR": 0,
                "retentionRate30Day": 0,
                "retentionRate90Day": 0,
                "churnRate": 0,
                "avgIntegrationTimeDays": 0,
                "activationRatePercent": 0,
                "supportSatisfactionScore": 0,
                "onboardingNPS": 0,
                "monthlySupportTickets": 0,
                "integrationSuccessRate": 0
            },
            "market": {
                "TAMUSD": 1000000000,
                "SAMUSD": 100000000,
                "SOMUSD": 10000000,
                "keyRegions": ["India"],
                "marketGrowthRateYoY": 20,
                "macros": {
                    "UPIPenetration": "NA",
                    "MerchantDigitizationRate": "NA",
                    "RBI Compliance Readiness": "NA"
                },
                "emergingTrends": []
            },
            "competitorLandscape": {
                "primaryCompetitors": [],
                "positioningMatrix": {
                    "xAxis": "Market Position",
                    "yAxis": "Innovation",
                    "coordinates": {}
                }
            },
            "financials": {
                "monthlyBurnINR": 100000,
                "revenueToBurnRatio": 0,
                "runwayMonths": 12,
                "fundingRequiredINR": 5000000,
                "valuationINR": 20000000,
                "plannedUseOfFunds": {
                    "Engineering": 50,
                    "Marketing": 30,
                    "Compliance": 10,
                    "Infrastructure": 10,
                    "Other": 0
                },
                "existingInvestors": []
            },
            "aiInsights": {
                "summary": "Mock analysis generated due to AI unavailability. Please review submission manually.",
                "autoGeneratedDealMemo": False,
                "confidenceScore": 30.0,
                "keyDifferentiators": [],
                "flaggedRisks": ["AI analysis unavailable", "Manual review required"],
                "investmentReadiness": "Low",
                "recommendedNextStep": "Manual review and data collection"
            },
            "scores": {
                "FounderMarketFit": 5.0,
                "ProductDifferentiation": 5.0,
                "GoToMarketStrategy": 5.0,
                "CXScore": 5.0,
                "Traction": 5.0,
                "FinancialHealth": 5.0,
                "TeamQuality": 5.0,
                "MarketPotential": 5.0,
                "RiskAdjustedScore": 5.0,
                "OverallScore": 5.0
            },
            "agentPipeline": [
                {
                    "agentName": "multimodal-ingestor",
                    "status": "completed",
                    "outputs": ["text"]
                },
                {
                    "agentName": "curation-mapper",
                    "status": "completed",
                    "mappedMetrics": 10
                },
                {
                    "agentName": "public-data-enhancer",
                    "status": "failed",
                    "enrichedFields": []
                },
                {
                    "agentName": "deal-note-generator",
                    "status": "completed",
                    "confidenceScore": 30.0
                }
            ],
            "timestamps": {
                "submittedAt": submission.get('submittedAt', current_time),
                "processedAt": current_time,
                "lastUpdated": current_time
            },
            "version": "1.1"
        }
    
    def _save_ai_report(self, submission_id: str, ai_report: Dict[str, Any]) -> None:
        """
        Save the AI-generated report to Firebase
        """
        try:
            # Save to startup_evaluation_reports collection
            report_ref = firebase_service.db.collection('startup_evaluation_reports').document(submission_id)
            report_ref.set(ai_report)
            
            logger.info(f"AI report saved for submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error saving AI report for {submission_id}: {e}")
            raise
    
    def _update_submission_status(self, submission_id: str, status: str) -> None:
        """
        Update submission status in Firebase
        """
        try:
            submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
            submission_ref.update({
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Updated submission {submission_id} status to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating submission status for {submission_id}: {e}")
            raise

# Global instance
ai_agent = AIAgent()
