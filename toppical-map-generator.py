from dotenv import load_dotenv
import anthropic
import numpy as np
import json
from typing import Dict, List, Any, Tuple, Optional
import asyncio
import os

load_dotenv()

# Initialize Anthropic client with API key from environment
CLIENT = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ClaudeAPI:
    """Wrapper for Claude API with specialized methods for SEO tasks"""
    
    @staticmethod
    async def make_request(prompt: str, max_tokens: int = 1000) -> str:         
        """Generic Claude API request handler"""
        response = await CLIENT.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        print("in make_request, resonse", response.content)
        return response.content[0].text

    @classmethod
    async def research_keywords(cls, seed: List[str], industry: str) -> List[Dict]:
        """Get keyword suggestions from Claude"""
        prompt = f"""You are an advanced SEO keyword researcher. Generate 25-30 relevant keywords for the 
        {industry} industry based on these seed keywords: {', '.join(seed)}. Include search volume estimates 
        (1-100 scale) and competition scores (0.0-1.0). Return as JSON:
        {{"keywords": [{{"keyword": str, "volume": int, "competition": float}}]}}"""

        print("cls",cls)
        print("seed",seed)
        print("industry",industry)
        response = await cls.make_request(prompt)
        print("response:", response)
        return json.loads(response)["keywords"]
    
    @classmethod
    async def analyze_semantics(cls, keywords: List[str]) -> Dict:
        """Perform semantic analysis on keywords"""
        prompt = f"""Analyze these keywords for semantic relationships: {', '.join(keywords[:20])}. 
        Group them into thematic clusters and identify:
        1. Primary theme for each cluster
        2. Secondary related themes
        3. Parent/child topic relationships
        Return as JSON: {{"clusters": [{{"primary": str, "secondary": [str], "parent": Optional[str], "children": [str]}}]}}"""
        
        response = await cls.make_request(prompt)
        return json.loads(response)
    
    @classmethod
    async def classify_intent(cls, keyword: str) -> str:
        """Classify search intent using Claude"""
        prompt = f"""Classify the search intent for "{keyword}" into one of these categories: 
        Informational, Commercial, Transactional, or Navigational. Return ONLY the category name."""
        
        return await cls.make_request(prompt)
    
    @classmethod
    async def identify_gaps(cls, topics: List[str]) -> List[Dict]:
        """Identify content gaps using Claude"""
        prompt = f"""Analyze these topics for content gaps: {', '.join(topics[:15])}. 
        Suggest 3-5 missing topics with opportunity scores (0-1) and recommended formats.
        Return as JSON: {{"gaps": [{{"topic": str, "opportunity": float, "format": str}}]}}"""
        
        response = await cls.make_request(prompt)
        return json.loads(response)["gaps"]
    
    @classmethod
    async def cluster_keywords(cls, keywords: List[str]) -> List[Dict]:
        """Cluster keywords semantically using Claude"""
        prompt = f"""Group these keywords into 5-7 thematic clusters: {', '.join(keywords[:30])}. 
        For each cluster:
        - Give a short theme name
        - List 3-5 core keywords
        - Estimate total search volume (1-100 scale)
        Return as JSON: {{"clusters": [{{"theme": str, "keywords": [str], "volume": int}}]}}"""
        
        response = await cls.make_request(prompt)
        return json.loads(response)["clusters"]

class AdvancedKeywordResearcher:
    def __init__(self):
        self.claude = ClaudeAPI()
    
    async def research_comprehensive_keywords(self, seed_keywords: List[str], 
                                           industry: str, geo_targets: List[str]) -> List[Dict]:
        keywords = await self.claude.research_keywords(seed_keywords, industry)
        # Add geo-specific modifiers
        geo_modified = []
        for geo in geo_targets:
            for kw in keywords:
                geo_modified.append({
                    "keyword": f"{kw['keyword']} {geo}",
                    "volume": max(1, int(kw['volume'] * 0.7)),
                    "competition": min(1.0, kw['competition'] * 1.2)
                })
        return keywords + geo_modified

class SemanticAnalyzer:
    def __init__(self):
        self.claude = ClaudeAPI()
    
    async def vectorize_keywords(self, keywords: List[str]) -> List[List[float]]:
        """Simulate embeddings - In production, replace with real embeddings"""
        return [[hash(kw) % 100 / 100] * 3 for kw in keywords]
    
    async def extract_cluster_theme(self, keywords: List[str]) -> str:
        analysis = await self.claude.analyze_semantics(keywords)
        return analysis["clusters"][0]["primary"]
    
    async def extract_sub_themes(self, keywords: List[str]) -> List[str]:
        analysis = await self.claude.analyze_semantics(keywords)
        return analysis["clusters"][0]["secondary"]
    
    async def identify_parent_topic(self, keywords: List[str]) -> Optional[str]:
        analysis = await self.claude.analyze_semantics(keywords)
        return analysis["clusters"][0].get("parent")
    
    async def identify_child_topics(self, keywords: List[str]) -> List[str]:
        analysis = await self.claude.analyze_semantics(keywords)
        return analysis["clusters"][0].get("children", [])

class ContentGapAnalyzer:
    def __init__(self):
        self.claude = ClaudeAPI()
    
    async def identify_gaps(self, topical_map: Dict) -> List[Dict]:
        all_topics = [c["primary_theme"] for c in topical_map["topic_clusters"]]
        return await self.claude.identify_gaps(all_topics)

class TopicClusterer:
    def __init__(self):
        self.claude = ClaudeAPI()
    
    async def cluster_keywords(self, embeddings: List[List[float]], 
                            algorithm: str, distance_threshold: float) -> List[Dict]:
        """Hybrid approach: Claude for initial clustering, algorithmic refinement"""
        # Get keyword texts from embeddings
        keywords = [f"kw_{i}" for i in range(len(embeddings))]
        
        # Get initial clusters from Claude
        clusters = await self.claude.cluster_keywords(keywords)
        
        # Refine with algorithmic approach
        refined = []
        for i, cluster in enumerate(clusters):
            refined.append({
                "id": i,
                "theme": cluster["theme"],
                "keywords": cluster["keywords"],
                "volume": cluster["volume"]
            })
        return refined

class SearchIntentClassifier:
    def __init__(self):
        self.claude = ClaudeAPI()
    
    async def classify(self, keyword: str) -> str:
        return await self.claude.classify_intent(keyword)
    
    async def recommend_content_type(self, intent: str) -> str:
        mapping = {
            "Informational": "Guide/Blog Post",
            "Commercial": "Comparison/Review",
            "Transactional": "Product Page",
            "Navigational": "Resource Hub"
        }
        return mapping.get(intent, "Blog Post")

class TopicalMapGenerator:
    def __init__(self):
        self.keyword_researcher = AdvancedKeywordResearcher()
        self.semantic_analyzer = SemanticAnalyzer()
        self.content_gap_analyzer = ContentGapAnalyzer()
        self.topic_clusterer = TopicClusterer()
        self.intent_classifier = SearchIntentClassifier()
    
    async def generate_adaptive_topical_map(self, industry_data: Dict, 
                                         algorithm_updates: List[str]) -> Dict:
        # Base keyword research
        base_keywords = await self.keyword_researcher.research_comprehensive_keywords(
            seed_keywords=industry_data['core_keywords'],
            industry=industry_data['industry'],
            geo_targets=industry_data['geo_targets']
        )
        
        # Incorporate trending topics
        trending_keywords = await self.incorporate_trending_topics(
            base_keywords, industry_data['emerging_topics']
        )
        
        # Adapt for algorithm updates
        adapted_keywords = await self.adapt_for_algorithm_updates(
            trending_keywords, algorithm_updates
        )
        
        # Generate semantic clusters
        topic_clusters = await self.create_semantic_clusters(adapted_keywords)
        
        # Create content hierarchy
        content_hierarchy = await self.build_content_hierarchy(topic_clusters)
        
        # Optimize for search intent
        intent_optimized_map = await self.optimize_for_search_intent(content_hierarchy)
        result = {
            'topical_map': intent_optimized_map,
            'priority_topics': await self.identify_priority_topics(intent_optimized_map),
            'content_gaps': await self.content_gap_analyzer.identify_gaps(
                {"topic_clusters": topic_clusters}),
            'update_recommendations': self.generate_update_recommendations(intent_optimized_map)
        }
        print(result)
        return result
    
    async def incorporate_trending_topics(self, base_keywords: List[Dict], 
                                       emerging_topics: List[str]) -> List[Dict]:
        new_keywords = base_keywords.copy()
        for topic in emerging_topics:
            new_keywords.append({
                "keyword": topic,
                "volume": 7500,  # High initial volume for trends
                "competition": 0.4  # Lower competition for emerging topics
            })
        return new_keywords
    
    async def adapt_for_algorithm_updates(self, keywords: List[Dict], 
                                       updates: List[str]) -> List[Dict]:
        if "EEAT Update" in updates:
            return [kw for kw in keywords if kw["competition"] < 0.7]
        return keywords
    
    async def create_semantic_clusters(self, keywords: List[Dict]) -> List[Dict]:
        kw_texts = [kw["keyword"] for kw in keywords]
        embeddings = await self.semantic_analyzer.vectorize_keywords(kw_texts)
        
        clusters = await self.topic_clusterer.cluster_keywords(
            embeddings, algorithm='hierarchical', distance_threshold=0.3
        )
        
        # Enrich clusters with semantic analysis
        enriched_clusters = []
        for cluster in clusters:
            kw_list = [k["keyword"] for k in keywords if k["keyword"] in cluster["keywords"]]
            enriched_clusters.append({
                "cluster_id": cluster["id"],
                "primary_theme": await self.semantic_analyzer.extract_cluster_theme(kw_list),
                "secondary_themes": await self.semantic_analyzer.extract_sub_themes(kw_list),
                "keywords": [k for k in keywords if k["keyword"] in cluster["keywords"]],
                "search_volume": sum(k["volume"] for k in keywords if k["keyword"] in cluster["keywords"]),
                "competition_score": np.mean([k["competition"] for k in keywords if k["keyword"] in cluster["keywords"]]),
                "parent_topic": await self.semantic_analyzer.identify_parent_topic(kw_list),
                "child_topics": await self.semantic_analyzer.identify_child_topics(kw_list)
            })
        return enriched_clusters
    
    async def build_content_hierarchy(self, clusters: List[Dict]) -> Dict:
        hierarchy = {'pillar_pages': [], 'cluster_pages': []}
        
        for cluster in clusters:
            if cluster['search_volume'] > 5000:
                hierarchy['pillar_pages'].append({
                    'topic': cluster['primary_theme'],
                    'target_keyword': max(cluster['keywords'], key=lambda x: x['volume'])['keyword'],
                    'supporting_keywords': [k['keyword'] for k in cluster['keywords'][:5]]
                })
            else:
                hierarchy['cluster_pages'].append({
                    'topic': cluster['primary_theme'],
                    'target_keyword': max(cluster['keywords'], key=lambda x: x['volume'])['keyword'],
                    'parent_pillar': cluster.get('parent_topic')
                })
        return hierarchy
    
    async def optimize_for_search_intent(self, hierarchy: Dict) -> Dict:
        for page_type in ['pillar_pages', 'cluster_pages']:
            for page in hierarchy[page_type]:
                intent = await self.intent_classifier.classify(page['target_keyword'])
                page['intent'] = intent
                page['recommended_content_type'] = await self.intent_classifier.recommend_content_type(intent)
        return hierarchy
    
    async def identify_priority_topics(self, topical_map: Dict) -> List[Dict]:
        return sorted(
            topical_map['pillar_pages'],
            key=lambda x: len(x['supporting_keywords']),
            reverse=True
        )[:3]
    
    def generate_update_recommendations(self, topical_map: Dict) -> List[str]:
        recs = []
        for page in topical_map['pillar_pages']:
            if page['intent'] == "Informational":
                recs.append(f"Enhance EEAT signals for '{page['topic']}' with expert credentials")
        return recs
    
    async def test_claude(self):
        response = await ClaudeAPI().make_request("Hi are you there?")
        print("Test response:", response)

# Example Usage
async def main():

    industry_data = {
        "core_keywords": ["SEO", "content marketing"],
        "industry": "Digital Marketing",
        "geo_targets": ["US", "UK"],
        "emerging_topics": ["AI content creation", "voice search optimization"]
    }
    
    algorithm_updates = ["EEAT Update", "Core Web Vitals Boost"]
    
    generator = TopicalMapGenerator()
    results = await generator.generate_adaptive_topical_map(industry_data, algorithm_updates)
    
    print("Topical Map Structure:")
    print(json.dumps(results['topical_map'], indent=2))
    
    print("\nPriority Topics:")
    for topic in results['priority_topics']:
        print(f"- {topic['topic']} (Volume: {topic.get('search_volume', 'N/A')})")
    
    print("\nContent Gaps:")
    for gap in results['content_gaps']:
        print(f"- {gap['topic']} (Opportunity: {gap['opportunity']:.2f})")

if __name__ == "__main__":
    asyncio.run(main())