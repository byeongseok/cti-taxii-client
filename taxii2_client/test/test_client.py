import pytest
import responses

from taxii2_client import (MEDIA_TYPE_STIX_V20, MEDIA_TYPE_TAXII_V20, ApiRoot,
                           Collection, ServerDiscovery, TAXII2Client)

TAXII_SERVER = 'example.com'
DISCOVERY_URL = 'https://{}/taxii/'.format(TAXII_SERVER)
API_ROOT_URL = 'https://{}/api1/'.format(TAXII_SERVER)
COLLECTIONS_URL = API_ROOT_URL + 'collections/'
COLLECTION_URL = COLLECTIONS_URL + '91a7b528-80eb-42ed-a74d-c6fbd5a26116/'
OBJECTS_URL = COLLECTION_URL + 'objects/'
GET_OBJECTS_URL = OBJECTS_URL
ADD_OBJECTS_URL = OBJECTS_URL
GET_OBJECT_URL = OBJECTS_URL + 'indicator--252c7c11-daf2-42bd-843b-be65edca9f61/'
MANIFEST_URL = COLLECTION_URL + 'manifest/'

# These responses are provided as examples in the TAXII 2.0 specification.
DISCOVERY_RESPONSE = """{
  "title": "Some TAXII Server",
  "description": "This TAXII Server contains a listing of...",
  "contact": "string containing contact information",
  "default": "https://example.com/api2/",
  "api_roots": [
    "https://example.com/api1/",
    "https://example.com/api2/",
    "https://example.net/trustgroup1/"
  ]
}"""
API_ROOT_RESPONSE = """{
  "title": "Malware Research Group",
  "description": "A trust group setup for malware researchers",
  "versions": ["taxii-2.0"],
  "max_content_length": 9765625
}"""
COLLECTIONS_RESPONSE = """{
  "collections": [
    {
      "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
      "title": "High Value Indicator Collection",
      "description": "This data collection is for collecting high value IOCs",
      "can_read": true,
      "can_write": false,
      "media_types": [
        "application/vnd.oasis.stix+json; version=2.0"
      ]
    },
    {
      "id": "52892447-4d7e-4f70-b94d-d7f22742ff63",
      "title": "Indicators from the past 24-hours",
      "description": "This data collection is for collecting current IOCs",
      "can_read": true,
      "can_write": false,
      "media_types": [
        "application/vnd.oasis.stix+json; version=2.0"
      ]
    }
  ]
}"""
COLLECTION_RESPONSE = """{
  "id": "91a7b528-80eb-42ed-a74d-c6fbd5a26116",
  "title": "High Value Indicator Collection",
  "description": "This data collection is for collecting high value IOCs",
  "can_read": true,
  "can_write": false,
  "media_types": [
    "application/vnd.oasis.stix+json; version=2.0"
  ]
}"""
GET_OBJECTS_RESPONSE = """{
  "type": "bundle",
  "id": "bundle--5d0092c5-5f74-4287-9642-33f4c354e56d",
  "spec_version": "2.0",
  "objects": [
    {
      "type": "indicator",
      "id": "indicator--252c7c11-daf2-42bd-843b-be65edca9f61",
      "created": "2016-04-06T20:03:48.000Z",
      "modified": "2016-04-06T20:03:48.000Z",
      "pattern": "[ file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e' ]",
      "valid_from": "2016-01-01T00:00:00Z"
    }
  ]
}"""


@pytest.fixture
def client():
    """TAXII Client with no authentication."""
    return TAXII2Client(None, None)


@pytest.fixture
def server(client):
    """Default ServerDiscovery object for example.com"""
    return ServerDiscovery('example.com', client=client)


@pytest.fixture
def api_root(client):
    """Default API Root object"""
    return ApiRoot(API_ROOT_URL, client=client)


@pytest.fixture
def collection(client):
    """Default Collection object"""
    return Collection(COLLECTION_URL, client=client)


def set_discovery_response(response):
    responses.add(responses.GET, DISCOVERY_URL, body=response, status=200,
                  content_type=MEDIA_TYPE_TAXII_V20)


def set_collection_response(response=COLLECTION_RESPONSE):
    responses.add(responses.GET, COLLECTION_URL, response, status=200,
                  content_type=MEDIA_TYPE_TAXII_V20)


@responses.activate
def test_server_discovery(server):
    set_discovery_response(DISCOVERY_RESPONSE)

    assert server._loaded is False
    assert server.title == "Some TAXII Server"
    assert server._loaded is True
    assert server.description == "This TAXII Server contains a listing of..."
    assert server.contact == "string containing contact information"
    assert len(server.api_roots) == 3
    assert server.default is not None

    assert server.api_roots[1] == server.default

    api_root = server.api_roots[0]
    assert api_root.url == API_ROOT_URL
    # The URL is populated based on the discovery response, so the rest of the
    # information is not loaded yet.
    assert api_root._loaded_information is False


@responses.activate
def test_minimal_discovery_response(server):
    # `title` is the only required field on a Discovery Response
    set_discovery_response('{"title": "Some TAXII Server"}')

    assert server.title == "Some TAXII Server"
    assert server.description is None
    assert server.contact is None
    assert server.api_roots == []
    assert server.default is None


@responses.activate
def test_discovery_with_no_default(server):
    response = """{
      "title": "Some TAXII Server",
      "description": "This TAXII Server contains a listing of...",
      "contact": "string containing contact information",
      "api_roots": [
        "https://example.com/api1/",
        "https://example.com/api2/",
        "https://example.net/trustgroup1/"
      ]
    }"""
    set_discovery_response(response)

    assert len(server.api_roots) == 3
    assert server.default is None


@responses.activate
def test_api_root(api_root):
    responses.add(responses.GET, API_ROOT_URL, API_ROOT_RESPONSE,
                  status=200, content_type=MEDIA_TYPE_TAXII_V20)

    assert api_root._loaded_information is False
    assert api_root.title == "Malware Research Group"
    assert api_root._loaded_information is True
    assert api_root.description == "A trust group setup for malware researchers"
    assert api_root.versions == ['taxii-2.0']
    assert api_root.max_content_length == 9765625


@responses.activate
def test_api_root_collections(api_root):
    responses.add(responses.GET, COLLECTIONS_URL, COLLECTIONS_RESPONSE, status=200,
                  content_type=MEDIA_TYPE_TAXII_V20)

    assert api_root._loaded_collections is False
    assert len(api_root.collections) == 2
    assert api_root._loaded_collections is True

    coll = api_root.collections[0]
    # A collection populated from an API Root is automatically loaded
    assert coll._loaded is True
    assert coll.id == '91a7b528-80eb-42ed-a74d-c6fbd5a26116'
    assert coll.url == COLLECTION_URL
    assert coll.title == "High Value Indicator Collection"
    assert coll.description == "This data collection is for collecting high value IOCs"
    assert coll.can_read is True
    assert coll.can_write is False
    assert coll.media_types == [MEDIA_TYPE_STIX_V20]


@responses.activate
def test_collection(collection):
    set_collection_response()

    assert collection._loaded is False
    assert collection.id == '91a7b528-80eb-42ed-a74d-c6fbd5a26116'
    assert collection._loaded is True
    assert collection.url == COLLECTION_URL
    assert collection.title == "High Value Indicator Collection"
    assert collection.description == "This data collection is for collecting high value IOCs"
    assert collection.can_read is True
    assert collection.can_write is False
    assert collection.media_types == [MEDIA_TYPE_STIX_V20]


def test_collection_unexpected_kwarg():
    with pytest.raises(TypeError):
        Collection(url="", client=None, foo="bar")


@responses.activate
def test_get_collection_objects(collection):
    # The Collection Response needs to be set to get the Collection information.
    set_collection_response()
    responses.add(responses.GET, GET_OBJECTS_URL, GET_OBJECTS_RESPONSE,
                  status=200, content_type=MEDIA_TYPE_STIX_V20)

    response = collection.get_objects()

    assert response['spec_version'] == '2.0'
    assert response['objects'][0]['id'] == 'indicator--252c7c11-daf2-42bd-843b-be65edca9f61'
