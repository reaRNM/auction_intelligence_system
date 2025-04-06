from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from decimal import Decimal

from .base_reporter import BaseReporter

logger = logging.getLogger(__name__)

class AuctionReporter(BaseReporter):
    """Generator for post-auction analysis reports."""
    
    def __init__(self):
        """Initialize the auction reporter."""
        super().__init__()
        
        # Performance thresholds
        self.performance_thresholds = {
            'excellent': 1.2,
            'good': 1.0,
            'fair': 0.8,
            'poor': 0.6
        }
    
    def generate_post_auction_report(self, data: Dict, format: str = 'dashboard') -> Union[str, bytes]:
        """Generate post-auction analysis report.
        
        Args:
            data: Raw auction data
            format: Output format
            
        Returns:
            Report in requested format
        """
        try:
            # Process data
            summary = self._process_auction_summary(data.get('auctions', []))
            performance = self._analyze_performance(data.get('auctions', []))
            patterns = self._analyze_bidding_patterns(data.get('auctions', []))
            
            # Generate report
            report_data = {
                'summary': summary,
                'performance': performance,
                'patterns': patterns
            }
            
            return self.generate_report('post_auction', report_data, format)
            
        except Exception as e:
            logger.error(f"Post-auction report generation failed: {e}")
            return None
    
    def _process_auction_summary(self, auctions: List[Dict]) -> Dict:
        """Process auction summary data.
        
        Args:
            auctions: List of auction data
            
        Returns:
            Processed summary data
        """
        try:
            summary = {
                'total_auctions': len(auctions),
                'won_auctions': 0,
                'lost_auctions': 0,
                'total_spent': Decimal('0'),
                'total_value': Decimal('0'),
                'categories': {},
                'time_periods': {
                    'morning': 0,
                    'afternoon': 0,
                    'evening': 0,
                    'night': 0
                }
            }
            
            for auction in auctions:
                # Count won/lost
                if auction['won']:
                    summary['won_auctions'] += 1
                    summary['total_spent'] += Decimal(str(auction['winning_bid']))
                    summary['total_value'] += Decimal(str(auction['estimated_value']))
                else:
                    summary['lost_auctions'] += 1
                
                # Count by category
                category = auction['category']
                if category not in summary['categories']:
                    summary['categories'][category] = {
                        'total': 0,
                        'won': 0,
                        'lost': 0,
                        'spent': Decimal('0'),
                        'value': Decimal('0')
                    }
                
                cat_stats = summary['categories'][category]
                cat_stats['total'] += 1
                if auction['won']:
                    cat_stats['won'] += 1
                    cat_stats['spent'] += Decimal(str(auction['winning_bid']))
                    cat_stats['value'] += Decimal(str(auction['estimated_value']))
                else:
                    cat_stats['lost'] += 1
                
                # Count by time period
                hour = auction['end_time'].hour
                if 6 <= hour < 12:
                    summary['time_periods']['morning'] += 1
                elif 12 <= hour < 17:
                    summary['time_periods']['afternoon'] += 1
                elif 17 <= hour < 22:
                    summary['time_periods']['evening'] += 1
                else:
                    summary['time_periods']['night'] += 1
            
            # Calculate percentages
            if summary['total_auctions'] > 0:
                summary['win_rate'] = summary['won_auctions'] / summary['total_auctions']
                summary['value_ratio'] = summary['total_value'] / summary['total_spent'] if summary['total_spent'] > 0 else Decimal('0')
            
            return summary
            
        except Exception as e:
            logger.error(f"Auction summary processing failed: {e}")
            return {}
    
    def _analyze_performance(self, auctions: List[Dict]) -> Dict:
        """Analyze auction performance.
        
        Args:
            auctions: List of auction data
            
        Returns:
            Performance analysis
        """
        try:
            performance = {
                'overall': {
                    'actual_value': Decimal('0'),
                    'predicted_value': Decimal('0'),
                    'accuracy': 0,
                    'bias': 0
                },
                'by_category': {},
                'by_condition': {},
                'by_price_range': {
                    '0-50': {'count': 0, 'accuracy': 0},
                    '50-100': {'count': 0, 'accuracy': 0},
                    '100-500': {'count': 0, 'accuracy': 0},
                    '500+': {'count': 0, 'accuracy': 0}
                }
            }
            
            for auction in auctions:
                if not auction['won']:
                    continue
                
                actual_value = Decimal(str(auction['actual_value']))
                predicted_value = Decimal(str(auction['estimated_value']))
                
                # Overall performance
                performance['overall']['actual_value'] += actual_value
                performance['overall']['predicted_value'] += predicted_value
                
                # Category performance
                category = auction['category']
                if category not in performance['by_category']:
                    performance['by_category'][category] = {
                        'count': 0,
                        'actual_value': Decimal('0'),
                        'predicted_value': Decimal('0'),
                        'accuracy': 0
                    }
                
                cat_perf = performance['by_category'][category]
                cat_perf['count'] += 1
                cat_perf['actual_value'] += actual_value
                cat_perf['predicted_value'] += predicted_value
                
                # Condition performance
                condition = auction['condition']
                if condition not in performance['by_condition']:
                    performance['by_condition'][condition] = {
                        'count': 0,
                        'actual_value': Decimal('0'),
                        'predicted_value': Decimal('0'),
                        'accuracy': 0
                    }
                
                cond_perf = performance['by_condition'][condition]
                cond_perf['count'] += 1
                cond_perf['actual_value'] += actual_value
                cond_perf['predicted_value'] += predicted_value
                
                # Price range performance
                price_range = self._get_price_range(auction['winning_bid'])
                price_perf = performance['by_price_range'][price_range]
                price_perf['count'] += 1
            
            # Calculate accuracy and bias
            self._calculate_performance_metrics(performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {}
    
    def _analyze_bidding_patterns(self, auctions: List[Dict]) -> Dict:
        """Analyze bidding patterns.
        
        Args:
            auctions: List of auction data
            
        Returns:
            Bidding pattern analysis
        """
        try:
            patterns = {
                'bidding_times': {
                    'early': 0,
                    'middle': 0,
                    'late': 0
                },
                'bid_increments': {
                    'small': 0,
                    'medium': 0,
                    'large': 0
                },
                'competitor_patterns': {},
                'winning_strategies': {
                    'aggressive': 0,
                    'moderate': 0,
                    'conservative': 0
                }
            }
            
            for auction in auctions:
                if not auction['won']:
                    continue
                
                # Analyze bidding timing
                bid_timing = self._analyze_bid_timing(auction)
                patterns['bidding_times'][bid_timing] += 1
                
                # Analyze bid increments
                increment = self._analyze_bid_increment(auction)
                patterns['bid_increments'][increment] += 1
                
                # Analyze competitor patterns
                for competitor in auction.get('competitors', []):
                    competitor_id = competitor['id']
                    if competitor_id not in patterns['competitor_patterns']:
                        patterns['competitor_patterns'][competitor_id] = {
                            'total_bids': 0,
                            'avg_increment': 0,
                            'win_rate': 0,
                            'categories': set()
                        }
                    
                    comp_pattern = patterns['competitor_patterns'][competitor_id]
                    comp_pattern['total_bids'] += competitor['bid_count']
                    comp_pattern['avg_increment'] = (
                        (comp_pattern['avg_increment'] * (comp_pattern['total_bids'] - 1) +
                         competitor['avg_increment']) / comp_pattern['total_bids']
                    )
                    comp_pattern['categories'].add(auction['category'])
                
                # Analyze winning strategy
                strategy = self._analyze_winning_strategy(auction)
                patterns['winning_strategies'][strategy] += 1
            
            # Convert sets to lists for JSON serialization
            for competitor in patterns['competitor_patterns'].values():
                competitor['categories'] = list(competitor['categories'])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Bidding pattern analysis failed: {e}")
            return {}
    
    def _get_price_range(self, price: float) -> str:
        """Get price range category.
        
        Args:
            price: Price value
            
        Returns:
            Price range category
        """
        if price <= 50:
            return '0-50'
        elif price <= 100:
            return '50-100'
        elif price <= 500:
            return '100-500'
        else:
            return '500+'
    
    def _calculate_performance_metrics(self, performance: Dict) -> None:
        """Calculate performance metrics.
        
        Args:
            performance: Performance data to update
        """
        try:
            # Overall performance
            if performance['overall']['predicted_value'] > 0:
                performance['overall']['accuracy'] = (
                    performance['overall']['actual_value'] /
                    performance['overall']['predicted_value']
                )
                performance['overall']['bias'] = (
                    (performance['overall']['predicted_value'] -
                     performance['overall']['actual_value']) /
                    performance['overall']['actual_value']
                )
            
            # Category performance
            for category in performance['by_category'].values():
                if category['predicted_value'] > 0:
                    category['accuracy'] = (
                        category['actual_value'] /
                        category['predicted_value']
                    )
            
            # Condition performance
            for condition in performance['by_condition'].values():
                if condition['predicted_value'] > 0:
                    condition['accuracy'] = (
                        condition['actual_value'] /
                        condition['predicted_value']
                    )
            
            # Price range performance
            for price_range in performance['by_price_range'].values():
                if price_range['count'] > 0:
                    price_range['accuracy'] = price_range['count'] / len(performance['by_price_range'])
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
    
    def _analyze_bid_timing(self, auction: Dict) -> str:
        """Analyze bidding timing pattern.
        
        Args:
            auction: Auction data
            
        Returns:
            Timing pattern category
        """
        try:
            total_time = (auction['end_time'] - auction['start_time']).total_seconds()
            first_bid_time = (auction['first_bid_time'] - auction['start_time']).total_seconds()
            
            if first_bid_time < total_time * 0.3:
                return 'early'
            elif first_bid_time < total_time * 0.7:
                return 'middle'
            else:
                return 'late'
                
        except Exception as e:
            logger.error(f"Bid timing analysis failed: {e}")
            return 'middle'
    
    def _analyze_bid_increment(self, auction: Dict) -> str:
        """Analyze bid increment pattern.
        
        Args:
            auction: Auction data
            
        Returns:
            Increment pattern category
        """
        try:
            avg_increment = auction['avg_bid_increment']
            starting_price = auction['starting_price']
            
            if avg_increment < starting_price * 0.05:
                return 'small'
            elif avg_increment < starting_price * 0.15:
                return 'medium'
            else:
                return 'large'
                
        except Exception as e:
            logger.error(f"Bid increment analysis failed: {e}")
            return 'medium'
    
    def _analyze_winning_strategy(self, auction: Dict) -> str:
        """Analyze winning bidding strategy.
        
        Args:
            auction: Auction data
            
        Returns:
            Strategy category
        """
        try:
            bid_count = auction['bid_count']
            price_increase = (
                auction['winning_bid'] - auction['starting_price']
            ) / auction['starting_price']
            
            if bid_count > 5 and price_increase > 0.3:
                return 'aggressive'
            elif bid_count > 2 and price_increase > 0.1:
                return 'moderate'
            else:
                return 'conservative'
                
        except Exception as e:
            logger.error(f"Winning strategy analysis failed: {e}")
            return 'moderate' 