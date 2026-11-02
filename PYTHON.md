# Python policy for native-integrations

Python files are ignored by default. New production tooling belongs in Buoy or BuoyScript.

The following exact files remain temporary production compatibility exceptions:

| File | Required capability |
| --- | --- |
| `containers/integrations/pdf-patch/build-pdf-package.py` | Builds the explicit native PDF compatibility archive needed by the PDF integration; no native replacement exists yet. |

An exception may be removed after its native replacement passes the corresponding build or runtime checks.
Review additions file by file; directory-wide and wildcard Python exceptions are not allowed.
