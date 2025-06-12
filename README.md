# 🍽️ Lindholmen Lunch

A modern web application that aggregates and displays daily lunch menus from restaurants in Lindholmen, Gothenburg. Updated automatically every weekday morning.

## 🌐 Live Website

Visit the live application: **[Your GitHub Pages URL will be here]**

## ✨ Features

- **🔄 Daily Updates**: Automatically scrapes fresh lunch data every weekday morning
- **🌍 Bilingual**: Full English/Swedish language support with localStorage persistence
- **🎲 Random Selection**: "I'm feeling hungry!" button for random restaurant discovery
- **📱 Responsive Design**: Perfect experience on desktop, tablet, and mobile
- **🔗 Restaurant Links**: Direct links to restaurant websites and Google Maps
- **⚡ Fast Loading**: Static site with optimized performance
- **🎨 Modern UI**: Clean, contemporary design with smooth animations

## 🏪 Supported Restaurants

The app currently scrapes lunch menus from 15+ restaurants in Lindholmen:

- Kooperativet
- District One
- Bombay Bistro
- Cuckoo's Nest
- Uni3 World of Food
- Miss F
- Benne Pastabar
- LS Kitchen
- Bistrot
- Mimolett
- Oishii
- Mat & Minnen
- Encounter Asian
- Masala
- Restaurant Pier 11

## 🛠️ Technical Details

### Built With

- **Python 3.9+** - Backend scraping and data processing
- **Selenium** - Web scraping for dynamic content
- **BeautifulSoup** - HTML parsing
- **Jinja2** - Template rendering
- **GitHub Actions** - Automated daily updates
- **GitHub Pages** - Static site hosting

### Architecture

1. **Scrapers** (`scrapers/`) - Individual scrapers for each restaurant
2. **Data Processing** (`utils/`) - Text processing and emoji annotation
3. **Template Rendering** (`templates/`) - HTML generation with Jinja2
4. **Static Output** (`docs/`) - Generated HTML files for GitHub Pages
5. **Automation** (`.github/workflows/`) - Daily scraping and deployment

### Automated Workflow

1. **6:00 AM UTC** (8:00 AM CEST) - GitHub Actions triggers daily
2. **Scraping** - Fetches fresh lunch data from all restaurants
3. **Processing** - Handles long text, emoji annotation, and formatting
4. **Generation** - Creates updated HTML with current data
5. **Deployment** - Publishes to GitHub Pages automatically

## 🚀 Local Development

### Prerequisites

- Python 3.9+
- Chrome browser (for Selenium)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lindholmen_lunch.git
   cd lindholmen_lunch
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the scraper**
   ```bash
   python main.py  # Scrapes today's data
   python main.py --day monday  # Scrape specific day
   python main.py --all  # Scrape all weekdays
   ```

5. **Serve locally**
   ```bash
   cd docs
   python -m http.server 8000
   ```

6. **Visit** [http://localhost:8000](http://iamjaydesign.com/lindholmen-lunch/)

## 📝 Contributing

Contributions are welcome! Here's how you can help:

### Adding New Restaurants

1. Create a new scraper in `scrapers/` following the existing pattern
2. Inherit from `LunchScraper` base class
3. Implement `get_menu_for_day()` and/or `get_all_menus()`
4. Add to `SCRAPERS` list in `main.py`
5. Add restaurant links in `restaurant_links.json`

### Improving Existing Features

- Enhance the UI/UX design
- Add new language support
- Improve error handling
- Optimize performance

### Bug Reports

Please open an issue with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable

## 🔧 Configuration

### Restaurant Links

Edit `restaurant_links.json` to add/update restaurant websites and map links:

```json
{
  "RestaurantName": {
    "url": "https://restaurant-website.com",
    "map": "https://maps.google.com/..."
  }
}
```

### Scheduling

The scraper runs automatically via GitHub Actions. To modify the schedule, edit `.github/workflows/update-and-deploy.yml`:

```yaml
schedule:
  - cron: '0 6 * * 1-5'  # 6 AM UTC, Monday-Friday
```

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 💬 Contact

- **GitHub Issues**: For bug reports and feature requests
- **Email**: fawenah@gmail.com
- **Project**: https://github.com/Fawenah/lindholmen_lunch

---

**Made with ❤️ for the Lindholmen community**
