from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from decimal import Decimal

from .base_reporter import BaseReporter

logger = logging.getLogger(__name__)

class OpportunityReporter(BaseReporter):
    """Generator for daily opportunity reports."""
    
    def __init__(self):
        """Initialize the opportunity reporter."""
        super().__init__()
        
        # Risk/reward thresholds
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        self.reward_thresholds = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.7
        }
    
    def generate_daily_report(self, data: Dict, format: str = 'dashboard') -> Union[str, bytes]:
        """Generate daily opportunity report.
        
        Args:
            data: Raw data for the report
            format: Output format
            
        Returns:
            Report in requested format
        """
        try:
            # Process data
            opportunities = self._process_opportunities(data.get('opportunities', []))
            risk_reward = self._calculate_risk_reward(opportunities)
            budget = self._calculate_budget_allocation(opportunities)
            
            # Generate report
            report_data = {
                'opportunities': opportunities,
                'risk_reward': risk_reward,
                'budget': budget
            }
            
            return self.generate_report('daily_opportunity', report_data, format)
            
        except Exception as e:
            logger.error(f"Daily opportunity report generation failed: {e}")
            return None
    
    def _process_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Process and rank opportunities.
        
        Args:
            opportunities: Raw opportunity data
            
        Returns:
            Processed and ranked opportunities
        """
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(opportunities)
            
            # Calculate opportunity score
            df['opportunity_score'] = self._calculate_opportunity_score(df)
            
            # Sort by opportunity score
            df = df.sort_values('opportunity_score', ascending=False)
            
            # Take top 10
            df = df.head(10)
            
            # Convert back to list of dictionaries
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Opportunity processing failed: {e}")
            return []
    
    def _calculate_opportunity_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate opportunity score for each item.
        
        Args:
            df: DataFrame of opportunities
            
        Returns:
            Series of opportunity scores
        """
        try:
            # Calculate profit potential
            profit_potential = (df['estimated_value'] - df['current_price']) / df['current_price']
            
            # Calculate market demand
            market_demand = df['search_volume'] / df['search_volume'].max()
            
            # Calculate competition level
            competition = 1 - (df['number_of_sellers'] / df['number_of_sellers'].max())
            
            # Calculate price stability
            price_stability = 1 - (df['price_volatility'] / df['price_volatility'].max())
            
            # Combine factors
            score = (
                0.4 * profit_potential +
                0.3 * market_demand +
                0.2 * competition +
                0.1 * price_stability
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Opportunity score calculation failed: {e}")
            return pd.Series([0] * len(df))
    
    def _calculate_risk_reward(self, opportunities: List[Dict]) -> Dict:
        """Calculate risk/reward matrix.
        
        Args:
            opportunities: Processed opportunities
            
        Returns:
            Risk/reward matrix
        """
        try:
            risk_reward = {}
            
            for opp in opportunities:
                category = opp['category']
                
                # Calculate risk score
                risk_score = self._calculate_risk_score(opp)
                
                # Calculate reward score
                reward_score = self._calculate_reward_score(opp)
                
                # Add to matrix
                if category not in risk_reward:
                    risk_reward[category] = {
                        'risk': risk_score,
                        'reward': reward_score,
                        'count': 1
                    }
                else:
                    # Average with existing scores
                    existing = risk_reward[category]
                    count = existing['count'] + 1
                    risk_reward[category] = {
                        'risk': (existing['risk'] * existing['count'] + risk_score) / count,
                        'reward': (existing['reward'] * existing['count'] + reward_score) / count,
                        'count': count
                    }
            
            return risk_reward
            
        except Exception as e:
            logger.error(f"Risk/reward calculation failed: {e}")
            return {}
    
    def _calculate_risk_score(self, opportunity: Dict) -> float:
        """Calculate risk score for an opportunity.
        
        Args:
            opportunity: Opportunity data
            
        Returns:
            Risk score between 0 and 1
        """
        try:
            # Price volatility risk
            price_risk = opportunity['price_volatility']
            
            # Competition risk
            competition_risk = opportunity['number_of_sellers'] / 100  # Normalize
            
            # Market demand risk
            demand_risk = 1 - (opportunity['search_volume'] / 1000)  # Normalize
            
            # Condition risk
            condition_risk = 1 - opportunity['condition_score']
            
            # Combine risks
            risk_score = (
                0.3 * price_risk +
                0.3 * competition_risk +
                0.2 * demand_risk +
                0.2 * condition_risk
            )
            
            return min(max(risk_score, 0), 1)
            
        except Exception as e:
            logger.error(f"Risk score calculation failed: {e}")
            return 0.5
    
    def _calculate_reward_score(self, opportunity: Dict) -> float:
        """Calculate reward score for an opportunity.
        
        Args:
            opportunity: Opportunity data
            
        Returns:
            Reward score between 0 and 1
        """
        try:
            # Profit potential
            profit_potential = (opportunity['estimated_value'] - opportunity['current_price']) / opportunity['current_price']
            
            # Market demand
            market_demand = opportunity['search_volume'] / 1000  # Normalize
            
            # Price stability
            price_stability = 1 - opportunity['price_volatility']
            
            # Condition value
            condition_value = opportunity['condition_score']
            
            # Combine factors
            reward_score = (
                0.4 * profit_potential +
                0.3 * market_demand +
                0.2 * price_stability +
                0.1 * condition_value
            )
            
            return min(max(reward_score, 0), 1)
            
        except Exception as e:
            logger.error(f"Reward score calculation failed: {e}")
            return 0.5
    
    def _calculate_budget_allocation(self, opportunities: List[Dict]) -> Dict:
        """Calculate budget allocation suggestions.
        
        Args:
            opportunities: Processed opportunities
            
        Returns:
            Budget allocation suggestions
        """
        try:
            budget = {}
            total_score = 0
            
            # Calculate total opportunity score
            for opp in opportunities:
                total_score += opp['opportunity_score']
            
            # Allocate budget based on opportunity scores
            for opp in opportunities:
                category = opp['category']
                allocation = opp['opportunity_score'] / total_score
                
                if category not in budget:
                    budget[category] = {
                        'amount': allocation,
                        'percentage': allocation * 100
                    }
                else:
                    # Add to existing allocation
                    existing = budget[category]
                    budget[category] = {
                        'amount': existing['amount'] + allocation,
                        'percentage': (existing['amount'] + allocation) * 100
                    }
            
            return budget
            
        except Exception as e:
            logger.error(f"Budget allocation calculation failed: {e}")
            return {} 