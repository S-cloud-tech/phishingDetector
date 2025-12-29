from detector.ai_detector import AITextDetector

# Initialize with transformer model
detect = AITextDetector(use_transformer=True)

# Detect AI text
text = """Dear PayPal User,

        It is important to note that we have identified potential security vulnerabilities affecting your account. Furthermore, our fraud detection algorithms have flagged several transactions that require your immediate attention. Moreover, it is worth noting that these irregular activities pose a significant risk to your financial security.

        However, it is crucial to understand that we are taking proactive measures to protect your interests. On the other hand, we require your cooperation to complete the verification process. Additionally, failure to respond to this notification may result in limited account access.

        Hence, we strongly encourage you to click the following secure link to verify your account information:
        https://paypal-secure-verification.top/account/confirm?id=user12345

        In conclusion, we value your trust and remain committed to providing a secure payment platform. Furthermore, our dedicated support team is available 24/7 to assist you with any concerns. Moreover, we continuously update our security protocols to ensure the safety of your transactions.

        Sincerely,
        PayPal Security Team

        Please note that this is an automated security message. Thus, direct replies to this email will not be received by our support staff."""
result = detect.detect(text)

print(f"AI Generated: {result['is_ai_generated']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Level: {detect.get_confidence_level(result['confidence'])}")