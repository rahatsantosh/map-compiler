import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase


class TestExtractParam(TestCase):
    def test_extracts_click_hash(self):
        from core.views import _extract_param
        url = "/std/?click_hash=abc123&request_script=x"
        assert _extract_param(url, r"click_hash=([^&]+)") == "abc123"

    def test_extracts_script(self):
        from core.views import _extract_param
        url = "/std/?click_hash=abc&request_script=print(1)&"
        assert _extract_param(url, r"request_script=([^&]+)") == "print(1)"

    def test_returns_none_when_missing(self):
        from core.views import _extract_param
        assert _extract_param("/std/?foo=bar", r"click_hash=([^&]+)") is None

    def test_extracts_bbox(self):
        from core.views import _extract_param
        url = "/wms/?bbox=1.0,2.0,3.0,4.0&click_hash=abc"
        result = _extract_param(url, r"bbox=([^&]+)")
        assert result == "1.0,2.0,3.0,4.0"


class TestNonMapRequestView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_no_script_returns_error(self, mock_env, mock_compile):
        from core.views import nonmaprequest
        request = self.factory.get("/std/?click_hash=abc")
        response = nonmaprequest(request)
        data = json.loads(response.content)
        assert data["error"] is True
        assert "No script" in data["console"]
        mock_compile.assert_not_called()

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_script_calls_compiler(self, mock_env, mock_compile):
        from core.views import nonmaprequest
        mock_compile.return_value = {
            "console": "3\n",
            "graph": None,
            "error": False,
        }
        request = self.factory.get("/std/?click_hash=abc&request_script=print(1%2B2)")
        response = nonmaprequest(request)
        data = json.loads(response.content)
        assert data["error"] is False
        assert data["console"] == "3\n"
        mock_compile.assert_called_once()

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_import_blocked(self, mock_env, mock_compile):
        from core.views import nonmaprequest
        mock_compile.return_value = {
            "console": "Import statements are not allowed",
            "graph": None,
            "error": True,
        }
        request = self.factory.get("/std/?click_hash=abc&request_script=import%20os")
        response = nonmaprequest(request)
        data = json.loads(response.content)
        assert data["error"] is True


class TestMapRequestView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_no_script_returns_400(self, mock_env, mock_compile):
        from core.views import maprequest
        request = self.factory.get("/wms/?click_hash=abc")
        response = maprequest(request)
        assert response.status_code == 400

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_script_with_response(self, mock_env, mock_compile):
        from core.views import maprequest
        tile = MagicMock()
        mock_compile.return_value = {
            "response": tile,
            "console": None,
            "graph": None,
            "error": False,
        }
        request = self.factory.get(
            "/wms/?click_hash=abc&request_script=x%3D1"
            "&bbox=1.0,2.0,3.0,4.0"
        )
        response = maprequest(request)
        assert response is tile

    @patch("core.views.compile_and_execute")
    @patch("core.views._build_compiler_env", return_value={})
    def test_no_response_returns_204(self, mock_env, mock_compile):
        from core.views import maprequest
        mock_compile.return_value = {
            "response": None,
            "console": None,
            "graph": None,
            "error": False,
        }
        request = self.factory.get(
            "/wms/?click_hash=abc&request_script=x%3D1"
        )
        response = maprequest(request)
        assert response.status_code == 204


class TestListDatasetsView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("core.views.settings")
    def test_empty_when_dir_missing(self, mock_settings):
        from core.views import list_datasets
        mock_settings.DATA_DIR = Path("/nonexistent/path")
        request = self.factory.get("/api/datasets/")
        response = list_datasets(request)
        data = json.loads(response.content)
        assert data == {"datasets": []}

    def test_finds_tif_files(self):
        import tempfile

        from core.views import list_datasets

        with tempfile.TemporaryDirectory() as tmpdir:
            tif = Path(tmpdir) / "test.tif"
            tif.write_bytes(b"\x00" * 1024)
            with patch("core.views.settings") as mock_settings:
                mock_settings.DATA_DIR = Path(tmpdir)
                request = self.factory.get("/api/datasets/")
                response = list_datasets(request)
                data = json.loads(response.content)
                assert len(data["datasets"]) == 1
                assert data["datasets"][0]["name"] == "test.tif"
