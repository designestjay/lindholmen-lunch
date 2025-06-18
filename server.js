const express = require('express');
const path = require('path');
const { scrapeForDay } = require('./scrape');
const { generateIndexPage } = require('./generate');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from docs directory
app.use(express.static('docs'));
app.use(express.static('.'));

// API endpoints
app.get('/api/scrape/:day', async (req, res) => {
    try {
        const { day } = req.params;
        const refresh = req.query.refresh === 'true';
        
        await scrapeForDay(day, refresh);
        res.json({ success: true, message: `Scraped data for ${day}` });
    } catch (error) {
        console.error('Scrape error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/generate', async (req, res) => {
    try {
        await generateIndexPage();
        res.json({ success: true, message: 'Generated index page' });
    } catch (error) {
        console.error('Generate error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'docs', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    
    // Generate initial page
    generateIndexPage().catch(console.error);
});