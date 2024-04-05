# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2021-2024 Caltech.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resources serializers tests."""

import pytest

from invenio_rdm_records.resources.serializers import (
    DataCite43JSONSerializer,
    DataCite43XMLSerializer,
)


@pytest.fixture(scope="function")
def minimal_record(minimal_record, parent_record):
    """Minimal record metadata with added parent metadata."""
    minimal_record["parent"] = parent_record
    minimal_record["links"] = dict(self_html="https://self-link.com")
    return minimal_record


@pytest.fixture(scope="function")
def full_record(full_record, parent_record):
    """Minimal record metadata with added parent metadata."""
    full_record["links"] = dict(self_html="https://self-link.com")
    return full_record


@pytest.fixture
def full_modified_record(full_record):
    full_record["pids"]["unknown-scheme"] = {
        "identifier": "unknown-1234",
        "provider": "unknown",
        "client": "unknown",
    }

    full_record["metadata"]["identifiers"] = [
        {"identifier": "unknown-1234-a", "scheme": "unknown-scheme"}
    ]

    full_record["metadata"]["related_identifiers"] = [
        {
            "identifier": "unknown-1234-b",
            "scheme": "unknown-scheme",
            "relation_type": {"id": "iscitedby", "title": {"en": "Is cited by"}},
        }
    ]

    full_record["metadata"]["creators"][0]["person_or_org"]["identifiers"] = [
        {"identifier": "unknown-2345", "scheme": "unknown-scheme"}
    ]

    return full_record


@pytest.fixture
def full_geolocation_box_record(full_record):
    full_record["metadata"]["locations"]["features"] = [
        {
            "geometry": {
                "coordinates": [
                    [
                        [-105.92, 33.17],
                        [-106.0, 33.17],
                        [-106.0, 33.0],
                        [-105.92, 33.0],
                        [-105.92, 33.17],
                    ]
                ],
                "type": "Polygon",
            }
        }
    ]
    return full_record


@pytest.fixture
def full_geolocation_polygon_record(full_record):
    full_record["metadata"]["locations"]["features"] = [
        {
            "geometry": {
                "coordinates": [
                    [
                        [33.17, -105.92],
                        [33.17, -106.0],
                        [33.0, -106.0],
                        [33.0, -105.92],
                        [33.12, -105.92],
                        [33.17, -105.32],
                    ]
                ],
                "type": "Polygon",
            }
        }
    ]
    return full_record


@pytest.fixture
def full_modified_date_record(full_record):
    full_record["updated"] = "2022-12-12T22:50:10.573125+00:00"
    return full_record


def test_datacite43_serializer(running_app, full_record):
    """Test serializer to DataCite 4.3 JSON"""
    full_record["metadata"]["rights"].append(
        {
            "title": {"en": "No rightsUri license"},
        }
    )
    # for HTML stripping test purposes
    expected_data = {
        "types": {"resourceTypeGeneral": "Image", "resourceType": "Photo"},
        "creators": [
            {
                "name": "Nielsen, Lars Holm",
                "nameType": "Personal",
                "givenName": "Lars Holm",
                "familyName": "Nielsen",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "0000-0001-8135-3489",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "affiliation": [
                    {"name": "free-text"},
                    {
                        "name": "CERN",
                        "affiliationIdentifier": "https://ror.org/01ggx4157",
                        "affiliationIdentifierScheme": "ROR",
                    },
                ],
            }
        ],
        "titles": [
            {"title": "InvenioRDM"},
            {
                "title": "a research data management platform",
                "titleType": "Subtitle",
                "lang": "eng",
            },
        ],
        "publisher": "InvenioRDM",
        "publicationYear": "2018",
        "subjects": [
            {"subject": "custom"},
            {
                "subject": "Abdominal Injuries",
                "subjectScheme": "MeSH",
                "valueURI": "http://id.nlm.nih.gov/mesh/A-D000007",
            },
        ],
        "contributors": [
            {
                "name": "Nielsen, Lars Holm",
                "nameType": "Personal",
                "contributorType": "Other",
                "givenName": "Lars Holm",
                "familyName": "Nielsen",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "0000-0001-8135-3489",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "affiliation": [
                    {
                        "name": "CERN",
                        "affiliationIdentifier": "https://ror.org/01ggx4157",
                        "affiliationIdentifierScheme": "ROR",
                    }
                ],
            }
        ],
        "dates": [
            {"date": "2018/2020-09", "dateType": "Issued"},
            {"date": "1939/1945", "dateType": "Other", "dateInformation": "A date"},
            {"date": "2023-01-02", "dateType": "Updated"},
        ],
        "language": "dan",
        "identifiers": [
            {"identifier": "https://self-link.com", "identifierType": "URL"},
            {"identifier": "10.1234/inveniordm.1234", "identifierType": "DOI"},
            {"identifier": "oai:vvv.com:abcde-fghij", "identifierType": "oai"},
            {"identifier": "1924MNRAS..84..308E", "identifierType": "bibcode"},
        ],
        "relatedIdentifiers": [
            {
                "relatedIdentifier": "10.1234/foo.bar",
                "relatedIdentifierType": "DOI",
                "relationType": "IsCitedBy",
                "resourceTypeGeneral": "Dataset",
            },
            {
                "relatedIdentifier": "10.1234/inveniordm.1234.parent",
                "relatedIdentifierType": "DOI",
                "relationType": "IsVersionOf",
            },
        ],
        "sizes": ["11 pages"],
        "formats": ["application/pdf"],
        "version": "v1.0",
        "rightsList": [
            {
                "rights": "A custom license",
                "rightsUri": "https://customlicense.org/licenses/by/4.0/",
            },
            {"rights": "No rightsUri license"},
            {
                "rights": "Creative Commons Attribution 4.0 International",
                "rightsIdentifierScheme": "spdx",
                "rightsIdentifier": "cc-by-4.0",
                "rightsUri": "https://creativecommons.org/licenses/by/4.0/legalcode",
            },
        ],
        "descriptions": [
            {
                "description": "A description \nwith HTML tags",
                "descriptionType": "Abstract",
            },
            {"description": "Bla bla bla", "descriptionType": "Methods", "lang": "eng"},
        ],
        "geoLocations": [
            {
                "geoLocationPoint": {
                    "pointLongitude": "-32.94682",
                    "pointLatitude": "-60.63932",
                },
                "geoLocationPlace": "test location place",
            }
        ],
        "fundingReferences": [
            {
                "funderName": "European Commission",
                "funderIdentifier": "00k4n6c32",
                "funderIdentifierType": "ROR",
                "awardTitle": (
                    "Personalised Treatment For Cystic Fibrosis Patients With "
                    "Ultra-rare CFTR Mutations (and beyond)"
                ),
                "awardNumber": "755021",
                "awardURI": "https://cordis.europa.eu/project/id/755021",
            }
        ],
        "schemaVersion": "http://datacite.org/schema/kernel-4",
    }

    serializer = DataCite43JSONSerializer()
    serialized_record = serializer.dump_obj(full_record)

    assert serialized_record == expected_data


def test_datacite43_xml_serializer(running_app, full_record):
    expected_data = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<resource xmlns="http://datacite.org/schema/kernel-4" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4.3/metadata.xsd">',  # noqa
        '  <identifier identifierType="DOI">10.1234/inveniordm.1234</identifier>',  # noqa
        "  <alternateIdentifiers>",
        '    <alternateIdentifier alternateIdentifierType="URL">https://self-link.com</alternateIdentifier>',
        '    <alternateIdentifier alternateIdentifierType="oai">oai:vvv.com:abcde-fghij</alternateIdentifier>',
        '    <alternateIdentifier alternateIdentifierType="bibcode">1924MNRAS..84..308E</alternateIdentifier>',  # noqa
        "  </alternateIdentifiers>",
        "  <creators>",
        "    <creator>",
        '      <creatorName nameType="Personal">Nielsen, Lars Holm</creatorName>',  # noqa
        "      <givenName>Lars Holm</givenName>",
        "      <familyName>Nielsen</familyName>",
        '      <nameIdentifier nameIdentifierScheme="ORCID">0000-0001-8135-3489</nameIdentifier>',  # noqa
        "      <affiliation>free-text</affiliation>",
        '      <affiliation affiliationIdentifier="https://ror.org/01ggx4157" affiliationIdentifierScheme="ROR">CERN</affiliation>',  # noqa
        "    </creator>",
        "  </creators>",
        "  <titles>",
        "    <title>InvenioRDM</title>",
        '    <title xml:lang="eng" titleType="Subtitle">a research data management platform</title>',  # noqa
        "  </titles>",
        "  <publisher>InvenioRDM</publisher>",
        "  <publicationYear>2018</publicationYear>",
        "  <subjects>",
        "    <subject>custom</subject>",
        '    <subject subjectScheme="MeSH">Abdominal Injuries</subject>',
        "  </subjects>",
        "  <contributors>",
        '    <contributor contributorType="Other">',
        '      <contributorName nameType="Personal">Nielsen, Lars Holm</contributorName>',  # noqa
        "      <givenName>Lars Holm</givenName>",
        "      <familyName>Nielsen</familyName>",
        '      <nameIdentifier nameIdentifierScheme="ORCID">0000-0001-8135-3489</nameIdentifier>',  # noqa
        '      <affiliation affiliationIdentifier="https://ror.org/01ggx4157" affiliationIdentifierScheme="ROR">CERN</affiliation>',  # noqa
        "    </contributor>",
        "  </contributors>",
        "  <dates>",
        '    <date dateType="Issued">2018/2020-09</date>',
        '    <date dateType="Other" dateInformation="A date">1939/1945</date>',  # noqa
        '    <date dateType="Updated">2023-01-02</date>',
        "  </dates>",
        "  <language>dan</language>",
        '  <resourceType resourceTypeGeneral="Image">Photo</resourceType>',
        "  <relatedIdentifiers>",
        '    <relatedIdentifier relatedIdentifierType="DOI" relationType="IsCitedBy" resourceTypeGeneral="Dataset">10.1234/foo.bar</relatedIdentifier>',  # noqa
        '    <relatedIdentifier relatedIdentifierType="DOI" relationType="IsVersionOf">10.1234/inveniordm.1234.parent</relatedIdentifier>',  # noqa
        "  </relatedIdentifiers>",
        "  <sizes>",
        "    <size>11 pages</size>",
        "  </sizes>",
        "  <formats>",
        "    <format>application/pdf</format>",
        "  </formats>",
        "  <version>v1.0</version>",
        "  <rightsList>",
        '    <rights rightsURI="https://customlicense.org/licenses/by/4.0/">A custom license</rights>',  # noqa
        '    <rights rightsURI="https://creativecommons.org/licenses/by/4.0/legalcode" rightsIdentifierScheme="spdx" rightsIdentifier="cc-by-4.0">Creative Commons Attribution 4.0 International</rights>',  # noqa
        "  </rightsList>",
        "  <descriptions>",
        '    <description descriptionType="Abstract">A description ',
        "with HTML tags</description>",
        '    <description descriptionType="Methods" xml:lang="eng">Bla bla bla</description>',  # noqa
        "  </descriptions>",
        "  <geoLocations>",
        "    <geoLocation>",
        "      <geoLocationPlace>test location place</geoLocationPlace>",
        "      <geoLocationPoint>",
        "        <pointLongitude>-32.94682</pointLongitude>",
        "        <pointLatitude>-60.63932</pointLatitude>",
        "      </geoLocationPoint>",
        "    </geoLocation>",
        "  </geoLocations>",
        "  <fundingReferences>",
        "    <fundingReference>",
        "      <funderName>European Commission</funderName>",
        '      <funderIdentifier funderIdentifierType="ROR">00k4n6c32</funderIdentifier>',  # noqa
        "      <awardNumber>755021</awardNumber>",
        "      <awardTitle>Personalised Treatment For Cystic Fibrosis Patients With Ultra-rare CFTR Mutations (and beyond)</awardTitle>",  # noqa
        "    </fundingReference>",
        "  </fundingReferences>",
        "</resource>",
        "",  # this is because of the split
    ]

    serializer = DataCite43XMLSerializer()
    serialized_record = serializer.serialize_object(full_record)

    assert serialized_record == "\n".join(expected_data)


def test_datacite43_identifiers(running_app, minimal_record):
    """Test serialization of records with DOI alternate identifiers"""
    # Mimic user putting DOI in alternate identifier field
    minimal_record["metadata"]["identifiers"] = [
        {"identifier": "10.1234/inveniordm.1234", "scheme": "doi"}
    ]

    serializer = DataCite43JSONSerializer()
    serialized_record = serializer.dump_obj(minimal_record)

    assert len(serialized_record["identifiers"]) == 1

    minimal_record["pids"] = {
        "doi": {
            "identifier": "10.1234/inveniordm.1234",
            "provider": "datacite",
            "client": "inveniordm",
        }
    }

    serialized_record = serializer.dump_obj(minimal_record)
    assert len(serialized_record["identifiers"]) == 2
    identifier = serialized_record["identifiers"][0]["identifier"]
    assert identifier == "https://self-link.com"
    identifier = serialized_record["identifiers"][1]["identifier"]
    assert identifier == "10.1234/inveniordm.1234"


def test_datacite43_serializer_with_unknown_id_schemes(
    running_app, full_modified_record
):
    """Test if the DataCite 4.3 JSON serializer can handle unknown schemes."""
    # this test is there to ensure that there are no KeyErrors during the
    # lookup of unknown PID schemes during DataCite 4.3 serialization
    # if the behaviour of the datacite serializer is changed, the asserts
    # below should probably be adjusted accordingly

    expected_pid_id = {"identifier": "unknown-1234", "identifierType": "unknown-scheme"}
    expected_pid_id_2 = {
        "identifier": "unknown-1234-a",
        "identifierType": "unknown-scheme",
    }
    expected_related_id = {
        "relatedIdentifier": "unknown-1234-b",
        "relatedIdentifierType": "unknown-scheme",
        "relationType": "IsCitedBy",
    }
    expected_creator_id = {
        "nameIdentifier": "unknown-2345",
        "nameIdentifierScheme": "unknown-scheme",
    }

    serializer = DataCite43JSONSerializer()
    serialized_record = serializer.dump_obj(full_modified_record)

    assert expected_pid_id in serialized_record["identifiers"]
    assert expected_pid_id_2 in serialized_record["identifiers"]
    assert len(serialized_record["identifiers"]) == 5

    assert expected_related_id not in serialized_record["relatedIdentifiers"]
    assert len(serialized_record["relatedIdentifiers"]) == 1

    creator_ids = serialized_record["creators"][0]["nameIdentifiers"]
    assert expected_creator_id in creator_ids
    assert len(creator_ids) == 1


def test_datacite43_xml_serializer_with_unknown_id_schemes(
    running_app, full_modified_record
):
    """Test if the DataCite 4.3 XML serializer can handle unknown schemes."""
    serializer = DataCite43XMLSerializer()
    serialized_record = serializer.serialize_object(full_modified_record)
    expected_pid_id = '<alternateIdentifier alternateIdentifierType="unknown-scheme">unknown-1234</alternateIdentifier>'  # noqa
    expected_pid_id_2 = '<alternateIdentifier alternateIdentifierType="unknown-scheme">unknown-1234-a</alternateIdentifier>'  # noqa
    expected_related_id = '<relatedIdentifier relatedIdentifierType="unknown-scheme" relationType="IsCitedBy">unknown-1234-b</relatedIdentifier>'  # noqa
    expected_creator_id = '<nameIdentifier nameIdentifierScheme="unknown-scheme">unknown-2345</nameIdentifier>'  # noqa

    assert expected_pid_id in serialized_record
    assert expected_pid_id_2 in serialized_record
    assert expected_related_id not in serialized_record
    assert expected_creator_id in serialized_record


def test_datacite43_serializer_with_box(running_app, full_geolocation_box_record):
    """Test if the DataCite 4.3 JSON serializer handles geolocation boxes."""

    expected_box = {
        "geoLocationBox": {
            "eastBoundLongitude": "-105.92",
            "northBoundLatitude": "33.17",
            "southBoundLatitude": "33.0",
            "westBoundLongitude": "-106.0",
        }
    }

    serializer = DataCite43JSONSerializer()

    serialized_record_box = serializer.dump_obj(full_geolocation_box_record)

    assert expected_box in serialized_record_box["geoLocations"]


def test_datacite43_serializer_with_polygon(
    running_app, full_geolocation_polygon_record
):
    """Test if the DataCite 4.3 JSON serializer handles geolocation polygons."""

    expected_polygon = {
        "geoLocationPolygon": [
            {"polygonPoint": {"pointLongitude": "33.17", "pointLatitude": "-105.92"}},
            {"polygonPoint": {"pointLongitude": "33.17", "pointLatitude": "-106.0"}},
            {"polygonPoint": {"pointLongitude": "33.0", "pointLatitude": "-106.0"}},
            {"polygonPoint": {"pointLongitude": "33.0", "pointLatitude": "-105.92"}},
            {"polygonPoint": {"pointLongitude": "33.12", "pointLatitude": "-105.92"}},
            {"polygonPoint": {"pointLongitude": "33.17", "pointLatitude": "-105.32"}},
        ]
    }

    serializer = DataCite43JSONSerializer()

    serialized_record_polygon = serializer.dump_obj(full_geolocation_polygon_record)

    assert expected_polygon in serialized_record_polygon["geoLocations"]


def test_datacite43_serializer_updated_date(running_app, full_modified_date_record):
    """Test if the DataCite 4.3 JSON serializer adds system updated date."""

    expected_dates = [
        {"date": "2018/2020-09", "dateType": "Issued"},
        {"date": "1939/1945", "dateType": "Other", "dateInformation": "A date"},
        {"date": "2022-12-12", "dateType": "Updated"},
    ]

    serializer = DataCite43JSONSerializer()
    serialized_record = serializer.dump_obj(full_modified_date_record)

    assert expected_dates == serialized_record["dates"]
    assert len(serialized_record["dates"]) == 3
