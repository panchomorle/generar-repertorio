import json
from unittest.mock import patch, MagicMock
from repertorio.search import search_song


def test_search_song_empty():
    assert search_song("") is None
    assert search_song("   ") is None


def test_search_song_success():
    mock_data = {
        "response": {
            "docs": [
                {
                    "art": "Coldplay",
                    "txt": "The Scientist",
                    "dns": "coldplay",
                    "url": "the-scientist",
                }
            ]
        }
    }
    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_url.return_value = mock_resp

        res = search_song("the scientist")
        assert res is not None
        assert res["artist"] == "Coldplay"
        assert res["title"] == "The Scientist"
        assert res["dns"] == "coldplay"
        assert res["url"] == "the-scientist"


def test_search_song_not_found():
    mock_data = {"response": {"docs": []}}
    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_url.return_value = mock_resp

        res = search_song("song_that_does_not_exist_xyz123")
        assert res is None
