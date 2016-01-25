#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extract data from a listing, export to json."""

import sys
import logging
from bs4 import BeautifulSoup
import csv

logging.basicConfig(filename='scraper.log', level=logging.INFO)


def strip_dirty_html(listing_text):
    '''
    When listing if modified, an extra <br> is added to the
    MainPlaceHolder_LabelPublicado tag. This <br> silently breaks
    BeautifulSoup's parser - Publishing date and Observations are simply cut
    out of the description table representation.
    By replacing this stray <br> tag, we avoid this problem.'''
    return listing_text.replace('</br>Publicado', '~Publicado')


def get_field_from_tag_id(table, tag_id):
    '''Helper function to get data field from tag id.'''
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


def extract_description_fields(listing, page_type):
    """
    Extract property type, number of bed and bath, and other features from
    the property descriptions section of a Cubisima listing.

    Note: MainPlaceHolder_LabelCantPers* and MainPlaceHolder_LabelEstado*
    tags appear to always be empty.
    """
    # Change description table and data field tags
    # ids based on the HTML template in use.
    if page_type == 'no-photos':
        table_id = 'casa_detalles_sinfoto_izquierda'
        # In template for listings with no photos,
        # all tag ids randomly have a 0 at the end
        # - except for construction_era, which has it's own modifier.
        tag_text_modifier = '0'
        const_era_tag_text_modifier = 'SF'
    elif page_type == 'photos':
        table_id = 'renta_detalles_confoto_izquierda'
        # Listings with photos have same table tag ids as those without,
        # save for no 0 at the end. ¯\_(ツ)_/¯
        tag_text_modifier = ''
        const_era_tag_text_modifier = 'F'
    elif page_type == 'certified':
        table_id = 'certificada_detalles_izquierda'
        tag_text_modifier = 'C'
        const_era_tag_text_modifier = 'C'

    # This div contains all description table fields.
    description_table = listing.find(id=table_id)

    # TODO: SHOULD THIS BREAK LOUDLY IF IT CAN'T FIND TAGS OR TEXT?
    # Parse first table row - property type, numbed of bedrooms, bathrooms.
    # Text to parse: "<b>Casa</b> 4 cuartos, 2 banos"
    property_id = 'MainPlaceHolder_LabelBasicInfo%s' % tag_text_modifier
    property_type_bed_bath_tag = description_table.find(id=property_id)

    # Get property type.
    # Extract property type from bold section tag text.
    property_type = property_type_bed_bath_tag.b.text

    # Get number of bed and bath.
    num_bed_and_bath_string = property_type_bed_bath_tag.text.replace(property_type, '')
    num_bed = int(num_bed_and_bath_string.split()[0])
    num_bath = int(num_bed_and_bath_string.split()[2])

    # Parse price (second) table field.
    # Text to parse: "Precio: 40,000 cuc"
    price_id = 'MainPlaceHolder_LabelPrecio%s' % tag_text_modifier
    price = get_field_from_tag_id(description_table, price_id)

    # Parse meters² field.
    # Text to parse: "Metros²: 235"
    meters_squared_id = 'MainPlaceHolder_LabelMetros%s' % tag_text_modifier
    meters_squared = get_field_from_tag_id(description_table, meters_squared_id)

    # Parse construction era field.
    construction_era_id = 'MainPlaceHolder_LabelAno%s' % const_era_tag_text_modifier
    construction_era = get_field_from_tag_id(description_table, construction_era_id)

    # Parse location field.
    location_id = 'MainPlaceHolder_LabelDireccion%s' % tag_text_modifier
    location = get_field_from_tag_id(description_table, location_id)

    # Extract "near to" field.
    # Text to parse: "Cerca De: "
    near_to_id = 'MainPlaceHolder_LabelCercaDe%s' % tag_text_modifier
    near_to = get_field_from_tag_id(description_table, near_to_id)

    # Parse published on date and optional modified on fields.
    # Note: this section wrestles with badly formatted html, and is very brittle.
    date_id = 'MainPlaceHolder_LabelPublicado%s' % tag_text_modifier
    if 'Modificado:' in listing.text:
        modified = True
        tag_text = description_table.find(id=date_id).text
        # Note: this only works if strip_dirty_html successfully replaces <br>
        # that appears after the modification date with ~ char.
        mod_date = tag_text.split('~')[0].split('\xa0')[1]
        pub_date = tag_text.split('~')[1].split('\xa0')[1]
    else:
        modified = False
        mod_date = None
        pub_date = get_field_from_tag_id(description_table, date_id)

    # Parse free text "observaciones" field.
    notes_id = 'MainPlaceHolder_LabelObservaciones%s' % tag_text_modifier
    notes = get_field_from_tag_id(description_table, notes_id)

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


def extract_characteristics_fields(listing, page_type):
    if page_type == 'photos':
        table_id = 'renta_detalles_confoto_derecha'
    elif page_type == 'no-photos':
        table_id = 'casa_detalles_sinfoto_centro'
    characteristics_table = listing.find(id=table_id)
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


def extract_contact_fields(listing, page_type):
    if page_type == 'photos':
        table_id = 'renta_detalles_confoto_derecha'
        tag_text_modifier = ''
    elif page_type == 'no-photos':
        table_id = 'casa_detalles_sinfoto_derecha'
        tag_text_modifier = '0'

    contact_table = listing.find(id=table_id)

    # Parse contact name field.
    contact_name_id = 'MainPlaceHolder_LabelContacto%s' % tag_text_modifier
    contact_name = get_field_from_tag_id(contact_table, contact_name_id)

    # Parse contact number field.
    # Note: phone numbers are displayed as images,
    # but actual number is stored in photo's alt attribute.
    contact_phone_tag = contact_table.find(id='MainPlaceHolder_ImageTelefono%s' % tag_text_modifier)
    if contact_phone_tag is None:
        phone_number = None
    else:
        phone_number = contact_phone_tag['alt']

    # Parse mobile phone field.
    contact_mobile_tag = contact_table.find(id='MainPlaceHolder_ImageMovil%s' % tag_text_modifier)
    if contact_mobile_tag is None:
        mobile_number = None
    else:
        mobile_number = contact_mobile_tag['alt']

    # Parse "other info" field.
    # It looks like this: "Otra informacion: -" or "Otra informacion: <free text>"
    other_info_id = 'MainPlaceHolder_LabelOtraInfo%s' % tag_text_modifier
    other_info = get_field_from_tag_id(contact_table, other_info_id)

    contact_fields = {}
    contact_fields['contact_name'] = contact_name
    contact_fields['phone_number'] = phone_number
    contact_fields['mobile_number'] = mobile_number
    contact_fields['other_info'] = other_info
    return contact_fields


def find_page_type(listing):
    '''
    Infer HTML template used on page - certified listings, listing with photos,
    listing without photos - based on on presence of tags that should only
    appear under each template.
    '''
    certified_tag = listing.find(id='MainPlaceHolder_TableCertificada')
    if certified_tag is not None:
        return 'certified'
    else:
        photo_tag = listing.find(id='renta_detalles_confoto_izquierda')
        if photo_tag is None:
            return 'no-photos'
        else:
            return 'photos'

def extract_listing_fields(listing_file):
    # Open and parse listing html into tree.
    listing_text = open(listing_file, mode='r', encoding='utf-8').read()
    listing_text = strip_dirty_html(listing_text)
    listing = BeautifulSoup(listing_text, "html.parser")

    # If listing is 'cerfified', or has photos, the ids of the html tags
    # where the data fields fields change.
    page_type = find_page_type(listing)

    # Extract data fields from the "DESCRIPCIÓN DE LA VIVIENDA" table.
    # Example: http://www.cubisima.com/casas/17000-cuc-apartamento-de-2-cuartos-en-la-habana-cerro!56458.htm
    # This left-hard table provides the overview description of the property:
    # number of rooms, price, square footage, location, etc.
    description_fields = extract_description_fields(listing, page_type)

    # Extract data fields from the "CARACTERÍSTICAS" table.
    # This center table is details property amenities using checkboxes:
    # whether property has living room, dining room, telephone, water, etc.
    characteristics_fields = extract_characteristics_fields(listing, page_type)

    # Extract data fields from the "DATOS DE LA PERSONA A CONTACTAR" table.
    # This right hand table has the contact info for the listing:
    # Lister name, contact phone number, cellphone, etc.
    contact_fields = extract_contact_fields(listing, page_type)

    # Extract unique id of the listing.
    listing_id = listing_file.split('!')[1].replace('.htm', '')

    listing_fields = {'id': listing_id, **description_fields, **characteristics_fields, **contact_fields}

    return listing_fields


def main(out_row, listing_file):

    # Examples of non-photo, photo, and certified listings,
    # to make debugging easier.
    # listing_file = 'raw/listings/http:__www.cubisima.com_casas_vendo-casa-planta-baja-en-biplanta-reparto-sevillano-llamar-6405034!210.htm'
    # listing_file = 'apartamento-de-4-cuartos-145000-cuc-en-miramar-playa-la-habana!286824.htm'
    # listing_file = 'prop-horizontal-de-5-cuartos-75000-cuc-en-calle-cocos-santos-suarez-10-de-octubre-la-habana!106935.htm'
    fields = extract_listing_fields(listing_file)

    headers = ['azotea compartida', 'balcon', 'modified', 'corriente 220V',
               'sala-comedor', 'other_info', 'cocina', 'piscina', 'location',
               'agua las 24 horas', 'near_to', 'garaje', 'gas de balon',
               'independiente', 'patio', 'contact_name', 'tanque instalado',
               'bajos', 'telefono', 'placa libre', 'posibilidad de garaje',
               'pasillo', 'corriente 110V', 'interior', 'meters_squared',
               'puntal alto', 'num_bed', 'elevador', 'construction_era',
               'num_bath', 'id', 'azotea libre', 'terraza', 'mobile_number',
               'price', 'patinejo', 'puerta calle', 'pub_date', 'phone_number',
               'portal', 'gas de la calle', 'cocina-comedor', 'hall', 'altos',
               'property_type', 'saleta', 'comedor', 'barbacoa', 'jardin',
               'notes', 'carposhe', 'sala', 'mod_date']
    writer = csv.DictWriter(sys.stdout, headers)
    if out_row == 'header':
        writer.writeheader()
    elif out_row == 'fields':
        writer.writerow(fields)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
