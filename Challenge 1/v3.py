import re
from typing import Tuple, List


def validate_email(email: str) -> bool:
    """
    Validate email address using regex pattern matching based on simplified RFC 5322 standards.
    
    This function checks if an email address conforms to common email format requirements,
    including support for plus addressing, subdomains, and standard special characters.
    
    Args:
        email (str): The email address string to validate
        
    Returns:
        bool: True if the email is valid according to the pattern, False otherwise
        
    Supported Features:
        - Plus addressing: user+tag@example.com
        - Subdomains: user@mail.subdomain.example.com
        - Multiple dots in local part: john.doe.smith@example.com
        - Numbers: user123@example.com
        - Hyphens in domain: user@my-company.com
        - Underscores and percent signs: user_name%test@example.com
        
    Examples:
        >>> validate_email("john.doe@example.com")
        True
        >>> validate_email("user+newsletter@mail.company.co.uk")
        True
        >>> validate_email("invalid@")
        False
        >>> validate_email("no-at-sign.com")
        False
        >>> validate_email("user@@domain.com")
        False
        
    Note:
        This is a simplified implementation. Full RFC 5322 compliance is extremely complex
        and may allow edge cases that are technically valid but rarely used in practice.
    """
    
    # Regex Pattern Breakdown:
    # -------------------------
    # ^                          - Anchor: start of string
    # [a-zA-Z0-9._%+-]+          - Local part (before @):
    #                              - Letters (a-z, A-Z)
    #                              - Digits (0-9)
    #                              - Special chars: dot(.), underscore(_), percent(%), plus(+), hyphen(-)
    #                              - Quantifier: + (one or more characters required)
    # @                          - Literal @ symbol (required separator)
    # [a-zA-Z0-9.-]+             - Domain name:
    #                              - Letters, digits, dots (for subdomains), hyphens
    #                              - Quantifier: + (one or more characters required)
    # \.                         - Literal dot before TLD (escaped with backslash)
    # [a-zA-Z]{2,}               - Top-level domain (TLD):
    #                              - Only letters allowed
    #                              - Quantifier: {2,} (minimum 2 characters, e.g., .com, .uk, .info)
    # $                          - Anchor: end of string
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Additional validation to reject edge cases not caught by regex
    if email.startswith('.') or email.endswith('.'):
        return False
    
    if '..' in email:
        return False
    
    if email.count('@') != 1:
        return False
    
    return bool(re.match(pattern, email))


# ============================================================================
# COMPREHENSIVE TEST SUITE
# ============================================================================

def run_comprehensive_tests() -> None:
    """
    Execute comprehensive test suite for email validation function.
    
    Tests are organized into valid and invalid categories with descriptive names
    to clearly communicate what each test case validates.
    """
    
    # Test cases: (email, expected_result, test_description)
    test_cases: List[Tuple[str, bool, str]] = [
        # ---- VALID EMAIL ADDRESSES (8 test cases) ----
        ("john.doe@example.com", True, 
         "valid_standard_email_with_dot_in_local_part"),
        
        ("user123@domain.org", True, 
         "valid_email_with_numbers_in_local_part"),
        
        ("john+newsletter@example.com", True, 
         "valid_plus_addressing_for_email_filtering"),
        
        ("admin+alerts@company.io", True, 
         "valid_plus_addressing_with_short_tld"),
        
        ("contact@mail.example.com", True, 
         "valid_email_with_single_subdomain"),
        
        ("support@mail.support.company.co.uk", True, 
         "valid_email_with_multiple_subdomains"),
        
        ("john.doe.smith@example.com", True, 
         "valid_email_with_multiple_dots_in_local_part"),
        
        ("user@my-company.com", True, 
         "valid_email_with_hyphen_in_domain"),
        
        # ---- INVALID EMAIL ADDRESSES (4+ test cases) ----
        ("invalid.email.com", False, 
         "invalid_missing_at_symbol"),
        
        ("user@@example.com", False, 
         "invalid_multiple_at_symbols"),
        
        ("user name@example.com", False, 
         "invalid_space_in_local_part"),
        
        ("user@domain", False, 
         "invalid_missing_tld_extension"),
        
        ("@example.com", False, 
         "invalid_missing_local_part"),
        
        ("user@", False, 
         "invalid_missing_domain_and_tld"),
        
        (".user@example.com", False, 
         "invalid_local_part_starts_with_dot"),
        
        ("user.@example.com", False, 
         "invalid_local_part_ends_with_dot"),
        
        ("user..name@example.com", False, 
         "invalid_consecutive_dots_in_local_part"),
        
        ("user@domain.c", False, 
         "invalid_tld_too_short_one_character"),
        
        ("", False, 
         "invalid_empty_string"),
        
        ("user@.example.com", False, 
         "invalid_domain_starts_with_dot"),
    ]
    
    # Execute tests and track results
    print("=" * 100)
    print("EMAIL VALIDATION TEST SUITE - PRODUCTION READY")
    print("=" * 100)
    print(f"{'Test Case':<50} {'Email':<30} {'Expected':<10} {'Actual':<10} {'Status':<10}")
    print("-" * 100)
    
    passed_tests = 0
    failed_tests = 0
    
    for email, expected, test_name in test_cases:
        actual = validate_email(email)
        status = "✓ PASS" if actual == expected else "✗ FAIL"
        
        if actual == expected:
            passed_tests += 1
        else:
            failed_tests += 1
        
        # Truncate long values for clean display
        display_email = (email[:27] + "...") if len(email) > 30 else email
        display_test_name = (test_name[:47] + "...") if len(test_name) > 50 else test_name
        
        print(f"{display_test_name:<50} {display_email:<30} {str(expected):<10} {str(actual):<10} {status:<10}")
    
    # Summary
    print("-" * 100)
    total_tests = len(test_cases)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTEST SUMMARY:")
    print(f"  Total Tests:    {total_tests}")
    print(f"  Passed:         {passed_tests}")
    print(f"  Failed:         {failed_tests}")
    print(f"  Success Rate:   {success_rate:.1f}%")
    
    # Display failed test details
    if failed_tests > 0:
        print(f"\n{'!' * 100}")
        print("FAILED TEST DETAILS:")
        print("!" * 100)
        for email, expected, test_name in test_cases:
            if validate_email(email) != expected:
                print(f"\n  Test: {test_name}")
                print(f"  Email: '{email}'")
                print(f"  Expected: {expected}, Got: {validate_email(email)}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    run_comprehensive_tests()