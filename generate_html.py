# file: lindholmen_lunch/generate_html.py

import json
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta, timezone
from pathlib import Path
from utils.annotate_food_types import annotate_file
from utils.utils import get_today_english

def load_restaurant_links() -> dict:
    try:
        with open("data/restaurant_links.json", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARN] restaurant_links.json missing or malformed, skipping links.")
        return {}

def generate_lunch_summary(day: str):
    data_path = f"data/lunch_data_{day}.json"
    if not os.path.exists(data_path):
        print(f"[WARN] No data file for {day}: {data_path}")
        return
    
    # Annotate food types in the data file
    annotate_file(data_path)

    with open(data_path, encoding="utf-8") as f:
        lunch_data = json.load(f)

    restaurant_links = load_restaurant_links()

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("summary_template.html")

    # CEST / Sweden local time (UTC+2)
    sweden_tz = timezone(timedelta(hours=2))

    output_html = template.render(
        day=day.capitalize(),
        lunch_data=lunch_data,
        restaurant_links=restaurant_links,
        last_updated=datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")
    )

    os.makedirs("docs", exist_ok=True)
    output_path = f"docs/lunch_{day}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"[INFO] Generated HTML summary for {day}: {output_path}")


def generate_index_page():
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    # Get today's day and load today's data
    today = get_today_english().lower()
    
    # Load today's lunch data
    today_data_path = f"data/lunch_data_{today}.json"
    lunch_data = {}
    if os.path.exists(today_data_path):
        with open(today_data_path, encoding="utf-8") as f:
            lunch_data = json.load(f)
    
    restaurant_links = load_restaurant_links()

    # CEST / Sweden local time (UTC+2)
    sweden_tz = timezone(timedelta(hours=2))
    last_updated = datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")

    # Create restaurant list for random selection
    restaurant_names = list(lunch_data.keys()) if lunch_data else []

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-LMDT71XZ0C"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-LMDT71XZ0C');
    </script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7499028717075061"
     crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="iUNSsOQ8Uw21911zTxrbq0FNyaY7uwQu6iq8XffofsA" />
    <title>Today's lunch in Lindholmen</title>
    <meta name="description" content="Today's lunch from restaurants in Lindholmen – updated daily." />
    
    <style>
        /* Modern CSS Reset and Variables */
        :root {
            --background: #ffffff;
            --foreground: #020617;
            --card: #ffffff;
            --card-foreground: #020617;
            --primary: #1e40af;
            --primary-foreground: #ffffff;
            --secondary: #f1f5f9;
            --secondary-foreground: #0f172a;
            --muted: #f8fafc;
            --muted-foreground: #64748b;
            --accent: #f1f5f9;
            --accent-foreground: #0f172a;
            --border: rgba(0, 0, 0, 0.1);
            --radius: 0.5rem;
            --orange: #ea580c;
            --orange-hover: #dc2626;
            --green: #16a34a;
            --green-light: #dcfce7;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(to bottom right, #dbeafe, #e0e7ff);
            min-height: 100vh;
            color: var(--foreground);
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .header-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-title {
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--foreground);
            margin: 0;
            cursor: pointer;
            transition: color 0.2s ease;
        }

        .header-title:hover {
            color: var(--primary);
        }

        .header-subtitle {
            font-size: 0.875rem;
            color: var(--muted-foreground);
            margin: 0;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .language-toggle {
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--secondary-foreground);
            transition: all 0.2s ease;
        }

        .language-toggle:hover {
            background: var(--accent);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.5rem 1rem;
            background: var(--primary);
            color: var(--primary-foreground);
            border-radius: var(--radius);
            font-size: 0.875rem;
            font-weight: 500;
        }

        /* Main Content */
        .main-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }

        .hero-section {
            text-align: center;
            margin-bottom: 3rem;
        }

        .hero-section h1 {
            font-size: 3rem;
            font-weight: 700;
            color: var(--foreground);
            margin-bottom: 1rem;
        }

        .hero-section p {
            font-size: 1.125rem;
            color: var(--muted-foreground);
            max-width: 42rem;
            margin: 0 auto 2rem;
        }

        /* Random Selection */
        .random-section {
            text-align: center;
            margin-bottom: 3rem;
        }

        .random-button {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(to right, var(--orange), var(--orange-hover));
            color: white;
            padding: 1rem 2rem;
            border-radius: var(--radius);
            font-size: 1.125rem;
            text-decoration: none;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3);
        }

        .random-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(234, 88, 12, 0.4);
        }

        /* Restaurant Grid */
        .restaurant-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            align-items: start; /* Allow cards to have their natural height */
        }

        .restaurant-card {
            background: var(--card);
            border-radius: calc(var(--radius) + 4px);
            border: 1px solid var(--border);
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            position: relative;
            display: flex;
            flex-direction: column; /* Stack header and content vertically */
        }

        .restaurant-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }

        .restaurant-card.highlighted {
            border: 2px solid var(--orange);
            box-shadow: 0 10px 25px rgba(234, 88, 12, 0.3);
            transform: translateY(-4px) scale(1.02);
        }

        .restaurant-header {
            padding: 1.25rem;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
        }

        .restaurant-info {
            flex: 1;
            min-width: 0;
        }

        .restaurant-name {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0 0 0.25rem 0;
            color: var(--foreground);
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
        }

        .restaurant-meta {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            font-size: 0.875rem;
            color: var(--muted-foreground);
        }

        .restaurant-meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .cuisine-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: var(--secondary);
            color: var(--secondary-foreground);
            border-radius: calc(var(--radius) - 2px);
            font-size: 0.75rem;
            font-weight: 500;
            margin-top: 0.5rem;
        }

        .restaurant-links {
            display: flex;
            gap: 0.5rem;
            align-items: flex-start;
            flex-shrink: 0;
        }

        .restaurant-links a {
            color: var(--primary);
            text-decoration: none;
            font-size: 1.2rem;
            opacity: 0.8;
            transition: opacity 0.2s ease;
        }

        .restaurant-links a:hover {
            opacity: 1;
        }

        .restaurant-content {
            padding: 0 1.25rem 1.25rem;
            flex-grow: 1; /* Take up remaining space */
            display: flex;
            flex-direction: column;
        }

        .menu-section h3 {
            font-size: 1rem;
            font-weight: 600;
            color: var(--foreground);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .menu-items {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .menu-item {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            padding: 0.75rem;
            background: var(--muted);
            border-radius: var(--radius);
            transition: background 0.2s ease;
            min-height: fit-content;
        }

        .menu-item:hover {
            background: var(--accent);
        }

        .menu-item-details {
            flex: 1;
            min-width: 0;
        }

        .menu-item-name {
            font-weight: 600;
            color: var(--foreground);
            margin-bottom: 0.25rem;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            line-height: 1.4;
        }

        .menu-item-description {
            font-size: 0.875rem;
            color: var(--muted-foreground);
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            line-height: 1.4;
        }

        .menu-item-price {
            font-weight: 600;
            color: var(--primary);
            align-self: flex-start;
            flex-shrink: 0;
            margin-left: 0.5rem;
            max-width: 180px; /* Set maximum width */
            text-align: right;
            line-height: 1.3;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
        }

        .emoji-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-top: 0.5rem;
        }

        .emoji-tag {
            font-size: 1.1rem;
        }

        /* Separator */
        .separator {
            height: 1px;
            background: var(--border);
            margin: 1.5rem 0;
        }

        /* Special Offer */
        .special-offer {
            background: var(--green-light);
            color: var(--green);
            padding: 1rem;
            border-radius: var(--radius);
            font-weight: 500;
            border: 1px solid rgba(22, 163, 74, 0.2);
            margin-top: auto; /* Push to bottom of card */
        }



        /* Footer */
        .footer {
            max-width: 1280px;
            margin: 3rem auto 0;
            padding: 2rem 1.5rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--muted-foreground);
        }

        .footer p {
            margin: 0.5rem 0;
        }

        .footer a {
            color: var(--primary);
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        /* Icons using CSS */
        .icon-utensils::before { content: "🍽️"; }
        .icon-clock::before { content: "🕐"; }
        .icon-map::before { content: "📍"; }
        .icon-menu::before { content: "📋"; }
        .icon-shuffle::before { content: "🎲"; }
        .icon-language::before { content: "🌐"; }

        /* No Data Message */
        .no-data {
            text-align: center;
            padding: 3rem;
            color: var(--muted-foreground);
        }

        .no-data h2 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--foreground);
        }

        /* Hidden class for language switching */
        .hidden {
            display: none;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .hero-section h1 {
                font-size: 2rem;
            }
            
            .restaurant-grid {
                grid-template-columns: 1fr;
            }
            
            .restaurant-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.75rem;
            }
            
            .restaurant-links {
                align-self: flex-end;
            }
        }

        @media (max-width: 480px) {
            .restaurant-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .menu-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
                padding: 1rem;
            }
            
            .menu-item-details {
                width: 100%;
            }
            
            .menu-item-name {
                font-size: 0.95rem;
                line-height: 1.3;
            }
            
            .menu-item-description {
                font-size: 0.8rem;
                line-height: 1.3;
            }
            
            .menu-item-price {
                align-self: flex-end;
                margin-left: 0;
                margin-top: 0.25rem;
                max-width: 100%; /* Allow full width on mobile */
                text-align: left; /* Left align on mobile */
            }

            .restaurant-header {
                flex-direction: column;
                align-items: stretch;
            }

            .restaurant-links {
                align-self: flex-start;
            }
        }
    </style>
</head>

<body>
    <!-- Header -->
    <header class="header">
        <div class="header-container">
            <div class="header-left">
                <span class="icon-utensils" style="font-size: 2rem; color: var(--primary);"></span>
                <div>
                    <h1 class="header-title" onclick="goToTop()">Lindholmen Lunch</h1>
                    <p class="header-subtitle">
                        <span class="en">Today's lunch in Lindholmen, Gothenburg</span>
                        <span class="sv hidden">Dagens lunch i Lindholmen, Göteborg</span>
                    </p>
                </div>
            </div>
            <div class="header-right">
                <button class="language-toggle" onclick="toggleLanguage()">
                    <span class="icon-language"></span>
                    <span class="en">Svenska</span>
                    <span class="sv hidden">English</span>
                </button>
                <div class="badge">
                    <span class="icon-clock"></span>
                    <span class="en">Today: """ + today.capitalize() + """</span>
                    <span class="sv hidden">Idag: """ + today.replace("monday", "Måndag").replace("tuesday", "Tisdag").replace("wednesday", "Onsdag").replace("thursday", "Torsdag").replace("friday", "Fredag") + """</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-container">
        <div class="hero-section">
            <h1>
                <span class="en">What should you eat today?</span>
                <span class="sv hidden">Vad ska du äta idag?</span>
            </h1>
            <p>
                <span class="en">Explore today's lunch offers in Lindholmen or let us choose for you!</span>
                <span class="sv hidden">Upptäck dagens luncherbjudanden i Lindholmen eller låt oss välja åt dig!</span>
            </p>
        </div>

        <!-- Random Selection -->
        <div class="random-section">
            <button class="random-button" onclick="selectRandomRestaurant()">
                <span class="icon-shuffle"></span>
                <span class="en">I'm feeling hungry!</span>
                <span class="sv hidden">Jag är hungrig!</span>
            </button>
        </div>
    """

    if lunch_data:
        html += '<div class="restaurant-grid">'
        
        for restaurant_name, restaurant_data in lunch_data.items():
            clean_name = restaurant_name.replace('Scraper', '').replace('_', ' ')
            
            html += f"""
            <div class="restaurant-card" id="restaurant-{restaurant_name}">
                <div class="restaurant-header">
                    <div class="restaurant-info">
                        <h2 class="restaurant-name">{clean_name}</h2>
                        <div class="restaurant-meta">
                            <div class="restaurant-meta-item">
                                <span class="icon-map"></span>
                                <span class="en">Lindholmen</span>
                                <span class="sv hidden">Lindholmen</span>
                            </div>
                            <div class="restaurant-meta-item">
                                <span class="icon-clock"></span>
                                <span class="en">11:00 - 14:00</span>
                                <span class="sv hidden">11:00 - 14:00</span>
                            </div>
                        </div>
                        <div class="cuisine-badge">
                            <span class="en">Restaurant</span>
                            <span class="sv hidden">Restaurang</span>
                        </div>
                    </div>
                    <div class="restaurant-links">"""
            
            if restaurant_links.get(restaurant_name.replace('Scraper', '')):
                links = restaurant_links[restaurant_name.replace('Scraper', '')]
                if links.get('url'):
                    html += f'<a href="{links["url"]}" target="_blank" title="Website">🔗</a>'
                if links.get('map'):
                    html += f'<a href="{links["map"]}" target="_blank" title="Google Maps">🗺️</a>'
            
            html += """</div>
                </div>
                
                <div class="restaurant-content">"""
            
            if restaurant_data.get("items"):
                html += """
                    <div class="menu-section">
                        <h3>
                            <span class="icon-menu"></span>
                            <span class="en">Today's lunch</span>
                            <span class="sv hidden">Dagens lunch</span>
                        </h3>
                        <div class="menu-items">"""
                
                for item in restaurant_data["items"]:
                    html += f"""
                            <div class="menu-item">
                                <div class="menu-item-details">"""
                    
                    # Handle long menu names (LsKitchen fix)
                    name = item.get("name", "")
                    description = item.get("description", "")
                    
                    if len(name) > 50 and not description:
                        html += f"""
                                    <div class="menu-item-name">
                                        <span class="en">Today's Special</span>
                                        <span class="sv hidden">Dagens Special</span>
                                    </div>
                                    <div class="menu-item-description">{name}</div>"""
                    else:
                        html += f'<div class="menu-item-name">{name}</div>'
                        if description:
                            html += f'<div class="menu-item-description">{description}</div>'
                    
                    if item.get("category"):
                        html += f'<div class="emoji-tags"><span class="emoji-tag">{item["category"]}</span></div>'
                    
                    html += '</div>'
                    
                    if item.get("price"):
                        html += f'<div class="menu-item-price">{item["price"]}</div>'
                    
                    html += '</div>'
                
                html += """
                        </div>
                    </div>
                    
                    <div class="separator"></div>"""
            else:
                html += """<div class="menu-section">
                    <p style="color: var(--muted-foreground); font-style: italic;">
                        <span class="en">No menu available today</span>
                        <span class="sv hidden">Ingen meny tillgänglig idag</span>
                    </p>
                </div>"""
            
            html += f"""
                    <div class="special-offer">
                        ✨ <span class="en">Last updated: {last_updated}</span>
                        <span class="sv hidden">Senast uppdaterad: {last_updated}</span>
                    </div>
                </div>
            </div>"""
        
        html += '</div>'
    else:
        html += f"""
        <div class="no-data">
            <h2>
                <span class="en">No menu data available for today</span>
                <span class="sv hidden">Ingen menydata tillgänglig för idag</span>
            </h2>
            <p>
                <span class="en">We couldn't find any lunch menus for today. Please try again later.</span>
                <span class="sv hidden">Vi kunde inte hitta några lunchmenyer för idag. Försök igen senare.</span>
            </p>
        </div>"""

    html += f"""
    </main>
    
    <!-- Footer -->
    <footer class="footer">
        <p>
            <span class="icon-map"></span> 
            <span class="en">Lindholmen, Gothenburg</span>
            <span class="sv hidden">Lindholmen, Göteborg</span>
        </p>
        <p>
            <span class="en">Discover the best lunch options in the Lindholmen area</span>
            <span class="sv hidden">Upptäck de bästa lunchalternativen i Lindholmen området</span>
        </p>
        <p>
            <span class="en">This lunch compilation is open source –</span>
            <span class="sv hidden">Denna lunchsammanställning är öppen källkod –</span>
            <a href="https://github.com/Fawenah/lindholmen_lunch" target="_blank">GitHub - Lindholmen Lunch</a>
        </p>
        <p>
            <span class="en">Questions, feedback or missing your favorite restaurant? Open an issue, pull request, contact me via GitHub or via</span>
            <span class="sv hidden">Har du frågor, feedback eller saknar din favoritrestaurang? Öppna ett issue, pull request, kontakta mig via GitHub eller via</span>
            <a href="mailto:fawenah@gmail.com">fawenah@gmail.com</a>.
        </p>
        <p style="margin-top: 1rem; font-size: 0.8rem;">
            <a href="privacy.html">
                <span class="en">Privacy Policy</span>
                <span class="sv hidden">Integritetspolicy</span>
            </a>
        </p>
    </footer>

    <script>
        // Language switching
        function toggleLanguage() {{
            const enElements = document.querySelectorAll('.en');
            const svElements = document.querySelectorAll('.sv');
            
            enElements.forEach(el => el.classList.toggle('hidden'));
            svElements.forEach(el => el.classList.toggle('hidden'));
            
            // Update page language attribute
            const isSwedish = document.querySelector('.sv:not(.hidden)') !== null;
            document.documentElement.lang = isSwedish ? 'sv' : 'en';
            
            // Save language preference
            localStorage.setItem('language', isSwedish ? 'sv' : 'en');
        }}



        // Random restaurant selection
        function selectRandomRestaurant() {{
            const restaurants = {restaurant_names};
            if (restaurants.length === 0) return;
            
            // Clear previous highlights
            document.querySelectorAll('.restaurant-card.highlighted').forEach(card => {{
                card.classList.remove('highlighted');
            }});
            
            // Add some animation
            const button = document.querySelector('.random-button');
            button.style.transform = 'scale(0.95)';
            
            const isSwedish = document.querySelector('.sv:not(.hidden)') !== null;
            button.innerHTML = isSwedish ? 
                '<span class="icon-shuffle"></span> Väljer...' : 
                '<span class="icon-shuffle"></span> Choosing...';
            
            setTimeout(() => {{
                const randomRestaurant = restaurants[Math.floor(Math.random() * restaurants.length)];
                const restaurantCard = document.getElementById('restaurant-' + randomRestaurant);
                
                if (restaurantCard) {{
                    restaurantCard.classList.add('highlighted');
                    restaurantCard.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
                
                // Reset button
                button.style.transform = '';
                button.innerHTML = isSwedish ? 
                    '<span class="icon-shuffle"></span> Jag är hungrig!' : 
                    '<span class="icon-shuffle"></span> I am feeling hungry!';
            }}, 1000);
        }}

        // Go to top and reset random selection
        function goToTop() {{
            // Clear any highlighted restaurants
            document.querySelectorAll('.restaurant-card.highlighted').forEach(card => {{
                card.classList.remove('highlighted');
            }});
            
            // Scroll to top
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // Load saved language preference
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLanguage = localStorage.getItem('language');
            if (savedLanguage === 'sv') {{
                // Switch to Swedish if saved
                const enElements = document.querySelectorAll('.en');
                const svElements = document.querySelectorAll('.sv');
                
                enElements.forEach(el => el.classList.add('hidden'));
                svElements.forEach(el => el.classList.remove('hidden'));
                
                document.documentElement.lang = 'sv';
            }}
        }});
    </script>
</body>
</html>
    """

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"[INFO] Generated weekly index page: {index_path}")
