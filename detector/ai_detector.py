import re
import numpy as np
from collections import Counter
import torch
import warnings
warnings.filterwarnings('ignore')
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class AITextDetector:
   
    def __init__(self, use_transformer=False):
        
        self.use_transformer = use_transformer
        self.model = None
        self.tokenizer = None
        
        # AI-generated text patterns (updated for GPT-4, Claude, etc.)
        self.ai_patterns = {
            'common_phrases': [
                # GPT-style phrases
                'as an ai', 'language model', 'i don\'t have personal',
                'i cannot', 'i\'m sorry, but', 'i apologize',
                
                # Common AI transitions
                'it\'s worth noting', 'it is important to note',
                'it\'s important to understand', 'keep in mind',
                
                # AI filler words
                'furthermore', 'moreover', 'additionally', 'consequently',
                'nevertheless', 'nonetheless', 'hence', 'thus',
                
                # Hedging language (AI is uncertain)
                'it seems that', 'it appears that', 'one might say',
                'it could be argued', 'some may argue',
                
                # Generic conclusions
                'in conclusion', 'to summarize', 'in summary',
                'ultimately', 'overall', 'all in all'
            ],
            
            'suspicious_patterns': [
                # Overly formal in casual context
                'utilize', 'leverage', 'facilitate', 'endeavor',
                'subsequent', 'aforementioned', 'heretofore',
                
                # AI action words
                'delve into', 'delve deeper', 'explore the nuances',
                'navigate the landscape', 'unpack',
                
                # Repetitive structures
                'not only.*but also', 'on the one hand.*on the other hand',
                'while.*it is also important'
            ],

            'repetitive_phrases': [
                'it is important to note',
                'it\'s worth noting',
                'in conclusion',
                'furthermore',
                'moreover',
                'however, it is important',
                'on the other hand'
            ],

            'generic_phrases': [
                'as an AI',
                'I don\'t have personal',
                'I cannot provide',
                'delve into',
                'leverage',
                'robust solution'
            ]
        }
        
        if use_transformer:
            self._load_transformer_model()
    
    def _load_transformer_model(self):
        try:

            model_name = "roberta-base-openai-detector"

            print(f"Loading AI detection model: {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            print("Model loaded successfully")
            
        except Exception as e:
            print(f"Could not load transformer model: {e}")
            print("Falling back to heuristic detection only")
            self.use_transformer = False
    
    
    def _transformer_detection(self, text):
    
        try:
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            )
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=-1)
                
                # Assuming class 1 is "AI-generated"
                # (This depends on the model, may need to check model card)
                ai_probability = predictions[0][1].item()
            
            return ai_probability
            
        except Exception as e:
            print(f"Transformer detection error: {e}")
            return None
    
    def _calculate_perplexity(self, text):
        """
        Calculate perplexity approximation.
        AI text has lower perplexity (more predictable).
        Returns 0-1 (higher = more likely AI).
        """
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        # Calculate word frequency distribution
        word_freq = Counter(words)
        total_words = len(words)
        
        # Calculate entropy as proxy for perplexity
        entropy = 0
        for count in word_freq.values():
            prob = count / total_words
            if prob > 0:
                entropy -= prob * np.log2(prob)
        
        # Normalize entropy to 0-1 scale
        # Typical ranges: AI (3-5), Human (5-8)
        max_expected_entropy = 8
        normalized_entropy = min(entropy / max_expected_entropy, 1.0)
        
        # Invert: low entropy = high AI probability
        ai_score = 1.0 - normalized_entropy
        
        return ai_score
    
    def _calculate_burstiness(self, text):
        """
        Calculate burstiness (sentence length variation).
        AI text has low burstiness (uniform sentences).
        Returns 0-1 (higher = more likely AI).
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return 0.0
        
        # Calculate sentence lengths
        lengths = [len(s.split()) for s in sentences]
        
        if not lengths or len(lengths) < 2:
            return 0.0
        
        mean_length = np.mean(lengths)
        std_length = np.std(lengths)
        
        # Coefficient of variation
        if mean_length > 0:
            cv = std_length / mean_length
        else:
            return 0.0
        
        # AI text typically has CV < 0.3, Human > 0.5
        if cv < 0.2:
            return 0.9
        elif cv < 0.3:
            return 0.7
        elif cv < 0.4:
            return 0.5
        elif cv < 0.5:
            return 0.3
        else:
            return 0.1
    
    def _check_ai_patterns(self, text):
        """
        Check for common AI-generated phrases and patterns.
        Returns 0-1 (higher = more likely AI).
        """
        text_lower = text.lower()
        pattern_count = 0
        max_score = 0
        
        # Check common phrases
        for phrase in self.ai_patterns['common_phrases']:
            if phrase in text_lower:
                pattern_count += 1
        
        # Checking suspicious patterns (regex)
        for pattern in self.ai_patterns['suspicious_patterns']:
            if re.search(pattern, text_lower):
                pattern_count += 2
        
        # Checking for excessive use of formal connectors
        formal_connectors = ['furthermore', 'moreover', 'however', 'therefore', 
                            'thus', 'hence', 'consequently', 'additionally']
        connector_count = sum(1 for c in formal_connectors if c in text_lower)
        
        # Checking for hedging language frequency
        hedging = ['perhaps', 'possibly', 'might', 'could', 'may', 'seems']
        hedge_count = sum(text_lower.count(h) for h in hedging)
        
        # Combine scores
        word_count = len(text.split())
        if word_count > 0:
            connector_ratio = (connector_count / word_count) * 100
            hedge_ratio = (hedge_count / word_count) * 100
            
            # AI often has 2-5% connectors and 1-3% hedging
            score = (pattern_count * 0.1) + (connector_ratio * 0.3) + (hedge_ratio * 0.2)
            max_score = min(score, 1.0)
        
        return max_score
    
    def _check_sentence_uniformity(self, text):
        """
        Check sentence starting words and structure uniformity.
        AI text often has less variety.
        Returns 0-1 (higher = more likely AI).
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return 0.0
        
        # Check starting words diversity
        start_words = []
        for s in sentences:
            words = s.split()
            if words:
                start_words.append(words[0].lower())
        
        if not start_words:
            return 0.0
        
        unique_starts = len(set(start_words))
        variety_ratio = unique_starts / len(start_words)
        
        # AI text: variety_ratio < 0.5, Human: > 0.7
        if variety_ratio < 0.4:
            return 0.8
        elif variety_ratio < 0.5:
            return 0.6
        elif variety_ratio < 0.6:
            return 0.4
        else:
            return 0.2
    
    def _analyze_vocabulary_diversity(self, text):
        """
        Analyze vocabulary richness (Type-Token Ratio).
        Returns 0-1 (higher = more diverse = less likely AI).
        """
        words = re.findall(r'\b\w+\b', text.lower())
        
        if len(words) < 50:
            return 0.5  # Not enough data
        
        unique_words = len(set(words))
        total_words = len(words)
        
        # Type-Token Ratio
        ttr = unique_words / total_words
        
        # AI text typically has TTR 0.4-0.6, Human 0.6-0.8
        # Return inverted: lower diversity = higher AI score
        if ttr < 0.4:
            return 0.2  # Very low diversity (likely AI)
        elif ttr < 0.5:
            return 0.4
        elif ttr < 0.6:
            return 0.6
        else:
            return 0.8  # High diversity (likely human)
    
    def _analyze_sentence_structure(self, text):
        """
        Analyze sentence structure complexity.
        Returns 0-1 (higher = more likely AI).
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return 0.0
        
        # Count commas per sentence (complexity indicator)
        comma_counts = [s.count(',') for s in sentences]
        avg_commas = np.mean(comma_counts)
        
        # Count subordinate clauses (words like 'which', 'that', 'who')
        clause_markers = ['which', 'that', 'who', 'where', 'when']
        clause_count = sum(
            sum(1 for marker in clause_markers if marker in s.lower())
            for s in sentences
        )
        
        avg_clauses = clause_count / len(sentences)
        
        # AI often has very consistent complexity
        # Human has more variation
        comma_std = np.std(comma_counts)
        
        if comma_std < 0.5 and 1.0 < avg_commas < 2.5:
            return 0.7  # Very consistent complexity (AI)
        elif avg_clauses > 1.5:
            return 0.6  # Many subordinate clauses (AI)
        else:
            return 0.3
    
    def get_confidence_level(self, confidence):
        """Convert confidence score to readable level."""
        if confidence < 0.3:
            return 'LOW - Likely Human-Written'
        elif confidence < 0.5:
            return 'MEDIUM-LOW - Possibly Human'
        elif confidence < 0.65:
            return 'MEDIUM - Uncertain'
        elif confidence < 0.8:
            return 'MEDIUM-HIGH - Likely AI'
        elif confidence < 0.9:
            return 'HIGH - Very Likely AI'
        else:
            return 'VERY HIGH - Almost Certainly AI'
    
    def batch_detect(self, texts):
        results = []
        for text in texts:
            result = self.detect(text)
            results.append(result)
        return results
    
    def detect(self, text):
        """
        Main detection method using multiple techniques.
        
        Returns:
            dict: Analysis results with confidence score and indicators
        """
        if not text or len(text.strip()) < 50:
            return {
                'text_sample': text,
                'is_ai_generated': False,
                'confidence': 0.0,
                'indicators': ['Text too short for reliable detection'],
                'scores': {}
            }
        
        result = {
            'text_sample': text[:200] + '...' if len(text) > 200 else text,
            'is_ai_generated': False,
            'confidence': 0.0,
            'indicators': [],
            'scores': {},
            'method': 'hybrid'
        }

        # Detection Methods Used for detecting AI
        
        # Method 1: Transformer-based detection (most accurate)
        if self.use_transformer and self.model:
            transformer_score = self._transformer_detection(text)
            result['scores']['transformer'] = transformer_score
            result['scores']['transformer_weight'] = 0.6
        else:
            transformer_score = None
        
        # Method 2: Statistical analysis
        perplexity_score = self._calculate_perplexity(text)
        burstiness_score = self._calculate_burstiness(text)
        result['scores']['perplexity'] = perplexity_score
        result['scores']['burstiness'] = burstiness_score
        
        # Method 3: Pattern matching
        pattern_score = self._check_ai_patterns(text)
        result['scores']['pattern_match'] = pattern_score
        
        # Method 4: Linguistic analysis
        uniformity_score = self._check_sentence_uniformity(text)
        vocabulary_score = self._analyze_vocabulary_diversity(text)
        result['scores']['uniformity'] = uniformity_score
        result['scores']['vocabulary_diversity'] = vocabulary_score
        
        # Method 5: Sentence-level analysis
        sentence_score = self._analyze_sentence_structure(text)
        result['scores']['sentence_structure'] = sentence_score
        
        # Combine all scores with weights
        if transformer_score is not None:
            final_score = (
                transformer_score * 0.5 +
                perplexity_score * 0.15 +
                burstiness_score * 0.15 +
                pattern_score * 0.1 +
                uniformity_score * 0.05 +
                vocabulary_score * 0.05
            )
            result['method'] = 'transformer-hybrid'
        else:
            # Heuristic-only approach
            final_score = (
                perplexity_score * 0.25 +
                burstiness_score * 0.25 +
                pattern_score * 0.20 +
                uniformity_score * 0.15 +
                vocabulary_score * 0.10 +
                sentence_score * 0.05
            )
            result['method'] = 'heuristic-only'
        
        result['confidence'] = min(final_score, 1.0)
        
        # Determine if AI-generated based on confidence
        threshold = 0.65 if transformer_score else 0.70
        if result['confidence'] > threshold:
            result['is_ai_generated'] = True
            result['indicators'].append(f'High AI probability ({result["confidence"]:.1%})')
        
        # Add specific indicators
        if perplexity_score > 0.7:
            result['indicators'].append('Low perplexity (predictable text)')
        if burstiness_score > 0.7:
            result['indicators'].append('Low burstiness (uniform sentences)')
        if pattern_score > 0.5:
            result['indicators'].append('Contains common AI phrases')
        if uniformity_score > 0.6:
            result['indicators'].append('Repetitive sentence structure')
        if vocabulary_score < 0.3:
            result['indicators'].append('Limited vocabulary diversity')
        
        return result
    


# Example usage and testing
if __name__ == '__main__':
    # Initialize detector
    print("="*60)
    print("AI Text Detector - Testing")
    print("="*60)
    
    # Try with transformer model first
    print("\n1. Attempting to load transformer model...")
    detector = AITextDetector(use_transformer=True)
    
    # If transformer failed, use heuristic-only
    if not detector.use_transformer:
        print("\n2. Using heuristic-only detection")
        detector = AITextDetector(use_transformer=False)
    
    # Test cases
    test_texts = {
        "AI-generated (GPT-style)": """
        Dear Valued Customer,It is important to note that we have received your recent order. However,
        we have encountered an issue with the payment method you provided. Furthermore,
        to ensure timely delivery of your items, we need you to verify your payment
        information. Moreover, it is worth noting that your order will be automatically cancelled
        if we do not receive confirmation within 24 hours. On the other hand,
        completing this verification will ensure that your order is processed without delay
        Please click the following secure link to update your payment details:
        https://amazon-verify-payment.click/order/verify?id=AMZ123456.In conclusion, we appreciate your prompt attention to this matter.
        Additionally, if you have any questions, feel free to contact our customer
        service team.Best regards,
        Amazon Customer Service. This is an automated message. Please do not reply to this email.
        """,
        
        "Human-written (casual)": """
        Hey! Just wanted to check in and see how you're doing. I tried calling 
        earlier but you didn't pick up - everything ok? Let me know when you're 
        free to chat. Oh, and did you see that crazy game last night?? Insane! 
        Talk soon :)
        """,
        
        "Human-written (professional)": """
        I reviewed the Q3 report and have some concerns about our projections. 
        The numbers look good on paper, but I'm worried we're being too optimistic. 
        Last quarter we missed our targets by 15%, and I don't see what's changed. 
        Can we schedule a call to discuss? I think we need to be more conservative 
        with our estimates.
        """,
        
        # "AI-generated (formal)": """
        # The implementation of blockchain technology represents a paradigm shift 
        # in how we approach data security. It is essential to understand that 
        # this decentralized approach offers numerous advantages. Furthermore, 
        # the transparency and immutability of blockchain transactions provide 
        # unprecedented security. Additionally, smart contracts facilitate 
        # automated processes, thus enhancing efficiency. Overall, blockchain 
        # technology holds tremendous potential for various industries.
        # """
    }
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    
    for label, text in test_texts.items():
        print(f"\n{'='*60}")
        print(f"Test: {label}")
        print(f"{'='*60}")
        
        result = detector.detect(text)
        
        print(f"\nAI Generated: {result['is_ai_generated']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Level: {detector.get_confidence_level(result['confidence'])}")
        print(f"Method: {result['method']}")
        
        print(f"\nDetailed Scores:")
        for score_name, score_value in result['scores'].items():
            if isinstance(score_value, float):
                print(f"  {score_name}: {score_value:.3f}")
        
        if result['indicators']:
            print(f"\nIndicators:")
            for indicator in result['indicators']:
                print(f"  • {indicator}")
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    