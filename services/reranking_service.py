"""
Reranking Service for AI Investment Platform
Handles startup recommendation reranking based on investor preferences
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from services.ai_agent import ai_agent
from services.firebase_service import firebase_service
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class RerankingService:
    """Service for reranking startup recommendations based on investor preferences"""
    
    def __init__(self):
        self.ai_agent = ai_agent
    
    def _generate_data_hash(self, preferences: Dict[str, Any], startup_reports: List[Dict[str, Any]]) -> str:
        """Generate a hash of the current data to detect changes"""
        try:
            # Create a stable representation of the data
            data_to_hash = {
                'preferences': preferences,
                'startup_count': len(startup_reports),
                'startup_ids': sorted([report.get('startup_id', '') for report in startup_reports]),
                'startup_hashes': []
            }
            
            # Add hash of each startup's key data
            for report in startup_reports:
                startup_data = {
                    'startup_id': report.get('startup_id', ''),
                    'submission': report.get('submission', {}),
                    'scores': report.get('scores', {}),
                    'aiInsights': report.get('aiInsights', {})
                }
                startup_hash = hashlib.md5(json.dumps(startup_data, sort_keys=True).encode()).hexdigest()
                data_to_hash['startup_hashes'].append(startup_hash)
            
            # Sort startup hashes for consistency
            data_to_hash['startup_hashes'].sort()
            
            # Generate final hash
            data_string = json.dumps(data_to_hash, sort_keys=True)
            return hashlib.md5(data_string.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating data hash: {e}")
            return ""
    
    def _get_cached_recommendations(self, investor_id: str) -> Optional[Dict[str, Any]]:
        """Get cached recommendations for an investor"""
        try:
            if not firebase_service.db:
                return None
            
            cache_ref = firebase_service.db.collection('investor_recommendations_cache').document(investor_id)
            cache_doc = cache_ref.get()
            
            if cache_doc.exists:
                cache_data = cache_doc.to_dict()
                return cache_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached recommendations: {e}")
            return None
    
    def _save_cached_recommendations(self, investor_id: str, recommendations: Dict[str, Any], data_hash: str) -> None:
        """Save recommendations to cache with data hash"""
        try:
            if not firebase_service.db:
                return
            
            cache_data = {
                'recommendations': recommendations,
                'data_hash': data_hash,
                'cached_at': firestore.SERVER_TIMESTAMP,
                'investor_id': investor_id
            }
            
            cache_ref = firebase_service.db.collection('investor_recommendations_cache').document(investor_id)
            cache_ref.set(cache_data)
            
            logger.info(f"Cached recommendations for investor {investor_id}")
            
        except Exception as e:
            logger.error(f"Error saving cached recommendations: {e}")
    
    def _is_reranking_needed(self, investor_id: str, preferences: Dict[str, Any], startup_reports: List[Dict[str, Any]]) -> bool:
        """Check if reranking is needed based on data changes"""
        try:
            # Generate current data hash
            current_hash = self._generate_data_hash(preferences, startup_reports)
            if not current_hash:
                logger.warning("Could not generate data hash, proceeding with reranking")
                return True
            
            # Get cached recommendations
            cached_data = self._get_cached_recommendations(investor_id)
            if not cached_data:
                logger.info("No cached recommendations found, reranking needed")
                return True
            
            # Check if data hash matches
            cached_hash = cached_data.get('data_hash', '')
            if current_hash != cached_hash:
                logger.info("Data has changed, reranking needed")
                return True
            
            logger.info("No changes detected, using cached recommendations")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if reranking needed: {e}")
            return True
    
    def rerank_startups_for_investor(self, investor_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rerank startups based on investor preferences using LLM
        
        Args:
            investor_id: The investor's user ID
            preferences: Investor's investment preferences
            
        Returns:
            Dict containing reranked startup recommendations
        """
        try:
            # Get all startup evaluation reports
            startup_reports = self._get_startup_evaluation_reports()
            
            if not startup_reports:
                logger.warning("No startup evaluation reports found for reranking")
                return {"success": False, "message": "No startup data available"}
            
            # Check if reranking is needed
            if not self._is_reranking_needed(investor_id, preferences, startup_reports):
                logger.info(f"Using cached recommendations for investor {investor_id}")
                # Get cached recommendations
                cached_data = self._get_cached_recommendations(investor_id)
                if cached_data:
                    return {
                        "success": True,
                        "recommendations": cached_data.get('recommendations', {}),
                        "total_startups": len(startup_reports),
                        "timestamp": cached_data.get('cached_at', datetime.now(timezone.utc).isoformat()),
                        "cached": True
                    }
            
            logger.info(f"Reranking needed for investor {investor_id}")
            
            # Prepare data for LLM reranking
            reranking_prompt = self._build_reranking_prompt(preferences, startup_reports)
            
            # Call LLM for reranking
            reranked_results = self._call_llm_for_reranking(reranking_prompt)
            
            # Generate data hash for caching
            data_hash = self._generate_data_hash(preferences, startup_reports)
            
            # Save reranked results to Firebase
            self._save_reranked_recommendations(investor_id, reranked_results, preferences)
            
            # Cache the results
            if data_hash:
                self._save_cached_recommendations(investor_id, reranked_results, data_hash)
            
            logger.info(f"Successfully reranked {len(startup_reports)} startups for investor {investor_id}")
            
            return {
                "success": True,
                "recommendations": reranked_results,
                "total_startups": len(startup_reports),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"Error in reranking startups for investor {investor_id}: {e}")
            return {"success": False, "message": f"Reranking failed: {str(e)}"}
    
    def _get_startup_evaluation_reports(self) -> List[Dict[str, Any]]:
        """Get all startup evaluation reports from Firebase"""
        try:
            if not firebase_service.db:
                logger.error("Firebase database not available")
                return []
            
            reports_ref = firebase_service.db.collection('startup_evaluation_reports')
            reports_docs = reports_ref.stream()
            
            reports = []
            for doc in reports_docs:
                report_data = doc.to_dict()
                report_data['startup_id'] = doc.id
                reports.append(report_data)
            
            logger.info(f"Retrieved {len(reports)} startup evaluation reports")
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving startup evaluation reports: {e}")
            return []
    
    def _build_reranking_prompt(self, preferences: Dict[str, Any], startup_reports: List[Dict[str, Any]]) -> str:
        """Build the prompt for LLM reranking"""
        
        # Extract key preference information
        sectors = preferences.get('sectors', [])
        ticket_size_min = preferences.get('ticket_size_min', 0)
        ticket_size_max = preferences.get('ticket_size_max', float('inf'))
        risk_tolerance = preferences.get('risk_tolerance', 'Medium')
        geography = preferences.get('geography', [])
        investment_stage = preferences.get('investment_stage', [])
        
        # Build startup summaries for LLM
        startup_summaries = []
        for report in startup_reports:
            submission = report.get('submission', {})
            company_profile = report.get('companyProfile', {})
            scores = report.get('scores', {})
            ai_insights = report.get('aiInsights', {})
            
            summary = {
                "startup_id": report.get('startup_id', 'unknown'),
                "name": submission.get('startupName', 'Unknown'),
                "sector": company_profile.get('sector', 'Unknown'),
                "description": company_profile.get('description', 'No description'),
                "location": submission.get('location', {}),
                "overall_score": scores.get('OverallScore', 0),
                "founder_market_fit": scores.get('FounderMarketFit', 0),
                "product_differentiation": scores.get('ProductDifferentiation', 0),
                "traction": scores.get('Traction', 0),
                "market_potential": scores.get('MarketPotential', 0),
                "confidence_score": ai_insights.get('confidenceScore', 0),
                "investment_readiness": ai_insights.get('investmentReadiness', 'Unknown'),
                "key_differentiators": ai_insights.get('keyDifferentiators', []),
                "flagged_risks": ai_insights.get('flaggedRisks', [])
            }
            startup_summaries.append(summary)
        
        prompt = f"""
You are an AI investment advisor helping to rank startup investment opportunities based on an investor's preferences.

INVESTOR PREFERENCES:
- Preferred Sectors: {', '.join(sectors) if sectors else 'No specific preference'}
- Ticket Size Range: ${ticket_size_min:,.0f} - ${ticket_size_max:,.0f}
- Risk Tolerance: {risk_tolerance}
- Preferred Geography: {', '.join(geography) if geography else 'No specific preference'}
- Investment Stage: {', '.join(investment_stage) if investment_stage else 'No specific preference'}

STARTUP DATA:
{json.dumps(startup_summaries, indent=2)}

TASK:
Rank these startups from 1 to {len(startup_summaries)} based on how well they match the investor's preferences. Consider:
1. Sector alignment
2. Investment stage match
3. Geographic preference
4. Risk profile alignment
5. Overall investment potential
6. Founder-market fit
7. Product differentiation
8. Traction and market potential

CRITICAL: You must respond with ONLY valid JSON. No markdown, no explanations, no additional text. Just the JSON object.

Return this exact JSON format:
{{
    "rankings": [
        {{
            "startup_id": "startup_id_here",
            "rank": 1,
            "match_score": 95.5,
            "reasoning": "Brief explanation of why this startup matches well"
        }},
        {{
            "startup_id": "startup_id_here_2",
            "rank": 2,
            "match_score": 87.2,
            "reasoning": "Brief explanation of why this startup matches well"
        }}
    ],
    "summary": {{
        "total_startups": {len(startup_summaries)},
        "high_match_count": 0,
        "medium_match_count": 0,
        "low_match_count": 0,
        "top_recommendations": ["startup_id_1", "startup_id_2", "startup_id_3"]
    }}
}}

Ensure the rankings are ordered from best match (rank 1) to worst match (rank {len(startup_summaries)}).
"""
        
        return prompt
    
    def _call_llm_for_reranking(self, prompt: str) -> Dict[str, Any]:
        """Call LLM to perform the reranking"""
        try:
            # Use the existing AI agent to make the LLM call
            response = self.ai_agent.make_llm_request(prompt)
            
            if not response:
                raise Exception("No response from LLM")
            
            # Try to extract JSON from the response
            json_text = self._extract_json_from_response(response)
            
            # Parse the JSON response
            try:
                reranking_result = json.loads(json_text)
                return reranking_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                logger.error(f"Extracted JSON: {json_text}")
                # Return a fallback response
                return self._create_fallback_reranking_response()
                
        except Exception as e:
            logger.error(f"Error calling LLM for reranking: {e}")
            # Return a fallback response instead of raising
            return self._create_fallback_reranking_response()
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from LLM response, handling cases where it's wrapped in markdown or other text"""
        try:
            # First, try to parse the entire response as JSON
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within markdown code blocks
        import re
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ```
            r'\{.*\}',                 # Any JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match.strip())
                    return match.strip()
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, return the original response
        return response_text
    
    def _create_fallback_reranking_response(self) -> Dict[str, Any]:
        """Create a fallback response when LLM fails"""
        logger.warning("Using fallback reranking response due to LLM failure")
        
        # Get startup reports to create a basic ranking
        startup_reports = self._get_startup_evaluation_reports()
        
        # Create a simple ranking based on overall scores
        rankings = []
        for i, report in enumerate(startup_reports):
            scores = report.get('scores', {})
            overall_score = scores.get('OverallScore', 0)
            
            rankings.append({
                "startup_id": report.get('startup_id', f'startup_{i}'),
                "rank": i + 1,
                "match_score": min(overall_score * 10, 100),  # Convert to percentage
                "reasoning": f"Ranked based on overall score of {overall_score}/10"
            })
        
        # Sort by score (highest first)
        rankings.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Update ranks after sorting
        for i, ranking in enumerate(rankings):
            ranking['rank'] = i + 1
        
        return {
            "rankings": rankings,
            "summary": {
                "total_startups": len(startup_reports),
                "high_match_count": len([r for r in rankings if r['match_score'] >= 80]),
                "medium_match_count": len([r for r in rankings if 50 <= r['match_score'] < 80]),
                "low_match_count": len([r for r in rankings if r['match_score'] < 50]),
                "top_recommendations": [r['startup_id'] for r in rankings[:3]]
            }
        }
    
    def _save_reranked_recommendations(self, investor_id: str, reranking_results: Dict[str, Any], preferences: Dict[str, Any]) -> None:
        """Save reranked recommendations to Firebase"""
        try:
            if not firebase_service.db:
                logger.error("Firebase database not available")
                return
            
            # Prepare the document data
            doc_data = {
                'investor_id': investor_id,
                'preferences_used': preferences,
                'rankings': reranking_results.get('rankings', []),
                'summary': reranking_results.get('summary', {}),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            }
            
            # Save to investor_recommendations collection
            recommendations_ref = firebase_service.db.collection('investor_recommendations').document(investor_id)
            recommendations_ref.set(doc_data)
            
            logger.info(f"Saved reranked recommendations for investor {investor_id}")
            
        except Exception as e:
            logger.error(f"Error saving reranked recommendations: {e}")
            raise
    
    def get_investor_recommendations(self, investor_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest recommendations for an investor"""
        try:
            if not firebase_service.db:
                return None
            
            recommendations_ref = firebase_service.db.collection('investor_recommendations').document(investor_id)
            doc = recommendations_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting investor recommendations: {e}")
            return None
    
    def trigger_reranking_on_preference_change(self, investor_id: str) -> Dict[str, Any]:
        """Trigger reranking when investor preferences change"""
        try:
            # Get current investor preferences
            if not firebase_service.db:
                return {"success": False, "message": "Database not available"}
            
            user_doc = firebase_service.db.collection('users').document(investor_id).get()
            if not user_doc.exists:
                return {"success": False, "message": "Investor not found"}
            
            preferences = user_doc.to_dict().get('preferences', {})
            if not preferences:
                return {"success": False, "message": "No preferences found"}
            
            # Perform reranking
            result = self.rerank_startups_for_investor(investor_id, preferences)
            
            return result
            
        except Exception as e:
            logger.error(f"Error triggering reranking on preference change: {e}")
            return {"success": False, "message": f"Reranking failed: {str(e)}"}
    
    def invalidate_cache_for_investor(self, investor_id: str) -> None:
        """Invalidate cached recommendations for a specific investor"""
        try:
            if not firebase_service.db:
                return
            
            cache_ref = firebase_service.db.collection('investor_recommendations_cache').document(investor_id)
            cache_ref.delete()
            
            logger.info(f"Invalidated cache for investor {investor_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for investor {investor_id}: {e}")
    
    def invalidate_all_caches(self) -> None:
        """Invalidate all cached recommendations (useful when startup data changes)"""
        try:
            if not firebase_service.db:
                return
            
            cache_collection = firebase_service.db.collection('investor_recommendations_cache')
            docs = cache_collection.stream()
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} cached recommendations")
            
        except Exception as e:
            logger.error(f"Error invalidating all caches: {e}")
    
    def trigger_reranking_on_new_startup(self) -> Dict[str, Any]:
        """Trigger reranking for all investors when a new startup is added"""
        try:
            if not firebase_service.db:
                return {"success": False, "message": "Database not available"}
            
            # Invalidate all caches since startup data has changed
            self.invalidate_all_caches()
            
            # Get all investors
            investors_ref = firebase_service.db.collection('users').where('role', '==', 'investor')
            investors_docs = investors_ref.stream()
            
            results = []
            for doc in investors_docs:
                investor_id = doc.id
                investor_data = doc.to_dict()
                preferences = investor_data.get('preferences', {})
                
                if preferences:
                    result = self.rerank_startups_for_investor(investor_id, preferences)
                    results.append({
                        'investor_id': investor_id,
                        'success': result.get('success', False),
                        'message': result.get('message', ''),
                        'cached': result.get('cached', False)
                    })
            
            logger.info(f"Triggered reranking for {len(results)} investors")
            
            return {
                "success": True,
                "message": f"Reranking triggered for {len(results)} investors",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error triggering reranking on new startup: {e}")
            return {"success": False, "message": f"Reranking failed: {str(e)}"}


# Global instance
reranking_service = RerankingService()
