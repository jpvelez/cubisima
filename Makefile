# Run this file to scrape all real estate listings on Cubisima.com.

# Define data dirs
LISTING_PAGES_DIR="raw/listing_pages/"
LISTINGS_DIR="raw/listings/"

# Get real estate listing pages from Cubisima.com
raw/listing_pages/complete:
	python get_listing_pages.py $(LISTING_PAGES_DIR)
	touch $@

# Get individual real estate listings.
raw/listings/complete: raw/listing_pages/complete
	mkdir -p $(LISTINGS_DIR)
	ls $(LISTING_PAGES_DIR) | xargs python get_listings_from_listing_page.py $(LISTING_PAGES_DIR) $(LISTINGS_DIR) && touch $@

# Turn listing documents into single csv dataset.
listings.csv: raw/listings/complete
	# Output csv headers first.
	find $(LISTINGS_DIR) -name 'http*' | head -n1 | xargs -n1 python extract_data_from_listing.py header > $@
	# Parse listings in parallel. Each listing becomes csv row, appended to single csv file.
	find $(LISTINGS_DIR) -name 'http*' | parallel --bibtex -n1 python extract_data_from_listing.py fields >> $@
