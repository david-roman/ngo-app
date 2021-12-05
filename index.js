const express = require('express');

const app = express();

const result = {
    name: 'Sample NGO',
    mail: 'example@gmail.com',
    phone: '123456789',
    address: 'C/Street 1, Barcelona, Spain',
};

app.get('/recommended ', (request, response) => {
    response.json(result);
});

const PORT = 3001;
app.listen(PORT);
