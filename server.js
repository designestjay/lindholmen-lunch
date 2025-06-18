const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;

// Serve static files from the prototype directory
app.use(express.static(path.join(__dirname, 'prototype')));

// Serve other static files from the root directory
app.use('/docs', express.static(path.join(__dirname, 'docs')));
app.use('/example', express.static(path.join(__dirname, 'example')));

// Default route to serve the prototype
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'prototype', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Serving prototype from /prototype directory`);
});