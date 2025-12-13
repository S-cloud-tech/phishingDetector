import requests
import re
from urllib.parse import urlparse
import whois
from datetime import datetime, timedelta
import socket

class LinkAnalyzer:
    """Analyzes URLs for phishing indicators."""
    
    def __init__(self):
        # Common suspicious TLDs
        self.suspicious_tlds = ['.xyz', '.top', '.work', '.click', '.loan', 
                                '.download', '.stream', '.racing', '.bid']
        
        # Legitimate domains (whitelist)
        self.trusted_domains = [
            'google.com', 'gmail.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'amazon.com', 'paypal.com', 'microsoft.com',
            'apple.com', 'github.com'
        ]
        
        self.phishing_keywords = [
            'verify', 'account', 'suspend', 'click', 'update', 'confirm',
            'login', 'secure', 'billing', 'urgently', 'immediately'
        ]
    
    def analyze_url(self, url):
        """
        Comprehensive URL analysis for phishing detection.
        Returns a dictionary with analysis results.
        """
        result = {
            'url': url,
            'is_suspicious': False,
            'risk_score': 0,
            'indicators': [],
            'details': {}
        }
        
        try:
            # Parse URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if it's a trusted domain
            if any(trusted in domain for trusted in self.trusted_domains):
                result['details']['trusted_domain'] = True
                return result
            
            # Analyze components
            self._check_url_length(url, result)
            self._check_suspicious_tld(parsed, result)
            self._check_ip_address(domain, result)
            self._check_suspicious_patterns(url, result)
            self._check_domain_age(domain, result)
            self._check_https(parsed, result)
            self._check_redirects(url, result)
            self._check_suspicious_subdomains(domain, result)
            
            # Calculate final risk score
            if result['risk_score'] >= 50:
                result['is_suspicious'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_url_length(self, url, result):
        """Phishing URLs are often very long."""
        if len(url) > 75:
            result['risk_score'] += 10
            result['indicators'].append('Unusually long URL')
    
    def _check_suspicious_tld(self, parsed, result):
        """Check for suspicious top-level domains."""
        for tld in self.suspicious_tlds:
            if parsed.netloc.endswith(tld):
                result['risk_score'] += 20
                result['indicators'].append(f'Suspicious TLD: {tld}')
                break
    
    def _check_ip_address(self, domain, result):
        """URLs with IP addresses instead of domains are suspicious."""
        ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        if re.match(ip_pattern, domain):
            result['risk_score'] += 25
            result['indicators'].append('IP address instead of domain name')
    
    def _check_suspicious_patterns(self, url, result):
        """Check for common phishing patterns in URL."""
        url_lower = url.lower()
        
        # Multiple subdomains
        if url_lower.count('.') > 4:
            result['risk_score'] += 15
            result['indicators'].append('Multiple subdomains')
        
        # @ symbol (used to obscure real domain)
        if '@' in url:
            result['risk_score'] += 20
            result['indicators'].append('Contains @ symbol')
        
        # Double slashes in path
        if url_lower.count('//') > 1:
            result['risk_score'] += 10
            result['indicators'].append('Multiple // in URL')
        
        # Suspicious keywords
        for keyword in self.phishing_keywords:
            if keyword in url_lower:
                result['risk_score'] += 5
                result['indicators'].append(f'Suspicious keyword: {keyword}')
                break
    
    def _check_domain_age(self, domain, result):
        """Young domains are more likely to be phishing."""
        try:
            w = whois.whois(domain)
            if w.creation_date:
                creation_date = w.creation_date
                if isinstance(creation_date, list):
                    creation_date = creation_date[0]
                
                age = datetime.now() - creation_date
                
                if age < timedelta(days=30):
                    result['risk_score'] += 25
                    result['indicators'].append('Domain less than 30 days old')
                elif age < timedelta(days=180):
                    result['risk_score'] += 10
                    result['indicators'].append('Domain less than 6 months old')
                
                result['details']['domain_age_days'] = age.days
        except Exception:
            result['details']['domain_age'] = 'Unable to retrieve'
    
    def _check_https(self, parsed, result):
        """Check if URL uses HTTPS."""
        if parsed.scheme != 'https':
            result['risk_score'] += 15
            result['indicators'].append('Not using HTTPS')
        result['details']['uses_https'] = parsed.scheme == 'https'
    
    def _check_redirects(self, url, result):
        """Check for excessive redirects."""
        try:
            response = requests.get(url, allow_redirects=True, timeout=5)
            redirect_count = len(response.history)
            
            if redirect_count > 2:
                result['risk_score'] += 15
                result['indicators'].append(f'Multiple redirects: {redirect_count}')
            
            result['details']['redirect_count'] = redirect_count
        except Exception:
            result['details']['redirects'] = 'Unable to check'
    
    def _check_suspicious_subdomains(self, domain, result):
        """Check for brand impersonation in subdomains."""
        brands = ['paypal', 'amazon', 'google', 'microsoft', 'apple', 'facebook']
        
        for brand in brands:
            if brand in domain and not domain.endswith(f'{brand}.com'):
                result['risk_score'] += 30
                result['indicators'].append(f'Possible {brand} impersonation')
                break
    
    def analyze_multiple_links(self, links):
        """Analyze multiple links and return results."""
        results = []
        for link in links:
            analysis = self.analyze_url(link)
            results.append(analysis)
        return results
    
    def get_risk_level(self, risk_score):
        """Convert risk score to risk level."""
        if risk_score < 20:
            return 'LOW'
        elif risk_score < 50:
            return 'MEDIUM'
        elif risk_score < 75:
            return 'HIGH'
        else:
            return 'CRITICAL'


# Example usage
if __name__ == '__main__':
    analyzer = LinkAnalyzer()
    
    # Test URLs
    test_urls = [
        'https://www.google.com',
        'http://paypal-verify-account.xyz/login',
        'https://192.168.1.1/update',
        'https://secure-login.suspicious-site.top/verify'
    ]
    
    for url in test_urls:
        result = analyzer.analyze_url(url)
        print(f"\nURL: {url}")
        print(f"Suspicious: {result['is_suspicious']}")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Risk Level: {analyzer.get_risk_level(result['risk_score'])}")
        print(f"Indicators: {', '.join(result['indicators']) if result['indicators'] else 'None'}")
