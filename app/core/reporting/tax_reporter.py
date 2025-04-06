from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from decimal import Decimal

from .base_reporter import BaseReporter

logger = logging.getLogger(__name__)

class TaxReporter(BaseReporter):
    """Generator for tax preparation reports."""
    
    def __init__(self):
        """Initialize the tax reporter."""
        super().__init__()
        
        # Tax rates
        self.sales_tax_rates = {
            'standard': Decimal('0.0825'),  # 8.25%
            'reduced': Decimal('0.0625'),   # 6.25%
            'exempt': Decimal('0.0')        # 0%
        }
        
        # Fee categories
        self.fee_categories = {
            'platform_fees': ['listing_fee', 'final_value_fee', 'store_fee'],
            'payment_fees': ['payment_processing_fee', 'currency_conversion_fee'],
            'shipping_fees': ['shipping_cost', 'handling_fee', 'insurance_fee'],
            'other_fees': ['promotion_fee', 'subscription_fee', 'other_fee']
        }
    
    def generate_tax_report(self, data: Dict, format: str = 'dashboard') -> Union[str, bytes]:
        """Generate tax preparation report.
        
        Args:
            data: Raw tax data
            format: Output format
            
        Returns:
            Report in requested format
        """
        try:
            # Process data
            fees = self._process_fees(data.get('fees', []))
            inventory = self._process_inventory(data.get('inventory', []))
            sales_tax = self._process_sales_tax(data.get('sales', []))
            
            # Generate report
            report_data = {
                'fees': fees,
                'inventory': inventory,
                'sales_tax': sales_tax
            }
            
            return self.generate_report('tax_prep', report_data, format)
            
        except Exception as e:
            logger.error(f"Tax report generation failed: {e}")
            return None
    
    def _process_fees(self, fees: List[Dict]) -> Dict:
        """Process fee data.
        
        Args:
            fees: List of fee data
            
        Returns:
            Processed fee data
        """
        try:
            fee_summary = {
                'total_fees': Decimal('0'),
                'by_category': {},
                'by_month': {},
                'deductible': Decimal('0'),
                'non_deductible': Decimal('0')
            }
            
            for fee in fees:
                amount = Decimal(str(fee['amount']))
                category = fee['category']
                month = fee['date'].strftime('%Y-%m')
                is_deductible = fee.get('deductible', True)
                
                # Add to total
                fee_summary['total_fees'] += amount
                
                # Add to category
                if category not in fee_summary['by_category']:
                    fee_summary['by_category'][category] = Decimal('0')
                fee_summary['by_category'][category] += amount
                
                # Add to month
                if month not in fee_summary['by_month']:
                    fee_summary['by_month'][month] = Decimal('0')
                fee_summary['by_month'][month] += amount
                
                # Add to deductible/non-deductible
                if is_deductible:
                    fee_summary['deductible'] += amount
                else:
                    fee_summary['non_deductible'] += amount
            
            # Calculate percentages
            if fee_summary['total_fees'] > 0:
                fee_summary['deductible_percentage'] = (
                    fee_summary['deductible'] / fee_summary['total_fees']
                ) * 100
                fee_summary['non_deductible_percentage'] = (
                    fee_summary['non_deductible'] / fee_summary['total_fees']
                ) * 100
            
            return fee_summary
            
        except Exception as e:
            logger.error(f"Fee processing failed: {e}")
            return {}
    
    def _process_inventory(self, inventory: List[Dict]) -> Dict:
        """Process inventory data.
        
        Args:
            inventory: List of inventory data
            
        Returns:
            Processed inventory data
        """
        try:
            inventory_summary = {
                'total_items': len(inventory),
                'total_value': Decimal('0'),
                'by_category': {},
                'by_condition': {},
                'age_distribution': {
                    '0-30_days': 0,
                    '31-90_days': 0,
                    '91-180_days': 0,
                    '180+_days': 0
                },
                'valuation_methods': {
                    'cost': Decimal('0'),
                    'market': Decimal('0'),
                    'lower_of_cost_or_market': Decimal('0')
                }
            }
            
            for item in inventory:
                cost = Decimal(str(item['cost']))
                market_value = Decimal(str(item['market_value']))
                category = item['category']
                condition = item['condition']
                age_days = (datetime.now() - item['purchase_date']).days
                
                # Add to total value
                inventory_summary['total_value'] += cost
                
                # Add to category
                if category not in inventory_summary['by_category']:
                    inventory_summary['by_category'][category] = {
                        'count': 0,
                        'value': Decimal('0')
                    }
                cat_stats = inventory_summary['by_category'][category]
                cat_stats['count'] += 1
                cat_stats['value'] += cost
                
                # Add to condition
                if condition not in inventory_summary['by_condition']:
                    inventory_summary['by_condition'][condition] = {
                        'count': 0,
                        'value': Decimal('0')
                    }
                cond_stats = inventory_summary['by_condition'][condition]
                cond_stats['count'] += 1
                cond_stats['value'] += cost
                
                # Add to age distribution
                if age_days <= 30:
                    inventory_summary['age_distribution']['0-30_days'] += 1
                elif age_days <= 90:
                    inventory_summary['age_distribution']['31-90_days'] += 1
                elif age_days <= 180:
                    inventory_summary['age_distribution']['91-180_days'] += 1
                else:
                    inventory_summary['age_distribution']['180+_days'] += 1
                
                # Add to valuation methods
                inventory_summary['valuation_methods']['cost'] += cost
                inventory_summary['valuation_methods']['market'] += market_value
                inventory_summary['valuation_methods']['lower_of_cost_or_market'] += min(cost, market_value)
            
            # Calculate percentages
            for category in inventory_summary['by_category'].values():
                if inventory_summary['total_value'] > 0:
                    category['percentage'] = (
                        category['value'] / inventory_summary['total_value']
                    ) * 100
            
            for condition in inventory_summary['by_condition'].values():
                if inventory_summary['total_value'] > 0:
                    condition['percentage'] = (
                        condition['value'] / inventory_summary['total_value']
                    ) * 100
            
            return inventory_summary
            
        except Exception as e:
            logger.error(f"Inventory processing failed: {e}")
            return {}
    
    def _process_sales_tax(self, sales: List[Dict]) -> Dict:
        """Process sales tax data.
        
        Args:
            sales: List of sales data
            
        Returns:
            Processed sales tax data
        """
        try:
            sales_tax_summary = {
                'total_sales': Decimal('0'),
                'total_tax': Decimal('0'),
                'by_state': {},
                'by_category': {},
                'by_rate': {
                    'standard': Decimal('0'),
                    'reduced': Decimal('0'),
                    'exempt': Decimal('0')
                },
                'monthly_totals': {}
            }
            
            for sale in sales:
                amount = Decimal(str(sale['amount']))
                tax_rate = sale.get('tax_rate', 'standard')
                state = sale['state']
                category = sale['category']
                month = sale['date'].strftime('%Y-%m')
                
                # Calculate tax
                tax_amount = amount * self.sales_tax_rates[tax_rate]
                
                # Add to totals
                sales_tax_summary['total_sales'] += amount
                sales_tax_summary['total_tax'] += tax_amount
                
                # Add to state
                if state not in sales_tax_summary['by_state']:
                    sales_tax_summary['by_state'][state] = {
                        'sales': Decimal('0'),
                        'tax': Decimal('0')
                    }
                state_stats = sales_tax_summary['by_state'][state]
                state_stats['sales'] += amount
                state_stats['tax'] += tax_amount
                
                # Add to category
                if category not in sales_tax_summary['by_category']:
                    sales_tax_summary['by_category'][category] = {
                        'sales': Decimal('0'),
                        'tax': Decimal('0')
                    }
                cat_stats = sales_tax_summary['by_category'][category]
                cat_stats['sales'] += amount
                cat_stats['tax'] += tax_amount
                
                # Add to rate
                sales_tax_summary['by_rate'][tax_rate] += tax_amount
                
                # Add to monthly totals
                if month not in sales_tax_summary['monthly_totals']:
                    sales_tax_summary['monthly_totals'][month] = {
                        'sales': Decimal('0'),
                        'tax': Decimal('0')
                    }
                month_stats = sales_tax_summary['monthly_totals'][month]
                month_stats['sales'] += amount
                month_stats['tax'] += tax_amount
            
            # Calculate percentages
            if sales_tax_summary['total_sales'] > 0:
                sales_tax_summary['effective_tax_rate'] = (
                    sales_tax_summary['total_tax'] / sales_tax_summary['total_sales']
                ) * 100
            
            for state in sales_tax_summary['by_state'].values():
                if state['sales'] > 0:
                    state['rate'] = (state['tax'] / state['sales']) * 100
            
            for category in sales_tax_summary['by_category'].values():
                if category['sales'] > 0:
                    category['rate'] = (category['tax'] / category['sales']) * 100
            
            return sales_tax_summary
            
        except Exception as e:
            logger.error(f"Sales tax processing failed: {e}")
            return {} 