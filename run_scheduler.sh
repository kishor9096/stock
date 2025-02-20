# filepath: /home/ubuntu/LLM/stock/run_max_pain_sensibull.sh
#!/bin/bash
# to fetch latest news on scheduled basis
source /home/ubuntu/LLM/TechunarStocksAI/.venv/bin/activate
/home/ubuntu/LLM/TechunarStocksAI/.venv/bin/python /home/ubuntu/LLM/TechunarStocksAI/ExtractNews.py >> /home/ubuntu/LLM/TechunarStocksAI/ExtractNews_cron_log.txt 2>&1
cd /home/ubuntu/immich/immich-app
docker compose pull && docker compose up -d
docker image prune