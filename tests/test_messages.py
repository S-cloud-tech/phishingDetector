from detector.gmail_client import GmailClient

def test_pagination():
    client = GmailClient()
    
    # Authenticate
    if not client.authenticate():
        print("Auth failed")
        return
    
    # Test different limits
    for limit in [1, 5, 10, 25, 50, 500]:
        msgs = client.get_messages(max_results=limit)
        print(f"Limit: {limit:3d} | Got: {len(msgs):3d} | {'✓' if len(msgs) == limit or len(msgs) == limit else '✗'}")

if __name__ == '__main__':
    test_pagination()