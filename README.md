# PWP SPRING 2021
# Nearby Events booking

#Package requirements
The required packages to be installed are found in the requirements.txt

# Setting the environment before running
You must set the correct environment variables before running:

    set FLASK_APP=nearbyEvents

    set FLASK_ENV=development

With linux change "set" to "export"
# How to initialize and populate test data to database
When running first time, the database must be initialized with:

    flask initializeDatabase

It is possible to populate the database with test data:

    flask generateTestDatabase

# Database testing
The project includes test functions for the database in the tests folder. This is run using 
    pytest.

You can run the tests by just using the command:

    pytest

# Group information
* Student 1. Mitja Kärki mitja.karki ät hotmail dot com
* Student 2. Antti Keränen anttikeranen ät hotmail dot com
* Student 3. Eetu Laukka eetu.laukka ät student dot oulu dot fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__


