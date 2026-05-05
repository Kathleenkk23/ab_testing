#!/usr/bin/env python3
"""
🎨 Creative Component Demo - Real-World A/B Testing Examples

This script demonstrates how to use the creative component system
in real A/B testing scenarios.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def demo_creative_workflow():
    """Complete creative testing workflow demonstration"""

    print("🎨 CREATIVE COMPONENT A/B TESTING DEMO")
    print("=" * 50)

    # Step 1: Create an experiment
    print("\n1. Creating A/B Test Experiment...")
    experiment_response = requests.post(f"{BASE_URL}/experiment/", json={
        "name": f"homepage_hero_banner_test_{int(time.time())}"  # Unique name
    })
    if experiment_response.status_code != 200:
        print(f"❌ Failed to create experiment: {experiment_response.text}")
        return
        
    experiment = experiment_response.json()
    experiment_id = experiment["id"]
    print(f"✅ Created experiment: {experiment['name']} (ID: {experiment_id})")

    # Step 2: Create creative assets
    print("\n2. Creating Creative Assets...")

    # Control creative (current design)
    control_response = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Hero Banner - Control",
        "description": "Current blue banner with generic headline",
        "creative_type": "html",
        "content": """
        <div class="hero-banner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px; text-align: center;">
            <h1>Welcome to Our Platform</h1>
            <p>Discover amazing features that will transform your workflow</p>
            <button style="background: #ff6b6b; color: white; border: none; padding: 15px 30px; border-radius: 5px; font-size: 18px;">Get Started</button>
        </div>
        """,
        "metadata": {
            "background_color": "#667eea",
            "headline": "Welcome to Our Platform",
            "cta_text": "Get Started",
            "design_style": "gradient_background"
        }
    })
    if control_response.status_code != 200:
        print(f"❌ Failed to create control creative: {control_response.text}")
        return
    control_creative = control_response.json()
    print(f"✅ Created control creative: {control_creative['name']} (ID: {control_creative['id']})")

    # Treatment creative (new design)
    treatment_response = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Hero Banner - Treatment A",
        "description": "New orange banner with benefit-focused headline",
        "creative_type": "html",
        "content": """
        <div class="hero-banner" style="background: linear-gradient(135deg, #ff9a56 0%, #ff6b6b 100%); color: white; padding: 60px; text-align: center;">
            <h1>🚀 Boost Your Productivity by 300%</h1>
            <p>Join 50,000+ users who have transformed their workflow</p>
            <button style="background: #4ecdc4; color: white; border: none; padding: 15px 30px; border-radius: 25px; font-size: 18px; font-weight: bold;">Start Free Trial</button>
        </div>
        """,
        "metadata": {
            "background_color": "#ff9a56",
            "headline": "🚀 Boost Your Productivity by 300%",
            "cta_text": "Start Free Trial",
            "design_style": "benefit_focused",
            "urgency_element": "50,000+ users"
        }
    })
    if treatment_response.status_code != 200:
        print(f"❌ Failed to create treatment creative: {treatment_response.text}")
        return
    treatment_creative = treatment_response.json()
    print(f"✅ Created treatment creative: {treatment_creative['name']} (ID: {treatment_creative['id']})")

    # Step 3: Assign creatives to experiment variants
    print("\n3. Assigning Creatives to Experiment Variants...")

    # Assign control creative
    requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": experiment_id,
        "variant": "control",
        "creative_id": control_creative["id"]
    })
    print(f"✅ Assigned control creative to experiment {experiment_id}")

    # Assign treatment creative
    requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": experiment_id,
        "variant": "treatment",
        "creative_id": treatment_creative["id"]
    })
    print(f"✅ Assigned treatment creative to experiment {experiment_id}")

    # Step 4: Simulate user traffic and track events
    print("\n4. Simulating User Traffic...")

    # Simulate 100 users
    for user_id in range(1, 101):
        # Assign user to variant
        assignment = requests.get(f"{BASE_URL}/assign/", params={
            "user_id": user_id,
            "experiment_id": experiment_id
        }).json()

        variant = assignment["variant"]
        creative = assignment.get("creative", {})

        print(f"User {user_id} → {variant} variant (Creative: {creative.get('name', 'None')})")

        # Simulate user behavior
        # 100% see the banner (impression)
        requests.post(f"{BASE_URL}/event/", json={
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "event_type": "impression"
        })

        # 20% click the CTA
        if user_id % 5 == 0:
            requests.post(f"{BASE_URL}/event/", json={
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant": variant,
                "event_type": "click"
            })

            # 50% of clickers convert (10% total conversion rate)
            if user_id % 10 == 0:
                requests.post(f"{BASE_URL}/event/", json={
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "variant": variant,
                    "event_type": "conversion"
                })

    print("✅ Simulated 100 users with realistic behavior patterns")

    # Step 5: Check results
    print("\n5. Checking Experiment Results...")
    time.sleep(1)  # Allow results to process

    results = requests.get(f"{BASE_URL}/results/", params={"experiment_id": experiment_id}).json()
    print(f"📊 Results for experiment '{experiment['name']}':")
    print(f"   - Control: {results['control']['conversion_rate']:.1%} conversion rate ({results['control']['conversions']}/{results['control']['impressions']} conversions)")
    print(f"   - Treatment: {results['treatment']['conversion_rate']:.1%} conversion rate ({results['treatment']['conversions']}/{results['treatment']['impressions']} conversions)")
    print(f"   - Uplift: {results['uplift']:.1%} (Treatment vs Control)")
    print(f"   - Statistical significance: {'✅ Significant' if results['is_significant'] else '❌ Not significant'} (p={results['p_value']:.3f})")
    
    winner = "Control" if results['control_conversion_rate'] > results['treatment_conversion_rate'] else "Treatment"
    winner_rate = max(results['control_conversion_rate'], results['treatment_conversion_rate'])
    print(f"   - Current winner: {winner} ({winner_rate:.1%})")

    # Step 6: Get creative-specific analytics
    print("\n6. Creative Performance Analytics...")

    control_usage = requests.get(f"{BASE_URL}/creative/{control_creative['id']}/usage").json()
    treatment_usage = requests.get(f"{BASE_URL}/creative/{treatment_creative['id']}/usage").json()

    print(f"🎨 Control Creative '{control_creative['name']}':")
    print(f"   - Used in {len(control_usage['experiments'])} experiments")
    print(f"   - Total events: {control_usage['total_events']}")

    print(f"🎨 Treatment Creative '{treatment_creative['name']}':")
    print(f"   - Used in {len(treatment_usage['experiments'])} experiments")
    print(f"   - Total events: {treatment_usage['total_events']}")

    print("\n" + "=" * 50)
    print("🎉 CREATIVE A/B TESTING WORKFLOW COMPLETE!")
    print("\n💡 Real-World Usage Patterns:")
    print("   • Use this system for testing:")
    print("     - Landing page designs")
    print("     - Email campaign creatives")
    print("     - Ad banner variations")
    print("     - Product page layouts")
    print("     - Call-to-action buttons")
    print("     - Headline and copy variations")
    print("\n   • Integration with your app:")
    print("     1. Assign user to experiment variant")
    print("     2. Get creative for that variant")
    print("     3. Serve creative to user")
    print("     4. Track impressions, clicks, conversions")


def demo_image_creative_test():
    """Example of testing different product images"""

    print("\n🖼️  PRODUCT IMAGE A/B TEST EXAMPLE")
    print("-" * 40)

    # Create experiment
    exp_response = requests.post(f"{BASE_URL}/experiment/", json={
        "name": "product_page_image_test"
    })
    if exp_response.status_code != 200:
        print(f"❌ Failed to create image experiment: {exp_response.text}")
        return
    exp = exp_response.json()

    # Create image creatives
    image_a_response = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Product Image - Lifestyle Shot",
        "description": "Photo of person using product in real environment",
        "creative_type": "image",
        "content": "https://example.com/product-lifestyle.jpg",
        "metadata": {
            "image_type": "lifestyle",
            "alt_text": "Happy customer using our product",
            "dimensions": "800x600"
        }
    })
    if image_a_response.status_code != 200:
        print(f"❌ Failed to create image A: {image_a_response.text}")
        return
    image_a = image_a_response.json()

    image_b_response = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Product Image - Clean Studio Shot",
        "description": "Professional studio photograph on white background",
        "creative_type": "image",
        "content": "https://example.com/product-studio.jpg",
        "metadata": {
            "image_type": "studio",
            "alt_text": "Product on white background",
            "dimensions": "800x600"
        }
    })
    if image_b_response.status_code != 200:
        print(f"❌ Failed to create image B: {image_b_response.text}")
        return
    image_b = image_b_response.json()

    # Assign to variants
    assign_a = requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": exp["id"], "variant": "control", "creative_id": image_a["id"]
    })
    if assign_a.status_code != 200:
        print(f"❌ Failed to assign image A: {assign_a.text}")
        return
        
    assign_b = requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": exp["id"], "variant": "treatment", "creative_id": image_b["id"]
    })
    if assign_b.status_code != 200:
        print(f"❌ Failed to assign image B: {assign_b.text}")
        return

    print(f"✅ Created image A/B test: {exp['name']}")
    print("   Control: Lifestyle photo")
    print("   Treatment: Studio photo")


def demo_copy_creative_test():
    """Example of testing different copy variations"""

    print("\n📝 COPY VARIATION A/B TEST EXAMPLE")
    print("-" * 40)

    # Create experiment
    exp_response = requests.post(f"{BASE_URL}/experiment/", json={
        "name": "homepage_headline_test"
    })
    if exp_response.status_code != 200:
        print(f"❌ Failed to create copy experiment: {exp_response.text}")
        return
    exp = exp_response.json()

    # Create copy creatives
    copy_a_response = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Headline - Feature Focused",
        "description": "Emphasizes product features",
        "creative_type": "copy",
        "content": "Advanced Analytics, Real-time Reporting, Custom Dashboards",
        "metadata": {
            "tone": "professional",
            "focus": "features",
            "length": "short"
        }
    })
    if copy_a_response.status_code != 200:
        print(f"❌ Failed to create copy A: {copy_a_response.text}")
        return
    copy_a = copy_a_response.json()

    copy_b = requests.post(f"{BASE_URL}/creative/", json={
        "name": "Headline - Benefit Focused",
        "description": "Emphasizes user benefits",
        "creative_type": "copy",
        "content": "Save 5 hours per week, Increase productivity by 300%, Make better decisions",
        "metadata": {
            "tone": "benefit-driven",
            "focus": "outcomes",
            "length": "medium"
        }
    })
    if copy_b.status_code != 200:
        print(f"❌ Failed to create copy B: {copy_b.text}")
        return
    copy_b = copy_b.json()

    # Assign to variants
    assign_copy_a = requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": exp["id"], "variant": "control", "creative_id": copy_a["id"]
    })
    if assign_copy_a.status_code != 200:
        print(f"❌ Failed to assign copy A: {assign_copy_a.text}")
        return
        
    assign_copy_b = requests.post(f"{BASE_URL}/creative/assign", json={
        "experiment_id": exp["id"], "variant": "treatment", "creative_id": copy_b["id"]
    })
    if assign_copy_b.status_code != 200:
        print(f"❌ Failed to assign copy B: {assign_copy_b.text}")
        return

    print(f"✅ Created copy A/B test: {exp['name']}")
    print("   Control: Feature-focused copy")
    print("   Treatment: Benefit-focused copy")


if __name__ == "__main__":
    try:
        # Run the main creative workflow demo
        demo_creative_workflow()

        # Show additional examples
        demo_image_creative_test()
        demo_copy_creative_test()

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server. Make sure it's running on http://localhost:8000")
        print("   Start with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")