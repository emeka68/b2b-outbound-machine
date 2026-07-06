"""
personalizer.py — AI-powered personalized email icebreaker generation

Author: Nnaemeka Duru (emekaduru09@gmail.com)

Generates hyper-personalized cold email icebreakers using OpenAI API.
Falls back to template-based personalization if API key not available.
"""

import pandas as pd
import os
import logging
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Falling back to template-based personalization.")


class EmailPersonalizer:
    """Generates personalized email icebreakers for cold outreach."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize personalizer with optional OpenAI API key.
        If no key provided, falls back to template-based mode.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.use_api = OPENAI_AVAILABLE and bool(self.api_key)

        if self.use_api:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI API initialized (model={self.model}). Using AI-powered personalization.")
        else:
            logger.info("No OpenAI API key found. Using template-based fallback mode.")
    
    @staticmethod
    def _clean(value, default: str) -> str:
        """Coerce missing/NaN/placeholder values to a sensible default.

        pandas reads empty CSV cells as float NaN, so ``dict.get(key, default)``
        returns NaN (not the default) and renders as the literal string "nan".
        """
        text = str(value).strip()
        if not text or text.lower() in ('nan', 'none', 'n/a', 'unknown'):
            return default
        return text

    def generate_dpp_icebreaker_ai(self, row: Dict) -> str:
        """
        Generate DPP campaign icebreaker using OpenAI.
        """
        company = row.get('company', 'their company')
        signals = row.get('signals_found', 'sustainability initiatives')
        industry = row.get('industry', 'manufacturing')
        description = row.get('description_snippet', '')
        
        prompt = f"""Generate a compelling 2-3 sentence cold email icebreaker for a B2B sales outreach.

Company: {company}
Industry: {industry}
Compliance Signals Found: {signals}
Company Description: {description}

Campaign: Digital Product Passport (DPP) Compliance Solutions
Objective: Help them understand DPP requirements and implement solutions

Write a personalized, engaging icebreaker that:
- References their specific compliance signals or industry
- Shows you've done research on their business
- Creates urgency around DPP compliance (EU regulation)
- Is professional but conversational
- Does NOT include generic phrases

Return ONLY the icebreaker text, no additional commentary."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API failed for {company}: {str(e)}. Using fallback.")
            return self.generate_dpp_icebreaker_fallback(row)
    
    def generate_dpp_icebreaker_fallback(self, row: Dict) -> str:
        """
        Template-based DPP icebreaker (no API).
        """
        company = self._clean(row.get('company'), 'your company')
        signals = self._clean(row.get('signals_found'), 'sustainability')
        industry = self._clean(row.get('industry'), 'brands')
        primary_signal = signals.split(',')[0]

        templates = [
            f"We noticed {company} is focused on {primary_signal}. "
            f"With EU's Digital Product Passport mandate coming, we're helping {industry} build compliance-ready systems.",

            f"Saw that {company} is tracking {primary_signal}. "
            f"Our DPP solutions automate compliance and unlock competitive advantages.",

            f"{company} is positioned perfectly for DPP. We help manufacturers like you implement passport systems that reduce time-to-compliance by 60%.",
        ]
        
        return templates[hash(company) % len(templates)]
    
    def generate_commerce_icebreaker_ai(self, row: Dict) -> str:
        """
        Generate B2B Commerce campaign icebreaker using OpenAI.
        """
        company = row.get('company', 'their company')
        tech_stack = row.get('tech_stack', 'legacy systems')
        industry = row.get('industry', 'ecommerce')
        
        prompt = f"""Generate a compelling 2-3 sentence cold email icebreaker for a B2B sales outreach.

Company: {company}
Industry: {industry}
Current Tech Stack: {tech_stack}

Campaign: B2B Commerce Modernization
Objective: Help them upgrade from legacy commerce platforms to modern solutions

Write a personalized, engaging icebreaker that:
- References their current tech stack pain points
- Shows empathy for modernization challenges
- Highlights ROI of upgrading (speed, flexibility, integrations)
- Is professional but conversational
- Does NOT include generic phrases

Return ONLY the icebreaker text, no additional commentary."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI API failed for {company}: {str(e)}. Using fallback.")
            return self.generate_commerce_icebreaker_fallback(row)
    
    def generate_commerce_icebreaker_fallback(self, row: Dict) -> str:
        """
        Template-based Commerce icebreaker (no API).
        """
        company = self._clean(row.get('company'), 'your company')
        tech_stack = self._clean(row.get('tech_stack'), 'legacy systems')
        industry = self._clean(row.get('industry'), 'companies')

        templates = [
            f"We spotted {company} running {tech_stack}. Modern B2B buyers expect seamless integrations and APIs. "
            f"We help {industry} migrate to flexible platforms in weeks, not months.",

            f"{company} has the growth but {tech_stack} is holding you back. Our modernization approach keeps your data intact while unlocking 10x faster deployments.",

            f"Most {industry} teams using {tech_stack} are losing deals to faster, more flexible competitors. "
            f"Let's talk about a migration that pays for itself.",
        ]
        
        return templates[hash(company) % len(templates)]
    
    def personalize_row(self, row: Dict) -> Dict:
        """
        Generate personalized icebreaker for a single lead.
        """
        campaign = row.get('recommended_campaign', 'DPP')
        
        if campaign == 'DPP':
            icebreaker = self.generate_dpp_icebreaker_ai(row) if self.use_api else self.generate_dpp_icebreaker_fallback(row)
        else:
            icebreaker = self.generate_commerce_icebreaker_ai(row) if self.use_api else self.generate_commerce_icebreaker_fallback(row)
        
        return {**row, 'icebreaker': icebreaker}
    
    def personalize_csv(self, input_path: str, output_path: str) -> pd.DataFrame:
        """
        Read scored CSV, generate icebreakers, write output.
        """
        logger.info(f"Loading scored leads from {input_path}")
        df = pd.read_csv(input_path)
        
        logger.info(f"Personalizing {len(df)} icebreakers...")
        personalized_rows = []
        
        for idx, row in df.iterrows():
            personalized = self.personalize_row(row.to_dict())
            personalized_rows.append(personalized)
            logger.info(f"[{idx+1}/{len(df)}] Generated icebreaker for {row.get('company', 'Unknown')}")
        
        personalized_df = pd.DataFrame(personalized_rows)
        personalized_df.to_csv(output_path, index=False)
        logger.info(f"Personalized data saved to {output_path}")
        
        return personalized_df


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python personalizer.py <scored_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'personalized_leads.csv'
    
    personalizer = EmailPersonalizer()
    personalizer.personalize_csv(input_file, output_file)
