# Cubisima

Analysis of Cuba's real estate market, based on real estate listing data from [cubisima.com](http://cubisima.com).

Right now, there's just a scraper to extract data from the site.

## Installation
You'll need drake and python installed. Create an AWS micro instance, scp up `boostrap.sh`, ssh in and run `chmod 777 bootsrap.sh`, and run the file to set up the production environment.

## Usage
While in the project directory, run `drake` in a tmux session to start the scraper.

## To-do
* Extract data from scraped pages
* Analyze data
* Profit