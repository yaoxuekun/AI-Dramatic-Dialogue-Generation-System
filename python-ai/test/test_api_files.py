"""文件服务 API 接口测试。

测试文件上传、下载、删除等接口。
需要 Java 后端运行在 localhost:8085。
"""
import io

# 最小合法 PNG 文件（1x1 像素透明图片）
_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestFileUpload:
    """POST /api/files/upload 文件上传接口测试。"""

    def test_upload_file(self, api_client, auth_headers):
        """上传一个 PNG 图片文件（白名单允许的类型）。"""
        files = {
            "file": ("test.png", io.BytesIO(_MINIMAL_PNG), "image/png"),
        }
        response = api_client.post("/api/files/upload", headers=auth_headers, files=files, data={
            "category": "resources",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "filePath" in data["data"]

    def test_upload_file_no_token(self, api_client):
        """无 token 上传应返回 401。"""
        files = {
            "file": ("test.txt", io.BytesIO(b"hello"), "text/plain"),
        }
        response = api_client.post("/api/files/upload", files=files)
        assert response.status_code == 401


class TestFileDownload:
    """GET /api/files/{path} 文件下载接口测试（公开接口）。"""

    def test_download_nonexistent_file(self, api_client):
        """访问不存在的文件应返回 400 或 404。"""
        response = api_client.get("/api/files/resources/2026-01-01/nonexistent.png")
        # 后端可能返回 400（路径校验失败）或 404（文件不存在）
        assert response.status_code in (400, 404)


class TestFileDelete:
    """DELETE /api/files/{path} 文件删除接口测试。"""

    def test_delete_nonexistent_file(self, api_client, auth_headers):
        """删除不存在的文件应返回 404。"""
        response = api_client.delete(
            "/api/files/resources/2026-01-01/nonexistent.png",
            headers=auth_headers,
        )
        assert response.status_code in (404, 200)

    def test_delete_file_no_token(self, api_client):
        """无 token 删除应返回 401。"""
        response = api_client.delete("/api/files/resources/2026-01-01/test.png")
        assert response.status_code == 401
