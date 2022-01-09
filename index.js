const express = require('express');
const { spawn } = require('child_process');
const cors = require('cors');

const app = express();

app.use(cors());
app.use(express.json());

app.post('/recommended', (request, response) => {
    const requirements = request.body;
    const returnVal = [];
    const python = spawn('python', ['./python/recommender/Recommender.py', JSON.stringify(requirements)]);
    python.stdout.on('data', (data) => {
        returnVal.push(JSON.parse(data.toString()
            .replace(/{'/g, '{"')
            .replace(/':/g, '":')
            .replace(/: '/g, ': "')
            .replace(/, '/g, ', "')
            .replace(/', /g, '", ')
            .replace(/'}/g, '"}')
            .replace(/None/g, 'null')
            .trim()));
    });
    python.on('close', () => {
        response.json(returnVal);
    });
});

const PORT = 3002;
app.listen(PORT);
