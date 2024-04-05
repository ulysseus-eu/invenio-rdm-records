# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2024 CERN
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resources serializers tests."""

from io import BytesIO

import pytest
from dateutil.parser import parse
from invenio_access.permissions import system_identity

from invenio_rdm_records.proxies import current_rdm_records, current_rdm_records_service
from invenio_rdm_records.resources.serializers.marcxml import MARCXMLSerializer

# Local fixtures


@pytest.fixture(scope="function")
def updated_full_record(full_record):
    """Update fields (done after record create) for MARCXML serializer."""
    full_record["access"]["status"] = "embargoed"
    full_record["metadata"]["creators"].append(
        {
            "person_or_org": {
                "name": "Bar, Foo the Creator",
                "type": "personal",
                "given_name": "Foo the Creator",
                "family_name": "Bar",
                "identifiers": [
                    {
                        "scheme": "orcid",
                        "identifier": "0000-0002-1825-0097",
                    }
                ],
            },
            "affiliations": [{"id": "cern"}, {"name": "free-text"}],
        }
    )
    full_record["metadata"]["contributors"] = [
        {
            "person_or_org": {
                "name": "Test, Full Name Contributor",
                "type": "personal",
                "given_name": "Test",
                "family_name": "Full Name",
            },
            "role": {"id": "other"},
            "affiliations": [{"id": "cern"}, {"name": "free-text"}],
        },
        {
            "person_or_org": {
                "name": "Doe, John the Contributor",
                "type": "personal",
                "given_name": "John the Contributor",
                "family_name": "Doe",
                "identifiers": [
                    {
                        "scheme": "orcid",
                        "identifier": "0000-0001-8135-3489",
                    },
                    {
                        "scheme": "gnd",
                        "identifier": "gnd:4079154-3",
                    },
                ],
            },
            "role": {"id": "other"},
            "affiliations": [{"id": "cern"}, {"name": "free-text"}],
        },
    ]

    return full_record


# Tests
def test_marcxml_serializer_minimal_record(running_app, minimal_record, parent):
    """Test minimal serializer for MARCXML."""
    serializer = MARCXMLSerializer()
    service = current_rdm_records.records_service
    draft = service.create(system_identity, minimal_record)
    record = service.publish(id_=draft.id, identity=system_identity)

    serialized_record = serializer.serialize_object(record.data)

    expected_data = f"""\
<?xml version='1.0' encoding='utf-8'?>
<record xmlns="http://www.loc.gov/MARC21/slim">
  <leader>00000nam##2200000uu#4500</leader>
  <controlfield tag="001">{record.id}</controlfield>
  <datafield tag="024" ind1=" " ind2=" ">
    <subfield code="2">doi</subfield>
    <subfield code="a">10.1234/{record.id}</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="O">
    <subfield code="o">oai:inveniordm:{record.id}</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Troy Inc.</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">A Romans story</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Brown, Troy</subfield>
  </datafield>
  <datafield tag="540" ind1=" " ind2=" ">
    <subfield code="a">info:eu-repo/semantics/metadata-onlyAccess</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="b">Acme Inc</subfield>
    <subfield code="c">2020-06-01</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">info:eu-repo/semantics/other</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">image</subfield>
    <subfield code="b">photo</subfield>
  </datafield>
  <controlfield tag="005">{parse(record["updated"]).strftime("%Y%m%d%H%M%S.0")}</controlfield>
  <datafield tag="542" ind1=" " ind2=" ">
    <subfield code="l">metadata-only</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="a">10.1234/{record.data["parent"]["id"]}</subfield>
    <subfield code="i">isVersionOf</subfield>
    <subfield code="n">doi</subfield>
  </datafield>
</record>
"""

    assert serialized_record == expected_data


def _add_file_to_record(recid, client, headers):
    """Adds a file to the record."""
    # Attach a file to it
    response = client.post(
        f"/records/{recid}/draft/files", headers=headers, json=[{"key": "test.pdf"}]
    )
    assert response.status_code == 201
    response = client.put(
        f"/records/{recid}/draft/files/test.pdf/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b"testfile"),
    )
    assert response.status_code == 200
    response = client.post(
        f"/records/{recid}/draft/files/test.pdf/commit", headers=headers
    )
    assert response.status_code == 200


def _add_record_to_communities(db, recid, community, community2):
    """Add record to communities."""
    record = current_rdm_records_service.read(
        id_=recid, identity=system_identity
    )._record

    record.parent.communities.add(community._record, default=True)
    record.parent.communities.add(community2._record, default=False)
    record.parent.commit()
    db.session.commit()
    current_rdm_records_service.indexer.index(record, arguments={"refresh": True})


def test_marcxml_serializer_full_record(
    db,
    running_app,
    updated_full_record,
    client_with_login,
    headers,
    community,
    community2,
):
    """Test serializer for MARCXML with a"""
    serializer = MARCXMLSerializer()
    updated_full_record["files"] = {"enabled": True}
    response = client_with_login.post(
        "/records", json=updated_full_record, headers=headers
    )
    assert response.status_code == 201
    recid = response.json["id"]

    _add_file_to_record(recid, client_with_login, headers)

    # Publish it
    response = client_with_login.post(
        f"/records/{recid}/draft/actions/publish", headers=headers
    )
    assert response.status_code == 202

    _add_record_to_communities(db, recid, community, community2)

    record = current_rdm_records_service.read(id_=recid, identity=system_identity)

    # We are setting explicitly the order of the communities as it's required to match the expected data
    record.data["parent"]["communities"]["ids"] = [community.id, community2.id]
    record.data["custom_fields"] = {}
    # TODO: This is cheating, try to set this in the `updated_full_record` method above
    record.data["custom_fields"]["thesis:university"] = "A university"

    record.data["custom_fields"]["journal:journal"] = {
        "title": "Journal Title",
        "pages": "100",
        "volume": "5",
        "issue": "10",
    }
    serialized_record = serializer.serialize_object(record.data)

    expected_data = f"""\
<?xml version='1.0' encoding='utf-8'?>
<record xmlns="http://www.loc.gov/MARC21/slim">
  <leader>00000nam##2200000uu#4500</leader>
  <controlfield tag="001">{recid}</controlfield>
  <datafield tag="024" ind1=" " ind2=" ">
    <subfield code="2">doi</subfield>
    <subfield code="a">10.1234/inveniordm.1234</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="O">
    <subfield code="o">oai:vvv.com:abcde-fghij</subfield>
    <subfield code="p">user-blr</subfield>
    <subfield code="p">user-rdm</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Full Name, Test</subfield>
    <subfield code="u">CERN</subfield>
    <subfield code="4">oth</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Doe, John the Contributor</subfield>
    <subfield code="0">(orcid)0000-0001-8135-3489</subfield>
    <subfield code="0">(gnd)gnd:4079154-3</subfield>
    <subfield code="u">CERN</subfield>
    <subfield code="4">oth</subfield>
  </datafield>
  <datafield tag="700" ind1=" " ind2=" ">
    <subfield code="a">Bar, Foo the Creator</subfield>
    <subfield code="0">(orcid)0000-0002-1825-0097</subfield>
    <subfield code="u">CERN</subfield>
  </datafield>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">InvenioRDM</subfield>
  </datafield>
  <datafield tag="100" ind1=" " ind2=" ">
    <subfield code="a">Nielsen, Lars Holm</subfield>
    <subfield code="0">(orcid)0000-0001-8135-3489</subfield>
    <subfield code="u">CERN</subfield>
  </datafield>
  <datafield tag="856" ind1=" " ind2="2">
    <subfield code="a">doi:10.1234/foo.bar</subfield>
  </datafield>
  <datafield tag="540" ind1=" " ind2=" ">
    <subfield code="a">info:eu-repo/semantics/embargoedAccess</subfield>
  </datafield>
  <datafield tag="540" ind1=" " ind2=" ">
    <subfield code="a">A custom license</subfield>
    <subfield code="u">https://customlicense.org/licenses/by/4.0/</subfield>
  </datafield>
  <datafield tag="540" ind1=" " ind2=" ">
    <subfield code="a">Creative Commons Attribution 4.0 International</subfield>
    <subfield code="u">https://creativecommons.org/licenses/by/4.0/legalcode</subfield>
  </datafield>
  <datafield tag="653" ind1=" " ind2=" ">
    <subfield code="a">Abdominal Injuries</subfield>
  </datafield>
  <datafield tag="653" ind1=" " ind2=" ">
    <subfield code="a">custom</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">&amp;lt;h1&amp;gt;A description&amp;lt;/h1&amp;gt; &amp;lt;p&amp;gt;with HTML tags&amp;lt;/p&amp;gt;</subfield>
  </datafield>
  <datafield tag="500" ind1=" " ind2=" ">
    <subfield code="a">Bla bla bla</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">dan</subfield>
  </datafield>
  <datafield tag="041" ind1=" " ind2=" ">
    <subfield code="a">eng</subfield>
  </datafield>
  <datafield tag="999" ind1="C" ind2="5">
    <subfield code="x">0000 0001 1456 7559</subfield>
  </datafield>
  <datafield tag="260" ind1=" " ind2=" ">
    <subfield code="b">InvenioRDM</subfield>
    <subfield code="c">2018/2020-09</subfield>
    <subfield code="c">info:eu-repo/date/embargoEnd/2131-01-01</subfield>
  </datafield>
  <datafield tag="502" ind1=" " ind2=" ">
    <subfield code="c">A university</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">user-blr</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">user-rdm</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">info:eu-repo/semantics/other</subfield>
  </datafield>
  <datafield tag="980" ind1=" " ind2=" ">
    <subfield code="a">image</subfield>
    <subfield code="b">photo</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2="1">
    <subfield code="a">application/pdf</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2="2">
    <subfield code="a">11 pages</subfield>
  </datafield>
  <datafield tag="536" ind1=" " ind2=" ">
    <subfield code="c">755021</subfield>
    <subfield code="a">Personalised Treatment For Cystic Fibrosis Patients With Ultra-rare CFTR Mutations (and beyond)</subfield>
  </datafield>
  <controlfield tag="005">{parse(record["updated"]).strftime("%Y%m%d%H%M%S.0")}</controlfield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="s">8</subfield>
    <subfield code="z">md5:8bc944dbd052ef51652e70a5104492e3</subfield>
    <subfield code="u">https://127.0.0.1:5000/records/{recid}/files/test.pdf</subfield>
  </datafield>
  <datafield tag="542" ind1=" " ind2=" ">
    <subfield code="l">embargoed</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="a">10.1234/foo.bar</subfield>
    <subfield code="i">Is cited by</subfield>
    <subfield code="n">doi</subfield>
  </datafield>
  <datafield tag="773" ind1=" " ind2=" ">
    <subfield code="a">10.1234/{record["parent"]["id"]}</subfield>
    <subfield code="i">isVersionOf</subfield>
    <subfield code="n">doi</subfield>
  </datafield>
  <datafield tag="909" ind1="C" ind2="4">
    <subfield code="p">Journal Title</subfield>
    <subfield code="v">5</subfield>
    <subfield code="n">10</subfield>
    <subfield code="c">100</subfield>
    <subfield code="y">2018/2020-09</subfield>
  </datafield>
</record>
"""

    assert serialized_record == expected_data
