"""
Utility Functions
"""
import requests
from datetime import datetime

def format_price(price):
    """Format price as Indian Rupees"""
    if price is None:
        return "₹0"
    return f"₹{price:,.2f}"

def format_date(date_obj):
    """Format datetime"""
    if not date_obj:
        return "N/A"
    
    now = datetime.utcnow()
    diff = now - date_obj
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    else:
        return date_obj.strftime("%d %b %Y")

def calculate_discount(original, final):
    """Calculate discount percentage"""
    if original <= 0 or final >= original:
        return 0
    return round(((original - final) / original) * 100, 1)

def validate_mobile(mobile):
    """Validate Indian mobile number"""
    return len(mobile) == 10 and mobile.isdigit()
