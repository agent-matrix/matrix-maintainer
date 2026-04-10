FROM node:20 AS frontend
WORKDIR /app/frontend
COPY apps/frontend/package.json ./package.json
RUN npm install
COPY apps/frontend .
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app

COPY apps/backend ./backend
RUN pip install --no-cache-dir fastapi uvicorn

COPY --from=frontend /app/frontend ./.frontend

EXPOSE 7860

CMD ["bash", "-lc", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & cd .frontend && npx next start -p 7860"]
