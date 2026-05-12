# API Reference

Uploaded GPX files are accepted only through the unified upload pipeline in `backend.app.core.file_uploads`. The pipeline validates filename safety, extension, MIME/signature, file size, and safeuploads audit logging before parsing. Validation failures return an error `message` and may include a safeuploads `code` in the response detail.

::: backend.app.gpx
    handler: python
    options:
      docstring_style: google