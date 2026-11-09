# Oracle Data Transforms Assistant

A small learning project that answers questions about Oracle Data Transforms using passages retrieved from official Oracle documentation. It supports a local Ollama model for development and Amazon Bedrock as a hosted provider.

## Current pipeline

`Oracle documentation → clean text → section-aware chunks → keyword retrieval → selected model → answer with source URLs`

The current retriever uses lexical keyword overlap. It does not use embeddings or a vector database yet. The project contains one ingested Oracle REST API page and its 12 section-aware chunks.

## Requirements

- Python 3.11 or newer
- This project's virtual environment and dependencies (`python -m pip install -e .`)
- For local inference: Docker Desktop and the Ollama container/model described below
- For Bedrock: a configured AWS identity, an available model, and non-zero account/Region quotas

## Run with the local Ollama container

Start the Ollama container from PowerShell. This project uses a temporary container without a persistent model volume, bound only to the local machine:

```powershell
docker run --rm --detach --name odt-ollama --publish 127.0.0.1:11434:11434 ollama/ollama
docker exec -it odt-ollama ollama pull qwen2.5:3b
```

Set these values in the local `.env` file:

```text
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

Then run the assistant from the project folder:

```powershell
& .\.venv\Scripts\python.exe -m odt_assistant "How do I list connections?"
```

The app prints the answer and retrieved source URLs. Ollama model requests run on the local computer; they do not invoke Bedrock. The local RAG path has passed two small sanity checks: it answered “How do I list connections?” from the matching passage, and abstained on an unsupported password-update question. These are not a formal quality evaluation; test more representative questions before making broader quality claims.

## Run with Amazon Bedrock

Set the provider and Bedrock settings in `.env`:

```text
MODEL_PROVIDER=bedrock
AWS_REGION=your-enabled-region
BEDROCK_MODEL_ID=your-available-model-id
AWS_PROFILE=odt-learning
```

Only choose a model after confirming its Region, agreement/access, and applied daily and per-minute quotas. The availability of a model in the Bedrock catalog alone does not guarantee that the account can invoke it. Bedrock inference is usage-billed; keep prompts/output small and inspect the account's credits and billing.

## Disposable-container cleanup

When finished for the day, stop the container:

```powershell
docker stop odt-ollama
```

Because it was started with `--rm`, Docker removes the container and temporary model files when it exits. The Ollama image remains. To remove that image too:

```powershell
docker image rm ollama/ollama:latest
```

With this disposable setup, the model must be downloaded again next session. Do not use broad commands such as `docker system prune --volumes`; they can remove data belonging to other projects.

## Notes on the implementation

- `src/odt_assistant/ingest.py` fetches and cleans the allowlisted Oracle documentation page.
- `src/odt_assistant/chunking.py` creates section-aware passages with source metadata.
- `src/odt_assistant/retrieval.py` ranks candidate chunks using keyword overlap.
- `src/odt_assistant/prompts.py` builds the shared prompt/evidence messages.
- `src/odt_assistant/ollama.py` calls the local Ollama HTTP API.
- `src/odt_assistant/bedrock.py` calls Amazon Bedrock Converse using Boto3.
- `src/odt_assistant/settings.py` selects the provider from `.env`.
- `src/odt_assistant/__main__.py` retrieves evidence, routes to the selected model, and prints the answer and source links.

## Official references

- [Oracle Data Transforms documentation](https://docs.oracle.com/en/database/data-integration/data-transforms/index.html)
- [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [Ollama official Docker image](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image)
- [Ollama Qwen2.5 models](https://ollama.com/library/qwen2.5)
