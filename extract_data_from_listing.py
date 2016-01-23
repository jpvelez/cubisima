#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extract data from a listing, export to json."""

import sys
import logging
from bs4 import BeautifulSoup

logging.basicConfig(filename='scraper.log', level=logging.INFO)


def extract_description_fields(description_table):
    """
    Extract property type, number of bed and bath, and other features from
    the property descriptions section of a Cubisima listing.
    """
    # Parse first table row - property type, numbed of bedrooms, bathrooms.
    # String to parse: "<b>Casa</b> 4 cuartos, 2 banos"
    property_type_bed_bath_tag = description_table.find(id='MainPlaceHolder_LabelBasicInfo0')

    print(property_type_bed_bath_tag.text)

    # Get property type.
    # Extract property type from bold section tag text.
    property_type = property_type_bed_bath_tag.b.text

    # Get number of bed and bath.
    num_bed_and_bath_string = property_type_bed_bath_tag.text.replace(property_type, '')
    num_bed = int(num_bed_and_bath_string.split()[0])
    num_bath = int(num_bed_and_bath_string.split()[2])

    # Parse price (second) table field.
    # String to parse: "Precio: 40,000 cuc"
    property_price_tag = description_table.find(id='MainPlaceHolder_LabelPrecio0') 
    propety_price_text = property_price_tag.text.split(u'\xa0')[1]
    if u'-' in propety_price_text:
        property_price = None
    else:
        property_price = float(propety_price_text.replace(',', '')) 



    # Parse meters^2 field.
    # TODO: do this
    # Extract property price from this kind of string: "Construccion: -" or "Construccion: Anos 50"
    # meters_squared_tag = description_table.find(id='MainPlaceHolder_LabelMetros0')
    # meters_squared_text = meters_squared_tag.text.split(u'Construcci\xf3n:')[1]
    # if meters_squared_text == u'\xa0-':
    #   meters_squared = None
    # else:
    #   meters_squared = meters_squared_text


    # Parse published on date field.
    # TODO: do this
    # Extract property price from this kind of string: "Construccion: -" or "Construccion: Anos 50"
    # meters_squared_tag = description_table.find(id='MainPlaceHolder_LabelPublicado0')
    # meters_squared_text = meters_squared_tag.text.split(u'Construcci\xf3n:')[1]
    # if meters_squared_text == u'\xa0-':
    #   meters_squared = None
    # else:
    #   meters_squared = meters_squared_text


    # Parse construction year field.
    # Extract property price from this kind of string: "Construccion: -" or "Construccion: Anos 50"
    construction_year_tag = description_table.find(id='MainPlaceHolder_LabelAnoSF')
    construction_year_text = construction_year_tag.text.split(u'Construcci\xf3n:')[1]
    if construction_year_text == u'\xa0-':
        construction_year = None
    else:
        construction_year = construction_year_text


    # Parse ? field.
    # TODO: implement this conditionally, not all listings have them.
    # property_type_bed_bath_tag = description_table.find(id='MainPlaceHolder_LabelCantPers0')

    # Parse ? field.
    # TODO: implement this conditionally, not all listings have them.
    # property_type_bed_bath_tag = description_table.find(id='MainPlaceHolder_LabelEstado0')

    # Parse location field.
    # Extract property price from this kind of string: "en Habana Vieja, La Habana"
    location_tag = description_table.find(id='MainPlaceHolder_LabelDireccion0')
    location_text = location_tag.text.split(u'Direcci\xf3n:\xa0')[1].strip().split(' en ')
    if len(location_text) > 1:
        address = location_text[0]
        location = location_text[1]
    else:
        address = None
        location = location_text[0].replace('en ', '')

    print(location)
    print(address)

    # Parse "near to" table field.
    # Extract property price from this kind of string: "Cerca De: "
    near_to_tag = description_table.find(id='MainPlaceHolder_LabelCercaDe0')
    near_to_text = near_to_tag.text.split(u'De:\xa0')[1]
    if near_to_text == '':
        near_to = None
    else:
        near_to = near_to_text

    # Parse modified? field.
    # TODO: implement this conditionally, not all listings have them.
    # tk = description_table.find(id='TK')

    # Parse free text "observations" field.
    # Extract property price from this kind of string: "TK"
    notes_tag = description_table.find(id='MainPlaceHolder_LabelObservaciones0')
    notes = notes_tag.text.split(u'Observaciones:\xa0')[1]

    # Save out features.
    description_fields = {}
    description_fields['property_type'] = property_type
    description_fields['num_bed'] = num_bed
    description_fields['num_bath'] = num_bath
    description_fields['property_price'] = property_price
    # meters squared?
    description_fields['construction_year'] = construction_year
    description_fields['address'] = address
    description_fields['location'] = location
    description_fields['near_to'] = near_to
    # pub date?
    description_fields['notes'] = notes

    return description_fields


def is_checked(checkbox_field):
    """
    Determine whether property has a given amenity by checking whether
    the given checkbox field in the amenities table has a "checked.png"
    or "notchecked.png" graphic.
    """
    if 'http://images.cubisima.com/checked.png' in checkbox_field.img['src']:
        return True
    else:
        return False


def extract_characteristics_fields(property_characteristics_table):

    # Loop through amenity checkbox table elements.
    property_characteristics_fields = {}
    for checkbox_field in property_characteristics_table.find_all('td'):

        # Get name of the amenity.
        amenity_name = checkbox_field.text.strip()

        # Determine whether property has the amenity.
        if is_checked(checkbox_field):
            property_characteristics_fields[amenity_name] = True
        else:
            property_characteristics_fields[amenity_name] = False

    return property_characteristics_fields

def extract_contact_fields(property_contact_table):
    # Parse contact name field.
    contact_name_tag = property_contact_table.find(id='MainPlaceHolder_LabelContacto0')
    contact_name = contact_name_tag.text.split(u'Contactar a:\xa0')[1].strip()

    # Parse contact number field.
    contact_phone_tag = property_contact_table.find(id='MainPlaceHolder_ImageTelefono0')
    if contact_phone_tag is None:
        phone_number = None
    else:
        phone_number = contact_phone_tag['alt']

    # Parse mobile phone field. 
    contact_mobile_tag = property_contact_table.find(id='MainPlaceHolder_ImageMovil0')
    if contact_mobile_tag is None:
        mobile_number = None
    else:
        mobile_number = contact_mobile_tag['alt']

    # Parse "other info" field.
    # It looks like this: "Otra informacion: -" or "Otra informacion: <free text>"
    other_info_tag = property_contact_table.find(id='MainPlaceHolder_LabelOtraInfo0')
    print(other_info_tag)
    if other_info_tag is None:
        other_info = None
    else:
        other_info_text = other_info_tag.text.split(u'Otra informaci\xf3n:')[1]
        if other_info_text == u'\xa0-':
            other_info = None
        else:
            other_info = other_info_text


    property_contact_fields = {}
    property_contact_fields['contact_name'] = contact_name
    property_contact_fields['phone_number'] = phone_number
    property_contact_fields['mobile_number'] = mobile_number
    property_contact_fields['other_info'] = other_info
    return property_contact_fields

def main(listings_dir, listing_file):
    listings_dir = 'raw/listings'
    listing_file = 'http://www.cubisima.com/casas/17000-cuc-apartamento-de-2-cuartos-en-la-habana-cerro!56458.htm'.replace('/','_')
    listing = BeautifulSoup(open(listings_dir + '/' + listing_file))
    print(listing_file)

    # Extract data fields from the "DESCRIPCIÓN DE LA VIVIENDA" table.
    # Example: http://www.cubisima.com/casas/17000-cuc-apartamento-de-2-cuartos-en-la-habana-cerro!56458.htm
    # This left-hard table provides the overview description of the property:
    # number of rooms, price, square footage, location, etc.
    description_table = listing.find(id='casa_detalles_sinfoto_izquierda')
    description_fields = extract_description_fields(description_table)

    print(description_fields)

    # Extract data fields from the "CARACTERÍSTICAS" table.
    # This center table is details property amenities using checkboxes:
    # whether property has living room, dining room, telephone, water, etc.
    characteristics_table = listing.find(id='casa_detalles_sinfoto_centro')
    characteristics_fields = extract_characteristics_fields(characteristics_table)
    print(characteristics_fields)

    # Extract data fields from the "DATOS DE LA PERSONA A CONTACTAR" table.
    # This right hand table has the contact info for the listing:
    # Lister name, contact phone number, cellphone, etc.
    contact_table = listing.find(id='casa_detalles_sinfoto_derecha')
    contact_fields = extract_contact_fields(contact_table)
    print(contact_fields)

    # Extract number of the listing.
    listing_number = listing_file.split('!')[1].replace('.htm', '')

    # Assemble final feature vector for property listing.
    features = {}
    features['listing_number'] = listing_number
    features.update(description_fields)
    features.update(characteristics_fields)
    features.update(contact_fields)

    print(features)

    for k, v in features.items():
        print '%s: %s' % (k, v)

    # TO DO

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
