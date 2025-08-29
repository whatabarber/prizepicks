export default function handler(req, res) {
  // This will serve your JSON files
  const fs = require('fs');
  const path = require('path');
  
  const { filename } = req.query;
  
  if (!filename) {
    return res.status(400).json({ error: 'Filename required' });
  }
  
  try {
    const filePath = path.join(process.cwd(), 'data', filename);
    const data = fs.readFileSync(filePath, 'utf8');
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    res.status(200).send(data);
  } catch (error) {
    res.status(404).json({ error: 'File not found' });
  }
}