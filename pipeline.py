"""
pipeline.py — Main orchestrator for B2B outbound automation

Author: Nnaemeka Duru (emekaduru09@gmail.com)

Runs the complete pipeline:
enricher → signal_detector → personalizer → lemlist_export

CLI usage:
  python pipeline.py --input leads.csv --min-score 60 --campaign DPP
"""

import click
import logging
import os
from datetime import datetime
from pathlib import Path

from enricher import CompanyEnricher
from signal_detector import SignalDetector
from personalizer import EmailPersonalizer
from lemlist_export import LemlistExporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OutboundPipeline:
    """Full B2B outbound automation pipeline."""
    
    def __init__(self, input_path: str, output_dir: str = None):
        """
        Initialize pipeline.
        
        Args:
            input_path: Path to input CSV with company/domain data
            output_dir: Directory for intermediate and final outputs. Defaults to current dir.
        """
        self.input_path = input_path
        self.output_dir = output_dir or '.'
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.enricher = CompanyEnricher()
        self.detector = SignalDetector()
        self.personalizer = EmailPersonalizer()
        self.exporter = LemlistExporter()
        
        # Output paths
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.enriched_path = os.path.join(self.output_dir, f'01_enriched_{timestamp}.csv')
        self.scored_path = os.path.join(self.output_dir, f'02_scored_{timestamp}.csv')
        self.personalized_path = os.path.join(self.output_dir, f'03_personalized_{timestamp}.csv')
        self.lemlist_path = os.path.join(self.output_dir, f'04_lemlist_import_{timestamp}.csv')
    
    def run(self, min_score: int = 0, campaign: str = None) -> dict:
        """
        Execute the full pipeline.
        
        Args:
            min_score: Minimum signal score threshold (0-100)
            campaign: Filter by campaign ('DPP' or 'B2B_Commerce'). None = include all.
        
        Returns:
            Dictionary with pipeline results and file paths
        """
        logger.info("=" * 70)
        logger.info("🚀 B2B OUTBOUND AUTOMATION PIPELINE")
        logger.info("=" * 70)
        
        # Step 1: Enrich
        logger.info("\n[STEP 1/4] ENRICHMENT")
        logger.info("-" * 70)
        enriched_df = self.enricher.enrich_csv(self.input_path, self.enriched_path)
        logger.info(f"✓ Enriched {len(enriched_df)} companies")
        logger.info(f"  Output: {self.enriched_path}")
        
        # Step 2: Score
        logger.info("\n[STEP 2/4] SIGNAL DETECTION & SCORING")
        logger.info("-" * 70)
        scored_df = self.detector.score_csv(self.enriched_path, self.scored_path)
        logger.info(f"✓ Scored {len(scored_df)} leads")
        logger.info(f"  Output: {self.scored_path}")
        
        # Step 3: Personalize
        logger.info("\n[STEP 3/4] PERSONALIZATION")
        logger.info("-" * 70)
        personalized_df = self.personalizer.personalize_csv(self.scored_path, self.personalized_path)
        logger.info(f"✓ Generated {len(personalized_df)} personalized icebreakers")
        logger.info(f"  Output: {self.personalized_path}")
        
        # Step 4: Export
        logger.info("\n[STEP 4/4] LEMLIST EXPORT")
        logger.info("-" * 70)
        lemlist_df = self.exporter.export_csv(
            self.personalized_path,
            self.lemlist_path,
            min_score=min_score,
            campaign_filter=campaign
        )
        logger.info(f"✓ Exported {len(lemlist_df)} leads to Lemlist format")
        logger.info(f"  Output: {self.lemlist_path}")
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Input file: {self.input_path}")
        logger.info(f"Total leads processed: {len(enriched_df)}")
        logger.info(f"Leads after filtering (min_score={min_score}, campaign={campaign}): {len(lemlist_df)}")
        logger.info(f"\nAll files saved to: {self.output_dir}")
        logger.info(f"  1. {os.path.basename(self.enriched_path)}")
        logger.info(f"  2. {os.path.basename(self.scored_path)}")
        logger.info(f"  3. {os.path.basename(self.personalized_path)}")
        logger.info(f"  4. {os.path.basename(self.lemlist_path)} ← READY FOR LEMLIST IMPORT")
        logger.info("=" * 70)
        
        return {
            'success': True,
            'total_leads': len(enriched_df),
            'exported_leads': len(lemlist_df),
            'enriched_file': self.enriched_path,
            'scored_file': self.scored_path,
            'personalized_file': self.personalized_path,
            'lemlist_file': self.lemlist_path,
        }


@click.command()
@click.option(
    '--input',
    required=True,
    help='Input CSV file with company/domain data'
)
@click.option(
    '--output-dir',
    default=None,
    help='Output directory for results (default: current directory)'
)
@click.option(
    '--min-score',
    default=0,
    type=int,
    help='Minimum signal score to include (0-100, default: 0)'
)
@click.option(
    '--campaign',
    default=None,
    type=click.Choice(['DPP', 'B2B_Commerce']),
    help='Filter by campaign type (optional)'
)
def main(input: str, output_dir: str, min_score: int, campaign: str):
    """
    Run B2B outbound automation pipeline.
    
    Takes company/domain data and enriches, scores, personalizes, and exports to Lemlist.
    """
    if not os.path.exists(input):
        logger.error(f"Input file not found: {input}")
        exit(1)
    
    pipeline = OutboundPipeline(input, output_dir)
    result = pipeline.run(min_score=min_score, campaign=campaign)
    
    if result['success']:
        logger.info("\n✅ Pipeline completed successfully!")
        exit(0)
    else:
        logger.error("\n❌ Pipeline failed!")
        exit(1)


if __name__ == '__main__':
    main()
