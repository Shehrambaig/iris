"""
Sample Company Data for Testing the RAG System
Add more companies to test multi-company queries.
"""

SAMPLE_COMPANIES = {
    "Google": """
Google LLC is an American multinational corporation and technology company focusing on online advertising, search engine technology, cloud computing, computer software, quantum computing, e-commerce, consumer electronics, and artificial intelligence (AI). It was founded by Larry Page and Sergey Brin in 1998.

What Google Does:
Google's core product is its search engine, which handles over 8.5 billion searches per day. The company also offers:
- Google Cloud Platform: Cloud computing services including computing, data storage, machine learning, and analytics.
- YouTube: The world's largest video sharing platform acquired in 2006.
- Android: The world's most popular mobile operating system.
- Google Workspace: Productivity tools including Gmail, Google Docs, Google Sheets, and Google Meet.
- Google Ads: The world's largest digital advertising platform.
- Hardware: Pixel smartphones, Nest smart home devices, and Fitbit wearables.

Products and Services:
- Search & Advertising: Google Search, Google Ads, AdSense
- Cloud Services: Google Cloud Platform (GCP), BigQuery, Cloud AI
- Consumer Products: Android, Chrome Browser, Gmail, Google Maps, YouTube
- Hardware: Pixel phones, Chromebooks, Nest devices, Fitbit

Board of Directors:
John L. Hennessy (Chairman)
Sundar Pichai (CEO)
Larry Page (Co-Founder)
Sergey Brin (Co-Founder)
L. John Doerr
Roger W. Ferguson Jr.
Ann Mather
Alan R. Mulally
K. Ram Shriram
Robin L. Washington
Frances H. Arnold

Executive Leadership:
Sundar Pichai - CEO of Alphabet and Google
Ruth Porat - President and Chief Investment Officer
Philipp Schindler - Chief Business Officer
Prabhakar Raghavan - Chief Technologist
""",

    "Apple": """
Apple Inc. is an American multinational corporation and technology company headquartered in Cupertino, California. Founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976, Apple is the world's largest technology company by revenue and market capitalization.

What Apple Does:
Apple designs, develops, and sells consumer electronics, computer software, and online services. The company is best known for its hardware products:
- iPhone: The flagship smartphone product that revolutionized the mobile industry
- Mac: Personal computers including MacBook, iMac, and Mac Pro
- iPad: Tablet computers for consumers and professionals
- Apple Watch: Smartwatch with health and fitness features
- AirPods: Wireless earphones and headphones
- Apple TV: Digital media player and streaming device

Services:
- App Store: Digital distribution platform for apps
- Apple Music: Music streaming subscription service
- iCloud: Cloud storage and computing service
- Apple Pay: Mobile payment and digital wallet service
- Apple TV+: Video streaming subscription service
- Apple Arcade: Gaming subscription service
- AppleCare: Extended warranty and support

Board of Directors:
Arthur D. Levinson (Chairman)
Tim Cook (CEO)
James A. Bell
Al Gore
Andrea Jung
Ronald D. Sugar
Susan L. Wagner
Monica Lozano

Executive Leadership:
Tim Cook - Chief Executive Officer
Luca Maestri - Chief Financial Officer
Jeff Williams - Chief Operating Officer
Craig Federighi - Senior VP of Software Engineering
Johny Srouji - Senior VP of Hardware Technologies
Eddy Cue - Senior VP of Services
Deirdre O'Brien - Senior VP of Retail + People
""",

    "Microsoft": """
Microsoft Corporation is an American multinational technology corporation that produces computer software, consumer electronics, personal computers, and related services. Founded by Bill Gates and Paul Allen in 1975, Microsoft is headquartered in Redmond, Washington.

What Microsoft Does:
Microsoft develops and supports software, services, devices, and solutions. Key business areas include:
- Productivity and Business Processes: Microsoft 365, LinkedIn, Dynamics 365
- Intelligent Cloud: Azure cloud platform, server products, enterprise services
- More Personal Computing: Windows, Surface devices, Xbox gaming

Major Products and Services:
- Windows: Operating system for PCs
- Microsoft 365: Office apps (Word, Excel, PowerPoint, Teams)
- Azure: Cloud computing platform competing with AWS and Google Cloud
- LinkedIn: Professional networking platform
- GitHub: Software development platform
- Xbox: Gaming console and gaming services
- Surface: Line of personal computers and tablets
- Bing: Search engine with AI capabilities
- Copilot: AI assistant integrated across Microsoft products

AI Investments:
Microsoft has made significant investments in artificial intelligence, including a multi-billion dollar partnership with OpenAI. This has led to the integration of AI capabilities across its product line through Microsoft Copilot.

Board of Directors:
Satya Nadella (Chairman and CEO)
John W. Thompson
Reid Hoffman
Penny Pritzker
Carlos A. Rodriguez
Charles W. Scharf
Emma Walmsley
Padmasree Warrior
Sandra E. Peterson
Barry L. Diller

Executive Leadership:
Satya Nadella - Chairman and CEO
Amy Hood - CFO and Executive VP
Brad Smith - Vice Chairman and President
Judson Althoff - Executive VP and Chief Commercial Officer
""",

    "Meta": """
Meta Platforms, Inc. (formerly Facebook, Inc.) is an American multinational technology conglomerate based in Menlo Park, California. Founded by Mark Zuckerberg and his Harvard roommates in 2004, Meta is the parent company of Facebook, Instagram, WhatsApp, and other products.

What Meta Does:
Meta builds products that help people connect, find communities, and grow businesses. The company operates across two segments:
- Family of Apps: Facebook, Instagram, Messenger, WhatsApp
- Reality Labs: Virtual reality hardware and metaverse development

Products and Services:
- Facebook: Social networking platform with over 3 billion monthly active users
- Instagram: Photo and video sharing platform
- WhatsApp: Messaging and voice communication app
- Messenger: Instant messaging application
- Meta Quest: Virtual reality headsets
- Threads: Text-based social media platform
- Horizon Worlds: Virtual reality platform for the metaverse

Revenue Model:
Meta generates nearly all its revenue from advertising across its platforms. The company also generates revenue from:
- Reality Labs hardware sales (Quest VR headsets)
- Business messaging services
- Marketplace commerce fees

AI Development:
Meta has invested heavily in AI research and development, releasing open-source AI models like LLaMA and developing AI features for its platforms including AI chatbots and content generation tools.

Board of Directors:
Mark Zuckerberg (Chairman and CEO)
Peggy Alford
Marc L. Andreessen
Andrew W. Houston
Nancy Killefer
Robert M. Kimmitt
Sheryl Sandberg
Tony Xu
Tracey T. Travis

Executive Leadership:
Mark Zuckerberg - Founder, Chairman, and CEO
Susan Li - Chief Financial Officer
Andrew Bosworth - Chief Technology Officer
Javier Olivan - Chief Operating Officer
Jennifer Newstead - Chief Legal Officer
""",

    "Tesla": """
Tesla, Inc. is an American multinational automotive and clean energy company headquartered in Austin, Texas. Founded in 2003 by Martin Eberhard and Marc Tarpenning, Tesla is best known for electric vehicles and energy storage systems. Elon Musk became the largest shareholder and chairman in 2004.

What Tesla Does:
Tesla designs, manufactures, and sells electric vehicles and energy solutions. The company's mission is to accelerate the world's transition to sustainable energy.

Products:
- Model S: Premium electric sedan
- Model 3: Mid-range electric sedan (best-selling EV worldwide)
- Model X: Premium electric SUV with falcon-wing doors
- Model Y: Mid-size electric SUV
- Cybertruck: All-electric pickup truck
- Tesla Semi: Electric semi-truck for commercial transportation
- Roadster: High-performance electric sports car (upcoming)

Energy Products:
- Solar Panels: Residential and commercial solar installations
- Solar Roof: Building-integrated photovoltaics
- Powerwall: Home battery storage
- Megapack: Utility-scale battery storage
- Supercharger Network: Global fast-charging network for Tesla vehicles

Technology:
- Autopilot: Driver assistance system
- Full Self-Driving (FSD): Advanced autonomous driving capability (beta)
- Optimus: Humanoid robot development
- Dojo: AI supercomputer for training neural networks

Board of Directors:
Robyn Denholm (Chairman)
Elon Musk (CEO)
Ira Ehrenpreis
Joe Gebbia
James Murdoch
Kimbal Musk
JB Straubel
Kathleen Wilson-Thompson

Executive Leadership:
Elon Musk - CEO and Product Architect
Vaibhav Taneja - Chief Financial Officer
Drew Baglino - Senior VP of Powertrain and Energy Engineering (former)
Tom Zhu - Senior VP of Automotive
"""
}


def add_sample_companies_to_rag(engine, companies=None):
    """
    Add sample company data to a RAG engine.
    
    Args:
        engine: RAGEngine instance
        companies: List of company names to add, or None for all
    """
    if companies is None:
        companies = list(SAMPLE_COMPANIES.keys())
    
    for company_name in companies:
        if company_name in SAMPLE_COMPANIES:
            print(f"Adding {company_name}...")
            engine.add_text(SAMPLE_COMPANIES[company_name], f"{company_name} Company Profile")
        else:
            print(f"Company '{company_name}' not found in sample data")
    
    return engine


if __name__ == "__main__":
    # Demo: Print available companies
    print("Available sample companies:")
    for name in SAMPLE_COMPANIES:
        content = SAMPLE_COMPANIES[name]
        word_count = len(content.split())
        print(f"  - {name}: {word_count} words")
    
    print("\nTo add these to your RAG system:")
    print("  from sample_companies import add_sample_companies_to_rag, SAMPLE_COMPANIES")
    print("  add_sample_companies_to_rag(engine, ['Google', 'Apple'])")
