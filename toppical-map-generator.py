import os
import json
import numpy as np
import asyncio
from typing import List, Dict, Optional
from dotenv import load_dotenv
import anthropic
import re

load_dotenv()
client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# async def make_request(prompt: str, max_tokens: int = 1000) -> str:
#     response = await client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=max_tokens,
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.content[0].text


async def make_request(prompt: str, max_tokens: int = 1000) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw_text = response.content[0].text.strip()

    # ✅ Remove triple backticks and language hints like ```json
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text, flags=re.IGNORECASE).strip()

    return cleaned


async def research_keywords(seed: List[str], industry: str) -> List[Dict]:
    prompt = f"""You are an advanced SEO keyword researcher. Generate 25-30 relevant keywords for the 
    {industry} industry based on these seed keywords: {', '.join(seed)}. Include search volume estimates 
    (1-100 scale) and competition scores (0.0-1.0). Return as JSON:
    {{"keywords": [{{"keyword": str, "volume": int, "competition": float}}]}}"""
    response = await make_request(prompt)
    print("response",response)
    return json.loads(response)["keywords"]

async def cluster_keywords(keywords: List[str]) -> List[Dict]:
    prompt = f"""Group these keywords into 5-7 thematic clusters: {', '.join(keywords[:30])}. 
    For each cluster:
    - Give a short theme name
    - List 3-5 core keywords
    - Estimate total search volume (1-100 scale)
    Return as JSON: {{"clusters": [{{"theme": str, "keywords": [str], "volume": int}}]}}"""
    response = await make_request(prompt)
    return json.loads(response)["clusters"]

async def analyze_semantics(keywords: List[str]) -> Dict:
    prompt = f"""Analyze these keywords for semantic relationships: {', '.join(keywords[:20])}. 
    Group them into thematic clusters and identify:
    1. Primary theme for each cluster
    2. Secondary related themes
    3. Parent/child topic relationships
    Return as JSON: {{"clusters": [{{"primary": str, "secondary": [str], "parent": Optional[str], "children": [str]}}]}}"""
    response = await make_request(prompt)
    print("priintng response",response)
    return json.loads(response)

async def classify_intent(keyword: str) -> str:
    prompt = f"""Classify the search intent for "{keyword}" into one of these categories: 
    Informational, Commercial, Transactional, or Navigational. Return ONLY the category name."""
    return await make_request(prompt)

def recommend_content_type(intent: str) -> str:
    return {
        "Informational": "Guide/Blog Post",
        "Commercial": "Comparison/Review",
        "Transactional": "Product Page",
        "Navigational": "Resource Hub"
    }.get(intent, "Blog Post")

async def identify_gaps(topics: List[str]) -> List[Dict]:
    prompt = f"""Analyze these topics for content gaps: {', '.join(topics[:15])}. 
    Suggest 3-5 missing topics with opportunity scores (0-1) and recommended formats.
    Return as JSON: {{"gaps": [{{"topic": str, "opportunity": float, "format": str}}]}}"""
    response = await make_request(prompt)
    return json.loads(response)["gaps"]

async def generate_topical_map(industry_data: Dict, algorithm_updates: List[str]) -> Dict:
    base_keywords = await research_keywords(industry_data['core_keywords'], industry_data['industry'])
    
    # Geo modify
    geo_modified = []
    for geo in industry_data['geo_targets']:
        for kw in base_keywords:
            geo_modified.append({
                "keyword": f"{kw['keyword']} {geo}",
                "volume": max(1, int(kw['volume'] * 0.7)),
                "competition": min(1.0, kw['competition'] * 1.2)
            })

    all_keywords = base_keywords + geo_modified

    # Add emerging topics
    for topic in industry_data['emerging_topics']:
        all_keywords.append({
            "keyword": topic,
            "volume": 75,
            "competition": 0.4
        })

    # Algorithm update filter
    if "EEAT Update" in algorithm_updates:
        all_keywords = [kw for kw in all_keywords if kw["competition"] < 0.7]

    kw_texts = [k['keyword'] for k in all_keywords]
    clusters = await cluster_keywords(kw_texts)

    enriched = []
    for i, cluster in enumerate(clusters):
        analysis = await analyze_semantics(cluster["keywords"])
        enriched.append({
            "cluster_id": i,
            "primary_theme": analysis["clusters"][0]["primary"],
            "secondary_themes": analysis["clusters"][0]["secondary"],
            "keywords": [k for k in all_keywords if k["keyword"] in cluster["keywords"]],
            "search_volume": sum(k["volume"] for k in all_keywords if k["keyword"] in cluster["keywords"]),
            "competition_score": np.mean([k["competition"] for k in all_keywords if k["keyword"] in cluster["keywords"]]),
            "parent_topic": analysis["clusters"][0].get("parent"),
            "child_topics": analysis["clusters"][0].get("children", [])
        })

    # Build content hierarchy
    pillar_pages, cluster_pages = [], []
    for cl in enriched:
        top_kw = max(cl['keywords'], key=lambda k: k['volume'])
        if cl['search_volume'] > 5000:
            pillar_pages.append({
                'topic': cl['primary_theme'],
                'target_keyword': top_kw['keyword'],
                'supporting_keywords': [k['keyword'] for k in cl['keywords'][:5]]
            })
        else:
            cluster_pages.append({
                'topic': cl['primary_theme'],
                'target_keyword': top_kw['keyword'],
                'parent_pillar': cl.get('parent_topic')
            })

    # Optimize for intent
    for page in pillar_pages + cluster_pages:
        intent = await classify_intent(page['target_keyword'])
        page['intent'] = intent
        page['recommended_content_type'] = recommend_content_type(intent)

    topical_map = {
        "pillar_pages": pillar_pages,
        "cluster_pages": cluster_pages
    }

    priority_topics = sorted(pillar_pages, key=lambda x: len(x['supporting_keywords']), reverse=True)[:3]
    content_gaps = await identify_gaps([c["primary_theme"] for c in enriched])
    update_recommendations = [
        f"Enhance EEAT signals for '{page['topic']}' with expert credentials"
        for page in pillar_pages if page['intent'] == "Informational"
    ]

    return {
        "topical_map": topical_map,
        "priority_topics": priority_topics,
        "content_gaps": content_gaps,
        "update_recommendations": update_recommendations
    }

async def main():
    industry_data = {
        "core_keywords": ["SEO", "content marketing"],
        "industry": "Digital Marketing",
        "geo_targets": ["US", "UK"],
        "emerging_topics": ["AI content creation", "voice search optimization"]
    }

    algorithm_updates = ["EEAT Update", "Core Web Vitals Boost"]
    result = await generate_topical_map(industry_data, algorithm_updates)

    print("Topical Map Structure:")
    print(json.dumps(result['topical_map'], indent=2))

    print("\nPriority Topics:")
    for topic in result['priority_topics']:
        print(f"- {topic['topic']} (Intent: {topic['intent']})")

    print("\nContent Gaps:")
    for gap in result['content_gaps']:
        print(f"- {gap['topic']} (Opportunity: {gap['opportunity']:.2f})")

    print("\nUpdate Recommendations:")
    for rec in result['update_recommendations']:
        print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main())
