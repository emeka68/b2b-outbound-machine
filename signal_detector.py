"""
signal_detector.py — B2B buying signal scoring & prioritization

Author: Nnaemeka Duru (emekaduru09@gmail.com)

Analyzes enriched lead data to score buying signals:
- DPP Signal Score: 0-100 based on compliance readiness
- Commerce Signal Score: 0-100 based on legacy tech stack
- Priority tier: HOT / WARM / COLD
- Recommended campaign: DPP or B2B_Commerce
"""

import pandas as pd
import logging
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SignalDetector:
    """Scores and prioritizes leads based on buying signals."""
    
    # Legacy tech platforms indicate commerce pain points
    LEGACY_PLATFORMS = ['magento', 'woocommerce', 'prestashop', 'sap']
    
    # Strong DPP indicators
    DPP_COMPLIANCE_KEYWORDS = [
        'digital product passport',
        'sustainability',
        'traceability',
        'EU compliance',
        'circular economy',
    ]
    
    def __init__(self):
        pass
    
    def calculate_dpp_score(self, dpp_ready: int, signals_found: str) -> int:
        """
        Calculate DPP Signal Score (0-100).
        Based on existing DPP readiness and signals found.
        """
        base_score = min(100, dpp_ready)
        
        # Bonus for compliance keywords in signals
        signal_list = [s.strip() for s in str(signals_found).split(',') if s.strip()]
        keyword_count = sum(1 for sig in signal_list if any(kw in sig.lower() for kw in self.DPP_COMPLIANCE_KEYWORDS))
        
        bonus = min(20, keyword_count * 10)
        return min(100, base_score + bonus)
    
    def calculate_commerce_score(self, tech_stack: str) -> int:
        """
        Calculate Commerce Signal Score (0-100).
        Higher score = more legacy/outdated tech = higher pain point.
        """
        if not tech_stack or tech_stack == 'Unknown' or tech_stack == 'N/A':
            return 0
        
        tech_list = [t.strip().lower() for t in str(tech_stack).split(',')]
        legacy_count = sum(1 for tech in tech_list if any(legacy in tech for legacy in self.LEGACY_PLATFORMS))
        
        # Score: each legacy platform = 25 points
        score = min(100, legacy_count * 25)
        return score
    
    def determine_priority(self, dpp_score: int, commerce_score: int) -> str:
        """
        Determine priority tier: HOT / WARM / COLD
        """
        combined_signal = max(dpp_score, commerce_score)
        
        if combined_signal >= 70:
            return 'HOT'
        elif combined_signal >= 40:
            return 'WARM'
        else:
            return 'COLD'
    
    def recommend_campaign(self, dpp_score: int, commerce_score: int) -> str:
        """
        Recommend campaign type based on primary signal.
        """
        if dpp_score > commerce_score:
            return 'DPP'
        else:
            return 'B2B_Commerce'
    
    def score_lead(self, row: Dict) -> Dict:
        """
        Score a single lead row.
        """
        dpp_ready = row.get('dpp_ready', 0)
        tech_stack = row.get('tech_stack', '')
        
        # Calculate scores
        dpp_score = self.calculate_dpp_score(dpp_ready, row.get('signals_found', ''))
        commerce_score = self.calculate_commerce_score(tech_stack)
        
        # Determine priority & campaign
        priority = self.determine_priority(dpp_score, commerce_score)
        campaign = self.recommend_campaign(dpp_score, commerce_score)
        
        return {
            **row,
            'dpp_signal_score': dpp_score,
            'commerce_signal_score': commerce_score,
            'priority': priority,
            'recommended_campaign': campaign,
        }
    
    def score_csv(self, input_path: str, output_path: str) -> pd.DataFrame:
        """
        Read enriched CSV, score each row, write output.
        """
        logger.info(f"Loading enriched data from {input_path}")
        df = pd.read_csv(input_path)
        
        logger.info(f"Scoring {len(df)} leads...")
        scored_rows = []
        
        for idx, row in df.iterrows():
            scored = self.score_lead(row.to_dict())
            scored_rows.append(scored)
            
            priority = scored.get('priority', 'COLD')
            logger.info(f"[{idx+1}/{len(df)}] {row.get('company', 'Unknown')}: {priority} "
                       f"(DPP: {scored.get('dpp_signal_score', 0)}, Commerce: {scored.get('commerce_signal_score', 0)})")
        
        scored_df = pd.DataFrame(scored_rows)
        
        # Summary stats
        hot_count = len(scored_df[scored_df['priority'] == 'HOT'])
        warm_count = len(scored_df[scored_df['priority'] == 'WARM'])
        cold_count = len(scored_df[scored_df['priority'] == 'COLD'])
        
        logger.info(f"\n=== SCORING SUMMARY ===")
        logger.info(f"HOT:  {hot_count} leads")
        logger.info(f"WARM: {warm_count} leads")
        logger.info(f"COLD: {cold_count} leads")
        
        scored_df.to_csv(output_path, index=False)
        logger.info(f"Scored data saved to {output_path}")
        
        return scored_df


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python signal_detector.py <enriched_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'scored_leads.csv'
    
    detector = SignalDetector()
    detector.score_csv(input_file, output_file)
