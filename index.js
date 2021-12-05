const express = require('express');
const { spawn } = require('child_process');

const app = express();

let result = {
    name: 'Sample NGO',
    mail: 'example@gmail.com',
    phone: '123456789',
    address: 'C/Street 1, Barcelona, Spain',
};

app.get('/recommended', (request, response) => {
    const python = spawn('python', ['./python/recommender.py', JSON.stringify(result)]);
    python.stdout.on('data', (data) => {
        result = JSON.parse(data.toString().trim().replace(/'/g, '"'));
    });
    // eslint-disable-next-line no-unused-vars
    python.on('close', (code) => {
        response.json(result);
    });
});

const PORT = 3001;
app.listen(PORT);
