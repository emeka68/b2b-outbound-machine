"""
enricher.py — Web scraping & company data enrichment

Author: Nnaemeka Duru (emekaduru09@gmail.com)

Takes a CSV of company names/domains and enriches them with:
- Tech stack signals (via meta tags, script sources, platform indicators)
- DPP compliance signals (digital product passport, EU compliance, sustainability)
- Description snippets and industry/size indicators
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CompanyEnricher:
    """Enriches company data by scraping and analyzing their websites."""
    
    # Tech stack indicators
    TECH_PLATFORMS = {
        'shopware': ['shopware', 'Shopware'],
        'magento': ['magento', 'Magento'],
        'woocommerce': ['woocommerce', 'WooCommerce', '/wp-json/'],
        'sap': ['sap', 'SAP', '/sap/'],
        'salesforce': ['salesforce', 'Salesforce'],
        'oracle': ['oracle', 'Oracle'],
        'prestashop': ['prestashop', 'PrestaShop'],
        'bigcommerce': ['bigcommerce', 'BigCommerce'],
    }
    
    # DPP (Digital Product Passport) compliance signals
    DPP_KEYWORDS = [
        'digital product passport',
        'DPP',
        'EU compliance',
        'product data',
        'sustainability',
        'traceability',
        'circular economy',
        'product passport',
        'compliance ready',
    ]
    
    # Industry indicators
    INDUSTRY_KEYWORDS = {
        'manufacturing': ['manufacturing', 'fabrication', 'production', 'industrial'],
        'ecommerce': ['shop', 'store', 'ecommerce', 'online store', 'marketplace'],
        'logistics': ['logistics', 'shipping', 'warehouse', 'supply chain'],
        'wholesale': ['wholesale', 'distributor', 'b2b supplier'],
    }
    
    def __init__(self, timeout=10, retries=2):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, domain: str) -> Tuple[str, bool]:
        """
        Fetch a webpage with retry logic.
        Returns tuple: (html_content, success_flag)
        """
        if not domain.startswith('http'):
            domain = f'https://{domain}'
        
        for attempt in range(self.retries):
            try:
                response = self.session.get(domain, timeout=self.timeout)
                response.raise_for_status()
                return response.text, True
            except requests.exceptions.RequestException as e:
                logger.debug(f"Attempt {attempt+1} failed for {domain}: {str(e)}")
                time.sleep(1)
        
        logger.warning(f"Failed to fetch {domain} after {self.retries} retries")
        return "", False
    
    def detect_tech_stack(self, html: str) -> Tuple[List[str], int]:
        """
        Detect tech stack from HTML content.
        Returns tuple: (tech_list, confidence_score)
        """
        soup = BeautifulSoup(html, 'html.parser')
        detected = []
        
        # Check meta tags
        meta_content = ' '.join([
            tag.get('content', '') for tag in soup.find_all('meta')
        ])
        
        # Check script sources
        script_content = ' '.join([
            tag.get('src', '') for tag in soup.find_all('script')
        ])
        
        # Check full HTML
        full_text = html.lower()
        
        for platform, keywords in self.TECH_PLATFORMS.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    detected.append(platform)
                    break
        
        confidence = min(100, len(detected) * 25)
        return detected, confidence
    
    def detect_dpp_signals(self, html: str, text: str) -> Tuple[int, List[str]]:
        """
        Detect DPP compliance signals.
        Returns tuple: (dpp_score 0-100, signals_found)
        """
        combined = (html + ' ' + text).lower()
        signals_found = []
        
        for keyword in self.DPP_KEYWORDS:
            if keyword.lower() in combined:
                signals_found.append(keyword)
        
        # Score based on signals
        dpp_score = min(100, len(signals_found) * 20)
        return dpp_score, signals_found
    
    def detect_industry(self, html: str, company_name: str) -> Tuple[str, List[str]]:
        """
        Detect industry from website content.
        Returns tuple: (primary_industry, signals_found)
        """
        full_text = (html + ' ' + company_name).lower()
        industry_scores = {ind: 0 for ind in self.INDUSTRY_KEYWORDS}
        
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    industry_scores[industry] += 1
        
        primary_industry = max(industry_scores, key=industry_scores.get) if any(industry_scores.values()) else 'Unknown'
        signals = [ind for ind, score in industry_scores.items() if score > 0]
        
        return primary_industry, signals
    
    def extract_description(self, html: str, domain: str) -> str:
        """
        Extract company description from meta tags or page content.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'][:200]
        
        # Try og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'][:200]
        
        # Try first paragraph
        p_tag = soup.find('p')
        if p_tag:
            return p_tag.get_text()[:200]
        
        return f"Website: {domain}"
    
    def enrich_row(self, row: Dict) -> Dict:
        """
        Enrich a single row with domain data.
        """
        domain = row.get('domain', '')
        company = row.get('company', 'Unknown')
        
        if not domain:
            logger.warning(f"No domain for {company}")
            return {**row, 'tech_stack': '', 'dpp_ready': 0, 'description_snippet': '', 'signals_found': ''}
        
        # Fetch page
        html, success = self.fetch_page(domain)
        
        if not success:
            return {**row, 'tech_stack': 'N/A', 'dpp_ready': 0, 'description_snippet': 'Could not fetch', 'signals_found': ''}
        
        # Detect tech stack
        tech_list, tech_score = self.detect_tech_stack(html)
        
        # Extract text content
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ')
        
        # Detect DPP signals
        dpp_score, dpp_signals = self.detect_dpp_signals(html, text)
        
        # Detect industry
        industry, industry_signals = self.detect_industry(html, company)
        
        # Extract description
        description = self.extract_description(html, domain)
        
        return {
            **row,
            'tech_stack': ','.join(tech_list) or 'Unknown',
            'dpp_ready': dpp_score,
            'description_snippet': description,
            'signals_found': ','.join(dpp_signals) or 'None',
            'industry': industry,
        }
    
    def enrich_csv(self, input_path: str, output_path: str) -> pd.DataFrame:
        """
        Read CSV, enrich each row, write output CSV.
        """
        logger.info(f"Loading {input_path}")
        df = pd.read_csv(input_path)
        
        logger.info(f"Enriching {len(df)} companies...")
        enriched_rows = []
        
        for idx, row in df.iterrows():
            logger.info(f"[{idx+1}/{len(df)}] Enriching {row.get('company', 'Unknown')}")
            enriched = self.enrich_row(row.to_dict())
            enriched_rows.append(enriched)
            time.sleep(0.5)  # Rate limiting
        
        enriched_df = pd.DataFrame(enriched_rows)
        enriched_df.to_csv(output_path, index=False)
        logger.info(f"Enriched data saved to {output_path}")
        
        return enriched_df


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python enricher.py <input_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'enriched_leads.csv'
    
    enricher = CompanyEnricher()
    enricher.enrich_csv(input_file, output_file)
