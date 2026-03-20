"""
lemlist_export.py — Export leads to Lemlist-compatible CSV

Author: Nnaemeka Duru (emekaduru09@gmail.com)

Exports personalized leads to Lemlist import format.
- Maps internal fields to Lemlist column names
- Filters by minimum signal score threshold
- Outputs timestamped CSV for bulk import
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LemlistExporter:
    """Exports scored & personalized leads to Lemlist format."""
    
    # Lemlist standard column names
    LEMLIST_COLUMNS = [
        'firstName',
        'lastName',
        'email',
        'companyName',
        'companyDomain',
        'icebreaker',
        'campaign',
        'priority',
        'dpp_signal_score',
        'commerce_signal_score',
    ]
    
    def __init__(self):
        pass
    
    def map_to_lemlist(self, row: dict) -> dict:
        """
        Map internal row format to Lemlist column names.
        """
        return {
            'firstName': row.get('contact_first', 'Contact'),
            'lastName': row.get('contact_last', ''),
            'email': row.get('email', ''),
            'companyName': row.get('company', ''),
            'companyDomain': row.get('domain', ''),
            'icebreaker': row.get('icebreaker', ''),
            'campaign': row.get('recommended_campaign', 'DPP'),
            'priority': row.get('priority', 'COLD'),
            'dpp_signal_score': row.get('dpp_signal_score', 0),
            'commerce_signal_score': row.get('commerce_signal_score', 0),
        }
    
    def export_csv(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        min_score: int = 0,
        campaign_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export personalized leads to Lemlist format.
        
        Args:
            input_path: Path to personalized CSV
            output_path: Optional output path. If None, uses lemlist_import_YYYY-MM-DD.csv
            min_score: Minimum priority score to include (0-100, based on max of DPP/Commerce scores)
            campaign_filter: Filter by campaign type ('DPP' or 'B2B_Commerce'). None = include all.
        """
        logger.info(f"Loading personalized leads from {input_path}")
        df = pd.read_csv(input_path)
        
        # Calculate composite score for filtering
        df['composite_score'] = df.apply(
            lambda row: max(
                row.get('dpp_signal_score', 0),
                row.get('commerce_signal_score', 0)
            ),
            axis=1
        )
        
        # Apply filters
        original_count = len(df)
        
        if min_score > 0:
            df = df[df['composite_score'] >= min_score]
            logger.info(f"Filtered by min_score >= {min_score}: {len(df)} leads remain")
        
        if campaign_filter:
            df = df[df['recommended_campaign'] == campaign_filter]
            logger.info(f"Filtered by campaign '{campaign_filter}': {len(df)} leads remain")
        
        # Map to Lemlist format
        lemlist_rows = []
        for idx, row in df.iterrows():
            lemlist_row = self.map_to_lemlist(row.to_dict())
            lemlist_rows.append(lemlist_row)
        
        lemlist_df = pd.DataFrame(lemlist_rows)
        
        # Set output path
        if output_path is None:
            now = datetime.now()
            output_path = f"lemlist_import_{now.strftime('%Y-%m-%d')}.csv"
        
        lemlist_df.to_csv(output_path, index=False)
        logger.info(f"\n=== LEMLIST EXPORT SUMMARY ===")
        logger.info(f"Original leads: {original_count}")
        logger.info(f"After filtering: {len(lemlist_df)}")
        logger.info(f"Export saved to: {output_path}")
        
        # Show campaign breakdown
        if 'campaign' in lemlist_df.columns:
            campaign_counts = lemlist_df['campaign'].value_counts()
            logger.info(f"\nCampaign breakdown:")
            for campaign, count in campaign_counts.items():
                logger.info(f"  {campaign}: {count}")
        
        # Show priority breakdown
        if 'priority' in lemlist_df.columns:
            priority_counts = lemlist_df['priority'].value_counts()
            logger.info(f"\nPriority breakdown:")
            for priority, count in priority_counts.items():
                logger.info(f"  {priority}: {count}")
        
        return lemlist_df


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lemlist_export.py <personalized_csv> [--output OUTPUT] [--min-score 60] [--campaign DPP]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    min_score = 0
    campaign = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--output':
            output_file = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '--min-score':
            min_score = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == '--campaign':
            campaign = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    exporter = LemlistExporter()
    exporter.export_csv(input_file, output_file, min_score, campaign)
