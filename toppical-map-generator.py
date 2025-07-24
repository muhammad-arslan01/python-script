import os
import json
import asyncio
from dotenv import load_dotenv
import httpx
from typing import Dict, List, Any
load_dotenv()

async def generate_topical_map(industry_data: Dict[str, Any], algorithm_updates: List[str]) -> Dict[str, Any]:
    """
    Generates topical map analysis using Claude API
    Returns: Dict with keys: topical_map, priority_topics, content_gaps, update_recommendations
    """
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("Missing ANTHROPIC_API_KEY environment variable")

    # Construct the comprehensive prompt
    prompt = f"""
    As an SEO Content Strategy Expert, generate a topical map analysis for:
    Industry: {industry_data['industry']}
    Core Keywords: {', '.join(industry_data['core_keywords'])}
    Geo Targets: {', '.join(industry_data['geo_targets'])}
    Emerging Topics: {', '.join(industry_data['emerging_topics'])}
    Algorithm Updates: {', '.join(algorithm_updates)}

    Create JSON output with these exact keys:
    1. "topical_map": Nested dictionary structure with topics/subtopics (3 levels deep)
    2. "priority_topics": List of dicts with "topic" and "intent"
    3. "content_gaps": List of dicts with "topic" and "opportunity" (float between 0-1)
    4. "update_recommendations": List of strategy strings
    5. "post_titles": List of dicts with "topic" and "titles" (3-5 SEO-friendly titles per topic)

    Guidelines:
    - Create a comprehensive topical map with 3 hierarchy levels
    - Prioritize topics by search volume and algorithm update impact
    - Identify content gaps with opportunity scores >0.7
    - Make recommendations actionable for {industry_data['industry']}
    - Include all provided emerging topics
    - Optimize for {industry_data['geo_targets']} audiences
    - Ensure EEAT principles are incorporated
    - Consider voice search optimization strategies
    - Account for AI-generated content best practices
    - Generate 3-5 engaging, click-worthy post titles for EACH priority topic and content gap
    - Titles should be 60-70 characters max, include power words, and target commercial/intent signals
    """
    
    # Claude API request
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-opus-20240229",
                "max_tokens": 4000,
                "system": "You are an SEO Content Strategy Expert. Return valid JSON only without any additional text.",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        result = response.json()
    
    # Extract and parse JSON content
    content = result["content"][0]["text"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback extraction if response isn't pure JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        return json.loads(content[start:end])

async def main():
    industry_data = {
        "core_keywords": ["chiropractic care", "spinal alignment", "back pain relief"],
        "industry": "Health & Wellness",
        "geo_targets": ["US", "UK"],
        "emerging_topics": [
            "non-invasive pain management", 
            "ergonomic health tips", 
            "chiropractic care for desk workers", 
            "drug-free treatment options"
        ]
    }

    algorithm_updates = ["Helpful Content Update", "Your Money Your Life (YMYL) Guidelines Boost"]

    result = await generate_topical_map(industry_data, algorithm_updates)

    # Print results in the specified format
    print("\nTopical Map Structure:")
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

     # New section for printing post titles
    print("\nPost Titles:")
    for item in result['post_titles']:
        print(f"\nTopic: {item['topic']}")
        for idx, title in enumerate(item['titles'], 1):
            print(f"  {idx}. {title}")    

if __name__ == "__main__":
    asyncio.run(main())