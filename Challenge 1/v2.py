import re

def validate_email(email):
    """
    Validates an email address using regex pattern matching.
    
    Args:
        email (str): The email address to validate
        
    Returns:
        bool: True if the email is valid, False otherwise
    """
    # Regex pattern breakdown:
    # ^                     - Start of string
    # [a-zA-Z0-9._%+-]+     - Local part: alphanumeric chars, dots, underscores, 
    #                         percent, plus, and hyphens (1 or more)
    # @                     - Literal @ symbol (required)
    # [a-zA-Z0-9.-]+        - Domain: alphanumeric chars, dots, and hyphens (supports subdomains)
    # \.                    - Literal dot before TLD
    # [a-zA-Z]{2,}          - Top-level domain: at least 2 alphabetic characters
    # $                     - End of string
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))


# ===========================
# TEST CASES
# ===========================

def run_tests():
    """
    Comprehensive test suite for email validation.
    Tests cover valid and invalid email formats.
    """
    
    test_cases = [
        # Valid standard emails
        ("john.doe@example.com", True, "Valid standard email"),
        ("user123@domain.org", True, "Valid with numbers in local part"),
        
        # Valid plus addressing (for email filtering/categorization)
        ("user+newsletter@example.com", True, "Valid plus addressing"),
        ("admin+alerts@company.io", True, "Valid plus addressing with subdomain"),
        
        # Valid subdomains
        ("contact@mail.example.com", True, "Valid single subdomain"),
        ("support@mail.support.company.co.uk", True, "Valid multiple subdomains"),
        
        # Invalid formats - missing components
        ("invalid.email", False, "Invalid: missing @ symbol"),
        ("@example.com", False, "Invalid: missing local part"),
        ("user@", False, "Invalid: missing domain"),
        ("user@domain", False, "Invalid: missing TLD"),
        
        # Invalid formats - invalid characters/structure
        ("user name@example.com", False, "Invalid: space in local part"),
        ("user@exam ple.com", False, "Invalid: space in domain"),
        ("user@@example.com", False, "Invalid: double @ symbol"),
        ("user@.example.com", False, "Invalid: domain starts with dot"),
        ("", False, "Invalid: empty string"),
        ("user@domain.c", False, "Invalid: TLD too short (1 char)"),
    ]
    
    print("EMAIL VALIDATION TEST RESULTS")
    print("=" * 80)
    print(f"{'Email':<40} {'Expected':<10} {'Result':<10} {'Status':<10}")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for email, expected, description in test_cases:
        result = validate_email(email)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        # Truncate long emails for display
        display_email = email if len(email) <= 37 else email[:34] + "..."
        print(f"{display_email:<40} {str(expected):<10} {str(result):<10} {status:<10}")
    
    print("-" * 80)
    print(f"\nTotal Tests: {len(test_cases)} | Passed: {passed} | Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    
    # Print descriptions for failed tests
    if failed > 0:
        print("\nFailed Test Details:")
        for email, expected, description in test_cases:
            if validate_email(email) != expected:
                print(f"  - {description}: '{email}'")


if __name__ == "__main__":
    run_tests()