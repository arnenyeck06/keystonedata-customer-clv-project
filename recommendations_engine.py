"""
Recommendations Engine for ChurnGuard
Provides actionable recommendations based on churn risk and Customer Lifetime Value (CLV)
"""

import pandas as pd
from typing import Dict, List, Tuple


class RecommendationsEngine:
    """Generate actionable recommendations for customer retention"""
    
    def __init__(self):
        self.avg_monthly_revenue = 64.76
        self.avg_customer_lifespan = 32  # months
        
    def calculate_clv(self, monthly_charges: float, tenure: int, churn_probability: float) -> Dict:
        """
        Calculate Customer Lifetime Value (CLV)
        
        CLV = (Average Monthly Revenue × Customer Lifespan) - Acquisition Cost
        Adjusted for churn probability
        """
        # Basic CLV calculation
        expected_lifespan = max(1, int((1 - churn_probability) * self.avg_customer_lifespan))
        acquisition_cost = 200  # Estimated customer acquisition cost
        
        # Calculate CLV
        gross_clv = monthly_charges * expected_lifespan
        net_clv = gross_clv - acquisition_cost
        
        # Risk-adjusted CLV
        risk_adjusted_clv = net_clv * (1 - churn_probability)
        
        # Potential CLV if retained
        potential_clv = monthly_charges * self.avg_customer_lifespan - acquisition_cost
        
        # Value at risk
        value_at_risk = potential_clv - risk_adjusted_clv
        
        return {
            'gross_clv': round(gross_clv, 2),
            'net_clv': round(net_clv, 2),
            'risk_adjusted_clv': round(risk_adjusted_clv, 2),
            'potential_clv': round(potential_clv, 2),
            'value_at_risk': round(value_at_risk, 2),
            'expected_lifespan': expected_lifespan,
            'monthly_charges': monthly_charges
        }
    
    def get_customer_segment(self, clv: Dict, churn_probability: float) -> str:
        """Categorize customer into strategic segment"""
        value_at_risk = clv['value_at_risk']
        
        if churn_probability > 0.7 and value_at_risk > 1500:
            return "CRITICAL_HIGH_VALUE"
        elif churn_probability > 0.7 and value_at_risk > 500:
            return "CRITICAL_MEDIUM_VALUE"
        elif churn_probability > 0.7:
            return "CRITICAL_LOW_VALUE"
        elif churn_probability > 0.4 and value_at_risk > 1500:
            return "AT_RISK_HIGH_VALUE"
        elif churn_probability > 0.4 and value_at_risk > 500:
            return "AT_RISK_MEDIUM_VALUE"
        elif churn_probability > 0.4:
            return "AT_RISK_LOW_VALUE"
        else:
            return "STABLE"
    
    def generate_recommendations(
        self, 
        customer_id: str,
        churn_probability: float,
        risk_level: str,
        tenure: int,
        monthly_charges: float,
        contract: str = None,
        payment_method: str = None,
        internet_service: str = None
    ) -> Dict:
        """
        Generate comprehensive actionable recommendations
        """
        # Calculate CLV
        clv = self.calculate_clv(monthly_charges, tenure, churn_probability)
        
        # Get customer segment
        segment = self.get_customer_segment(clv, churn_probability)
        
        # Generate recommendations based on segment and features
        recommendations = self._get_segment_recommendations(
            segment, churn_probability, tenure, monthly_charges, 
            contract, payment_method, internet_service
        )
        
        # Calculate ROI of retention
        retention_cost = self._estimate_retention_cost(segment)
        roi = ((clv['value_at_risk'] - retention_cost) / retention_cost * 100) if retention_cost > 0 else 0
        
        return {
            'customer_id': customer_id,
            'segment': segment,
            'clv_metrics': clv,
            'priority': self._get_priority_score(segment, clv['value_at_risk']),
            'recommended_actions': recommendations['actions'],
            'retention_tactics': recommendations['tactics'],
            'timeline': recommendations['timeline'],
            'estimated_retention_cost': retention_cost,
            'expected_roi': round(roi, 1),
            'success_probability': self._estimate_success_rate(segment, tenure)
        }
    
    def _get_segment_recommendations(
        self, 
        segment: str, 
        churn_prob: float,
        tenure: int,
        monthly_charges: float,
        contract: str,
        payment_method: str,
        internet_service: str
    ) -> Dict:
        """Get specific recommendations based on segment"""
        
        recommendations = {
            'CRITICAL_HIGH_VALUE': {
                'actions': [
                    '🚨 IMMEDIATE: Assign dedicated account manager',
                    '📞 URGENT: Executive-level outreach within 24 hours',
                    '💎 VIP: Offer premium loyalty package (20-30% discount)',
                    '🎁 INCENTIVE: Provide exclusive perks (free upgrades, priority support)',
                    '📋 CONTRACT: Propose long-term contract with locked-in rates'
                ],
                'tactics': [
                    'Personal phone call from senior leadership',
                    'Custom retention package tailored to usage patterns',
                    'Waive any outstanding fees or charges',
                    'Offer multi-year discount (lock in for 24+ months)',
                    'Include premium services at no additional cost'
                ],
                'timeline': 'IMMEDIATE (24-48 hours)'
            },
            'CRITICAL_MEDIUM_VALUE': {
                'actions': [
                    '⚠️ URGENT: Contact within 48-72 hours',
                    '💰 OFFER: 15-20% retention discount',
                    '🔄 UPGRADE: Propose service upgrade at current price',
                    '📞 SUPPORT: Assign retention specialist',
                    '📝 SURVEY: Conduct satisfaction survey to identify pain points'
                ],
                'tactics': [
                    'Direct phone call from retention team',
                    'Flexible payment plan options',
                    'Trial of premium features (3-6 months free)',
                    'Contract flexibility (monthly to yearly conversion)',
                    'Enhanced customer support tier'
                ],
                'timeline': 'URGENT (48-72 hours)'
            },
            'CRITICAL_LOW_VALUE': {
                'actions': [
                    '📧 EMAIL: Automated retention campaign',
                    '💳 DISCOUNT: 10-15% discount offer',
                    '🎯 TARGETED: Send personalized retention offers',
                    '📱 DIGITAL: In-app/web retention messaging',
                    '🤖 AUTOMATED: Trigger retention workflow'
                ],
                'tactics': [
                    'Automated email sequence (3-5 emails)',
                    'Limited-time discount offers',
                    'Simplified contract options',
                    'Self-service retention portal',
                    'Chat-based support intervention'
                ],
                'timeline': 'PROMPT (3-7 days)'
            },
            'AT_RISK_HIGH_VALUE': {
                'actions': [
                    '📞 PROACTIVE: Schedule retention call',
                    '🎁 LOYALTY: Enroll in VIP loyalty program',
                    '💎 PERKS: Add complimentary premium features',
                    '📊 REVIEW: Quarterly account review meetings',
                    '🔒 LOCK-IN: Incentivize long-term commitment'
                ],
                'tactics': [
                    'Proactive retention call within 1 week',
                    '10-15% loyalty discount',
                    'Free service upgrades',
                    'Dedicated support channel',
                    'Annual contract incentives'
                ],
                'timeline': 'PROACTIVE (1 week)'
            },
            'AT_RISK_MEDIUM_VALUE': {
                'actions': [
                    '📧 ENGAGE: Send engagement campaign',
                    '🎯 PERSONALIZED: Tailored service recommendations',
                    '💡 EDUCATE: Share product tips and best practices',
                    '🎁 SURPRISE: Small loyalty rewards',
                    '📱 TOUCH: Regular check-in communications'
                ],
                'tactics': [
                    'Email engagement campaign',
                    '5-10% loyalty discount',
                    'Feature education and training',
                    'Usage optimization recommendations',
                    'Flexible upgrade options'
                ],
                'timeline': 'PROACTIVE (1-2 weeks)'
            },
            'AT_RISK_LOW_VALUE': {
                'actions': [
                    '🤖 AUTOMATED: Trigger retention workflow',
                    '📧 NURTURE: Add to engagement email list',
                    '💡 VALUE: Highlight unused features',
                    '📊 MONITOR: Track engagement metrics',
                    '🎯 SEGMENT: Include in retention campaigns'
                ],
                'tactics': [
                    'Automated email nurture sequence',
                    'Self-service retention offers',
                    'Usage tips and feature highlights',
                    'Community engagement initiatives',
                    'Seasonal promotional offers'
                ],
                'timeline': 'ONGOING (2-4 weeks)'
            },
            'STABLE': {
                'actions': [
                    '✅ MAINTAIN: Continue current service level',
                    '📊 MONITOR: Regular engagement tracking',
                    '💡 EDUCATE: Share product updates',
                    '🎁 REWARD: Recognition for loyalty',
                    '📈 UPSELL: Identify growth opportunities'
                ],
                'tactics': [
                    'Standard communication cadence',
                    'Newsletter and product updates',
                    'Loyalty rewards program',
                    'Upsell/cross-sell opportunities',
                    'Annual satisfaction survey'
                ],
                'timeline': 'ONGOING'
            }
        }
        
        # Get base recommendations
        base_recs = recommendations.get(segment, recommendations['STABLE'])
        
        # Add specific feature-based recommendations
        additional_actions = []
        
        if contract == 'Month-to-month':
            additional_actions.append('📝 CONTRACT: Offer annual contract with 15% discount')
        
        if payment_method == 'Electronic check':
            additional_actions.append('💳 PAYMENT: Suggest automatic payment method (reduce friction)')
        
        if tenure < 12:
            additional_actions.append('🎓 ONBOARDING: Enhance onboarding and early-stage support')
        
        if monthly_charges > 80:
            additional_actions.append('💰 PRICING: Review pricing competitiveness')
        
        # Merge recommendations
        if additional_actions:
            base_recs['actions'].extend(additional_actions)
        
        return base_recs
    
    def _get_priority_score(self, segment: str, value_at_risk: float) -> int:
        """
        Calculate priority score (1-10, 10 being highest)
        """
        segment_scores = {
            'CRITICAL_HIGH_VALUE': 10,
            'CRITICAL_MEDIUM_VALUE': 9,
            'CRITICAL_LOW_VALUE': 7,
            'AT_RISK_HIGH_VALUE': 8,
            'AT_RISK_MEDIUM_VALUE': 6,
            'AT_RISK_LOW_VALUE': 4,
            'STABLE': 2
        }
        
        base_score = segment_scores.get(segment, 1)
        
        # Adjust for value at risk
        if value_at_risk > 2000:
            base_score = min(10, base_score + 1)
        
        return base_score
    
    def _estimate_retention_cost(self, segment: str) -> float:
        """Estimate cost to execute retention strategy"""
        costs = {
            'CRITICAL_HIGH_VALUE': 500,
            'CRITICAL_MEDIUM_VALUE': 250,
            'CRITICAL_LOW_VALUE': 100,
            'AT_RISK_HIGH_VALUE': 300,
            'AT_RISK_MEDIUM_VALUE': 150,
            'AT_RISK_LOW_VALUE': 50,
            'STABLE': 20
        }
        return costs.get(segment, 100)
    
    def _estimate_success_rate(self, segment: str, tenure: int) -> float:
        """Estimate probability of successful retention"""
        base_rates = {
            'CRITICAL_HIGH_VALUE': 0.65,
            'CRITICAL_MEDIUM_VALUE': 0.55,
            'CRITICAL_LOW_VALUE': 0.40,
            'AT_RISK_HIGH_VALUE': 0.70,
            'AT_RISK_MEDIUM_VALUE': 0.60,
            'AT_RISK_LOW_VALUE': 0.50,
            'STABLE': 0.95
        }
        
        base_rate = base_rates.get(segment, 0.50)
        
        # Adjust for tenure (longer tenure = easier to retain)
        if tenure > 24:
            base_rate += 0.10
        elif tenure < 6:
            base_rate -= 0.10
        
        return min(0.95, max(0.20, base_rate))
    
    def generate_batch_summary(self, predictions_df: pd.DataFrame) -> Dict:
        """
        Generate portfolio-level summary and recommendations
        """
        total_customers = len(predictions_df)
        
        # Calculate total value at risk
        total_value_at_risk = 0
        segments_breakdown = {}
        priority_customers = []
        
        for idx, row in predictions_df.iterrows():
            # Calculate CLV for each customer
            clv = self.calculate_clv(
                row.get('monthly_charges', self.avg_monthly_revenue),
                row.get('tenure', 12),
                row.get('churn_probability', 0.5)
            )
            
            segment = self.get_customer_segment(clv, row.get('churn_probability', 0.5))
            
            total_value_at_risk += clv['value_at_risk']
            
            segments_breakdown[segment] = segments_breakdown.get(segment, 0) + 1
            
            # Track high priority customers
            if segment in ['CRITICAL_HIGH_VALUE', 'CRITICAL_MEDIUM_VALUE', 'AT_RISK_HIGH_VALUE']:
                priority_customers.append({
                    'customer_id': row.get('customer_id'),
                    'segment': segment,
                    'value_at_risk': clv['value_at_risk'],
                    'churn_probability': row.get('churn_probability')
                })
        
        # Sort priority customers by value at risk
        priority_customers.sort(key=lambda x: x['value_at_risk'], reverse=True)
        
        return {
            'total_customers': total_customers,
            'total_value_at_risk': round(total_value_at_risk, 2),
            'avg_value_at_risk': round(total_value_at_risk / total_customers, 2),
            'segments_breakdown': segments_breakdown,
            'top_priority_customers': priority_customers[:20],  # Top 20
            'immediate_action_required': segments_breakdown.get('CRITICAL_HIGH_VALUE', 0) + 
                                        segments_breakdown.get('CRITICAL_MEDIUM_VALUE', 0),
            'portfolio_recommendations': self._get_portfolio_recommendations(
                segments_breakdown, total_value_at_risk
            )
        }
    
    def _get_portfolio_recommendations(self, segments: Dict, total_risk: float) -> List[str]:
        """Portfolio-level strategic recommendations"""
        recommendations = []
        
        critical_count = segments.get('CRITICAL_HIGH_VALUE', 0) + segments.get('CRITICAL_MEDIUM_VALUE', 0)
        
        if critical_count > 0:
            recommendations.append(
                f'🚨 URGENT: {critical_count} customers require immediate intervention (24-48 hours)'
            )
        
        if total_risk > 50000:
            recommendations.append(
                f'💰 HIGH RISK: ${total_risk:,.0f} in customer value at risk - allocate retention budget'
            )
        
        at_risk_high = segments.get('AT_RISK_HIGH_VALUE', 0)
        if at_risk_high > 10:
            recommendations.append(
                f'📞 PROACTIVE: {at_risk_high} high-value customers need proactive engagement'
            )
        
        recommendations.append(
            '📊 STRATEGY: Review retention tactics effectiveness and adjust campaigns'
        )
        
        recommendations.append(
            '🎯 SEGMENTATION: Personalize outreach based on customer segments'
        )
        
        return recommendations


# Convenience function for single customer
def get_recommendations(
    customer_id: str,
    churn_probability: float,
    risk_level: str,
    tenure: int,
    monthly_charges: float,
    contract: str = None,
    payment_method: str = None,
    internet_service: str = None
) -> Dict:
    """
    Quick function to get recommendations for a single customer
    """
    engine = RecommendationsEngine()
    return engine.generate_recommendations(
        customer_id, churn_probability, risk_level,
        tenure, monthly_charges, contract, payment_method, internet_service
    )
