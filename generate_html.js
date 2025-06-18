const fs = require('fs');
const path = require('path');

// Utility function to get today's day in English
function getTodayEnglish() {
    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const today = new Date();
    return days[today.getDay()];
}

// Load restaurant links
function loadRestaurantLinks() {
    try {
        const data = fs.readFileSync('data/restaurant_links.json', 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.warn('[WARN] restaurant_links.json missing or malformed, skipping links.');
        return {};
    }
}

// Generate index page
function generateIndexPage() {
    const outputDir = path.join(__dirname, 'docs');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    // Get today's day and load today's data
    const today = getTodayEnglish().toLowerCase();
    
    // Load today's lunch data
    const todayDataPath = `data/lunch_data_${today}.json`;
    let lunchData = {};
    if (fs.existsSync(todayDataPath)) {
        try {
            const data = fs.readFileSync(todayDataPath, 'utf8');
            lunchData = JSON.parse(data);
        } catch (error) {
            console.warn(`[WARN] Could not load lunch data for ${today}`);
        }
    }
    
    const restaurantLinks = loadRestaurantLinks();

    // CEST / Sweden local time (UTC+2)
    const lastUpdated = new Date(Date.now() + (2 * 60 * 60 * 1000)).toISOString().slice(0, 16).replace('T', ' ');

    // Create restaurant list for random selection
    const restaurantNames = Object.keys(lunchData);

    let html = `<!DOCTYPE html>
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
        /* CSS Variables matching reference design */
        :root {
            --background: #ffffff;
            --foreground: #0a0a0a;
            --card: #ffffff;
            --card-foreground: #0a0a0a;
            --primary: #030213;
            --primary-foreground: #ffffff;
            --secondary: #f3f4f6;
            --secondary-foreground: #030213;
            --muted: #f9fafb;
            --muted-foreground: #6b7280;
            --accent: #f3f4f6;
            --accent-foreground: #030213;
            --border: rgba(0, 0, 0, 0.1);
            --radius: 0.625rem;
            --blue-50: #eff6ff;
            --indigo-100: #e0e7ff;
            --blue-600: #2563eb;
            --orange-500: #f97316;
            --red-500: #ef4444;
            --green-50: #f0fdf4;
            --green-700: #15803d;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: var(--foreground);
            line-height: 1.5;
        }

        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.6);
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 1px 20px rgba(0, 0, 0, 0.05);
        }

        .header-container {
            max-width: 1792px;
            margin: 0 auto;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .icon-utensils {
            width: 2rem;
            height: 2rem;
            color: var(--blue-600);
        }

        .header-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1d1d1f;
            margin: 0;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
        }

        .header-subtitle {
            font-size: 0.875rem;
            color: #6e6e73;
            margin: 0;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .language-toggle {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 0.5px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            color: #1d1d1f;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .language-toggle:hover {
            background: rgba(255, 255, 255, 0.8);
            border: 0.5px solid rgba(0, 0, 0, 0.15);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.5rem 0.75rem;
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: #1d1d1f;
            border: 0.5px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        /* Main Content */
        .main-container {
            max-width: 1792px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }

        .hero-section {
            text-align: center;
            margin-bottom: 3rem;
            max-width: 42rem;
            margin-left: auto;
            margin-right: auto;
        }

        .hero-section h1 {
            font-size: 1.875rem;
            font-weight: 700;
            color: #1d1d1f;
            margin-bottom: 1rem;
            text-shadow: 0 1px 3px rgba(255, 255, 255, 0.5);
        }

        .hero-section p {
            font-size: 1.125rem;
            color: #6e6e73;
            margin-bottom: 2rem;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
        }

        /* Random Selection */
        .random-section {
            text-align: center;
            margin-bottom: 3rem;
        }

        /* Floating Random Button */
        .floating-random-button {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
            border: none;
            border-radius: 2rem;
            padding: 0.75rem 1.5rem;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4);
            white-space: nowrap;
            min-width: 200px;
            max-width: 280px;
            height: 48px;
        }

        .floating-random-button:hover {
            transform: translateX(-50%) translateY(-2px);
            background: linear-gradient(135deg, #ff8a5b 0%, #ffa726 100%);
            box-shadow: 0 6px 25px rgba(255, 107, 53, 0.5);
        }

        .floating-random-button:active {
            transform: translateX(-50%) translateY(0px) scale(0.98);
            transition: all 0.1s ease;
        }

        /* Mobile adjustments */
        @media (max-width: 768px) {
            .floating-random-button {
                bottom: 1.5rem;
                font-size: 0.8rem;
                padding: 0.625rem 1.25rem;
                min-width: 180px;
                max-width: 250px;
                height: 44px;
            }
        }

        .icon-shuffle {
            width: 1.25rem;
            height: 1.25rem;
        }

        /* Restaurant Grid - Simple Masonry Layout */
        .restaurant-grid {
            column-count: 1;
            column-gap: 1.5rem;
            width: 100%;
        }

        /* Responsive Columns */
        @media (min-width: 768px) {
            .restaurant-grid {
                column-count: 2;
            }
        }

        @media (min-width: 1024px) {
            .restaurant-grid {
                column-count: 3;
            }
        }

        .restaurant-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 20px;
            border: 0.5px solid rgba(255, 255, 255, 0.8);
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.08),
                0 2px 8px rgba(0, 0, 0, 0.04),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            break-inside: avoid;
            margin-bottom: 1.5rem;
            width: 100%;
        }

        .restaurant-card:hover {
            transform: translateY(-2px);
            box-shadow: 
                0 12px 40px rgba(0, 0, 0, 0.12),
                0 4px 12px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 1);
            background: rgba(255, 255, 255, 0.85);
            border: 0.5px solid rgba(255, 255, 255, 1);
        }

        .restaurant-card.highlighted {
            border: 2px solid var(--orange-500);
            box-shadow: 0 10px 25px rgba(249, 115, 22, 0.3);
            transform: translateY(-1px);
        }

        .restaurant-header {
            padding: 1.5rem 1.5rem 0;
            display: grid;
            grid-template-columns: 1fr auto;
            grid-template-rows: auto auto;
            gap: 1rem 1.5rem;
            align-items: start;
        }

        .restaurant-info {
            flex: 1;
            min-width: 0;
        }

        .restaurant-name {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0 0 0.25rem 0;
            color: #1d1d1f;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
        }

        .restaurant-meta {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            font-size: 0.875rem;
            color: #6e6e73;
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
            padding: 0 1.5rem 1.5rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        .menu-section h3 {
            font-size: 1rem;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
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
            background: rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            border: 0.5px solid rgba(255, 255, 255, 0.6);
            transition: all 0.2s ease;
            min-height: fit-content;
        }

        .menu-item:hover {
            background: rgba(255, 255, 255, 0.6);
            border: 0.5px solid rgba(255, 255, 255, 0.8);
        }

        .menu-item-details {
            flex: 1;
            min-width: 0;
        }

        .menu-item-name {
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 0.25rem;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            line-height: 1.4;
        }

        .menu-item-description {
            font-size: 0.875rem;
            color: #6e6e73;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            line-height: 1.4;
        }

        .menu-item-price {
            font-weight: 600;
            color: #1d1d1f;
            align-self: flex-start;
            flex-shrink: 0;
            margin-left: 0.5rem;
            max-width: 180px;
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
            background: var(--green-50);
            color: var(--green-700);
            padding: 0.75rem;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.875rem;
            margin-top: auto;
        }

        /* Footer */
        .footer {
            max-width: 1280px;
            margin: 3rem auto 0;
            padding: 2rem 1.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            text-align: center;
            color: #6e6e73;
        }

        .footer p {
            margin: 0.5rem 0;
        }

        .footer a {
            color: #1d1d1f;
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
                max-width: 100%;
                text-align: left;
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
                    <span class="en">Today: ${today.charAt(0).toUpperCase() + today.slice(1)}</span>
                    <span class="sv hidden">Idag: ${today.replace("monday", "Måndag").replace("tuesday", "Tisdag").replace("wednesday", "Onsdag").replace("thursday", "Torsdag").replace("friday", "Fredag")}</span>
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

    `;

    if (Object.keys(lunchData).length > 0) {
        html += '<div class="restaurant-grid">';
        
        for (const [restaurantName, restaurantData] of Object.entries(lunchData)) {
            const cleanName = restaurantName.replace('Scraper', '').replace('_', ' ');
            
            html += `
            <div class="restaurant-card" id="restaurant-${restaurantName}">
                <div class="restaurant-header">
                    <div class="restaurant-info">
                        <h2 class="restaurant-name">${cleanName}</h2>
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
                    <div class="restaurant-links">`;
            
            const links = restaurantLinks[restaurantName.replace('Scraper', '')];
            if (links) {
                if (links.url) {
                    html += `<a href="${links.url}" target="_blank" title="Website">🔗</a>`;
                }
                if (links.map) {
                    html += `<a href="${links.map}" target="_blank" title="Google Maps">🗺️</a>`;
                }
            }
            
            html += `</div>
                </div>
                
                <div class="restaurant-content">`;
            
            if (restaurantData.items && restaurantData.items.length > 0) {
                html += `
                    <div class="menu-section">
                        <h3>
                            <span class="icon-menu"></span>
                            <span class="en">Today's lunch</span>
                            <span class="sv hidden">Dagens lunch</span>
                        </h3>
                        <div class="menu-items">`;
                
                for (const item of restaurantData.items) {
                    html += `
                            <div class="menu-item">
                                <div class="menu-item-details">`;
                    
                    // Handle long menu names (LsKitchen fix)
                    const name = item.name || "";
                    const description = item.description || "";
                    
                    if (name.length > 50 && !description) {
                        html += `
                                    <div class="menu-item-name">
                                        <span class="en">Today's Special</span>
                                        <span class="sv hidden">Dagens Special</span>
                                    </div>
                                    <div class="menu-item-description">${name}</div>`;
                    } else {
                        html += `<div class="menu-item-name">${name}</div>`;
                        if (description) {
                            html += `<div class="menu-item-description">${description}</div>`;
                        }
                    }
                    
                    if (item.category) {
                        html += `<div class="emoji-tags"><span class="emoji-tag">${item.category}</span></div>`;
                    }
                    
                    html += '</div>';
                    
                    if (item.price) {
                        html += `<div class="menu-item-price">${item.price}</div>`;
                    }
                    
                    html += '</div>';
                }
                
                html += `
                        </div>
                    </div>
                    
                    <div class="separator"></div>`;
            } else {
                html += `<div class="menu-section">
                    <p style="color: var(--muted-foreground); font-style: italic;">
                        <span class="en">No menu available today</span>
                        <span class="sv hidden">Ingen meny tillgänglig idag</span>
                    </p>
                </div>`;
            }
            
            html += `
                    <div class="special-offer">
                        ✨ <span class="en">Last updated: ${lastUpdated}</span>
                        <span class="sv hidden">Senast uppdaterad: ${lastUpdated}</span>
                    </div>
                </div>
            </div>`;
        }
        
        html += '</div>';
    } else {
        html += `
        <div class="no-data">
            <h2>
                <span class="en">No menu data available for today</span>
                <span class="sv hidden">Ingen menydata tillgänglig för idag</span>
            </h2>
            <p>
                <span class="en">We couldn't find any lunch menus for today. Please try again later.</span>
                <span class="sv hidden">Vi kunde inte hitta några lunchmenyer för idag. Försök igen senare.</span>
            </p>
        </div>`;
    }

    html += `
    </main>
    
    <!-- Floating Random Button -->
    <button class="floating-random-button" onclick="selectRandomRestaurant()">
        <span class="en">I am feeling hungry!</span>
        <span class="sv hidden">Jag är hungrig!</span>
    </button>
    
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
            <span class="en">Enhanced version with modern UI/UX improvements –</span>
            <span class="sv hidden">Förbättrad version med modern UI/UX –</span>
            <a href="https://github.com/designestjay/lindholmen-lunch" target="_blank">GitHub - Lindholmen Lunch</a>
        </p>
        <p>
            <span class="en">Based on original work by</span>
            <span class="sv hidden">Baserat på ursprungligt arbete av</span>
            <a href="https://github.com/Fawenah/lindholmen_lunch" target="_blank">Fawenah</a>
            <span class="en">with design overhaul and UX enhancements</span>
            <span class="sv hidden">med designomarbetning och UX-förbättringar</span>
        </p>
        <p>
            <span class="en">Questions, feedback or suggestions? Feel free to open an issue or contact via GitHub</span>
            <span class="sv hidden">Frågor, feedback eller förslag? Öppna gärna ett issue eller kontakta via GitHub</span>
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
        function toggleLanguage() {
            const enElements = document.querySelectorAll('.en');
            const svElements = document.querySelectorAll('.sv');
            
            enElements.forEach(el => el.classList.toggle('hidden'));
            svElements.forEach(el => el.classList.toggle('hidden'));
            
            // Update page language attribute
            const isSwedish = document.querySelector('.sv:not(.hidden)') !== null;
            document.documentElement.lang = isSwedish ? 'sv' : 'en';
            
            // Save language preference
            localStorage.setItem('language', isSwedish ? 'sv' : 'en');
        }

        // Random restaurant selection
        function selectRandomRestaurant() {
            const restaurants = ${JSON.stringify(restaurantNames)};
            if (restaurants.length === 0) return;
            
            // Clear previous highlights
            document.querySelectorAll('.restaurant-card.highlighted').forEach(card => {
                card.classList.remove('highlighted');
            });
            
            // Update floating button
            const floatingButton = document.querySelector('.floating-random-button');
            
            const isSwedish = document.querySelector('.sv:not(.hidden)') !== null;
            const choosingText = isSwedish ? 
                '<span class="sv">Väljer...</span><span class="en hidden">Choosing...</span>' : 
                '<span class="en">Choosing...</span><span class="sv hidden">Väljer...</span>';
            
            if (floatingButton) {
                // Store original dimensions to prevent size changes
                const originalWidth = floatingButton.offsetWidth;
                const originalHeight = floatingButton.offsetHeight;
                floatingButton.style.width = originalWidth + 'px';
                floatingButton.style.height = originalHeight + 'px';
                floatingButton.innerHTML = choosingText;
            }
            
            setTimeout(() => {
                const randomRestaurant = restaurants[Math.floor(Math.random() * restaurants.length)];
                const restaurantCard = document.getElementById('restaurant-' + randomRestaurant);
                
                if (restaurantCard) {
                    restaurantCard.classList.add('highlighted');
                    restaurantCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                // Reset button
                const finalText = isSwedish ? 
                    '<span class="sv">Jag är hungrig!</span><span class="en hidden">I am feeling hungry!</span>' : 
                    '<span class="en">I am feeling hungry!</span><span class="sv hidden">Jag är hungrig!</span>';
                
                if (floatingButton) {
                    floatingButton.innerHTML = finalText;
                    // Remove fixed dimensions to allow natural sizing again
                    floatingButton.style.width = '';
                    floatingButton.style.height = '';
                }
            }, 1000);
        }

        // Go to top and reset random selection
        function goToTop() {
            // Clear any highlighted restaurants
            document.querySelectorAll('.restaurant-card.highlighted').forEach(card => {
                card.classList.remove('highlighted');
            });
            
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // Load saved language preference
        document.addEventListener('DOMContentLoaded', function() {
            const savedLanguage = localStorage.getItem('language');
            if (savedLanguage === 'sv') {
                // Switch to Swedish if saved
                const enElements = document.querySelectorAll('.en');
                const svElements = document.querySelectorAll('.sv');
                
                enElements.forEach(el => el.classList.add('hidden'));
                svElements.forEach(el => el.classList.remove('hidden'));
                
                document.documentElement.lang = 'sv';
            }
        });
    </script>
</body>
</html>
    `;

    // Write to docs directory
    const indexPath = path.join(outputDir, 'index.html');
    fs.writeFileSync(indexPath, html, 'utf8');
    console.log(`[INFO] Generated weekly index page: ${indexPath}`);
    
    // Also write to root directory for GitHub Pages
    const rootIndexPath = path.join(__dirname, 'index.html');
    fs.writeFileSync(rootIndexPath, html, 'utf8');
    console.log(`[INFO] Generated root index page: ${rootIndexPath}`);
}

if (require.main === module) {
    generateIndexPage();
}

module.exports = { generateIndexPage, getTodayEnglish };