# Design Documentation

> Supplementary design notes for [Open Source Dropbox](README.md).

## Contents

- [Assumptions](#assumptions)
- [Requirements](#requirements)
- [Design Approach](#design-approach)
- [Future Work](#future-work)
- [AI Usage](#ai-usage)


## Assumptions

| # | Assumption |
|---|------------|
| 1 | The user and server have already exchanged the shared HMAC secret prior to use. Making the secret exchange out of scope for this project. |
| 2 | Data placed in the source folder is assumed to be non-malicious. Protection against intentionally crafted malicious payloads is out of scope. |

---

## Requirements

| # | Requirement |
|---|-------------|
| 1 | The user shall be able to sync files from a source folder to a destination folder in real time. |
| 2 | The user shall be able to set the destination folder on a different machine. |
| 3 | The user shall be able to set the destination folder on a machine in a different network, requiring a self-signed or CertBot (Let's Encrypt) certificate for HTTPS. |
| 4 | The user shall be able to sync any file type. |
| 5 | The watchdog shall update the local manifest to capture file changes that occurred during offline periods. |
| 6 | The server shall expose an HTTP API that the client uses as its sole communication channel. |
| 7 | The client shall be able to issue upload (PUT) and delete (DELETE) file requests to the server. |
| 8 | The server shall reject any request that does not carry a valid HMAC-SHA256 signature, preventing unauthorised access. |
| 9 | All client–server communication shall be encrypted using TLS to protect data in transit. |

---

## Design Approach

- **Test-driven development (TDD)** — failing unit and integration test cases were written first. Implementation proceeded until all tests passed, ensuring verification for each iteration.

---

## Future Work

- **Accumulative-only sync mode** — add an option to disable the propagation of delete operations, so the destination folder only ever accumulates files and never loses them.
- **Many-to-one sync** — allow multiple client machines to sync into a single server destination.
- **Streaming large files** — replace the current in-memory upload with a streaming approach (`media_type="application/octet-stream"`) so that large files can be transferred without timeout risk or excessive memory consumption.
- **Graphical user interface** — provide a desktop UI with drag-and-drop support so non-technical users can configure and monitor sync without the CLI.

---

## AI Usage

- This project was developed inside **Cursor** using **Claude Sonnet 4.6** as the primary coding assistant, complemented by **LSP**-powered autocompletion.
- AI assistance was used to generate the self-signed TLS certificate logic and to implement the custom FastAPI HMAC-SHA256 request signing middleware.
