"""圖片內容與 GCS 條件請求驗證；不建立真實 GCS Client。"""
import importlib.util
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image
from fastapi import HTTPException
from tests.unit.test_account_permissions import isolated_app


@pytest.mark.parametrize('fmt,mime', [('JPEG','image/jpeg'), ('PNG','image/png'), ('WEBP','image/webp')])
def test_normalize_supported_content_and_strip_metadata(isolated_app, fmt, mime):
    from app.services.image_service import normalize_image
    source = BytesIO()
    exif = Image.Exif()
    exif[315] = 'test author metadata'
    Image.new('RGB', (12, 9), 'red').save(source, format=fmt, exif=exif)
    contents, content_type, extension, width, height = normalize_image(source.getvalue(), mime)
    assert content_type == mime and extension in ('jpg', 'png', 'webp')
    assert (width, height) == (12, 9)
    with Image.open(BytesIO(contents)) as image:
        assert not image.getexif()
        assert 'xmp' not in image.info


def test_reject_fake_content_size_dimensions_animation(isolated_app, monkeypatch):
    from app.services.image_service import normalize_image, MAX_BYTES, settings
    with pytest.raises(HTTPException) as exc:
        normalize_image(b'<svg>not a jpeg</svg>', 'image/jpeg')
    assert exc.value.status_code == 415
    with pytest.raises(HTTPException) as exc:
        normalize_image(b'x' * (MAX_BYTES + 1), 'image/jpeg')
    assert exc.value.status_code == 413
    source = BytesIO()
    Image.new('RGB', (10, 10)).save(source, format='PNG')
    with pytest.raises(HTTPException) as exc:
        normalize_image(source.getvalue(), 'image/jpeg')
    assert exc.value.status_code == 415
    monkeypatch.setattr(settings, 'IMAGE_MAX_DIMENSION', 5, raising=False)
    with pytest.raises(HTTPException) as exc:
        normalize_image(source.getvalue(), 'image/png')
    assert exc.value.status_code == 413
    monkeypatch.setattr(settings, 'IMAGE_MAX_DIMENSION', 8192)
    monkeypatch.setattr(settings, 'IMAGE_MAX_PIXELS', 50, raising=False)
    with pytest.raises(HTTPException) as exc:
        normalize_image(source.getvalue(), 'image/png')
    assert exc.value.status_code == 413
    monkeypatch.setattr(settings, 'IMAGE_MAX_PIXELS', 20_000_000)
    animated = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(animated, format='WEBP', save_all=True,
        append_images=[Image.new('RGB', (10, 10), 'blue')], duration=100, loop=0)
    with pytest.raises(HTTPException) as exc:
        normalize_image(animated.getvalue(), 'image/webp')
    assert exc.value.status_code == 415


def test_gcs_adapter_is_lazy_and_uses_generation_conditions(monkeypatch):
    spec = importlib.util.spec_from_file_location('image_gcs_adapter_test',
        Path(__file__).parents[2] / 'app/core/gcp_storage.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fake_client = Mock()
    client_constructor = Mock(return_value=fake_client)
    monkeypatch.setattr(module.storage, 'Client', client_constructor)
    adapter = module.GCPStorage()
    client_constructor.assert_not_called()
    blob = fake_client.bucket.return_value.blob.return_value
    blob.generation = 123
    assert adapter.upload_bytes('test-bucket', 'test-object', b'content', 'image/png', 'image-id', 'hash') == 123
    assert blob.upload_from_string.call_args.kwargs['if_generation_match'] == 0
    adapter.delete_generation('test-bucket', 'test-object', 123)
    assert blob.delete.call_args.kwargs['if_generation_match'] == 123
