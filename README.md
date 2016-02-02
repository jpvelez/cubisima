# Cubisima

A Quantitative Peek At Cuba's (Re-)Emerging Real Estate Market. To read the analysis, [click here](https://github.com/jpvelez/cubisima/blob/master/notebooks/cubisima_analysis.ipynb).

## Installation
You'll need make, python 3.5, and the anaconda package manager installed. To install required python packages, simply type  `conda create --name cubisima --file requirements.txt`.

## Usage
To start the scraper, run `make raw/listings/complete.` This can take day, so is best accomplished on a server, inside a tmux session.

Once all property listings are downloaded, type `make data/listings.csv` to parse listings and create the dataset for analysis.

The data is analyzed in Jupyter notebooks. To edit the notebook, type `jupter notebook`. To view it, [click here](https://github.com/jpvelez/cubisima/blob/master/notebooks/cubisima_analysis.ipynb).

