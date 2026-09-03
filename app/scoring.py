"""
Lead Scoring Module
Calculates lead quality scores based on captured information
"""

def calculate_lead_score(lead_data: dict) -> dict:
    """
    Calculate lead score based on available information
    
    Args:
        lead_data: Dictionary containing lead information
        
    Returns:
        dict: {
            "score": int (0-100),
            "priority": str (HOT/WARM/COLD/LOW),
            "reasons": list of strings,
            "icon": str (🔥/🟡/🔵/⚪)
        }
    """
    score = 0
    reasons = []
    missing = []
    
    # 1. Budget provided (20 points)
    if lead_data.get('budget'):
        score += 20
        reasons.append("✓ Has budget")
    else:
        missing.append("budget")
    
    # 2. Phone number provided (20 points)
    if lead_data.get('phone'):
        score += 20
        reasons.append("✓ Provided phone number")
    else:
        missing.append("phone")
    
    # 3. Specific location (15 points)
    if lead_data.get('location'):
        score += 15
        reasons.append("✓ Specific location")
    else:
        missing.append("location")
    
    # 4. Property type specified (15 points)
    if lead_data.get('property_type'):
        score += 15
        reasons.append("✓ Property type specified")
    else:
        missing.append("property type")
    
    # 5. Timeline (20 points) - buying soon is valuable
    timeline = lead_data.get('timeline', '').lower()
    if timeline:
        if any(word in timeline for word in ['month', 'immediate', 'soon', 'week', 'now']):
            score += 20
            reasons.append("✓ Buying within 1 month")
        elif any(word in timeline for word in ['2 month', '3 month', 'quarter']):
            score += 10
            reasons.append("✓ Buying within 3 months")
        else:
            score += 5
            reasons.append("✓ Timeline provided")
    else:
        missing.append("timeline")
    
    # 6. Name provided (10 points)
    if lead_data.get('name'):
        score += 10
        reasons.append("✓ Name provided")
    else:
        missing.append("name")
    
    # 7. Email provided (bonus 5 points)
    if lead_data.get('email'):
        score += 5
        reasons.append("✓ Email provided")
    
    # 8. Size/specs provided (bonus 5 points)
    if lead_data.get('size') or lead_data.get('bedrooms'):
        score += 5
        reasons.append("✓ Specific requirements")
    
    # 9. Purpose provided (bonus 5 points)
    if lead_data.get('purpose'):
        score += 5
        reasons.append("✓ Purpose specified")
    
    # Cap score at 100
    score = min(score, 100)
    
    # Determine priority with icons
    if score >= 80:
        priority = "HOT"
        icon = "🔥"
        description = "Ready to buy - contact immediately"
    elif score >= 60:
        priority = "WARM"
        icon = "🟡"
        description = "Interested - follow up soon"
    elif score >= 40:
        priority = "COLD"
        icon = "🔵"
        description = "Exploring options - nurture"
    else:
        priority = "LOW"
        icon = "⚪"
        description = "Needs more qualification"
    
    return {
        "score": score,
        "priority": priority,
        "icon": icon,
        "description": description,
        "reasons": reasons,
        "missing": missing,
        "needs_followup": score >= 60  # WARM or HOT needs followup
    }


def get_lead_summary(lead_data: dict, score_result: dict) -> dict:
    """
    Generate a human-readable summary of the lead
    """
    summary = {
        "title": f"{score_result['icon']} {score_result['priority']} LEAD",
        "score": f"{score_result['score']}/100",
        "status": score_result['description'],
        "details": []
    }
    
    # Add key details
    if lead_data.get('name'):
        summary['details'].append(f"Name: {lead_data['name']}")
    if lead_data.get('phone'):
        summary['details'].append(f"Phone: {lead_data['phone']}")
    if lead_data.get('location'):
        summary['details'].append(f"Location: {lead_data['location']}")
    if lead_data.get('property_type'):
        summary['details'].append(f"Property: {lead_data['property_type']}")
    if lead_data.get('size'):
        summary['details'].append(f"Size: {lead_data['size']}")
    if lead_data.get('budget'):
        summary['details'].append(f"Budget: {lead_data['budget']}")
    if lead_data.get('timeline'):
        summary['details'].append(f"Timeline: {lead_data['timeline']}")
    if lead_data.get('purpose'):
        summary['details'].append(f"Purpose: {lead_data['purpose']}")
    
    summary['reasons'] = score_result['reasons']
    summary['missing'] = score_result['missing']
    
    return summary


# Example usage and test
if __name__ == "__main__":
    # Test with sample data
    test_lead = {
        "name": "Ahmed Khan",
        "phone": "+92 300 1234567",
        "email": "ahmed@email.com",
        "location": "DHA Lahore",
        "property_type": "House",
        "size": "5 Marla",
        "budget": "2-2.5 Crore",
        "timeline": "Within 1 month",
        "purpose": "Family"
    }
    
    result = calculate_lead_score(test_lead)
    summary = get_lead_summary(test_lead, result)
    
    print("=" * 60)
    print("📊 LEAD SCORING TEST")
    print("=" * 60)
    print(f"{summary['title']}")
    print(f"Score: {summary['score']}")
    print(f"Status: {summary['status']}")
    print("\nDetails:")
    for detail in summary['details']:
        print(f"  • {detail}")
    print("\nReasons:")
    for reason in summary['reasons']:
        print(f"  {reason}")
    if summary['missing']:
        print("\nMissing:")
        for item in summary['missing']:
            print(f"  • {item}")
    print("=" * 60)