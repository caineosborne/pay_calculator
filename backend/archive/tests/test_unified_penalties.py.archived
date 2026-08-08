# """
# Test module for unified penalty structure.

# This module provides a test harness for the unified penalty structure.
# """

# from models.request_models import PayRequest
# from services.pay_calculator_test import PayCalculator
# from services.rule_engine import PayRules

# # Use the main rules directly since they now use the unified structure
# # No need for test versions anymore
# from services.rules.aged_care_rules import AgedCareRules
# from services.rules.hospitality_rules import HospitalityRules
# from services.rules.child_care_rules import ChildCareRules

# # Override the rule factory in PayRules to use the main rules
# def get_rules_for_award(award: str):
#     """
#     Factory function to get the appropriate rule set based on award type.
#     """
#     award_map = {
#         'aged_care': AgedCareRules,
#         'hospitality': HospitalityRules,
#         'child_care': ChildCareRules,
#     }
    
#     return award_map.get(award.lower(), HospitalityRules)

# PayRules._get_rules_for_award = get_rules_for_award

# def test_unified_penalties():
#     """
#     Test the unified penalty structure by processing a request with each award type.
#     """
#     # Test data for a single shift
#     test_data = {
#         'hourly_rate': 25.0,
#         'worker_type': 'shift',
#         'employment_type': 'full_time',
#         'contracted_hours': 38,
#         'shifts': [
#             {
#                 'day': 'Monday',
#                 'start': 14,  # 2pm
#                 'end': 22,    # 10pm
#                 'break_duration': 0.5
#             },
#             {
#                 'day': 'Tuesday',
#                 'start': 23,  # 11pm
#                 'end': 7,     # 7am next day
#                 'break_duration': 0.5
#             },
#             {
#                 'day': 'Saturday',
#                 'start': 9,   # 9am
#                 'end': 17,    # 5pm
#                 'break_duration': 0.5
#             }
#         ]
#     }
    
#     # Test each award type
#     for award in ['aged_care', 'hospitality', 'child_care']:
#         print(f"\nTesting {award} award with unified penalties (legacy code commented out)")
#         test_data['award'] = award
        
#         try:
#             # Create PayRequest (simplified for testing)
#             request = PayRequest(**test_data)
            
#             # Process the request
#             calculator = PayCalculator(request)
            
#             # Calculate hours without generating the full response
#             calculator.process_all_shifts()
            
#             # Print the breakdown instead of full response
#             print(f"Processed shifts for {award} award:")
#             for day, hours in calculator.breakdown.items():
#                 penalties = []
#                 if hours.get('penalty', 0) > 0:
#                     penalties.append(f"Weekend ({int(hours['penalty_rate'] * 100)}%)")
#                 if hours.get('shift_penalty', 0) > 0:
#                     penalties.append(f"Shift ({int(hours['shift_penalty_rate'] * 100)}%)")
#                 for hp in hours.get('hourly_penalties', []):
#                     penalties.append(f"{hp['description']} ({int(hp['rate'] * 100)}%)")
                
#                 print(f"  {day}: {hours['total']}h total, {hours['ordinary']}h ordinary, {hours['overtime']}h overtime")
#                 if penalties:
#                     print(f"    Penalties: {', '.join(penalties)}")
#                 print(f"    Applied Rules: {', '.join(hours['applied_rules'])}")
                
#         except Exception as e:
#             print(f"Error processing {award} award: {str(e)}")
    
#     print("\nTest completed. If you see penalty information for all awards, the unified structure is working.")

# if __name__ == "__main__":
#     test_unified_penalties()
