#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extract data from a listing, export to json."""

import sys
import logging
from bs4 import BeautifulSoup
import csv

logging.basicConfig(filename='scraper.log', level=logging.INFO)


def get_pub_date_if_modified(listing):
    '''
    Helper function to get pub date in rare case
    that modification date is present.
    Basically a necessary workaround due to poorly formatted html.
    '''
    for text in listing.find_all(text=True):
        if 'Publicado:\xa0' in text:  # Should catch all cases.
            return text.split()[1]


def get_field_from_tag_id(table, tag_id, listing_has_photos):
    # Listings with photos have same table tag ids,
    # save for no 0 at the end. ¯\_(ツ)_/¯
    if listing_has_photos:
        tag_id = tag_id.replace('0', '')
    tag = table.find(id=tag_id)
    # Most table rows separate field name from field value with a '\xa0' char,
    # some kind of unicode whitespace. Split on it to get field value.
    tag_text = tag.text.split(u'\xa0')[1]
    # Missing values are usually represented with '-' strings.
    if ('-' in tag_text or tag_text == '') \
       and 'Observaciones' not in tag_id:
        return None
    else:
        return tag_text


def extract_description_fields(listing):
    """
    Extract property type, number of bed and bath, and other features from
    the property descriptions section of a Cubisima listing.

    Note: MainPlaceHolder_LabelCantPers0 and MainPlaceHolder_LabelEstado0
    tags appear to always be empty.
    """
    description_table = listing.find(id='casa_detalles_sinfoto_izquierda')
    listing_has_photos = False

    # TODO: SHOULD THIS BREAK LOUDLY IF IT CAN'T FIND TAGS OR TEXT?
    # Parse first table row - property type, numbed of bedrooms, bathrooms.
    # Text to parse: "<b>Casa</b> 4 cuartos, 2 banos"
    property_type_bed_bath_tag = description_table.find(id='MainPlaceHolder_LabelBasicInfo0')

    # Get property type.
    # Extract property type from bold section tag text.
    property_type = property_type_bed_bath_tag.b.text

    # Get number of bed and bath.
    num_bed_and_bath_string = property_type_bed_bath_tag.text.replace(property_type, '')
    num_bed = int(num_bed_and_bath_string.split()[0])
    num_bath = int(num_bed_and_bath_string.split()[2])

    # Parse price (second) table field.
    # Text to parse: "Precio: 40,000 cuc"
    price_id = 'MainPlaceHolder_LabelPrecio0'
    price = get_field_from_tag_id(description_table, price_id, listing_has_photos)

    # Parse meters² field.
    # Text to parse: "Metros²: 235"
    # meters_squared_tag = description_table.find(id='MainPlaceHolder_LabelMetros0')
    # meters_squared_text = meters_squared_tag.text.split('\xa0')[1]
    # if meters_squared_text == '-':
    #    meters_squared = None
    # else:
    #    meters_squared = meters_squared_text
    meters_squared_id = 'MainPlaceHolder_LabelMetros0'
    meters_squared = get_field_from_tag_id(description_table, meters_squared_id, listing_has_photos)

    # Parse construction era field.
    # Text to parse: "Construccion: Anos 50"
    # construction_era_tag = description_table.find(id='MainPlaceHolder_LabelAnoSF')
    # construction_era_text = construction_era_tag.text.split('\xa0')[1]
    # if construction_era_text == '-':
    #     construction_era = None
    # else:
    #     construction_era = construction_era_text
    construction_era_id = 'MainPlaceHolder_LabelAnoSF'
    construction_era = get_field_from_tag_id(description_table, construction_era_id, listing_has_photos)

    # Parse location field.
    # Extract property price from this kind of string: "en Habana Vieja, La Habana"
    # location_tag = description_table.find(id='MainPlaceHolder_LabelDireccion0')
    # location_text = location_tag.text.split('\xa0')[1]
    # if location_text == '-':
    #    location = None
    # else:
    #    location = location_text
    location_id = 'MainPlaceHolder_LabelDireccion0'
    location = get_field_from_tag_id(description_table, location_id, listing_has_photos)

    # Extract "near to" field.
    # Text to parse: "Cerca De: "
    # near_to_tag = description_table.find(id='MainPlaceHolder_LabelCercaDe0')
    # near_to_text = near_to_tag.text.split('\xa0')[1]
    # if near_to_text == '':
    #     near_to = None
    # else:
    #     near_to = near_to_text
    near_to_id = 'MainPlaceHolder_LabelCercaDe0'
    near_to = get_field_from_tag_id(description_table, near_to_id, listing_has_photos)

    # Parse published on date and optional modified on fields.
    date_id = 'MainPlaceHolder_LabelPublicado0'
    date_field = get_field_from_tag_id(description_table, date_id, listing_has_photos)
    # In most cases, date_field is the publication date.
    # However, when "Modificado": field present, a poorly formatted </br> tag
    # somehow eliminates "Publicado: <date>" text.
    # date_field actually catches the modification date,
    # and publication date must be plucked from raw html, not parsed tree.
    modified = False
    mod_date = None
    pub_date = date_field
    if 'Modificado:' in listing.text:
        modified = True
        mod_date = date_field
        pub_date = get_pub_date_if_modified(listing)

    # Parse free text "observaciones" field.
    # notes_tag = description_table.find(id='MainPlaceHolder_LabelObservaciones0')
    # notes = notes_tag.text.split('\xa0')[1]
    notes_id = 'MainPlaceHolder_LabelObservaciones0'
    notes = get_field_from_tag_id(description_table, notes_id, listing_has_photos)

    # Save out features.
    description_fields = {}
    description_fields['property_type'] = property_type
    description_fields['num_bed'] = num_bed
    description_fields['num_bath'] = num_bath
    description_fields['price'] = price
    description_fields['meters_squared'] = meters_squared
    description_fields['construction_era'] = construction_era
    description_fields['location'] = location
    description_fields['near_to'] = near_to
    description_fields['pub_date'] = pub_date
    description_fields['mod_date'] = mod_date
    description_fields['modified'] = modified
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


def extract_characteristics_fields(listing):

    characteristics_table = listing.find(id='casa_detalles_sinfoto_centro')
    # Loop through amenity checkbox table elements.
    characteristics_fields = {}
    for checkbox_field in characteristics_table.find_all('td'):

        # Get name of the amenity.
        amenity_name = checkbox_field.text.strip()

        # Determine whether property has the amenity.
        if is_checked(checkbox_field):
            characteristics_fields[amenity_name] = True
        else:
            characteristics_fields[amenity_name] = False

    return characteristics_fields


def extract_contact_fields(listing):

    contact_table = listing.find(id='casa_detalles_sinfoto_derecha')
    # Parse contact name field.
    contact_name_tag = contact_table.find(id='MainPlaceHolder_LabelContacto0')
    contact_name = contact_name_tag.text.split(u'Contactar a:\xa0')[1].strip()

    # Parse contact number field.
    contact_phone_tag = contact_table.find(id='MainPlaceHolder_ImageTelefono0')
    if contact_phone_tag is None:
        phone_number = None
    else:
        phone_number = contact_phone_tag['alt']

    # Parse mobile phone field.
    contact_mobile_tag = contact_table.find(id='MainPlaceHolder_ImageMovil0')
    if contact_mobile_tag is None:
        mobile_number = None
    else:
        mobile_number = contact_mobile_tag['alt']

    # Parse "other info" field.
    # It looks like this: "Otra informacion: -" or "Otra informacion: <free text>"
    other_info_tag = contact_table.find(id='MainPlaceHolder_LabelOtraInfo0')
    if other_info_tag is None:
        other_info = None
    else:
        other_info_text = other_info_tag.text.split(u'Otra informaci\xf3n:')[1]
        if other_info_text == u'\xa0-':
            other_info = None
        else:
            other_info = other_info_text

    contact_fields = {}
    contact_fields['contact_name'] = contact_name
    contact_fields['phone_number'] = phone_number
    contact_fields['mobile_number'] = mobile_number
    contact_fields['other_info'] = other_info
    return contact_fields


def extract_listing_fields(listing):
    # Extract data fields from the "DESCRIPCIÓN DE LA VIVIENDA" table.
    # Example: http://www.cubisima.com/casas/17000-cuc-apartamento-de-2-cuartos-en-la-habana-cerro!56458.htm
    # This left-hard table provides the overview description of the property:
    # number of rooms, price, square footage, location, etc.
    description_fields = extract_description_fields(listing)

    # Extract data fields from the "CARACTERÍSTICAS" table.
    # This center table is details property amenities using checkboxes:
    # whether property has living room, dining room, telephone, water, etc.
    characteristics_fields = extract_characteristics_fields(listing)

    # Extract data fields from the "DATOS DE LA PERSONA A CONTACTAR" table.
    # This right hand table has the contact info for the listing:
    # Lister name, contact phone number, cellphone, etc.
    contact_fields = extract_contact_fields(listing)

    # Extract unique id of the listing.
    listing_id = listing_file.split('!')[1].replace('.htm', '')

    listing_fields = {'id': listing_id, **description_fields, **characteristics_fields, **contact_fields}

    return listing_fields

def main(listings_dir, listing_file):

    # listings_dir = 'raw/listings'
    # listing_file = 'http:__www.cubisima.com_casas_vendo-casa-planta-baja-en-biplanta-reparto-sevillano-llamar-6405034!210.htm'
    listing = BeautifulSoup(open(listings_dir + '/' + listing_file, mode='r',
                                 encoding='utf-8'), "html.parser")

    fields = extract_listing_fields(listing)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
