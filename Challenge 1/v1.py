import re

def validate_email(email):
    """
    Validates an email address using regex.
    
    Args:
        email (str): The email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Regex pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True
    return False


# Test cases
def test_email_validator():
    """Test the email validator with various cases"""
    
    # Valid emails
    valid_emails = [
        "user@example.com",
        "john.doe@company.co.uk",
        "alice_smith@test-domain.org",
        "contact+newsletter@website.io",
        "admin123@server.net",
        "info@sub.domain.com"
    ]
    
    # Invalid emails
    invalid_emails = [
        "invalid.email",           # Missing @
        "@example.com",            # Missing local part
        "user@",                   # Missing domain
        "user@domain",             # Missing TLD
        "user @example.com",       # Space in local part
        "user@exam ple.com",       # Space in domain
        "user@@example.com",       # Double @
        "user@.com",               # Domain starts with dot
        "user@domain..com",        # Consecutive dots
        "",                        # Empty string
        "user@domain.c"            # TLD too short
    ]
    
    print("Testing VALID emails:")
    print("-" * 50)
    for email in valid_emails:
        result = validate_email(email)
        print(f"{email:<35} -> {result}")
    
    print("\n\nTesting INVALID emails:")
    print("-" * 50)
    for email in invalid_emails:
        result = validate_email(email)
        print(f"{email:<35} -> {result}")


if __name__ == "__main__":
    test_email_validator()