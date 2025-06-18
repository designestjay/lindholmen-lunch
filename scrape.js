const fs = require('fs-extra');
const axios = require('axios');
const cheerio = require('cheerio');
const path = require('path');

// Utility functions
function getTodayEnglish() {
    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const today = new Date();
    return days[today.getDay()];
}

// Base scraper class
class BaseScraper {
    constructor(name) {
        this.name = name;
    }

    async fetchPage(url) {
        try {
            const response = await axios.get(url, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            });
            return response.data;
        } catch (error) {
            console.error(`[${this.name}] Error fetching ${url}:`, error.message);
            return null;
        }
    }

    async getMenuForDay(day) {
        // Override in subclasses
        return null;
    }

    async getAllMenus() {
        // Override in subclasses if weekly scraping is supported
        return null;
    }
}

// Simple mock scrapers for demonstration
class KooperativetScraper extends BaseScraper {
    constructor() {
        super('KooperativetScraper');
    }

    async getMenuForDay(day) {
        // Mock data - replace with actual scraping logic
        return {
            day: day,
            items: [
                {
                    name: "Today's Special",
                    description: "Delicious lunch option",
                    price: "125 SEK",
                    category: "🍽️"
                }
            ]
        };
    }
}

class DistrictOneScraper extends BaseScraper {
    constructor() {
        super('DistrictOneScraper');
    }

    async getMenuForDay(day) {
        return {
            day: day,
            items: [
                {
                    name: "Lunch Menu",
                    description: "Fresh daily selection",
                    price: "135 SEK",
                    category: "🥗"
                }
            ]
        };
    }
}

// Add more scrapers as needed
const SCRAPERS = [
    KooperativetScraper,
    DistrictOneScraper
];

const WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"];

async function scrapeForDay(day, refresh = false, cache = {}) {
    console.log(`Scraping lunch menus for ${day.charAt(0).toUpperCase() + day.slice(1)}`);

    const filepath = path.join('data', `lunch_data_${day}.json`);
    
    if (await fs.pathExists(filepath) && !refresh) {
        console.log(`Skipping scraping for ${day} (cached file exists).`);
        return;
    }

    const results = {};

    for (const ScraperClass of SCRAPERS) {
        let attempts = 0;
        const maxRetries = 2;

        while (attempts <= maxRetries) {
            try {
                let scraper;
                if (cache[ScraperClass.name]) {
                    scraper = cache[ScraperClass.name];
                } else {
                    scraper = new ScraperClass();
                    if (typeof scraper.getAllMenus === 'function') {
                        const allMenus = await scraper.getAllMenus();
                        if (allMenus) {
                            cache[ScraperClass.name] = scraper;
                        }
                    }
                }

                let menu;
                const allMenus = await scraper.getAllMenus();
                if (allMenus) {
                    menu = allMenus[day.toLowerCase()];
                    if (!menu) {
                        console.warn(`No menu found in getAllMenus() for ${ScraperClass.name} on ${day}`);
                        break;
                    }
                } else {
                    menu = await scraper.getMenuForDay(day);
                    if (!menu) {
                        console.warn(`No menu found for ${ScraperClass.name} on ${day}`);
                        break;
                    }
                }

                results[ScraperClass.name] = {
                    day: menu.day,
                    items: menu.items.map(item => ({
                        name: item.name || "",
                        category: item.category || "",
                        description: item.description || "",
                        price: item.price || ""
                    }))
                };
                break;

            } catch (error) {
                attempts++;
                console.error(`[${ScraperClass.name}] Error on attempt ${attempts} for ${day}:`, error.message);
                if (attempts > maxRetries) {
                    console.warn(`[${ScraperClass.name}] Gave up after ${maxRetries} retries.`);
                } else {
                    const delay = 2000 + (attempts * 1000);
                    console.log(`[${ScraperClass.name}] Retrying in ${delay/1000} seconds...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
    }

    if (Object.keys(results).length > 0) {
        await fs.ensureDir('data');
        await fs.writeJson(filepath, results, { spaces: 2 });
        console.log(`Wrote lunch data to ${filepath}`);
    } else {
        console.warn(`No results to write for ${day}. Skipping JSON.`);
    }
}

async function main() {
    const args = process.argv.slice(2);
    const isAll = args.includes('--all');
    const refresh = args.includes('--refresh');
    const dayIndex = args.findIndex(arg => arg === '--day');
    const day = dayIndex !== -1 && args[dayIndex + 1] ? args[dayIndex + 1] : getTodayEnglish();

    if (isAll) {
        const weeklyScraperCache = {};
        for (const weekday of WEEKDAYS) {
            await scrapeForDay(weekday, refresh, weeklyScraperCache);
        }
    } else {
        await scrapeForDay(day, refresh);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { scrapeForDay, main };