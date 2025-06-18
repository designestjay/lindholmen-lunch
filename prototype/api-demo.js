// Location-Based Lunch Service API Demo
// This demonstrates the backend architecture for the service

class LunchFinderAPI {
    constructor() {
        this.apiKey = 'demo_api_key';
        this.baseUrl = 'https://api.lunchfinder.com/v1';
        this.cache = new Map();
    }

    // Core API Methods

    /**
     * Detect restaurants near a location
     * @param {Object} location - {lat, lng}
     * @param {Object} options - Search options
     * @returns {Promise<Array>} List of restaurants
     */
    async findRestaurants(location, options = {}) {
        const {
            radius = 1000,
            cuisine = null,
            priceLevel = null,
            openNow = false,
            limit = 20
        } = options;

        const cacheKey = `restaurants_${location.lat}_${location.lng}_${radius}_${cuisine}_${priceLevel}_${openNow}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            // Simulate API call to Google Places
            const placesData = await this.searchGooglePlaces(location, radius, 'restaurant');
            
            // Enrich with menu data
            const enrichedRestaurants = await Promise.all(
                placesData.map(place => this.enrichRestaurantData(place))
            );

            // Apply filters
            let filtered = enrichedRestaurants.filter(restaurant => {
                if (cuisine && restaurant.cuisine !== cuisine) return false;
                if (priceLevel && restaurant.priceLevel !== priceLevel) return false;
                if (openNow && !restaurant.isOpen) return false;
                return true;
            });

            // Sort by distance and rating
            filtered = filtered
                .sort((a, b) => a.distance - b.distance)
                .slice(0, limit);

            // Cache results for 15 minutes
            this.cache.set(cacheKey, filtered);
            setTimeout(() => this.cache.delete(cacheKey), 15 * 60 * 1000);

            return filtered;

        } catch (error) {
            console.error('Error finding restaurants:', error);
            throw new Error('Failed to find restaurants');
        }
    }

    /**
     * Get detailed menu for a restaurant
     * @param {string} restaurantId - Restaurant identifier
     * @returns {Promise<Object>} Menu data
     */
    async getRestaurantMenu(restaurantId) {
        const cacheKey = `menu_${restaurantId}`;
        
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            // Get restaurant details
            const restaurant = await this.getRestaurantDetails(restaurantId);
            
            // Scrape menu from website
            const menuData = await this.scrapeRestaurantMenu(restaurant.website);
            
            // Process and categorize menu items
            const processedMenu = await this.processMenuData(menuData);
            
            // Cache for 1 hour
            this.cache.set(cacheKey, processedMenu);
            setTimeout(() => this.cache.delete(cacheKey), 60 * 60 * 1000);
            
            return processedMenu;

        } catch (error) {
            console.error('Error getting menu:', error);
            return this.getFallbackMenu(restaurantId);
        }
    }

    /**
     * Search Google Places API
     * @private
     */
    async searchGooglePlaces(location, radius, type) {
        // Simulate Google Places API call
        await this.delay(500);
        
        const mockPlaces = [
            {
                place_id: 'place_1',
                name: 'Bella Vista Italian',
                types: ['restaurant', 'food'],
                rating: 4.5,
                price_level: 2,
                geometry: {
                    location: {
                        lat: location.lat + (Math.random() - 0.5) * 0.01,
                        lng: location.lng + (Math.random() - 0.5) * 0.01
                    }
                },
                opening_hours: {
                    open_now: Math.random() > 0.3
                },
                vicinity: '123 Main Street',
                website: 'https://bellavista.com'
            },
            // Add more mock places...
        ];

        return mockPlaces;
    }

    /**
     * Enrich restaurant data with additional information
     * @private
     */
    async enrichRestaurantData(place) {
        const distance = this.calculateDistance(
            { lat: place.geometry.location.lat, lng: place.geometry.location.lng },
            this.userLocation
        );

        return {
            id: place.place_id,
            name: place.name,
            cuisine: this.detectCuisineType(place.name, place.types),
            rating: place.rating || 0,
            priceLevel: place.price_level || 1,
            distance: distance,
            isOpen: place.opening_hours?.open_now || false,
            address: place.vicinity,
            website: place.website,
            location: place.geometry.location,
            hasMenu: !!place.website,
            lastMenuUpdate: new Date().toISOString()
        };
    }

    /**
     * Scrape restaurant menu from website
     * @private
     */
    async scrapeRestaurantMenu(website) {
        if (!website) return null;

        try {
            // Simulate web scraping
            await this.delay(1000);
            
            // In real implementation, this would:
            // 1. Fetch the website
            // 2. Identify menu pages
            // 3. Extract menu items using AI/ML
            // 4. Handle different website structures
            
            return {
                items: [
                    {
                        name: 'Margherita Pizza',
                        description: 'Fresh tomato sauce, mozzarella, basil',
                        price: '$14.99',
                        category: 'Pizza',
                        dietary: ['vegetarian'],
                        image: 'https://example.com/pizza.jpg'
                    },
                    // More items...
                ],
                lastUpdated: new Date().toISOString(),
                source: 'website_scraping'
            };

        } catch (error) {
            console.error('Scraping error:', error);
            return null;
        }
    }

    /**
     * Process and categorize menu data
     * @private
     */
    async processMenuData(menuData) {
        if (!menuData) return null;

        // AI-powered menu processing would happen here:
        // 1. Categorize dishes
        // 2. Detect dietary restrictions
        // 3. Normalize prices
        // 4. Extract ingredients
        // 5. Generate tags

        return {
            ...menuData,
            categories: this.categorizeMenuItems(menuData.items),
            dietaryOptions: this.extractDietaryOptions(menuData.items),
            priceRange: this.calculatePriceRange(menuData.items),
            processed: true
        };
    }

    /**
     * Utility methods
     */
    calculateDistance(point1, point2) {
        const R = 6371e3; // Earth's radius in meters
        const φ1 = point1.lat * Math.PI/180;
        const φ2 = point2.lat * Math.PI/180;
        const Δφ = (point2.lat-point1.lat) * Math.PI/180;
        const Δλ = (point2.lng-point1.lng) * Math.PI/180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c;
    }

    detectCuisineType(name, types) {
        const cuisineKeywords = {
            italian: ['pizza', 'pasta', 'italian', 'bella', 'mama', 'nonna'],
            asian: ['sushi', 'asian', 'chinese', 'thai', 'japanese', 'dragon', 'bamboo'],
            mexican: ['mexican', 'taco', 'burrito', 'cantina', 'casa', 'el'],
            indian: ['indian', 'curry', 'tandoori', 'spice', 'taj', 'mumbai'],
            american: ['burger', 'grill', 'diner', 'american', 'bbq']
        };

        const nameLower = name.toLowerCase();
        for (const [cuisine, keywords] of Object.entries(cuisineKeywords)) {
            if (keywords.some(keyword => nameLower.includes(keyword))) {
                return cuisine;
            }
        }

        return 'general';
    }

    categorizeMenuItems(items) {
        // AI categorization logic would go here
        return ['appetizers', 'mains', 'desserts', 'beverages'];
    }

    extractDietaryOptions(items) {
        // Extract dietary information
        return ['vegetarian', 'vegan', 'gluten-free'];
    }

    calculatePriceRange(items) {
        const prices = items
            .map(item => parseFloat(item.price.replace(/[^0-9.]/g, '')))
            .filter(price => !isNaN(price));
        
        return {
            min: Math.min(...prices),
            max: Math.max(...prices),
            average: prices.reduce((a, b) => a + b, 0) / prices.length
        };
    }

    getFallbackMenu(restaurantId) {
        // Return basic menu from database or third-party source
        return {
            items: [
                { name: 'Daily Special', price: 'Market Price', category: 'Specials' }
            ],
            source: 'fallback',
            lastUpdated: new Date().toISOString()
        };
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage Example
async function demonstrateAPI() {
    const api = new LunchFinderAPI();
    
    // User's location (e.g., Gothenburg)
    const userLocation = { lat: 57.7089, lng: 11.9746 };
    
    try {
        // Find restaurants
        console.log('Finding restaurants...');
        const restaurants = await api.findRestaurants(userLocation, {
            radius: 1000,
            cuisine: 'italian',
            openNow: true
        });
        
        console.log(`Found ${restaurants.length} restaurants:`, restaurants);
        
        // Get menu for first restaurant
        if (restaurants.length > 0) {
            console.log('Getting menu...');
            const menu = await api.getRestaurantMenu(restaurants[0].id);
            console.log('Menu:', menu);
        }
        
    } catch (error) {
        console.error('API Demo Error:', error);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LunchFinderAPI;
}