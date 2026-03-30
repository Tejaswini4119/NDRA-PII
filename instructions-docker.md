

```bash

# Standard build
docker build -t ndra-stack:allinone .

# If you see temporary DNS/name-resolution failures during pip install,
# build with host networking:
docker build --network=host -t ndra-stack:allinone .

docker run --rm \
  -p 8001:8001 \
  -p 9090:9090 \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/output:/app/output" \
  -v "$PWD/quarantine:/app/quarantine" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/audit:/app/audit" \
  --name ndra-stack \
  ndra-stack:allinone

```

Use this exact run command every time you want ZIP enabled:
```bash
docker run -d --rm \
  -p 8001:8001 -p 9090:9090 \
  -e FREEZE_WORKING_SYSTEM=false \
  -e ENABLE_EXPERIMENTAL_INGESTION=true \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/output:/app/output" \
  -v "$PWD/quarantine:/app/quarantine" \
  -v "$PWD/artifacts:/app/artifacts" \
  -v "$PWD/audit:/app/audit" \
  --name ndra-stack \
  ndra-stack:allinone
```

Container startup uses the packaged entrypoint `ndra_stack.api:app`.