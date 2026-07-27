# Dependency Inventory

Generated: 2026-07-26

## Python Packages

| Package | Version | License | Purpose | Notes |
|---|---|---|---|---|
| fastapi | 0.139.2 | MIT | Web framework | Pinned |
| uvicorn | 0.51.0 | BSD-3-Clause | ASGI server | Pinned |
| pydantic | 2.13.4 | MIT | Data validation | Pinned |
| python-multipart | 0.0.32 | Apache-2.0 | File upload parsing | Pinned |
| scikit-learn | 1.9.0 | BSD-3-Clause | ML classification | Pinned |
| joblib | 1.5.3 | BSD-3-Clause | Model serialization | Pinned |
| Pillow | 12.3.0 | Historical | Image processing | Pinned |
| pytesseract | 0.3.13 | Apache-2.0 | OCR engine wrapper | Pinned |
| pyjwt | 2.13.0 | MIT | JWT implementation | Pinned |
| psutil | 7.0.0 | BSD-3-Clause | System monitoring | Pinned |

## Test Dependencies

| Package | Version | License | Purpose |
|---|---|---|---|
| pytest | 8.3.2 | MIT | Test framework |
| httpx | 0.27.0 | BSD-3-Clause | HTTP test client |

## System Dependencies

| Dependency | Purpose | Installation |
|---|---|---|
| Tesseract OCR | Text extraction from images | `apt: tesseract-ocr tesseract-ocr-eng` |

## Known Vulnerabilities

None identified at time of writing. All packages are at recent versions.
Regular CVE scanning is recommended as part of CI pipeline.

## License Compatibility

All dependencies use OSI-approved open-source licenses (MIT, BSD,
Apache-2.0). No GPL/AGPL dependencies that would impose
copyleft requirements on the project.
