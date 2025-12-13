from detector.gmail_client import GmailClient

def test_scan():
    print("="*60)
    print("Gmail Scanning Test")
    print("="*60)
    
    # Initialize client
    client = GmailClient()
    
    # Authenticate
    print("\n1. Authenticating with Gmail...")
    if not client.authenticate():
        print(" Authentication failed!")
        return
    
    print("Authentication successful!")
    
    # Test with different limits
    test_cases = [50]
    
    for max_msgs in test_cases:
        print(f"\n2. Testing scan with max_results={max_msgs}")
        print("-" * 60)
        
        emails = client.scan_inbox(max_results=max_msgs)
        
        print(f"\n Results:")
        print(f"Requested: {max_msgs}")
        print(f"Received:  {len(emails)}")
        
        if len(emails) == 0:
            print("  No emails returned!")
        elif len(emails) == 1:
            print("Only 1 email returned - this might be the bug!")
        else:
            print(f" Got {len(emails)} emails")
        
        # Show first few emails
        print(f"\n   First {min(50, len(emails))} emails:")
        for i, email in enumerate(emails[:50], 1):
            print(f"   {i}. {email['subject'][:50]}")
            print(f"      From: {email['sender']}")
            print(f"      Links: {len(email['links'])}")
        
        # Stop after first successful test for quick verification
        if len(emails) > 1:
            break
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == '__main__':
    test_scan()